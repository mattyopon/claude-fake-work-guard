#!/usr/bin/env python3
"""
fake-work-analyzer.py
Analyzes Claude Code transcripts to quantify fake work signals.

Fake work = completion claims without verify evidence within N turns.

Metrics produced:
- completion_claim_count: total "done/完了/✅" utterances
- verified_claims: claims with Bash/Read/Grep tool_use within preceding 10 entries
- unverified_claims: claims without recent verify tool_use
- fake_work_rate: unverified / total
- numeric_discrepancies: "X lines" claims where verify showed different number (heuristic)
- session_level_stats: per-session breakdown

Usage:
  python3 fake-work-analyzer.py [--dir PATH] [--output FORMAT] [--since DATE]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# Loose completion claim patterns (Japanese + English) — catches everything
LOOSE_COMPLETION_PATTERNS = [
    r"完了(?:しました|です)?",
    r"実行済(?:み)?",
    r"実行完了",
    r"作成完了",
    r"更新完了",
    r"実行しました",
    r"作成しました",
    r"更新しました",
    r"削除しました",
    r"追加しました",
    r"設定しました",
    r"修正しました",
    r"\bdone\b",
    r"\bcomplete[d]?\b",
    r"\bfinished\b",
    r"\bexecuted\b",
    r"\bimplemented\b",
    r"✅",
    r"🎉",
    r"\bCOMPLETE\b",
    r"\bDONE\b",
]
LOOSE_COMPLETION_REGEX = re.compile("|".join(LOOSE_COMPLETION_PATTERNS), re.IGNORECASE)

# Strict own-work completion patterns — only self-authored actions
STRICT_COMPLETION_PATTERNS = [
    r"作成しました",
    r"更新しました",
    r"削除しました",
    r"追加しました",
    r"設定しました",
    r"修正しました",
    r"実装しました",
    r"書きました",
    r"書き換え(?:ました|た)",
    r"コミットしました",
    r"commit(?:ted)?",
    r"\bimplemented\b",
    r"\bwrote\b",
    r"\bcreated\b",
    r"\bupdated\b",
    r"\badded\b",
    r"\bdeleted\b",
    r"\bfixed\b",
    r"完了しました",
    r"実行しました",
    r"\brewrote\b",
    r"\brewritten\b",
]
STRICT_COMPLETION_REGEX = re.compile("|".join(STRICT_COMPLETION_PATTERNS), re.IGNORECASE)

# Orchestration noise patterns — sub-agent status reports that look like claims but are not
NOISE_PATTERNS = re.compile(
    r"(researcher-\d+\s*完了|エージェントの?完了を待|agent[- _]?\d+\s*(?:done|完了)|"
    r"\bphase\s*\d.*(?:done|完了)|progress.*(?:done|完了)|"
    r"並列.*完了通知|完了通知を待|まだ\d+体|残り\d+体|残り\d+\s*(?:の|エージェント))",
    re.IGNORECASE,
)

# For backward compatibility
COMPLETION_REGEX = LOOSE_COMPLETION_REGEX

# Verify tool names
VERIFY_TOOLS = {"Bash", "Read", "Grep", "Glob", "Edit", "Write"}

# Numeric discrepancy pattern (e.g., "1178 lines", "10 pages", "3 files")
NUMERIC_CLAIM_REGEX = re.compile(
    r"(\d{1,6})\s*(?:lines?|pages?|files?|行|ページ|件|entries|items|bytes|KB|MB|seconds|秒|minutes|分|hours|時間)",
    re.IGNORECASE,
)

# Window size: how many preceding transcript entries to check for verify activity
VERIFY_LOOKBACK_WINDOW = 15


def extract_text_from_content(content):
    """Extract plain text from message content (list or string)."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts = []
    for c in content:
        if isinstance(c, dict):
            if c.get("type") == "text":
                parts.append(c.get("text", "") or "")
            elif c.get("type") == "tool_result":
                # tool_result may contain additional text
                inner = c.get("content", "")
                if isinstance(inner, str):
                    parts.append(inner)
                elif isinstance(inner, list):
                    for x in inner:
                        if isinstance(x, dict) and x.get("type") == "text":
                            parts.append(x.get("text", "") or "")
    return "\n".join(parts)


def extract_tool_uses(content):
    """Extract tool_use names from content."""
    if not isinstance(content, list):
        return []
    tools = []
    for c in content:
        if isinstance(c, dict) and c.get("type") == "tool_use":
            tools.append(c.get("name", ""))
    return tools


def analyze_transcript(path: Path, strict: bool = False):
    """Analyze a single JSONL transcript file.

    Args:
        path: JSONL transcript file path.
        strict: if True, use STRICT_COMPLETION_REGEX and exclude NOISE_PATTERNS.
                if False, use LOOSE_COMPLETION_REGEX (includes orchestration status).

    Returns dict with per-session metrics.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            entries = [json.loads(line) for line in f if line.strip()]
    except Exception:
        return None

    claim_regex = STRICT_COMPLETION_REGEX if strict else LOOSE_COMPLETION_REGEX

    completion_events = []  # list of (entry_index, text_snippet)
    verify_tool_positions = []  # list of entry_index where verify tool_use occurred
    noise_excluded = 0

    for i, entry in enumerate(entries):
        msg = entry.get("message", entry)
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", [])
        role = msg.get("role") or entry.get("type", "")

        # Only count completion claims in ASSISTANT text (not in user messages or tool results)
        if role == "assistant" or entry.get("type") == "assistant":
            text = extract_text_from_content(content)
            if text and claim_regex.search(text):
                # In strict mode, exclude orchestration noise
                if strict and NOISE_PATTERNS.search(text):
                    noise_excluded += 1
                else:
                    # Extract a short snippet around the first match
                    match = claim_regex.search(text)
                    start = max(0, match.start() - 40)
                    end = min(len(text), match.end() + 40)
                    snippet = text[start:end].replace("\n", " ").strip()
                    completion_events.append((i, snippet))

            tools_used = extract_tool_uses(content)
            for tool_name in tools_used:
                if tool_name in VERIFY_TOOLS:
                    verify_tool_positions.append(i)

    # Classify each completion event as verified / unverified
    verified_count = 0
    unverified_count = 0
    unverified_samples = []
    for event_idx, snippet in completion_events:
        # Check if any verify tool_use occurred in the lookback window
        window_start = event_idx - VERIFY_LOOKBACK_WINDOW
        recent_verify = any(
            window_start <= vp < event_idx for vp in verify_tool_positions
        )
        if recent_verify:
            verified_count += 1
        else:
            unverified_count += 1
            if len(unverified_samples) < 3:
                unverified_samples.append(snippet)

    total_claims = verified_count + unverified_count
    fake_rate = unverified_count / total_claims if total_claims > 0 else 0.0

    # Get session metadata
    try:
        mtime = path.stat().st_mtime
        mdate = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    except Exception:
        mdate = "unknown"

    return {
        "file": str(path),
        "date": mdate,
        "entries": len(entries),
        "total_completion_claims": total_claims,
        "verified": verified_count,
        "unverified": unverified_count,
        "fake_rate": round(fake_rate, 4),
        "verify_tool_uses": len(verify_tool_positions),
        "unverified_samples": unverified_samples,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="/home/user/.claude/projects",
        help="Directory containing transcript JSONL files",
    )
    parser.add_argument(
        "--output",
        choices=["summary", "json", "csv"],
        default="summary",
        help="Output format",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Only analyze files modified since this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--min-claims",
        type=int,
        default=1,
        help="Filter: only include sessions with >= this many completion claims",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Use strict own-work claim regex + exclude orchestration noise",
    )
    args = parser.parse_args()

    transcript_dir = Path(args.dir)
    if not transcript_dir.exists():
        print(f"Error: {transcript_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    since_ts = None
    if args.since:
        since_ts = datetime.strptime(args.since, "%Y-%m-%d").timestamp()

    all_results = []
    skipped = 0
    for path in transcript_dir.rglob("*.jsonl"):
        if since_ts and path.stat().st_mtime < since_ts:
            skipped += 1
            continue
        result = analyze_transcript(path, strict=args.strict)
        if result is None:
            skipped += 1
            continue
        if result["total_completion_claims"] < args.min_claims:
            continue
        all_results.append(result)

    if args.output == "json":
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
        return

    if args.output == "csv":
        print("file,date,entries,claims,verified,unverified,fake_rate,verify_tool_uses")
        for r in all_results:
            print(
                f"{r['file']},{r['date']},{r['entries']},{r['total_completion_claims']},"
                f"{r['verified']},{r['unverified']},{r['fake_rate']},{r['verify_tool_uses']}"
            )
        return

    # Default: summary
    total_sessions = len(all_results)
    total_claims = sum(r["total_completion_claims"] for r in all_results)
    total_verified = sum(r["verified"] for r in all_results)
    total_unverified = sum(r["unverified"] for r in all_results)
    total_entries = sum(r["entries"] for r in all_results)
    total_verify_tools = sum(r["verify_tool_uses"] for r in all_results)

    overall_fake_rate = (
        total_unverified / total_claims if total_claims > 0 else 0.0
    )

    print("=== Fake Work Analyzer Results ===")
    print(f"Directory: {transcript_dir}")
    if args.since:
        print(f"Since: {args.since}")
    print("")
    print(f"Sessions analyzed: {total_sessions}")
    print(f"Sessions skipped (parse error or filter): {skipped}")
    print(f"Total transcript entries: {total_entries:,}")
    print(f"Total verify tool uses (Bash/Read/Grep/Glob): {total_verify_tools:,}")
    print("")
    print("=== Completion Claim Analysis ===")
    print(f"Total completion claims: {total_claims:,}")
    print(f"  - Verified (with Bash/Read/Grep within {VERIFY_LOOKBACK_WINDOW} entries before): {total_verified:,}")
    print(f"  - Unverified (no recent verify): {total_unverified:,}")
    print(f"  - FAKE WORK RATE: {overall_fake_rate:.2%}")
    print("")
    print("=== Per-Session Distribution ===")
    # Sort by fake_rate desc
    sorted_results = sorted(all_results, key=lambda r: (-r["fake_rate"], -r["total_completion_claims"]))
    top_offenders = sorted_results[:10]
    print(f"Top 10 highest-fake-rate sessions (min {args.min_claims} claims):")
    for r in top_offenders:
        print(f"  [{r['date']}] fake={r['fake_rate']:.0%} ({r['unverified']}/{r['total_completion_claims']}) "
              f"{Path(r['file']).name[:20]}")

    # Unverified sample texts
    print("")
    print("=== Sample Unverified Completion Claims (first 5) ===")
    samples_shown = 0
    for r in sorted_results:
        for s in r.get("unverified_samples", []):
            if samples_shown >= 5:
                break
            print(f"  [{r['date']}] ...{s}...")
            samples_shown += 1
        if samples_shown >= 5:
            break


if __name__ == "__main__":
    main()
