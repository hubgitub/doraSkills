#!/usr/bin/env bash
# DORA Tracker Hook - Intercepts Bash PostToolUse events
# Detects git commits and deployment commands, logs them as DORA events
# Multi-user: each developer writes to their own file in data/events/

set -euo pipefail

# Determine project directory
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
EVENTS_DIR="$PROJECT_DIR/data/events"

# Identify current user (git user or system user)
GIT_USER=$(cd "$PROJECT_DIR" && git config user.name 2>/dev/null || echo "")
SYSTEM_USER=$(whoami 2>/dev/null || echo "unknown")
AUTHOR="${GIT_USER:-$SYSTEM_USER}"

# Sanitize username for filename (replace spaces/special chars with underscores)
SAFE_USER=$(echo "$AUTHOR" | tr ' /@\\:' '_____' | tr -cd '[:alnum:]_-')
DATA_FILE="$EVENTS_DIR/${SAFE_USER}.json"

# Ensure data directory and file exist
mkdir -p "$EVENTS_DIR"
if [ ! -f "$DATA_FILE" ]; then
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

# Generate a unique event ID: evt_{user}_{timestamp}_{random}
generate_id() {
  local ts random_part
  ts=$(date -u +"%Y%m%d%H%M%S")
  random_part=$(python3 -c "import random, string; print(''.join(random.choices(string.ascii_lowercase + string.digits, k=4)))" 2>/dev/null || echo "0000")
  echo "evt_${SAFE_USER}_${ts}_${random_part}"
}

# Get current ISO timestamp
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Detect git commit
if echo "$COMMAND" | grep -qE 'git\s+commit'; then
  # Extract info from the git repo
  cd "$PROJECT_DIR"

  HASH=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  MESSAGE=$(git log -1 --pretty=%s 2>/dev/null || echo "unknown")
  COMMIT_AUTHOR=$(git log -1 --pretty=%an 2>/dev/null || echo "$AUTHOR")
  BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

  EVT_ID=$(generate_id)

  # Use environment variables to safely pass data to Python (avoids shell escaping issues)
  DORA_EVT_ID="$EVT_ID" \
  DORA_TIMESTAMP="$TIMESTAMP" \
  DORA_HASH="$HASH" \
  DORA_MESSAGE="$MESSAGE" \
  DORA_AUTHOR="$COMMIT_AUTHOR" \
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
    'author': os.environ['DORA_AUTHOR'],
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

  # Find recent undeployed commits across ALL team event files
  COMMIT_IDS=$(python3 -c "
import json, glob, os

events_dir = '$EVENTS_DIR'
all_events = []
for f in glob.glob(os.path.join(events_dir, '*.json')):
    try:
        with open(f) as fh:
            all_events.extend(json.load(fh).get('events', []))
    except:
        pass

deployed = set()
for e in all_events:
    if e['type'] == 'deployment':
        for cid in e.get('data', {}).get('commit_ids', []):
            deployed.add(cid)

undeployed = []
for e in all_events:
    if e['type'] == 'commit':
        h = e.get('data', {}).get('hash', '')
        if h and h not in deployed:
            undeployed.append(h)

print(json.dumps(undeployed))
" 2>/dev/null || echo "[]")

  DORA_EVT_ID="$EVT_ID" \
  DORA_TIMESTAMP="$TIMESTAMP" \
  DORA_AUTHOR="$AUTHOR" \
  DORA_DEPLOY_METHOD="$DEPLOY_METHOD" \
  DORA_DATA_FILE="$DATA_FILE" \
  DORA_COMMIT_IDS="$COMMIT_IDS" \
  python3 -c "
import json, os

data_file = os.environ['DORA_DATA_FILE']
commit_ids = json.loads(os.environ['DORA_COMMIT_IDS'])

with open(data_file, 'r') as f:
    data = json.load(f)

event = {
    'id': os.environ['DORA_EVT_ID'],
    'type': 'deployment',
    'timestamp': os.environ['DORA_TIMESTAMP'],
    'author': os.environ['DORA_AUTHOR'],
    'data': {
        'environment': 'unknown',
        'version': 'auto-detected',
        'commit_ids': commit_ids,
        'method': os.environ['DORA_DEPLOY_METHOD']
    }
}

data['events'].append(event)

with open(data_file, 'w') as f:
    json.dump(data, f, indent=2)
" 2>/dev/null || true

  exit 0
fi
