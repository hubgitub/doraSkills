#!/usr/bin/env bash
# DORA Tracker Hook - Intercepts Bash PostToolUse events
# Detects git commits and deployment commands, logs them as DORA events

set -euo pipefail

# Determine project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
DATA_FILE="$PROJECT_DIR/data/dora-events.json"

# Ensure data file exists
if [ ! -f "$DATA_FILE" ]; then
  mkdir -p "$(dirname "$DATA_FILE")"
  echo '{"events":[]}' > "$DATA_FILE"
fi

# Read stdin (hook JSON input)
INPUT=$(cat)

# Extract the command from tool_input.command
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('tool_input', {}).get('command', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# Generate a unique event ID
generate_id() {
  local count
  count=$(python3 -c "
import json
with open('$DATA_FILE') as f:
    data = json.load(f)
print(len(data.get('events', [])) + 1)
" 2>/dev/null || echo "1")
  printf "evt_%03d" "$count"
}

# Get current ISO timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Detect git commit
if echo "$COMMAND" | grep -qE 'git\s+commit'; then
  # Extract info from the git repo
  cd "$PROJECT_DIR"

  HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  MESSAGE=$(git log -1 --pretty=%s 2>/dev/null || echo "unknown")
  AUTHOR=$(git log -1 --pretty=%an 2>/dev/null || echo "unknown")
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

  EVT_ID=$(generate_id)

  # Use environment variables to safely pass data to Python (avoids shell escaping issues)
  DORA_EVT_ID="$EVT_ID" \
  DORA_TIMESTAMP="$TIMESTAMP" \
  DORA_HASH="$HASH" \
  DORA_MESSAGE="$MESSAGE" \
  DORA_AUTHOR="$AUTHOR" \
  DORA_BRANCH="$BRANCH" \
  DORA_DATA_FILE="$DATA_FILE" \
  python3 -c "
import json, os, re

data_file = os.environ['DORA_DATA_FILE']
message = os.environ['DORA_MESSAGE']
jira_ids = re.findall(r'[A-Z]+-\d+', message)

with open(data_file, 'r') as f:
    data = json.load(f)

event = {
    'id': os.environ['DORA_EVT_ID'],
    'type': 'commit',
    'timestamp': os.environ['DORA_TIMESTAMP'],
    'data': {
        'hash': os.environ['DORA_HASH'],
        'message': message,
        'author': os.environ['DORA_AUTHOR'],
        'jira_ids': sorted(set(jira_ids)),
        'branch': os.environ['DORA_BRANCH']
    }
}

data['events'].append(event)

with open(data_file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true

  exit 0
fi

# Detect deployment commands
DEPLOY_METHOD=""
if echo "$COMMAND" | grep -qE 'docker\s+push'; then
  DEPLOY_METHOD="docker-push"
elif echo "$COMMAND" | grep -qE 'docker-compose\s+up|docker\s+compose\s+up'; then
  DEPLOY_METHOD="docker-compose"
elif echo "$COMMAND" | grep -qE 'kubectl\s+apply'; then
  DEPLOY_METHOD="kubectl-apply"
elif echo "$COMMAND" | grep -qE 'kubectl\s+rollout'; then
  DEPLOY_METHOD="kubectl-rollout"
elif echo "$COMMAND" | grep -qE 'helm\s+upgrade'; then
  DEPLOY_METHOD="helm-upgrade"
fi

if [ -n "$DEPLOY_METHOD" ]; then
  EVT_ID=$(generate_id)

  # Find recent undeployed commits
  COMMIT_IDS=$(python3 -c "
import json

with open('$DATA_FILE') as f:
    data = json.load(f)

deployed = set()
for e in data['events']:
    if e['type'] == 'deployment':
        for cid in e.get('data', {}).get('commit_ids', []):
            deployed.add(cid)

undeployed = []
for e in data['events']:
    if e['type'] == 'commit':
        h = e.get('data', {}).get('hash', '')
        if h and h not in deployed:
            undeployed.append(h)

print(json.dumps(undeployed))
" 2>/dev/null || echo "[]")

  python3 -c "
import json

with open('$DATA_FILE', 'r') as f:
    data = json.load(f)

event = {
    'id': '$EVT_ID',
    'type': 'deployment',
    'timestamp': '$TIMESTAMP',
    'data': {
        'environment': 'unknown',
        'version': 'auto-detected',
        'commit_ids': $COMMIT_IDS,
        'method': '$DEPLOY_METHOD'
    }
}

data['events'].append(event)

with open('$DATA_FILE', 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true

  exit 0
fi
