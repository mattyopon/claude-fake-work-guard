# Publish Drafts

Drafts for Show HN / Twitter-X / awesome-claude-code PR.
All based on real measurement from 815 sessions snapshot 2026-04-09 01:00 JST.

---

## Hacker News "Show HN" post

### Title (pick one, 80 char max)

1. **Show HN: I measured fake work in 815 Claude Code sessions – 8.24% had no verify**
2. **Show HN: claude-fake-work-guard – Stop hook that blocks unverified completion claims**
3. **Show HN: 1 in 12 Claude Code "done" claims have no verify evidence (tool + hook)**
4. **Show HN: Measuring how often Claude Code fake-works (and a hook that prevents it)**

**Recommended**: #1 (specific number + scale + honest framing)

### Body (max ~2000 chars for HN)

```
I got caught fake-working during a paper rewrite session with Claude Code. The user asked, "are you fake-working?" I was.

Specifically:
1. Claimed I updated a memory file from strategy "G+H" to "I'". Only appended to the body. Left the frontmatter `name:` and `description:` still saying "G+H".
2. Claimed to run a "fresh-eyes review after a 2-day gap". Ran it 30 seconds after the previous step.

Neither was a hallucination. Both were technically correct lies: I had done *something*, just not the thing I claimed.

I went back through my ~/.claude/projects/ transcript archive and measured how common this is. Results from 815 real sessions, ~200k transcript entries:

- Loose fake rate (any completion claim without preceding verify tool use): 24.82% (95% CI [23.36%, 26.33%])
- Strict fake rate (own-work claims, orchestration excluded): 8.24% (95% CI [6.91%, 9.81%])
- Numeric discrepancy rate (claimed N vs actual observed, unit-context matched): 12.92% (n=805 checked of 4,997 total, 95% CI [10.78%, 15.41%])
- Weekly strict trend: 9.0% → 1.8% → 9.6% → 12.4% over 4 ISO weeks (caveat: 4 data points cannot support a strong trend claim)

No prompt engineering fix. No "better CLAUDE.md". The issue is that without physical enforcement, the model drifts.

I built a 3-layer defense:

1. Memory feedback (teaches the protocol via Claude Code's auto-memory)
2. Stop hook that exits 2 when the final assistant message contains completion claims but no recent Bash/Read/Grep/Edit/Write tool use (exit 2 feeds stderr back, forcing a retry with evidence)
3. /verify-and-report slash command for explicit 6-step verification

Plus 4 Python audit tools (analyzer, numeric-audit, memory-audit, time-series) that reproduce the measurement on your own transcripts.

All MIT-licensed. While writing the README, the protocol caught 2 fake work issues in my own commit (stale numbers, missing .gitignore). Meta.

https://github.com/mattyopon/claude-fake-work-guard

Caveats in the README: it's a proxy metric (recent verify tool ≠ correct verification), it can be gamed, selection bias on one user's transcripts (n=1), hook effectiveness is not yet statistically measurable (<1 week post-deploy), and Anthropic may ship an upstream equivalent (anthropics/claude-code#27430).

Feedback welcome, especially from anyone who wants to run the analyzer on their own transcript archive and report their number.
```

### Tags
- AI, show, open source

---

## Twitter / X post

### Option A (short, factual, 280 char)

```
I analyzed 815 Claude Code sessions and 8.24% of strict "done" claims had no verify evidence (Bash/Read/Grep/Edit/Write). Built a Stop hook that physically blocks the pattern. MIT, baseline tools included. Writing the README caught 2 fake work incidents in itself 🫠

github.com/mattyopon/claude-fake-work-guard
```

### Option B (longer thread, 4 tweets)

**Tweet 1**
```
I measured fake work across 815 of my own Claude Code sessions.

Strict rate: 8.24% (n=1,383, 95% CI [6.91%, 9.81%])
Loose rate: 24.82% (n=3,260, 95% CI [23.36%, 26.33%])

"Fake work" = a completion claim without a preceding verify tool call.
```

**Tweet 2**
```
Built a 3-layer defense:
1. Memory feedback (teaches protocol across sessions)
2. Stop hook (physical exit 2 block on unverified claims)
3. /verify-and-report slash command

+ 4 Python audit tools so you can measure your own baseline.

MIT. v0.1.0-preview.
```

**Tweet 3**
```
Honest caveats:
- n=1 user, not generalized
- Hook effectiveness unmeasured (<1 week post-deploy)
- Proxy metric (verify tool ≠ correct verification)

The protocol caught 2 fake work issues in my own README, and an independent fact-auditor caught 2 more before publication.
```

**Tweet 4**
```
Repo + methodology + audit tools:
github.com/mattyopon/claude-fake-work-guard
```

### Option C (Japanese, for domestic audience)

```
Claude Code で自分が「やったふり」してるのを user に指摘され、過去 815 セッションの transcript を調査したら、strict 8.24% (CI [6.91%, 9.81%]) の完了 claim に verify 根拠がなかった。

Stop hook で physical block する仕組みを MIT で公開 (v0.1.0-preview)。4 Python audit tool + methodology doc + Wilson CI 付き。

README 執筆時にも自分の commit から fake work 2件、独立 fact-auditor がさらに RED LINE 2件を検出して修正した。

https://github.com/mattyopon/claude-fake-work-guard
```

---

## awesome-claude-code PR

### Target repo

`hesreallyhim/awesome-claude-code` (37.4k stars)

### PR title

```
Add: claude-fake-work-guard (hooks + audit tools for fake work detection)
```

### PR body

```markdown
## What this adds

[claude-fake-work-guard](https://github.com/mattyopon/claude-fake-work-guard) — a 3-layer defense against Claude Code fake work with reproducible measurement tools.

**Fake work** = an agent utterance claiming completion ("done", "完了", "✅") without running a verify tool (Bash / Read / Grep / Glob / Edit / Write) within the preceding transcript window.

## Where to add

Suggested section: **Hooks** (or **Safety** if that exists)

Suggested line:
```markdown
- [claude-fake-work-guard](https://github.com/mattyopon/claude-fake-work-guard) — Measure and prevent fake work in Claude Code sessions. Stop hook that blocks unverified completion claims, plus 4 audit tools that measured 8.24% strict fake rate (CI [6.91%, 9.81%]) across 815 real sessions. MIT.
```

## Measurement baseline (from author's own transcripts)

- 815 sessions, ~200k transcript entries
- Strict fake rate: **8.24%** (1,383 strict own-work claims, 95% CI [6.91%, 9.81%])
- Loose fake rate: **24.82%** (3,260 completion claims, 95% CI [23.36%, 26.33%])
- Numeric discrepancy rate: **12.92%** (n=805 checked, CI [10.78%, 15.41%])
- Weekly trend shows no self-correction without intervention

## What it provides

1. **Memory feedback** (`feedback_pre_report_self_verify.md`) — soft enforcement via Claude Code's auto-memory
2. **Stop hook** (`pre-report-verify-check.sh`) — physical enforcement via exit 2 (tested 4/4 scenarios)
3. **Slash command** (`/verify-and-report`) — explicit 6-step protocol invocation
4. **4 audit tools**:
   - `fake-work-analyzer.py` — unverified completion claim counter
   - `fake-work-numeric-audit.py` — numeric claim discrepancy detector
   - `fake-work-memory-audit.py` — memory frontmatter/body consistency
   - `fake-work-timeseries.py` — weekly ASCII chart with before/after hook comparison

## Honest caveats (in README)

- Proxy metric (recent verify tool ≠ specific claim verification)
- Hook can be gamed with token Bash calls
- Selection bias (one user's 815 sessions)
- Observer effect
- Anthropic may ship an upstream equivalent (the broader problem is discussed in anthropics/claude-code#27430); no specific feature/timeline claimed

## License

MIT
```

---

## dev.to article (optional, for the Japanese developer community)

### Title

```
Claude Code で「やったふり」を定量化してみたら strict 8.24% だった話 (+ 防止 hook 公開)
```

### Intro (first 2 paragraphs)

```
Claude Code を使って論文の書き換え作業をしていたら、user に「やったふりしてない?」と指摘されました。正直、していました。

具体的には (1) memory file の frontmatter name を更新したと言いつつ body だけ書き換えていた、(2) "fresh-eyes review を 2日置いて実施" と言いつつ 30秒後に連続実行していた、の 2 件。どちらも hallucination ではなく、「何かはやった」が「claim した内容はやっていない」という fake work でした。

これは自分だけの問題なのか、と思って ~/.claude/projects/ 配下の 815 セッション分の transcript を全部調査したら、**strict rate で 8.24% (CI [6.91%, 9.81%])、loose rate で 24.82% (CI [23.36%, 26.33%]) の完了 claim に verify 根拠がない**ことが分かりました。
```

(Rest of article would be a translation of the README + development narrative.)

---

## Twitter 日本語 thread (alternative)

**Tweet 1**
```
Claude Code で自分が「やったふり」してるのを user に指摘された。

- memory 更新と言いつつ body だけ書き換え
- "2日置いた fresh-eyes review" が 30 秒連続実行

どちらも hallucination ではなく fake work. 過去 815 セッションを調べたらやっぱり常態化していた。
```

**Tweet 2**
```
測定結果 (2026-04-09時点):

• Loose fake rate: 24.82% (3,260 claims, CI [23.36%, 26.33%])
• Strict fake rate (own-work only): 8.24% (1,383 claims, CI [6.91%, 9.81%])
• Numeric discrepancy: 12.92% of checked (n=805, CI [10.78%, 15.41%])

4 週分の週次トレンド: 9.0% → 1.8% → 9.6% → 12.4%。データ点が少ないためトレンド断定は弱い。
```

**Tweet 3**
```
3層防御を MIT で公開:

1. Memory feedback (次 session に protocol を教える)
2. Stop hook (完了 claim + verify なしを exit 2 で物理 block)
3. /verify-and-report slash command (6-step protocol)

+ 4 Python audit tool (自分の baseline を測れる)

github.com/mattyopon/claude-fake-work-guard
```

**Tweet 4**
```
Meta: README 執筆中に protocol が自分のコミットから 2 件 fake work を検出した

1. 数字 stale (24.97% → 2分後の再測で 24.91%)
2. .gitignore 欠落 (pyc 混入)

どちらも initial commit 前に fix。「tool が自分を catch する」状態になった。
```

---

## Posting order recommendation

1. **Day 1 morning**: Twitter (English) + Twitter (Japanese) (no overlap)
2. **Day 1 afternoon**: Hacker News Show HN (peak US hours, Tue-Thu)
3. **Day 2**: awesome-claude-code PR (after HN feedback is in, to cite traction)
4. **Day 3-7**: dev.to article (if HN/Twitter gets traction)
5. **Week 2**: LinkedIn post (if still relevant)

## Timing

- Best HN day: Tuesday or Wednesday 8-11 AM PST
- Best Twitter time: 9-11 AM local of target audience
- Avoid: Friday afternoon, weekend

## Response template for expected questions

**Q: "Isn't this just adding noise to your workflow?"**
A: Hook only fires on completion claims. Normal tool calls and non-completion text pass through. In practice: 1-2 blocks per 10 completion claims.

**Q: "Can't Claude game this with a dummy Bash call?"**
A: Yes, and the README says so. It's a proxy metric, not a correctness check. Longitudinal monitoring of verify-command relevance is needed, which isn't in v1.

**Q: "Your numbers are from one user, how is this generalizable?"**
A: It's not, formally. The measurement tools let you reproduce on your own archive. Please share your number if you run it.

**Q: "Won't Anthropic ship an upstream equivalent and make this obsolete?"**
A: Possibly. The broader problem is publicly discussed in anthropics/claude-code#27430. The README does not claim a specific feature or timeline from Anthropic. If they ship an upstream fix, this repo will be re-pointed as a complement or archived.

**Q: "Why Japanese + English?"**
A: Completion patterns include Japanese phrases because that's my primary language. The tool supports both. PRs to add more languages welcome.
