# /dora-log-recovery

Logs a recovery event for an existing incident, calculating MTTR automatically (attributed to the current user).

## Arguments

`$ARGUMENTS` contains the incident ID or description to match.
Examples:
- `/dora-log-recovery evt_alice_20260305120000_m3p9`
- `/dora-log-recovery API down`
- `/dora-log-recovery` (resolves the most recent unresolved incident)

## Instructions

When the user runs `/dora-log-recovery`:

1. Determine the current user:
   - Try `git config user.name` first
   - Fall back to `whoami`
   - Sanitize the username for use as a filename

2. Load **all** event files from `data/events/*.json` to find the incident to resolve (incidents can be logged by any team member).

3. Find the incident to resolve:
   - If `$ARGUMENTS` matches an event ID (e.g., `evt_alice_20260305120000_m3p9`), use that incident
   - If `$ARGUMENTS` is a description, find the most recent unresolved incident matching that description (partial match) across all team files
   - If `$ARGUMENTS` is empty, use the most recent unresolved incident across all team files
   - If no unresolved incidents exist, inform the user

4. Calculate MTTR:
   - `mttr_minutes` = difference in minutes between the current timestamp and the incident's timestamp

5. Generate a new event ID in the format `evt_{username}_{YYYYMMDDHHMMSS}_{4random}`.

6. Create a new recovery event in the **current user's** event file:
```json
{
  "id": "evt_bob_20260305133000_q8w1",
  "type": "recovery",
  "timestamp": "<current ISO timestamp>",
  "author": "<git user name>",
  "data": {
    "incident_id": "<matched incident ID>",
    "mttr_minutes": <calculated MTTR in minutes>
  }
}
```

7. **Also update the original incident event** in **its owner's file**: set `resolved: true` in the incident's data. This means you need to identify which file contains the incident and update that file.

8. Write back all modified files.

9. Display a confirmation:
```
Recovery logged:
  ID:          evt_bob_20260305133000_q8w1
  Author:      Bob
  Incident:    evt_alice_20260305120000_m3p9 (API down) [logged by Alice]
  MTTR:        1h 30m (90 minutes)
  Timestamp:   2026-03-05T13:30:00Z

Incident evt_alice_20260305120000_m3p9 marked as resolved.
```
