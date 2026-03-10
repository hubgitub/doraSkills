# /dora-log-deploy

Manually logs a deployment event.

## Arguments

`$ARGUMENTS` contains the deployment description, typically environment and version.
Examples:
- `/dora-log-deploy production v2.1.0`
- `/dora-log-deploy staging v2.1.0-rc1`
- `/dora-log-deploy production`

## Instructions

When the user runs `/dora-log-deploy`:

1. Read `data/dora-events.json` from the project root.

2. Parse `$ARGUMENTS`:
   - First word = environment (default: "production")
   - Second word = version (default: "manual")
   - If no arguments provided, ask the user for at least the environment.

3. Find all `commit` events that are not yet linked to any `deployment` event (by checking `commit_ids` across all existing deployments).

4. Generate a new event ID in the format `evt_XXX` (incrementing from the last event).

5. Create a new deployment event:
```json
{
  "id": "evt_XXX",
  "type": "deployment",
  "timestamp": "<current ISO timestamp>",
  "data": {
    "environment": "<parsed environment>",
    "version": "<parsed version>",
    "commit_ids": ["<list of undeployed commit hashes>"],
    "method": "manual"
  }
}
```

6. Append the event to the events array and write back to `data/dora-events.json`.

7. Display a confirmation:
```
Deployment logged:
  ID:          evt_XXX
  Environment: production
  Version:     v2.1.0
  Commits:     3 commits linked
  Timestamp:   2026-03-05T11:00:00Z
```
