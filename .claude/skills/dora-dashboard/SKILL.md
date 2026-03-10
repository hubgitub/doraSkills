# /dora-dashboard

Generates an interactive HTML dashboard displaying DORA metrics.

## Instructions

When the user runs `/dora-dashboard`:

1. Run the Python script to generate the dashboard:
```bash
python3 "$CLAUDE_PROJECT_DIR/.claude/skills/dora-dashboard/scripts/generate-dashboard.py" "$CLAUDE_PROJECT_DIR/data/dora-events.json" "$CLAUDE_PROJECT_DIR/data/dora-dashboard.html"
```

2. If the script succeeds, inform the user:
```
Dashboard generated: data/dora-dashboard.html
```

3. Open the dashboard in the default browser:
```bash
open data/dora-dashboard.html
```

4. If there are no events in the data file, still generate the dashboard but note that it will show empty/zero metrics.
