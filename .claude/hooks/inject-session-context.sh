#!/usr/bin/env bash
# Edison Hook: inject-session-context
# Type: UserPromptSubmit
# Description: Inject current session context before prompt
# Blocking: NO (always exit 0)

# Fast check: Skip if no Edison session file exists
# Edison creates {project_management_dir}/.session-id when a session is active

SESSION_FILE=".project/.session-id"
if [[ ! -f "$SESSION_FILE" ]]; then
  exit 0  # No Edison session, skip hook
fi

# Resolve config flags with safe defaults





# Build context summary
CONTEXT=""


WORKTREE=$(edison session status --json 2>/dev/null | jq -r '.worktree // empty' 2>/dev/null)
if [[ -n "$WORKTREE" && "$WORKTREE" != "null" ]]; then
  CONTEXT+="Worktree: $WORKTREE"$'\n'
fi



TASK_JSON=$(edison task status --current --json 2>/dev/null || echo '{}')
TASK_STATE=$(echo "$TASK_JSON" | jq -r '.state // empty' 2>/dev/null)
TASK_ID=$(echo "$TASK_JSON" | jq -r '.id // empty' 2>/dev/null)
if [[ -n "$TASK_STATE" && -n "$TASK_ID" ]]; then
  CONTEXT+="Current Task: $TASK_ID (state: $TASK_STATE)"$'\n'
fi



PACKS=$(edison config get packs.active --json 2>/dev/null | jq -r '.[]' 2>/dev/null | tr '\n' ', ' | sed 's/,$//')
if [[ -n "$PACKS" ]]; then
  CONTEXT+="Active Packs: $PACKS"$'\n'
fi


# Inject context if not empty
if [[ -n "$CONTEXT" ]]; then
  echo ""
  echo "## Edison Session Context"
  echo ""
  echo "$CONTEXT"
  echo ""
fi

exit 0