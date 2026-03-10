# /dora-log-incident

Logs an incident event linked to the most recent deployment.

## Arguments

`$ARGUMENTS` contains the incident description and severity, separated by ` - `.
Examples:
- `/dora-log-incident API down - critical`
- `/dora-log-incident Slow response times - minor`
- `/dora-log-incident Payment processing failed - major`

Severity levels: `critical`, `major`, `minor` (default: `major`)

## Instructions

When the user runs `/dora-log-incident`:

1. Read `data/dora-events.json` from the project root.

2. Parse `$ARGUMENTS`:
   - Split on ` - ` to separate description from severity
   - If no severity provided, default to `major`
   - If no arguments provided, ask the user for a description.

3. Find the most recent `deployment` event to link this incident to. If no deployments exist, still log the incident but with `deployment_id: null`.

4. Generate a new event ID in the format `evt_XXX`.

5. Create a new incident event:
```json
{
  "id": "evt_XXX",
  "type": "incident",
  "timestamp": "<current ISO timestamp>",
  "data": {
    "description": "<parsed description>",
    "severity": "<parsed severity>",
    "deployment_id": "<most recent deployment event ID or null>",
    "resolved": false
  }
}
```

6. Append the event and write back to `data/dora-events.json`.

7. Display a confirmation:
```
Incident logged:
  ID:          evt_XXX
  Description: API down
  Severity:    critical
  Linked to:   evt_002 (production v2.1.0)
  Timestamp:   2026-03-05T12:00:00Z

To log recovery, run: /dora-log-recovery evt_XXX
```
