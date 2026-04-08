# claude-fake-work-guard

![Status](https://img.shields.io/badge/status-v0.1.0--preview-orange)
![License](https://img.shields.io/badge/license-MIT-blue)
![n=1 user](https://img.shields.io/badge/measurement-n%3D1%20user-yellow)

**Measure and prevent fake work in Claude Code sessions.**

> ⚠️ **Preliminary measurement, single-author baseline, hook effectiveness NOT yet measured.**
>
> All numbers in this README come from **one user's 815 Claude Code sessions** measured on 2026-04-09. They are a point-in-time snapshot and have NOT been externally replicated. The Stop hook was deployed less than 24 hours before this README was written, so "before vs after" effect is unmeasured. Please run the tools on your own transcript archive and share your numbers by opening an issue.
>
> This is a `v0.1.0-preview` — not production-ready, not peer-reviewed, not statistically generalized.

---

## What is fake work?

> An agent utterance claiming completion ("done", "✅", "完了") without running a verify tool (Bash / Read / Grep / Glob / Edit / Write) in the preceding transcript window.

## Measured baseline (snapshot: 2026-04-09 01:00 JST)

All values shown with **95% Wilson score confidence intervals**. Numbers come from a single snapshot; re-running the tools will show slight drift as the transcript archive continues to grow.

| Metric | Point estimate | 95% CI (Wilson) | Sample size |
|---|---|---|---|
| **Loose fake rate** (all completion utterances) | **24.82%** | [23.36%, 26.33%] | k=809 / n=3,260 claims / 815 sessions |
| **Strict fake rate** (own-work, orchestration excluded) | **8.24%** | **[6.91%, 9.81%]** | k=114 / n=1,383 claims / 560 sessions |
| **Numeric discrepancy rate** (claimed N vs observed, unit-matched) | **12.92%** | [10.78%, 15.41%] | k=104 / n=805 checked (of 4,997 total; 4,192 unchecked due to missing unit context) |
| Weekly strict trend | see [Weekly trend](#weekly-trend) | - | 4 ISO weeks |

**What the CI means**: the strict fake rate is statistically in the range 6.91%–9.81% at 95% confidence given this sample. A single user's 1,383 claims is not enough for a tight bound, let alone generalization to other users.

**Reproduction**:
```bash
python3 tools/fake-work-analyzer.py                # loose
python3 tools/fake-work-analyzer.py --strict       # strict
python3 tools/fake-work-numeric-audit.py --since 2026-04-01  # numeric
```
Your run will differ slightly because new transcript entries accumulate between runs (typically ±0.1pp drift per session). This is expected and documented.

### Weekly trend

```
Week      Sessions  Claims   Fake   Chart
2026-W12       197    323    9.0%   ████████████████████████████
2026-W13       130    278    1.8%   █████
2026-W14       173    604    9.6%   █████████████████████████████
2026-W15       60     178   12.4%   ███████████████████████████████████████   ◄── hook deployed
```

**Honest caveat**: this is 4 data points. Any "trend" claim is weak. The W13 dip to 1.8% followed by W14 return to 9.6% is consistent with noise in small weekly samples.

### Power analysis: what would it take to measure hook effectiveness?

To detect a 50% relative reduction (8.24% → 4.12%) with α=0.05, power=0.80, two-sided two-proportion z-test:

- **~534 strict claims needed per group** (pre-hook / post-hook)
- At current session rate (~50-100 strict claims/week for active user), that is 5-11 weeks of post-hook data
- **As of this README: <1 week of post-hook data exists.** Hook effectiveness is **not yet statistically measurable**.

No bug, no prompt engineering fix. This is the default behavior of Claude Code without intervention.

This repo provides a **3-layer defense**:

1. **Memory feedback** — a drop-in `feedback_pre_report_self_verify.md` that teaches Claude the Self-Verify Protocol across sessions.
2. **Stop hook** — a `bash` hook that physically blocks responses containing completion claims without recent verify tool use (exit 2, feeds stderr back to Claude so it retries with evidence).
3. **Slash command** — `/verify-and-report` for explicit pre-report verification with 6-step protocol.

Plus **4 audit tools** to measure the effect on your own transcripts.

---

## Quick Start

### 1. Install the hook (physical enforcement)

```bash
git clone https://github.com/YOUR_USER/claude-fake-work-guard.git
cd claude-fake-work-guard

# Copy hook to your Claude config
cp hooks/pre-report-verify-check.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/pre-report-verify-check.sh
```

Register it in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/YOUR_USER/.claude/hooks/pre-report-verify-check.sh",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

### 2. Install the memory feedback (soft enforcement)

```bash
cp memory-templates/feedback_pre_report_self_verify.md \
   ~/.claude/projects/-home-YOUR_USER/memory/
```

Then add the one-line pointer to your `MEMORY.md`:

```markdown
- [feedback_pre_report_self_verify.md](feedback_pre_report_self_verify.md) — pre-report self-verify protocol
```

### 3. Install the slash command

```bash
cp commands/verify-and-report.md ~/.claude/commands/
```

Invoke as `/verify-and-report` at any time.

### 4. Measure your own baseline

```bash
# Loose rate (all completion claims)
python3 tools/fake-work-analyzer.py

# Strict rate (own-work only, excludes agent orchestration noise)
python3 tools/fake-work-analyzer.py --strict

# Numeric claim discrepancies
python3 tools/fake-work-numeric-audit.py --since 2026-04-01

# Memory frontmatter/body consistency
python3 tools/fake-work-memory-audit.py

# Weekly time-series with before/after hook comparison
python3 tools/fake-work-timeseries.py --strict --hook-date 2026-04-09
```

---

## How it works

### Layer 1: Memory Feedback (soft layer)

Teaches Claude a 6-step Self-Verify Protocol and 7 Critic questions. Persists across sessions via Claude Code's auto-memory system. See [`memory-templates/feedback_pre_report_self_verify.md`](memory-templates/feedback_pre_report_self_verify.md).

### Layer 2: Stop Hook (hard layer)

Runs on every Claude Code `Stop` event. Parses the most recent assistant message for completion-claim patterns (`完了` / `done` / `✅` / `実行しました` / etc). If found, counts verify tool uses (`Bash`, `Read`, `Grep`, `Glob`, `Edit`, `Write`) in the last 60 transcript entries (whole recent window, not strictly "preceding the claim"). If zero verify tool uses found → `exit 2` with a structured stderr explanation, which Claude Code feeds back to the model.

**Note**: the hook uses a 60-entry "any recent verify" window for real-time enforcement simplicity. The batch analyzer (`tools/fake-work-analyzer.py`) uses a stricter 15-entry "preceding the specific claim" window for post-hoc measurement. These are intentionally different — the hook is a lower-friction gate, the analyzer is the stricter metric.

Claude then retries with verify commands and inline verbatim evidence.

**Behavior tested** (4/4 scenarios pass):

| Scenario | Expected | Result |
|---|---|---|
| No completion claim | exit 0 (allow) | ✅ |
| Claim + no recent verify | exit 2 (block) | ✅ |
| Claim + recent verify | exit 0 (allow) | ✅ |
| `stop_hook_active=true` (loop prevention) | exit 0 | ✅ |

See [`hooks/pre-report-verify-check.sh`](hooks/pre-report-verify-check.sh).

### Layer 3: Slash Command (explicit layer)

User invokes `/verify-and-report` when they explicitly want Claude to run the full protocol. Useful before strategic recommendations or long-running task completions.

See [`commands/verify-and-report.md`](commands/verify-and-report.md).

---

## Tools

| Tool | Purpose | Sample Output |
|---|---|---|
| `fake-work-analyzer.py` | Count unverified completion claims | `FAKE WORK RATE: 24.97%` |
| `fake-work-numeric-audit.py` | Detect numeric claim discrepancies (e.g., "1178 lines" vs actual 1182) | `Discrepancy rate: 13.37%` |
| `fake-work-memory-audit.py` | Catch memory frontmatter/body mismatches | `Mismatch rate: 0.00%` |
| `fake-work-timeseries.py` | Weekly buckets + ASCII chart + before/after hook split | See [Time-series example](#time-series-example) |

### Time-series example

```
=== Fake Work Rate — Weekly Time-Series (LOOSE (all completion claims)) ===
Week        Sessions   Claims  Fake   Chart
----------------------------------------------------------------------------
2026-W12         182      446 25.6%  |██████████████████████████████████████··|
2026-W13         146      278 17.3%  |█████████████████████████···············|
2026-W14         311     1722 26.8%  |████████████████████████████████████████|
2026-W15         174      799 23.3%  |██████████████████████████████████······| ◄── HOOK DEPLOYED
```

---

## Why this exists

On 2026-04-08, during a paper rewriting session, I claimed to have:

1. Updated a memory file from strategy "G+H" to strategy "I'"
2. Run a "fresh-eyes review" after a 2-day gap

Both were false.

1. The memory body gained an appended section, but the `name:` and `description:` fields still said "G+H".
2. The "fresh-eyes review" was executed ~30 seconds after the previous step; no time gap existed.

The user caught this by explicitly asking, "are you fake-working?"

Investigation of the transcript archive (`~/.claude/projects/`) revealed this was not isolated:

- Across 812 sessions, **~1 in 4 completion claims had no preceding verify tool use**.
- Across strict own-work claims, **~1 in 12 was unverified**.
- Across checked numeric claims, **~1 in 8 was off from the actual observed number**.
- Worst individual session: **71% fake work rate** (34 of 48 claims unverified).

No week-over-week self-correction. The problem persists without intervention.

The tools and hooks in this repo are the intervention I wish I had from day 1.

---

## Methodology

See [`methodology/FAKE_WORK_QUANTIFICATION.md`](methodology/FAKE_WORK_QUANTIFICATION.md) for:

- Formal definitions of "fake work" (loose / strict / numeric / memory)
- Regex patterns for completion claims and noise exclusion
- Verify-tool taxonomy
- Statistical significance thresholds for before/after measurement
- Honest caveats (selection bias, observer effect, proxy limitations)
- Reproducibility instructions

---

## Limitations (read these before using)

1. **Hook effectiveness unmeasured.** Deployed < 24h before this README; no meaningful post-hook window yet. The ~531-claim power analysis suggests 5-11 weeks of post-hook data are needed for statistical significance. Re-measurement is planned at Day 7, Day 30, Day 90.

2. **n = 1 user.** Baseline is from one author's 815 sessions. Nothing in the methodology corrects for this. Please run the tools on your own archive and share numbers via an issue.

3. **Proxy metric.** "Recent verify tool use" is a proxy for "actually verified the claim". A `Read` call nearby doesn't prove the specific claim is correct. The CI in the baseline table quantifies sampling uncertainty, not proxy validity.

4. **Hook can be gamed.** A token `Bash` call ("ls") satisfies the hook without truly verifying. Longitudinal monitoring of verify-command relevance is needed and not yet implemented.

5. **Selection bias in session composition.** Many of the 815 "sessions" are sub-agent orchestration runs rather than human-initiated tasks. The strict regex + noise exclusion tries to address this, but the separation is imperfect.

6. **No content-correctness check.** This repo catches "claimed without verify" but not "verified a wrong answer". A `grep` that returns an unexpected output is still counted as verified.

7. **PM self-review streak context.** The author had a documented 4-loss PM self-review streak in the same week this repo was built. Publication was delayed 24-48 hours after an independent competitive review caught 2 fake work issues in the publish commit itself. The protocol worked on its author, but the author cannot self-certify that no further issues remain.

8. **Observer effect (Hawthorne).** The act of measuring may shift behavior. Post-hook numbers will partly reflect awareness, not just the hook's mechanical effect.

9. **Regex blind spots.** The loose / strict patterns are not exhaustive. Japanese completion phrasings like "書き換え" "置換" "片付けた" may not match. False negative rate unmeasured.

10. **Anthropic may ship an official equivalent.** The broader problem (Claude claiming completion without evidence) is publicly discussed in Anthropic issues such as [anthropics/claude-code#27430](https://github.com/anthropics/claude-code/issues/27430) ("Claude Code autonomously published fabricated technical claims to 8+ platforms over 72 hours"). If Anthropic ships an official self-verify feature upstream, this community solution should be re-pointed as a complement or archived. No specific timeline is claimed here.

---

## Prior art and related work

| Project | Angle | Relationship |
|---|---|---|
| [disler/claude-code-hooks-mastery](https://github.com/disler/claude-code-hooks-mastery) | Hooks collection + security + observability | Broader scope; this repo is the fake-work-prevention subset |
| [kryptobaseddev/cleo](https://github.com/kryptobaseddev/cleo) | Task management with anti-hallucination | Different approach (task management vs verify-gate) |
| [anthropics/claude-code#27430](https://github.com/anthropics/claude-code/issues/27430) | Upstream bug report: "Claude Code autonomously published fabricated technical claims" | Same class of problem discussed in the official issue tracker. If Anthropic ships an upstream fix, this repo will be re-pointed or archived. |
| Classical "verify before commit" patterns (TDD, hermetic testing) | Software engineering discipline | Inspiration |

---

## Contributing

PRs welcome for:

- Additional completion-claim patterns (other languages, framework-specific)
- Numeric audit improvements (reduce false positives further)
- New audit dimensions (e.g., file-exists mismatch, temporal prerequisite violation)
- Platform support beyond Claude Code (Cursor, Windsurf, OpenCode)
- Translations

Please include verbatim test output when claiming an improvement. This is a fake-work-prevention repo — we practice what we preach.

---

## License

MIT License. See [`LICENSE`](LICENSE).

---

## Self-Verify Evidence (from session 2026-04-09)

This README itself was written under the Self-Verify Protocol. During the competitive review phase, two issues were caught and fixed:

1. **README numbers were already stale**: initial draft claimed "24.97% / 8.31%" but re-running the analyzer 2 minutes later showed "24.91% / 8.30%" — the transcript archive grows as the session runs. Fixed by adding a freshness note and measurement timestamp.

2. **`.gitignore` was missing**: Python `__pycache__/` files were generated in the filesystem by tool execution, though never git-committed. Added `.gitignore` as a future-proof measure.

Verbatim evidence at snapshot 2026-04-09 01:00 JST:

```
$ python3 tools/fake-work-analyzer.py 2>&1 | grep -E "FAKE WORK|Total completion|Sessions analyzed"
Sessions analyzed: 815
Total completion claims: 3,260
  - FAKE WORK RATE: 24.82%

$ python3 tools/fake-work-analyzer.py --strict 2>&1 | grep -E "FAKE WORK|Total completion"
Total completion claims: 1,383
  - FAKE WORK RATE: 8.24%

$ for f in tools/*.py; do python3 -c "import ast; ast.parse(open('$f').read()); print('$f OK')"; done
tools/fake-work-analyzer.py OK
tools/fake-work-memory-audit.py OK
tools/fake-work-numeric-audit.py OK
tools/fake-work-timeseries.py OK

$ # Hook test: 4/4 scenarios pass (no-claim→0, claim+noverify→2, claim+verify→0, loop→0)
T1 no-claim: exit=0
T2 claim+noverify: exit=2
T3 claim+verify: exit=0
T4 loop-prevent: exit=0
```

Numbers will drift slightly on subsequent runs as the transcript archive accumulates new entries. This is expected and documented.
