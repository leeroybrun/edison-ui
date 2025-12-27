#!/usr/bin/env bash
# Edison Hook: compaction-reminder
# Type: PreCompact
# Description: Remind agent to re-read constitution after context compaction
#
# This hook is triggered automatically by Claude Code BEFORE context compaction.
# It reminds the agent to re-read its constitution after compaction completes.

# Fast check: Skip if no Edison session file exists

SESSION_FILE=".project/.session-id"
if [[ ! -f "$SESSION_FILE" ]]; then
  exit 0  # No Edison session, skip hook
fi



# Get session ID (best-effort)
SESSION_ID=$(cat "$SESSION_FILE" 2>/dev/null | head -1 || echo "")

_edison_audit_event() {
  # Fail-open: audit must never break hooks.
  local event="$1"
  shift || true
  edison audit event "$event" \
    --repo-root "$PWD" \
    --session "$SESSION_ID" \
    --field "hook_id=compaction-reminder" \
    --field "hook_type=PreCompact" \
    "$@" 2>/dev/null || true
}

# Configuration from hooks.yaml
ROLE="agents"

MESSAGE_TEMPLATE="⚠️ Context compacted. Re-read your constitution at: constitutions/{ROLE}.md"
NOTIFY="True"

# Expand {ROLE} placeholder in message template
MESSAGE="${MESSAGE_TEMPLATE//\{ROLE\}/$ROLE}"

# Output reminder (Claude Code will inject this into context)
if [ "$NOTIFY" = "true" ] || [ "$NOTIFY" = "True" ]; then
    echo "$MESSAGE"
fi

_edison_audit_event "hook.compaction-reminder" \
  --field "role=$ROLE" \
  --field "source=precompact" \
  --field "notify=$NOTIFY" \
  --field "message=$MESSAGE"

exit 0