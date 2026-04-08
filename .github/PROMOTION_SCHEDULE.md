# Promotion Schedule

**Decided**: 2026-04-09 (after fact-audit + competitive review)
**Strategy**: Staged rollout, low-risk → high-risk, with cooling-off windows for fix opportunities.

---

## Stage 1: Twitter / X (TODAY, 2026-04-09)

### Status
☐ Not yet posted

### Action
User posts the 4-tweet thread from `.github/PUBLISH_DRAFTS.md` § "Option B (longer thread)".

### Why first
- **Lowest stakes**: 280 chars × 4, can be deleted, scrutiny is moderate
- **Network reach**: author's followers + retweeters
- **First reaction signal**: gauges interest before escalating
- **Reversible**: can delete tweets if a major issue is found in the next 24-48h

### What user does
1. Open https://twitter.com/compose/tweet
2. Copy Tweet 1 from PUBLISH_DRAFTS.md, post
3. Reply to Tweet 1 with Tweet 2
4. Reply to Tweet 2 with Tweet 3
5. Reply to Tweet 3 with Tweet 4 (contains repo URL)
6. (optional) Pin the thread

### Time required
~5 minutes

### Acceptance criteria
- Each tweet ≤ 280 chars (verified in draft)
- Numbers match repo README current state
- Repo URL works

---

## Stage 2: Hacker News "Show HN" (24-48h after Stage 1)

### Status
☐ Not yet posted
☐ Cooling window: must wait until 2026-04-10 09:00 JST minimum

### Earliest post time
**2026-04-10 09:00 JST** (24h after Twitter)

### Best post time (audience optimization)
**Tuesday or Wednesday 8-11 AM PST** = JST 01:00-04:00 翌日 (or evening of Tue/Wed for Asia author)

### Why wait 24-48h
- **High stakes**: HN frontpage exposes repo to thousands of rigorous reviewers
- **Statistician audience**: Wilson CIs, n=1, proxy validity all get scrutinized
- **Bug-finding window**: Twitter reaction in first 24h often surfaces issues that should be fixed before HN exposure
- **Cannot easily reverse**: HN comments are permanent

### Pre-post checklist (run before submitting)
- [ ] Re-run `python3 tools/fake-work-analyzer.py --strict` and confirm point estimate within ±0.3pp of README
- [ ] Re-run hook 4-scenario test, confirm 4/4 pass
- [ ] Check for new GitHub issues opened in the 24-48h window — if any open, fix or acknowledge first
- [ ] Re-read README "Honest caveats" section as if HN commenter
- [ ] Confirm Twitter thread did not surface a critical bug

### What user does
1. Open https://news.ycombinator.com/submit
2. Title: "Show HN: I measured fake work in 815 Claude Code sessions – 8.24% had no verify"
3. URL: https://github.com/mattyopon/claude-fake-work-guard
4. Text: copy "Hacker News" body from PUBLISH_DRAFTS.md
5. Submit
6. Stay near a browser for 30-60 minutes to respond to early comments

### Acceptance criteria
- Stage 1 (Twitter) did not surface critical bug
- Last `git pull` was after any user-found issue fixes
- Author has 1-2 hours available to monitor comments

---

## Stage 3: awesome-claude-code PR (1 week after Stage 1)

### Status
☐ Not yet submitted
☐ Earliest: 2026-04-16 (1 week after Twitter)

### Why wait 1 week
- **Permanent merge**: hesreallyhim/awesome-claude-code is a curated list with 37.4k stars; merged entries are persistent
- **Need traction evidence**: PR description should reference HN/Twitter discussion to justify inclusion
- **Maintainer reputation**: a hasty PR that turns out buggy reflects on the maintainer too

### Pre-PR checklist
- [ ] Stage 2 (HN) completed without major issue
- [ ] HN comment thread captured (link in PR body as evidence of community validation)
- [ ] Star count > 50 (organic adoption signal)
- [ ] At least 1 issue or PR from external user (engagement signal)
- [ ] No outstanding RED LINE issues

### What user does
1. Fork https://github.com/hesreallyhim/awesome-claude-code
2. Edit README.md, add line under "Hooks" section (or appropriate)
3. Suggested line:
   ```markdown
   - [claude-fake-work-guard](https://github.com/mattyopon/claude-fake-work-guard) — Measure and prevent fake work in Claude Code sessions. Stop hook + 4 audit tools. Baseline: 8.24% strict fake rate (CI [6.91%, 9.81%]) across one user's 815 sessions. MIT.
   ```
4. Open PR with body from `.github/PUBLISH_DRAFTS.md` § "awesome-claude-code PR"
5. Wait for maintainer review (typically 1-7 days)

---

## Stage 4: Optional secondary channels (2-4 weeks after Stage 1)

Conditional on Stage 1-3 traction:

### dev.to / Qiita article
- Trigger: ≥200 stars by Day 14
- Content: long-form narrative, "I measured fake work in my own AI agent"
- Time: 4-8 hours of writing
- Audience: developer blog readers

### LinkedIn post
- Trigger: ≥500 stars or notable HN discussion
- Content: short professional framing, "Why I built fake-work-prevention tooling"
- Audience: enterprise dev / SRE leaders

### Reddit
- Subreddits: r/ClaudeAI, r/LocalLLaMA, r/MachineLearning (Show & Tell)
- Risk: each subreddit has different culture, can backfire
- Trigger: only if HN went well

---

## Re-measurement Schedule (independent of promotion)

These run regardless of promotion outcome:

| Date | Action | Purpose |
|---|---|---|
| 2026-04-16 (Day 7) | `python3 tools/fake-work-timeseries.py --strict --hook-date 2026-04-08` | First post-hook signal |
| 2026-05-09 (Day 30) | Same + write up | Statistical comparison vs baseline |
| 2026-07-08 (Day 90) | Same + decide if hook is durable | Long-term effect |

---

## Stop / Pivot Conditions

**Stop promotion immediately if**:
- A new RED LINE is found in the methodology
- A reproducibility failure is reported (someone runs the tool, gets totally different numbers, and the cause is a bug)
- Anthropic ships an official equivalent feature
- Author's PM self-review streak gets caught in another high-visibility incident

**Pivot to "complement" framing if**:
- Anthropic announces a similar feature in development (not shipped)
- A higher-quality competitor emerges (cleo or new entrant gets 2k+ stars and clearly does the same thing better)

---

## Post-Mortem Schedule

**2026-04-23 (2 weeks after Stage 1)**: Write a brief post-mortem to `docs/postmortem-2026-04.md`:
- Star count
- Fork count
- Issue / PR engagement
- Notable critique threads
- Things that worked
- Things that didn't
- Whether to escalate or wind down
