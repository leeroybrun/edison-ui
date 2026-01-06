#!/usr/bin/env bash
# SubagentStop hook logger - captures all data passed to hook

LOG_FILE="/tmp/subagent-stop-log.txt"

{
    echo "=== SUBAGENT STOP HOOK FIRED ==="
    echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)"
    echo "PID: $$"
    echo "PPID: $PPID"
    echo ""

    echo "=== STDIN PAYLOAD (JSON from Claude Code) ==="
    # Claude Code passes JSON payload via stdin
    cat
    echo ""
    echo ""

    echo "=== ENVIRONMENT ==="
    env | grep -iE "claude|agent|task|session|edison" | sort
    echo ""

    echo "---"
    echo ""
} >> "$LOG_FILE"

# Also output so it appears in Claude's context
echo "SubagentStop hook logged to $LOG_FILE"
