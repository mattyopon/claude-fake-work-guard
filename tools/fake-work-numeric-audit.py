#!/usr/bin/env python3
"""
fake-work-numeric-audit.py

Detects numeric discrepancy fake work: claims like "X lines" / "Y files" / "Z tests"
that don't match the actual verify output nearby in the same session.

Method:
1. Scan each transcript for assistant messages containing numeric claims
   (e.g., "1178 lines", "10 pages", "3 files").
2. Look at Bash/Read/Grep tool_result output within the same session for
   matching file paths or line counts.
3. Flag claims whose numbers do not match observed reality.

This catches the pattern from 2026-04-08 where I claimed "1178 lines"
but the actual file was 1182 lines.

Usage:
  python3 fake-work-numeric-audit.py [--dir PATH] [--since DATE]
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

# Numeric claim patterns: extract (number, unit)
NUMERIC_CLAIM = re.compile(
    r"(\d{1,7})\s*(?:行|lines?|pages?|files?|件|entries|items|tests?|"
    r"errors?|warnings?|commits?|sections?|components?)",
    re.IGNORECASE,
)

# Extract file path mentioned near a numeric claim
PATH_NEAR_NUMBER = re.compile(r"[\w\-./]+\.(?:tex|md|py|js|ts|json|yaml|yml|sh)")

# From Bash/Read/Grep output: common line-count patterns
WC_OUTPUT = re.compile(r"^\s*(\d+)\s+(\S.+?)\s*$")


def extract_text(content):
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
                inner = c.get("content", "")
                if isinstance(inner, str):
                    parts.append(inner)
                elif isinstance(inner, list):
                    for x in inner:
                        if isinstance(x, dict) and x.get("type") == "text":
                            parts.append(x.get("text", "") or "")
    return "\n".join(parts)


def audit_transcript(path):
    try:
        entries = [json.loads(l) for l in open(path) if l.strip()]
    except Exception:
        return None

    # Collect all verify outputs (indexed by position)
    # verify_outputs[i] = stdout text of tool_result at position i
    verify_outputs = {}
    claims = []  # list of (position, number, unit, snippet)

    for i, e in enumerate(entries):
        msg = e.get("message", e)
        if not isinstance(msg, dict):
            continue
        content = msg.get("content", [])

        # tool_result (from user messages after tool_use)
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict) and c.get("type") == "tool_result":
                    inner = c.get("content", "")
                    text = ""
                    if isinstance(inner, str):
                        text = inner
                    elif isinstance(inner, list):
                        for x in inner:
                            if isinstance(x, dict) and x.get("type") == "text":
                                text += x.get("text", "") or ""
                    if text:
                        verify_outputs[i] = text

        # Assistant text — find numeric claims
        role = msg.get("role") or e.get("type", "")
        if role == "assistant" or e.get("type") == "assistant":
            text = extract_text(content)
            if text:
                for m in NUMERIC_CLAIM.finditer(text):
                    number = int(m.group(1))
                    unit_match = m.group(0).lower()
                    # Extract surrounding context (50 chars)
                    start = max(0, m.start() - 60)
                    end = min(len(text), m.end() + 60)
                    snippet = text[start:end].replace("\n", " ").strip()
                    claims.append((i, number, unit_match, snippet))

    # For each claim, look for matching verify output within window
    WINDOW = 20
    discrepancies = []
    matched = 0
    unchecked = 0

    # Normalize the claim unit for matching against verify output
    def normalize_unit(unit_str):
        """Map claim unit strings to a canonical category."""
        u = unit_str.lower()
        if "line" in u or "行" in u:
            return "lines"
        if "page" in u or "ページ" in u:
            return "pages"
        if "file" in u:
            return "files"
        if "件" in u:
            return "count"
        if "test" in u:
            return "tests"
        if "error" in u:
            return "errors"
        if "warning" in u:
            return "warnings"
        if "commit" in u:
            return "commits"
        if "section" in u:
            return "sections"
        if "component" in u:
            return "components"
        if "entries" in u or "items" in u:
            return "items"
        return "unknown"

    # Unit keyword patterns in verify output (to ensure we match the same concept)
    UNIT_CONTEXT_PATTERNS = {
        "lines": re.compile(r"(\d{1,7})\s*(?:lines?|行|行目)", re.IGNORECASE),
        "pages": re.compile(r"(\d{1,5})\s*(?:pages?|ページ)", re.IGNORECASE),
        "files": re.compile(r"(\d{1,5})\s*(?:files?)", re.IGNORECASE),
        "count": re.compile(r"(\d{1,7})\s*件", re.IGNORECASE),
        "tests": re.compile(r"(\d{1,7})\s*(?:tests?|passed|failed)", re.IGNORECASE),
        "errors": re.compile(r"(\d{1,5})\s*errors?", re.IGNORECASE),
        "warnings": re.compile(r"(\d{1,5})\s*warnings?", re.IGNORECASE),
        "commits": re.compile(r"(\d{1,5})\s*commits?", re.IGNORECASE),
        "sections": re.compile(r"(\d{1,5})\s*sections?", re.IGNORECASE),
        "components": re.compile(r"(\d{1,5})\s*components?", re.IGNORECASE),
        "items": re.compile(r"(\d{1,5})\s*(?:entries|items)", re.IGNORECASE),
    }

    for pos, num, unit, snippet in claims:
        # Find verify outputs in window [pos-WINDOW, pos+WINDOW]
        relevant = {i: v for i, v in verify_outputs.items() if pos - WINDOW <= i <= pos + WINDOW}
        if not relevant:
            unchecked += 1
            continue

        claim_unit = normalize_unit(unit)
        if claim_unit == "unknown":
            unchecked += 1
            continue

        unit_regex = UNIT_CONTEXT_PATTERNS.get(claim_unit)
        if unit_regex is None:
            unchecked += 1
            continue

        # Only search for numbers that share the same unit in verify output
        # (eliminates false positives where random nearby numbers matched)
        found_exact = False
        found_close = None  # (observed_num, delta)
        found_any_unit_match = False

        for i, vout in relevant.items():
            for m in unit_regex.finditer(vout):
                observed = int(m.group(1))
                found_any_unit_match = True
                if observed == num:
                    found_exact = True
                    break
                delta = abs(observed - num)
                # Flag close-but-not-equal (within 10% or ±5 absolute)
                if delta > 0 and (delta <= 5 or delta <= max(1, num // 10)):
                    if 10 <= num <= 1_000_000 and 10 <= observed <= 1_000_000:
                        if found_close is None or delta < found_close[1]:
                            found_close = (observed, delta)
            if found_exact:
                break

        if found_exact:
            matched += 1
        elif found_close is not None:
            discrepancies.append({
                "position": pos,
                "claimed": num,
                "claimed_unit": claim_unit,
                "observed": found_close[0],
                "delta": found_close[1],
                "snippet": snippet[:150],
            })
        else:
            # No unit-matching number found — this claim cannot be verified from nearby output
            unchecked += 1

    return {
        "file": str(path),
        "total_numeric_claims": len(claims),
        "matched_exact": matched,
        "unchecked": unchecked,
        "discrepancies": discrepancies,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="/home/user/.claude/projects")
    parser.add_argument("--since", default=None)
    parser.add_argument("--show-samples", type=int, default=10)
    args = parser.parse_args()

    since_ts = None
    if args.since:
        since_ts = datetime.strptime(args.since, "%Y-%m-%d").timestamp()

    total_claims = 0
    total_matched = 0
    total_unchecked = 0
    total_discrepancies = 0
    all_discrepancy_samples = []

    for path in Path(args.dir).rglob("*.jsonl"):
        if since_ts and path.stat().st_mtime < since_ts:
            continue
        r = audit_transcript(path)
        if r is None:
            continue
        total_claims += r["total_numeric_claims"]
        total_matched += r["matched_exact"]
        total_unchecked += r["unchecked"]
        total_discrepancies += len(r["discrepancies"])
        for d in r["discrepancies"][:3]:
            all_discrepancy_samples.append((path.name[:25], d))

    print("=== Numeric Discrepancy Audit ===")
    print(f"Directory: {args.dir}")
    if args.since:
        print(f"Since: {args.since}")
    print()
    print(f"Total numeric claims in assistant text: {total_claims:,}")
    print(f"  - Matched exactly with nearby verify output: {total_matched:,}")
    print(f"  - Close but not matching (DISCREPANCY): {total_discrepancies:,}")
    print(f"  - Unchecked (no comparable verify nearby): {total_unchecked:,}")
    if total_claims > 0:
        check_rate = (total_matched + total_discrepancies) / total_claims
        disc_rate = total_discrepancies / (total_matched + total_discrepancies) if (total_matched + total_discrepancies) > 0 else 0
        print(f"  - Check rate: {check_rate:.2%}")
        print(f"  - Discrepancy rate (among checked): {disc_rate:.2%}")

    print()
    print(f"=== Sample discrepancies (first {args.show_samples}) ===")
    for fname, d in all_discrepancy_samples[: args.show_samples]:
        print(f"  [{fname}] claimed={d['claimed']} observed={d['observed']} Δ={d['delta']}")
        print(f"     \"{d['snippet']}...\"")


if __name__ == "__main__":
    main()
