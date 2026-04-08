# Contributing

Thank you for your interest in improving `claude-fake-work-guard`. This project exists to prevent fake work, so we have a strict rule: **all PR claims must include verbatim evidence**.

## Rules for PRs

### 1. No unverified claims

If your PR description says "reduced false positives by 30%", include the verbatim command and output:

```
$ python3 tools/fake-work-numeric-audit.py --since 2026-04-01
Discrepancy rate (among checked): 13.37%  (was 12.95% before change)
```

### 2. Self-verify before pushing

Before opening a PR, run through the 6-step Self-Verify Protocol from [`commands/verify-and-report.md`](commands/verify-and-report.md):

1. List what you're claiming to change
2. Map each claim to a verify command
3. Run them
4. Critic self-critique (7 questions)
5. Fix gaps before pushing
6. Include verbatim output in the PR description

### 3. Include before/after measurements

If your change affects the core metric (fake work rate), include before/after numbers on the committed transcripts:

```
Before:
  FAKE WORK RATE: 8.31% (strict, 1,372 claims)

After:
  FAKE WORK RATE: 7.89% (strict, 1,372 claims)
```

### 4. Test the hook

If your change touches `hooks/pre-report-verify-check.sh`, run the 4-scenario test:

```bash
# Scenario 1: No completion claim → should allow
echo '{"transcript_path":"/tmp/test1.jsonl","stop_hook_active":false}' | \
  ./hooks/pre-report-verify-check.sh; echo "exit=$?"

# Scenarios 2-4: see README
```

Include all 4 exit codes in your PR.

## What we accept

- Additional completion-claim patterns (other languages, framework-specific)
- Numeric audit false-positive reduction (with measurement)
- New audit dimensions (file-exists, temporal prerequisite, content mismatch)
- Platform support beyond Claude Code (Cursor, Windsurf, OpenCode)
- Documentation translations (Japanese, Chinese, Korean, Spanish)
- Bug fixes (include a regression test if possible)

## What we don't accept

- Claims without evidence
- "Refactors" that don't show before/after numbers
- Stylistic changes that break existing test scenarios
- Dependencies (this project is deliberately minimal — Python stdlib + bash only)

## Code style

- Python: standard library only, no external deps. Python 3.8+ compatible.
- Bash: `set -euo pipefail` at the top of every script.
- Markdown: wrap at 80 columns where practical.

## Governance

This project is maintained by a single person as an open-source side project. Response time to PRs/issues is typically 1-7 days. If you need urgent support, consider forking.

When Anthropic ships the official `VERIFICATION_AGENT` feature, this project will either:
- Be re-pointed as a complement to the official feature, or
- Be archived with a link to the official replacement.
