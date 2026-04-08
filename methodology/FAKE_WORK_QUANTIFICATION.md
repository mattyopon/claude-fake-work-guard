# Fake Work Quantification Methodology

**Snapshot**: 2026-04-09 01:00 JST (single author, n=1 user)

All numbers in this document are from one snapshot of one author's transcript archive. Running the tools again will show slight drift as new transcript entries accumulate. See the [Reproducibility](#9-reproducibility) section for exact commands.

---

## 1. Definition of "Fake Work"

**Fake work** = An agent utterance that claims completion of a task without verifiable evidence within a bounded temporal window preceding the claim.

### Primary Formal Definition

Let:
- `C(t)` = completion-claim utterance at transcript position `t`
- `V(t)` = set of verify-type tool uses (`Bash`, `Read`, `Grep`, `Glob`, `Edit`, `Write`) at position `t`
- `W` = lookback window (analyzer: 15 entries preceding the claim; hook: last 60 entries of transcript)

An utterance `C(t)` is **verified** iff:
```
(analyzer) ∃ t' ∈ [t - W, t) such that V(t') ≠ ∅
(hook)     ∃ t' in the last 60 transcript entries such that V(t') ≠ ∅
```

Otherwise, `C(t)` is **unverified** and counted as a fake work candidate.

**Why two windows?** The analyzer enforces strict "verify must precede the specific claim" causality for accurate measurement. The hook uses a wider "any verify in recent 60 entries" window for low-friction real-time enforcement. These are deliberately different tools for different purposes.

---

## 2. Claim Classification (Strict vs Loose)

### Loose claim patterns (LOOSE_COMPLETION_REGEX)
```regex
完了 | 実行済 | 実行しました | 作成しました | 更新しました | 削除しました |
追加しました | 設定しました | 修正しました | done | complete[d]? |
finished | executed | implemented | ✅ | 🎉 | COMPLETE | DONE
```

### Strict own-work patterns (STRICT_COMPLETION_REGEX)
```regex
作成しました | 更新しました | 削除しました | 追加しました | 設定しました |
修正しました | 実装しました | 書きました | 書き換え(ました|た) |
コミットしました | commit(ted)? | implemented | wrote | created |
updated | added | deleted | fixed | 完了しました | 実行しました |
rewrote | rewritten
```

### Orchestration noise exclusion (NOISE_PATTERNS, strict mode only)
```regex
researcher-\d+ 完了 | エージェントの?完了を待 | agent[-_ ]?\d+ (done|完了) |
phase \d.*(done|完了) | 完了通知を待 | まだ\d+体 | 残り\d+体
```

These describe sub-agent orchestration reports, not primary-agent self-claims.

---

## 3. Verify Tools

The following tool-use types count as verify evidence (for both analyzer and hook):
- **Bash**: shell command
- **Read**: file read
- **Grep**: content search
- **Glob**: file discovery
- **Edit**: file modification
- **Write**: file write

**Not counted as verify**:
- `WebSearch`, `WebFetch`: external data, doesn't verify local claims
- `Task` / `Agent`: delegation, sub-agent output must be verified separately
- `TodoWrite`: planning, not verification

---

## 4. Measured Snapshot (2026-04-09 01:00 JST)

### 4.1 Overall counts

| Metric | Value |
|---|---|
| Sessions with ≥1 loose completion claim | 815 |
| Sessions with ≥1 strict own-work claim | 560 |

### 4.2 Completion claim analysis

| Metric | Loose | Strict |
|---|---|---|
| Total claims | **3,260** | **1,383** |
| Verified | 2,451 | 1,269 |
| Unverified | 809 | 114 |
| **Fake work rate** | **24.82%** | **8.24%** |
| 95% Wilson CI | [23.36%, 26.33%] | [6.91%, 9.81%] |

### 4.3 Weekly strict time-series

```
Week      Sessions  Claims  Fake   Chart
2026-W12       197    323    9.0%  ████████████████████████████
2026-W13       130    278    1.8%  █████
2026-W14       173    604    9.6%  █████████████████████████████
2026-W15        60    178   12.4%  ███████████████████████████████████████  ◄── hook deployed
```

**Caveat**: 4 data points cannot support a strong "trend" claim. The W13 dip to 1.8% is consistent with sampling noise in a small weekly sample (n=278).

### 4.4 Numeric discrepancy audit

| Metric | Value |
|---|---|
| Total numeric claims in assistant text | 4,997 |
| Matched exactly with nearby unit-context verify output | 701 |
| Close but not matching (**discrepancy**) | 104 |
| Unchecked (no matching unit in nearby verify) | 4,192 |
| **Check rate** (checked / total) | **16.11%** |
| **Discrepancy rate (among checked)** | **12.92%** |
| 95% Wilson CI (n=805 checked) | [10.78%, 15.41%] |

---

## 5. Secondary Metrics

| Metric | Status | Tool |
|---|---|---|
| Unverified completion rate (loose/strict) | ✅ automated | `fake-work-analyzer.py` |
| Numeric discrepancy rate | ✅ automated | `fake-work-numeric-audit.py` |
| Memory frontmatter/body consistency | ✅ automated | `fake-work-memory-audit.py` |
| Weekly time-series with hook marker | ✅ automated | `fake-work-timeseries.py` |
| Content mismatch rate | ⏳ not automated | requires diff comparison |
| Partial-as-full rate | ⏳ not automated | requires numeric promise parsing |
| Temporal prerequisite violation rate | ⏳ not automated | requires timestamp arithmetic |

---

## 6. How to Measure Hook Effectiveness

### 6.1 Baseline

**8.24% strict (n=1,383 claims, 560 sessions)** at 2026-04-09 01:00 JST.

### 6.2 Treatment window

Hook `pre-report-verify-check.sh` deployed: **2026-04-08 23:30 JST**.

### 6.3 Post-hook measurement protocol

Re-run at three checkpoints:
- **Day 7** (2026-04-16)
- **Day 30** (2026-05-09)
- **Day 90** (2026-07-08)

### 6.4 Power analysis

Two-sided two-proportion z-test, α=0.05, power=0.80:

| Effect size | MDE | n per group |
|---|---|---|
| 50% relative reduction | 8.24% → 4.12% | **~534** |
| 25% relative reduction | 8.24% → 6.18% | ~2,800 |
| 2 pp absolute | 8.24% → 6.24% | ~3,000 |

At ~50-100 strict claims/week for an active user, detecting 50% relative reduction requires **5-11 weeks** of post-hook data.

### 6.5 Current post-hook status

**<1 week of post-hook data exists as of 2026-04-09.** No statistically significant effect claim can be made yet.

### 6.6 Null hypothesis

H0: Hook has no effect on strict fake work rate.
H1: Hook reduces strict fake work rate.
Test: Two-proportion z-test, α=0.05, one-sided.

---

## 7. Publishable Headlines (Ordered by Conservatism)

### Most conservative
> "Across 815 Claude Code sessions (3,260 loose completion claims), the author's strict own-work fake work rate was 8.24% (95% CI [6.91%, 9.81%]) at the 2026-04-09 snapshot. This is a single-user measurement and has not been externally replicated."

### Moderate (recommended)
> "In an analysis of 815 of the author's Claude Code sessions, ~1 in 12 strict own-work completion claims had no preceding verify tool use (8.24%, 95% CI [6.91%, 9.81%]). A 3-layer defense (memory feedback + Stop hook + slash command) and the measurement tools are released together. Hook effectiveness is not yet statistically measurable — <1 week of post-hook data exists."

### What you should NOT claim
- ❌ "Hook reduces fake work by X%" — unmeasured
- ❌ "Generalizable to all Claude Code users" — n=1
- ❌ "Statistically significant trend" — 4 weekly data points
- ❌ "Catches all fake work" — proxy metric, limited regex
- ❌ "Production-ready" — v0.1.0-preview

---

## 8. Limitations and Honest Caveats

### 8.1 Single-user selection bias
Data is from one user's transcripts. Generalization requires community submission.

### 8.2 Proxy validity
The 15-entry lookback (analyzer) and 60-entry scan (hook) are proxies for "actually verified the claim". A `Read` call nearby doesn't prove the specific claim is correct.

### 8.3 Hook gaming
A token `Bash` call ("ls") satisfies the hook without truly verifying. Longitudinal monitoring of verify-command relevance is needed and not yet implemented.

### 8.4 Strict patterns may miss real claims
The strict regex filters orchestration noise but may miss subtly-phrased real claims (e.g., "置換" "片付けた"). Loose is more comprehensive but noisier.

### 8.5 No content-correctness check
Catches "claimed without verify" but not "verified wrong answer".

### 8.6 Low numeric audit check rate
Only ~16% of detected numeric claims are checked (4,192 / 4,997 unchecked due to no comparable unit in nearby verify output). The 12.92% discrepancy applies only to the checked subset.

### 8.7 4-point weekly trend
Any "trend" claim from 4 data points is weak. The W13 dip to 1.8% is consistent with sampling noise.

### 8.8 Observer effect (Hawthorne)
Publishing and measuring may shift behavior. Post-hook numbers will partly reflect awareness, not just the hook's mechanical effect.

### 8.9 PM self-review context
The author had a documented 4-loss PM self-review streak during the week this methodology was developed. Publication was delayed 24-48 hours after an independent fact-auditor caught multiple issues in the initial draft (stale numbers, inconsistent documentation, power analysis error, unreproducible n=778, fabricated "VERIFICATION_AGENT" feature flag citation). Those issues are fixed in this version. Further issues may remain.

---

## 9. Reproducibility

### 9.1 Tools

- `tools/fake-work-analyzer.py` — loose/strict completion + verify counter
- `tools/fake-work-numeric-audit.py` — numeric discrepancy with unit-context matching
- `tools/fake-work-memory-audit.py` — memory frontmatter/body consistency
- `tools/fake-work-timeseries.py` — weekly ASCII chart with before/after marker

### 9.2 Run commands

```bash
# Loose (all completion utterances)
python3 tools/fake-work-analyzer.py --dir ~/.claude/projects

# Strict (own-work only)
python3 tools/fake-work-analyzer.py --dir ~/.claude/projects --strict

# Numeric discrepancy
python3 tools/fake-work-numeric-audit.py --since 2026-04-01

# Memory frontmatter/body
python3 tools/fake-work-memory-audit.py

# Weekly time-series with hook marker
python3 tools/fake-work-timeseries.py --strict --hook-date 2026-04-08
```

### 9.3 Expected variance

Re-running any tool against the same archive will show drift (±0.1-0.5pp) as new transcript entries accumulate. For publication-quality numbers, freeze a snapshot and record the timestamp.

---

## 10. Changelog

- **v0.1.0-preview (2026-04-09)** — Initial public version.
  - Fixed stale numbers: previous draft had 7.55% strict (from pre-release ad-hoc script with different regex) and 28.49% loose (mis-aligned). Current integrated `--strict` flag + noise filter: **8.24% strict / 24.82% loose**.
  - Fixed power analysis: previous draft claimed "~1,500 per window" which was under the standard α=0.05 power=0.80 requirement. Correct value: **~534 per group for 50% reduction** at standard α/power.
  - Fixed numeric audit sample size: previous draft had n=778, which was unreproducible. Current unit-context-matched audit: **n=805 checked**.
  - Removed "Anthropic VERIFICATION_AGENT feature flag" language: the linked GitHub issue (anthropics/claude-code#27430) is a bug report and does not mention any such feature flag. Replaced with an honest reference to the upstream issue.
  - Hook verify tool list aligned with analyzer (Bash/Read/Grep/Glob/Edit/Write).
