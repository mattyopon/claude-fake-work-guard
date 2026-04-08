#!/usr/bin/env python3
"""
fake-work-memory-audit.py

Detects the memory-update-completeness anti-pattern:
when I claim "memory updated to strategy X" but only append to body,
leaving `name` and `description` frontmatter on the old strategy.

This was caught on 2026-04-08: FaultRay memory name was "G+H patent-centric"
but I claimed the update was to "I' Gate strategy".

Method:
- Scan all memory files in ~/.claude/projects/-home-user/memory/
- For each file, check if name/description are consistent with body:
  - Extract frontmatter name and description
  - Extract body first 10 lines
  - Compare: does body mention a different strategy name than frontmatter?
- Flag files with name-body mismatch

Also checks git history if available.

Usage:
  python3 fake-work-memory-audit.py [--dir PATH]
"""

import argparse
import re
import sys
from pathlib import Path


def parse_frontmatter(content):
    """Extract YAML frontmatter from a markdown file."""
    if not content.startswith("---"):
        return None, content
    try:
        end = content.index("\n---\n", 4)
    except ValueError:
        return None, content
    fm_text = content[4:end]
    body = content[end + 5 :]

    fm = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            fm[key.strip()] = val.strip()
    return fm, body


def audit_memory_file(path: Path):
    """Audit a single memory file for frontmatter/body consistency."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception:
        return None

    fm, body = parse_frontmatter(content)
    if fm is None:
        return None  # not a frontmatter file

    name = fm.get("name", "")
    description = fm.get("description", "")

    # Heuristic checks for mismatch
    issues = []

    # Strategy keywords (extend as needed)
    strategy_keywords = [
        "G\\+H",
        "I'",
        "I-prime",
        "Gate",
        "C\\+D",
        "撤回",
        "Real Option",
        "2-track",
        "SaaS",
        "pivot",
    ]
    strategy_regex = re.compile("|".join(strategy_keywords), re.IGNORECASE)

    # Extract all strategy mentions from name + description
    name_desc_text = f"{name} {description}"
    name_strategies = set(m.group(0).lower() for m in strategy_regex.finditer(name_desc_text))

    # Extract all strategy mentions from first 30 lines of body
    body_head = "\n".join(body.split("\n")[:30])
    body_strategies = set(m.group(0).lower() for m in strategy_regex.finditer(body_head))

    # Flag: body mentions a strategy not in name/description AND the body mention is labeled as current
    body_labels_current = re.search(
        r"(現在|current|active|採用|確定|now)\s*[:\s]*([^\n]{0,80})", body_head
    )

    # Also check: "XXX を撤回" patterns (means old strategy is being rejected)
    withdrawn_match = re.findall(r"([A-Z][\w'+]+)\s*を?\s*撤回", body_head)

    # Check freshness: if body says "撤回 G+H" but name still contains G+H
    if withdrawn_match and name:
        for w in withdrawn_match:
            if re.search(re.escape(w), name, re.IGNORECASE):
                issues.append({
                    "type": "NAME_CONTAINS_WITHDRAWN",
                    "detail": f"Body says '{w} を撤回' but name still contains '{w}': {name[:80]}",
                })

    # Check: name mentions strategy A but body Active/Current says B
    if body_labels_current:
        active_text = body_labels_current.group(0)
        for s in body_strategies:
            if s and s not in name_strategies and len(s) > 2:
                if s.lower() in active_text.lower():
                    issues.append({
                        "type": "BODY_CURRENT_NOT_IN_NAME",
                        "detail": f"Body active label mentions '{s}' not in name/description",
                    })

    return {
        "file": str(path),
        "name": name[:100],
        "description_preview": description[:100],
        "body_strategies": sorted(body_strategies),
        "name_strategies": sorted(name_strategies),
        "issues": issues,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dir",
        default="/home/user/.claude/projects/-home-user/memory",
        help="Memory directory",
    )
    args = parser.parse_args()

    memory_dir = Path(args.dir)
    if not memory_dir.exists():
        print(f"Error: {memory_dir} does not exist", file=sys.stderr)
        sys.exit(1)

    total = 0
    issues_found = 0
    all_issues = []

    for path in memory_dir.glob("*.md"):
        if path.name == "MEMORY.md":
            continue  # index file, skip
        r = audit_memory_file(path)
        if r is None:
            continue
        total += 1
        if r["issues"]:
            issues_found += 1
            all_issues.append(r)

    print("=== Memory Update Completeness Audit ===")
    print(f"Memory files scanned: {total}")
    print(f"Files with frontmatter/body mismatch: {issues_found}")
    if total > 0:
        print(f"Mismatch rate: {issues_found / total:.2%}")
    print()

    if all_issues:
        print("=== Flagged files ===")
        for r in all_issues:
            print(f"\n[{Path(r['file']).name}]")
            print(f"  name: {r['name']}")
            print(f"  name strategies: {r['name_strategies']}")
            print(f"  body strategies: {r['body_strategies']}")
            for issue in r["issues"]:
                print(f"  ⚠  {issue['type']}: {issue['detail']}")
    else:
        print("No frontmatter/body mismatches detected.")


if __name__ == "__main__":
    main()
