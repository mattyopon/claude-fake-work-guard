#!/usr/bin/env python3
"""
fake-work-timeseries.py

Produces a weekly time-series report of fake work rate with an
ASCII chart, suitable for pasting into README / HN posts.

Reads transcripts from ~/.claude/projects/ and outputs:
1. Weekly buckets (ISO week) with claim counts + fake rate
2. ASCII bar chart (10-column width per bar, scaled)
3. Optional hook-deployment marker

Usage:
  python3 fake-work-timeseries.py [--strict] [--hook-date 2026-04-08]
"""

import argparse
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Reuse analyzer logic
sys.path.insert(0, str(Path(__file__).parent))
from importlib import import_module

analyzer_module = import_module("fake-work-analyzer")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="/home/user/.claude/projects")
    parser.add_argument("--strict", action="store_true", help="Use strict own-work regex")
    parser.add_argument(
        "--hook-date",
        default=None,
        help="Mark this date as hook deployment (YYYY-MM-DD)",
    )
    parser.add_argument("--chart-width", type=int, default=40)
    parser.add_argument("--since", default=None)
    args = parser.parse_args()

    since_ts = None
    if args.since:
        since_ts = datetime.strptime(args.since, "%Y-%m-%d").timestamp()

    hook_week = None
    if args.hook_date:
        hd = datetime.strptime(args.hook_date, "%Y-%m-%d")
        iso_year, iso_week, _ = hd.isocalendar()
        hook_week = f"{iso_year}-W{iso_week:02d}"

    # Collect per-week data
    weeks = defaultdict(lambda: {"claims": 0, "verified": 0, "unverified": 0, "sessions": 0})

    for path in Path(args.dir).rglob("*.jsonl"):
        if since_ts and path.stat().st_mtime < since_ts:
            continue
        r = analyzer_module.analyze_transcript(path, strict=args.strict)
        if r is None or r["total_completion_claims"] == 0:
            continue
        try:
            d = datetime.strptime(r["date"], "%Y-%m-%d")
            iso_year, iso_week, _ = d.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
        except ValueError:
            continue
        weeks[key]["claims"] += r["total_completion_claims"]
        weeks[key]["verified"] += r["verified"]
        weeks[key]["unverified"] += r["unverified"]
        weeks[key]["sessions"] += 1

    if not weeks:
        print("No data found.")
        return

    sorted_weeks = sorted(weeks.keys())
    max_rate = max(w["unverified"] / w["claims"] if w["claims"] > 0 else 0 for w in weeks.values())
    if max_rate == 0:
        max_rate = 1.0

    mode = "STRICT (own-work only)" if args.strict else "LOOSE (all completion claims)"
    print(f"=== Fake Work Rate — Weekly Time-Series ({mode}) ===")
    print(f"Directory: {args.dir}")
    if args.since:
        print(f"Since: {args.since}")
    print()
    print(f"{'Week':<10} {'Sessions':>9} {'Claims':>8} {'Fake':>5}   Chart")
    print("-" * (28 + args.chart_width + 8))

    for wk in sorted_weeks:
        v = weeks[wk]
        rate = v["unverified"] / v["claims"] if v["claims"] > 0 else 0.0
        bar_width = int((rate / max_rate) * args.chart_width) if max_rate > 0 else 0
        bar = "█" * bar_width + "·" * (args.chart_width - bar_width)

        marker = ""
        if hook_week and wk == hook_week:
            marker = " ◄── HOOK DEPLOYED"
        elif hook_week and wk > hook_week:
            marker = " (post-hook)"

        print(f"{wk:<10} {v['sessions']:>9} {v['claims']:>8} {rate:>5.1%}  |{bar}|{marker}")

    print()
    # Before/after split if hook-date provided
    if hook_week:
        before = {"claims": 0, "unverified": 0}
        after = {"claims": 0, "unverified": 0}
        for wk in sorted_weeks:
            target = after if wk >= hook_week else before
            target["claims"] += weeks[wk]["claims"]
            target["unverified"] += weeks[wk]["unverified"]
        b_rate = before["unverified"] / before["claims"] if before["claims"] > 0 else 0
        a_rate = after["unverified"] / after["claims"] if after["claims"] > 0 else 0
        print(f"=== Before/After Hook Deployment ({args.hook_date}) ===")
        print(f"Before: {before['claims']:,} claims, {before['unverified']:,} unverified → {b_rate:.2%}")
        print(f"After:  {after['claims']:,} claims, {after['unverified']:,} unverified → {a_rate:.2%}")
        if b_rate > 0:
            reduction = (b_rate - a_rate) / b_rate * 100
            print(f"Relative reduction: {reduction:+.1f}%")
        print()
        print("NOTE: Post-hook data is small until >= 1 week after deployment.")
        print("Run again in 7-30 days for statistical significance.")

    # Overall summary
    total_claims = sum(w["claims"] for w in weeks.values())
    total_unverified = sum(w["unverified"] for w in weeks.values())
    overall_rate = total_unverified / total_claims if total_claims > 0 else 0
    print()
    print("=== Overall ===")
    print(f"Weeks: {len(sorted_weeks)}")
    print(f"Total claims: {total_claims:,}")
    print(f"Total unverified: {total_unverified:,}")
    print(f"Overall fake rate: {overall_rate:.2%}")


if __name__ == "__main__":
    main()
