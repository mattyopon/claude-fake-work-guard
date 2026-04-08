#!/bin/bash
# pre-report-verify-check.sh
# Stop hook that blocks Claude responses claiming completion without recent verify commands.
#
# Rationale: Per feedback_pre_report_self_verify.md, "completion" reports must be
# accompanied by verbatim evidence from Bash/Read/Grep/Glob commands. This hook
# physically enforces that contract by blocking responses that claim completion
# without recent verify activity.
#
# Created: 2026-04-08 after fake work detection in FaultRay v12 rewrite session.
#
# Input (stdin): JSON with session_id, transcript_path, stop_hook_active, hook_event_name
# Exit codes:
#   0 = allow (no completion claim, or verify evidence present)
#   2 = block (completion claim detected but no recent verify)

set -euo pipefail

INPUT="$(cat)"

# Parse transcript_path from hook payload
TRANSCRIPT_PATH="$(echo "$INPUT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("transcript_path",""))' 2>/dev/null || echo "")"

# Guardrail: if we can't find transcript, don't block (fail-open)
if [ -z "$TRANSCRIPT_PATH" ] || [ ! -f "$TRANSCRIPT_PATH" ]; then
    exit 0
fi

# Guardrail: avoid infinite loop if this hook re-triggers itself
STOP_HOOK_ACTIVE="$(echo "$INPUT" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("stop_hook_active",False))' 2>/dev/null || echo "False")"
if [ "$STOP_HOOK_ACTIVE" = "True" ]; then
    exit 0
fi

# Extract the last assistant message text + count recent verify tool uses
RESULT="$(python3 <<PY
import json, sys, re

transcript_path = "$TRANSCRIPT_PATH"

# Load the JSONL transcript
try:
    with open(transcript_path, "r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
except Exception:
    print("SKIP")
    sys.exit(0)

# Walk backwards to find the most recent assistant text block and count verify tool calls since it
last_assistant_text = ""
verify_tool_count = 0
completion_keywords_found = False
scanned = 0

# Scan from the end of transcript backwards
for line in reversed(lines):
    scanned += 1
    if scanned > 60:  # look at last 60 entries only
        break
    try:
        entry = json.loads(line)
    except Exception:
        continue

    # Normalize: some entries are {"type":"assistant","message":{"content":[...]}}
    msg = entry.get("message", entry)
    if not isinstance(msg, dict):
        continue
    content = msg.get("content", [])

    # Assistant text block
    if entry.get("type") == "assistant" or msg.get("role") == "assistant":
        if isinstance(content, list):
            for c in content:
                if isinstance(c, dict):
                    if c.get("type") == "text":
                        # Prepend because we walk backwards
                        last_assistant_text = (c.get("text", "") or "") + last_assistant_text

    # Tool use blocks (from user messages containing tool_result, or assistant tool_use)
    if isinstance(content, list):
        for c in content:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                name = c.get("name", "")
                if name in ("Bash", "Read", "Grep", "Glob"):
                    verify_tool_count += 1

# Detect completion claim keywords in most recent assistant text
# Japanese: 完了 実行済 実行しました 実行完了 done 済みました 作成しました 作成完了 更新完了
# English: done, complete, finished, executed, implemented, ✅
patterns = [
    r"完了",
    r"実行済",
    r"実行完了",
    r"作成完了",
    r"更新完了",
    r"実行しました",
    r"作成しました",
    r"更新しました",
    r"\bdone\b",
    r"\bcomplete[d]?\b",
    r"\bfinished\b",
    r"\bexecuted\b",
    r"\bimplemented\b",
    r"✅",
    r"🎉",
    r"COMPLETE",
    r"DONE",
]
for p in patterns:
    if re.search(p, last_assistant_text, re.IGNORECASE):
        completion_keywords_found = True
        break

if not completion_keywords_found:
    print("NO_CLAIM")
    sys.exit(0)

if verify_tool_count >= 1:
    print(f"OK {verify_tool_count}")
    sys.exit(0)

# Completion claim with zero verify tool calls → block
print("BLOCK")
sys.exit(0)
PY
)"

case "$RESULT" in
    "NO_CLAIM")
        exit 0
        ;;
    OK*)
        exit 0
        ;;
    "BLOCK")
        echo "PRE-REPORT VERIFY CHECK FAILED" >&2
        echo "" >&2
        echo "Your response contains completion claims (完了/実行済/done/✅ etc)" >&2
        echo "but no recent Bash/Read/Grep/Glob verify tool calls were detected." >&2
        echo "" >&2
        echo "Per ~/.claude/projects/-home-user/memory/feedback_pre_report_self_verify.md," >&2
        echo "you MUST run the Self-Verify protocol before reporting completion:" >&2
        echo "  1. List what you claimed to complete" >&2
        echo "  2. Run Bash/Read/Grep commands to verify each claim" >&2
        echo "  3. Self-critique with the 7 questions" >&2
        echo "  4. Include verbatim verify output inline in your report" >&2
        echo "" >&2
        echo "Re-do your response with verify evidence, or rephrase to avoid claiming completion." >&2
        exit 2
        ;;
    *)
        # Unknown result (e.g., SKIP from parse failure) → fail-open
        exit 0
        ;;
esac
