# /dora-log-deploy

Manually logs a deployment event (attributed to the current user).

## Arguments

`$ARGUMENTS` contains the deployment description, typically environment and version.
Examples:
- `/dora-log-deploy production v2.1.0`
- `/dora-log-deploy staging v2.1.0-rc1`
- `/dora-log-deploy production`

## Instructions

When the user runs `/dora-log-deploy`:

1. Determine the current user:
   - Try `git config user.name` first
   - Fall back to `whoami`
   - Sanitize the username for use as a filename (replace spaces and special chars with underscores)

2. Load the user's event file from `data/events/{sanitized_username}.json`. Create it with `{"events": []}` if it doesn't exist.

3. Also load **all** event files from `data/events/*.json` to find undeployed commits across the whole team.

4. Parse `$ARGUMENTS`:
   - First word = environment (default: "production")
   - Second word = version (default: "manual")
   - If no arguments provided, ask the user for at least the environment.

5. Find all `commit` events (across all team files) that are not yet linked to any `deployment` event (by checking `commit_ids` across all existing deployments in all files).

6. Generate a new event ID in the format `evt_{username}_{YYYYMMDDHHMMSS}_{4random}`.

7. Create a new deployment event:
```json
{
  "id": "evt_alice_20260305110000_x7k2",
  "type": "deployment",
  "timestamp": "<current ISO timestamp>",
  "author": "<git user name>",
  "data": {
    "environment": "<parsed environment>",
    "version": "<parsed version>",
    "commit_ids": ["<list of undeployed commit hashes from all team members>"],
    "method": "manual"
  }
}
```

8. Append the event to the **user's** event file and write back.

9. Display a confirmation:
```
Deployment logged:
  ID:          evt_alice_20260305110000_x7k2
  Author:      Alice
  Environment: production
  Version:     v2.1.0
  Commits:     3 commits linked (from 2 contributors)
  Timestamp:   2026-03-05T11:00:00Z
```
