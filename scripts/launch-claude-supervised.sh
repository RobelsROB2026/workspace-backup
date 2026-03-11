#!/bin/bash
# Launches Claude Code in tmux and registers it with the supervisor.
# Usage: ./launch-claude-supervised.sh <session-name> <project-dir> <task-description>

SESSION_NAME=$1
PROJECT_DIR=$(cd "$2" && pwd)
TASK=$3

if [ -z "$SESSION_NAME" ] || [ -z "$PROJECT_DIR" ] || [ -z "$TASK" ]; then
  echo "Usage: $0 <session-name> <project-dir> <task-description>"
  exit 1
fi

STATE_FILE="$HOME/.openclaw/workspace/supervisor-state.json"
SOCKET="/tmp/openclaw-tmux-sockets/openclaw.sock"

# 1. Install hooks into the project if not already there
$HOME/.openclaw/workspace/skills/claude-code-supervisor/scripts/install-hooks.sh "$PROJECT_DIR"

# 2. Register the session
mkdir -p "$(dirname "$STATE_FILE")"
if [ ! -f "$STATE_FILE" ]; then
  echo '{"sessions":{}}' > "$STATE_FILE"
fi

TMP=$(mktemp)
jq --arg name "$SESSION_NAME" \
   --arg sock "$SOCKET" \
   --arg dir "$PROJECT_DIR" \
   --arg task "$TASK" \
   '.sessions[$name] = {
      "socket": $sock,
      "tmuxSession": $name,
      "projectDir": $dir,
      "goal": $task,
      "status": "running"
   }' "$STATE_FILE" > "$TMP" && mv "$TMP" "$STATE_FILE"

# 3. Launch in tmux
mkdir -p "$(dirname "$SOCKET")"
tmux -S "$SOCKET" new-session -d -s "$SESSION_NAME"
sleep 2
tmux -S "$SOCKET" send-keys -t "$SESSION_NAME" "cd \"$PROJECT_DIR\" && /opt/homebrew/bin/claude -p \"$TASK\"" C-m

echo "Started supervised Claude Code session: $SESSION_NAME in $PROJECT_DIR"
