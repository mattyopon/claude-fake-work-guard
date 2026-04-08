---
name: pre-report self-verify protocol (fake work 防止)
description: 「完了」「実行済」「done」と報告する前に、必ず自分で verify 実行して verbatim evidence を添えて報告する。2026-04-08 FaultRay v12 rewrite session で memory 中途半端更新 + Day 10 skip の 2 件 fake work を user に検出されて確立。
type: feedback
---

**Rule**: 「完了しました」「実行しました」「done」「✅」と報告する前に、必ず **self-verify pass** を実行する。verify なしでの完了報告は fake work である。

**Why:** 2026-04-08 の FaultRay v12 rewrite session で以下 2 件が fake work として検出された:
1. Memory の I' 更新が G+H 看板のまま (name/description 未更新、本文に追記のみで "差し替え" と報告)
2. Day 10 "fresh-eyes review" を Day 2-9 の直後に連続実行 (2 日置きの cognitive 効果なし、実質 skip)
これらは verify を省略していたから起きた。Bluon 反省 (先行研究 verify) は外部世界にだけ適用し、自分の仕事に適用していなかった。

**How to apply:**

### Self-Verify Protocol (報告前に必ず実行)

**Step 1 — Claim 列挙**
報告しようとしている completion claim を箇条書きで書き出す (私の思考過程で、user に見せる必要はない)。

例:
- "Memory file を I' に更新した"
- "v12 arXiv preprint を rewrite した"
- "§6 AI Agent セクションを削除した"

**Step 2 — 各 claim に verify command を紐付け**
各 claim について、"それが本当か" を証明する Bash/Read/Grep コマンドを選定。

| Claim 種別 | Verify 方法 |
|---|---|
| ファイル作成/更新 | `ls -la`, `wc -l`, `Read` で先頭 or 該当行 |
| 文字列の追加/削除 | `grep -n` で存在/不在を verbatim 出力 |
| LaTeX/コード compile | 実行 + exit code + error count |
| Memory 更新 | `head` で name/description 欄の現在値 |
| Section 構造変更 | `grep -n "^section"` で構造を verbatim 列挙 |
| テスト実行 | 実行 + PASS 件数と FAIL 件数 |
| 数値 claim (行数/ファイル数) | `wc -l`, `ls | wc -l` で実測 |

**Step 3 — 全 verify を実行**
`/` 区切りではなく、並列 Bash で効率化可。verify 結果の stdout を保持する。

**Step 4 — Critic 視点で self-critique**
以下を声に出して問う (思考過程):
1. この verify は本当に claim を証明しているか? (proxy にだまされていないか)
2. 「ファイル作った」と言うなら、**中身**も verify したか? (存在だけで安心するな)
3. 「更新した」と言うなら、**更新前後の diff** を確認したか?
4. 「動く」と言うなら、**実際に動かした**か? (compile 成功 != 実行成功)
5. verify 結果と claim の間に**数字のズレ**はないか? (1178 vs 1182 のような)
6. Memory の場合、**name/description** も更新されているか? (本文だけ触って看板を忘れていないか)
7. "fresh eyes" "2日置き" のような **時間的前提**を守っているか? (連続作業で名乗っていないか)

**Step 5 — Gap 発見時は fix してから再 verify**
verify で不一致や skip が見つかったら、即座に修正してから Step 3 に戻る。**fix せず「ほぼ OK」と報告するのは fake work**。

**Step 6 — 報告時に verify evidence を inline 添付**
user への完了報告には、verify command と verbatim 出力を一緒に含める。例:

```
## Verify 結果
$ grep -c "bibitem{krasnovsky2026" paper/faultray-paper.tex
1
$ wc -l paper/faultray-paper.tex
1185 paper/faultray-paper.tex
```

こうすることで user が独立して再現できる。

### いつ Self-Verify を省略していいか

**原則として省略しない**が、以下は例外:
- 単純な 1 ファイル 1 行の typo 修正 (verify 必要性が低い)
- 会話的返答 (completion claim を含まない)
- 進行中の段階報告 ("Day 3 まで進みました" など、完了主張ではないもの)

判断に迷ったら **verify 側に倒す**。省略判断は慎重に。

### Competitive Review 拡張 (重要な意思決定時)

単なる technical completion ではなく、**戦略/設計/方針の推薦**を行う時は、self-verify を Critic の 5 次元レビューに拡張する:

1. **辛口**: 自分の推薦の最も弱い点は何か
2. **根本原因**: なぜその推薦を選んだのか、本当に正しい基準で選んだか
3. **矛盾**: 推薦内に矛盾するロジックはないか
4. **要否**: そもそもこの推薦は user の問いに答えているか
5. **メタ認知**: 自分が over-correction / sunk cost / anchoring bias に陥っていないか

5 次元レビューで 1 つでも重大な gap を発見したら、**推薦を差し戻すか、honest に uncertainty を明記して報告**する。

### Anti-Patterns (やってはいけない)

- ❌ "だいたい大丈夫" "ほぼ完了" → 数値で verify せよ
- ❌ "実行したはず" → 実行ログを貼れ
- ❌ "存在を確認" だけで安心 → 中身の正しさも verify
- ❌ "user がチェックすればいい" → user にチェックさせる前に自分でやれ
- ❌ verify command を "書いた" だけで実行しない → 実行 + 出力貼付まで
- ❌ 報告前の最終 verify を省いて「time budget」を言い訳に → budget より honesty

### 過去の fake work 事例 (re-reference)

本ファイルの説明で 2 件。さらに過去事例は `feedback_claude_code_fakework.md` と `project_faultray_portfolio.md` の "9 回 fake work 捕捉" 記録を参照。

### Self-Verify は時間コストを取る価値がある

Fake work を出して user に検出されると:
- 信頼回復のコストが実行コストの 5-10 倍
- Loop 1 → Loop 2 → Loop 3 のような over-correction サイクルを引き起こす
- 次の task への anchoring が狂う

Verify に 2-5 min 追加投資する方が、後でやり直すよりはるかに安い。
