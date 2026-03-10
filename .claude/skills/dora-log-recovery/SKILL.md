# /dora-log-recovery

Logs a recovery event for an existing incident, calculating MTTR automatically.

## Arguments

`$ARGUMENTS` contains the incident ID or description to match.
Examples:
- `/dora-log-recovery evt_003`
- `/dora-log-recovery API down`
- `/dora-log-recovery` (resolves the most recent unresolved incident)

## Instructions

When the user runs `/dora-log-recovery`:

1. Read `data/dora-events.json` from the project root.

2. Find the incident to resolve:
   - If `$ARGUMENTS` matches an event ID (e.g., `evt_003`), use that incident
   - If `$ARGUMENTS` is a description, find the most recent unresolved incident matching that description (partial match)
   - If `$ARGUMENTS` is empty, use the most recent unresolved incident
   - If no unresolved incidents exist, inform the user

3. Calculate MTTR:
   - `mttr_minutes` = difference in minutes between the current timestamp and the incident's timestamp

4. Generate a new event ID in the format `evt_XXX`.

5. Create a new recovery event:
```json
{
  "id": "evt_XXX",
  "type": "recovery",
  "timestamp": "<current ISO timestamp>",
  "data": {
    "incident_id": "<matched incident ID>",
    "mttr_minutes": <calculated MTTR in minutes>
  }
}
```

6. **Also update the original incident event**: set `resolved: true` in the incident's data.

7. Write back to `data/dora-events.json`.

8. Display a confirmation:
```
Recovery logged:
  ID:          evt_XXX
  Incident:    evt_003 (API down)
  MTTR:        1h 30m (90 minutes)
  Timestamp:   2026-03-05T13:30:00Z

Incident evt_003 marked as resolved.
```
