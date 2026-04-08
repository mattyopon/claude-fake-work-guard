---
description: 完了報告前の必須Self-Verifyプロトコルを実行する
---

# /verify-and-report — Pre-Report Self-Verify Protocol

Before reporting ANY completion claim in this conversation, execute the full
Self-Verify protocol from `~/.claude/projects/-home-user/memory/feedback_pre_report_self_verify.md`.

**This is not optional. Do not skip any step.**

---

## Step 1: Claim 列挙 (Write Down What You Are About To Report)

Write out every completion claim you intend to make in the upcoming report.
Example:

```
Claims to verify:
- "v12 paper §6 AI Agent section を削除した"
- "新規 bibitem 9件を追加した"
- "Memory の I' Gate 戦略に更新した"
- "LaTeX compile が errors 0 で 10ページ PDF を生成した"
```

One claim per line. Do not aggregate.

---

## Step 2: Verify Command を各 Claim に紐付け

For each claim, pick a concrete Bash/Read/Grep/Glob command that *proves* it.

| Claim 種別 | Verify コマンド例 |
|---|---|
| File created/updated | `ls -la path` + `wc -l path` |
| String added/removed | `grep -n pattern path` (verbatim 出力) |
| LaTeX/code compile | 実行 + exit code + error count |
| Memory updated | `head -5 memory.md` で name/description 欄 |
| Section 構造変更 | `grep -n '^section' file` |
| Test execution | テストランナー実行 + PASS/FAIL 件数 |
| 数値 claim (行数/件数) | `wc -l` / `ls \| wc -l` |

---

## Step 3: 全 Verify を並列実行

Run all verify commands. Capture verbatim stdout.

Do NOT trust intermediate state — every claim gets its own verify command,
even if several share a file.

---

## Step 4: Critic Self-Critique (7 Questions)

Ask yourself, out loud in your reasoning:

1. **Proxy 検査**: Does this verify *actually* prove the claim, or is it just a proxy?
   (e.g., "file exists" does NOT prove "file content is correct")
2. **Content 検査**: For "created X", did I verify the *content*, not just existence?
3. **Diff 検査**: For "updated X", did I check before/after diff (or quote the new content)?
4. **Runtime 検査**: For "works", did I actually *run* it? (compile success ≠ runtime success)
5. **Numeric discrepancy**: Does reported number match verified number? (1178 vs 1182)
6. **Memory completeness**: For memory updates, did I update `name`/`description`,
   not just the body? (looking for the "updated body only" anti-pattern)
7. **Temporal prerequisite**: For "fresh eyes" / "2日置き" / "cooldown" claims,
   did I honor the time gap? (no consecutive execution under a "fresh" label)

If ANY question yields a concern, go to Step 5.

---

## Step 5: Gap Found → Fix → Re-Verify

Found a gap? Fix it *right now* and run verify again. Do NOT report
"ほぼ OK" or "概ね完了". That is fake work.

Only proceed to Step 6 when all 6 verify questions pass.

---

## Step 6: Report with Verbatim Evidence Inline

Your completion report MUST include the verify command AND its verbatim output.
Format example:

```
## Verify 結果

### Claim 1: §6 AI Agent section 削除
$ grep -n "^\\section" paper/faultray-paper.tex
84:\section{Introduction}
151:\section{Related Work}
292:\section{System Architecture}
374:\section{Cascade Engine --- Formal Specification}
578:\section{$N$-Layer Availability Limit Model}
738:\section{Evaluation}
...
(No §6 AI Agent section) ✅

### Claim 2: 新規 bibitem 9件追加
$ grep -c "bibitem{krasnovsky2026\|bibitem{casformer2025\|..." paper/faultray-paper.tex
9 ✅
```

Do not summarize the evidence. Paste the verbatim output.

---

## 5-Dimensional Critic Extension (Strategic Recommendations Only)

If this is a *strategic / design / recommendation* report (not just a technical
task completion), extend Step 4 with the 5-dimensional review:

1. **辛口**: What is the weakest point of my recommendation?
2. **根本原因**: Why did I pick this option? Is the selection criterion correct?
3. **矛盾**: Are there internal contradictions in my reasoning?
4. **要否**: Does this recommendation actually answer the user's question?
5. **メタ認知**: Am I in an over-correction / sunk cost / anchoring bias loop?

If any dimension surfaces a concern, document it honestly in the report rather
than hiding it.

---

## Anti-Patterns (ABSOLUTELY FORBIDDEN)

- ❌ "だいたい大丈夫" → 数値で verify
- ❌ "実行したはず" → ログを貼れ
- ❌ "存在確認" 止まり → 中身も verify
- ❌ "user が確認すればいい" → 自分で先にやれ
- ❌ verify command を書いただけで実行しない
- ❌ "budget 超える" を言い訳に verify skip

---

## Why This Exists

Created 2026-04-08 after FaultRay v12 rewrite session in which 2 fake work
incidents were detected:

1. Memory "I' update" claim had only appended lines — `name`/`description`
   remained on the previous G+H version.
2. "Day 10 fresh-eyes review" was executed consecutively after Day 2-9
   without any time gap, then reported as complete.

Both were caught only when the user explicitly asked "やったふりしてないか check".

This command exists to make that check the default, not the exception.

Reference: `~/.claude/projects/-home-user/memory/feedback_pre_report_self_verify.md`
