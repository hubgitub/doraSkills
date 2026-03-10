# /dora-log-incident

Logs an incident event linked to the most recent deployment (attributed to the current user).

## Arguments

`$ARGUMENTS` contains the incident description and severity, separated by ` - `.
Examples:
- `/dora-log-incident API down - critical`
- `/dora-log-incident Slow response times - minor`
- `/dora-log-incident Payment processing failed - major`

Severity levels: `critical`, `major`, `minor` (default: `major`)

## Instructions

When the user runs `/dora-log-incident`:

1. Determine the current user:
   - Try `git config user.name` first
   - Fall back to `whoami`
   - Sanitize the username for use as a filename

2. Load the user's event file from `data/events/{sanitized_username}.json`. Create it with `{"events": []}` if it doesn't exist.

3. Also load **all** event files from `data/events/*.json` to find the most recent deployment across the whole team.

4. Parse `$ARGUMENTS`:
   - Split on ` - ` to separate description from severity
   - If no severity provided, default to `major`
   - If no arguments provided, ask the user for a description.

5. Find the most recent `deployment` event across all team files to link this incident to. If no deployments exist, still log the incident but with `deployment_id: null`.

6. Generate a new event ID in the format `evt_{username}_{YYYYMMDDHHMMSS}_{4random}`.

7. Create a new incident event:
```json
{
  "id": "evt_alice_20260305120000_m3p9",
  "type": "incident",
  "timestamp": "<current ISO timestamp>",
  "author": "<git user name>",
  "data": {
    "description": "<parsed description>",
    "severity": "<parsed severity>",
    "deployment_id": "<most recent deployment event ID or null>",
    "resolved": false
  }
}
```

8. Append the event to the **user's** event file and write back.

9. Display a confirmation:
```
Incident logged:
  ID:          evt_alice_20260305120000_m3p9
  Author:      Alice
  Description: API down
  Severity:    critical
  Linked to:   evt_bob_20260305110000_x7k2 (production v2.1.0)
  Timestamp:   2026-03-05T12:00:00Z

To log recovery, run: /dora-log-recovery evt_alice_20260305120000_m3p9
```
