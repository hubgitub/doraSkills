# /dora-status

Displays a summary of the 4 DORA metrics calculated from tracked events.

## Instructions

When the user runs `/dora-status`:

1. Read the file `data/dora-events.json` from the project root.

2. Calculate the 4 DORA metrics over the last 30 days:

### Deployment Frequency
- Count the number of `deployment` events in the last 30 days
- Calculate the average per day
- Classification:
  - **Elite**: Multiple per day (avg > 1/day)
  - **High**: Between daily and weekly (avg >= 1/7 per day)
  - **Medium**: Between weekly and monthly (avg >= 1/30 per day)
  - **Low**: Less than monthly (avg < 1/30 per day)

### Lead Time for Changes
- For each deployment, find its linked commits via `commit_ids`
- Calculate the time between the earliest linked commit and the deployment timestamp
- Take the **median** of all lead times
- Classification:
  - **Elite**: < 1 hour
  - **High**: 1 hour to 1 day
  - **Medium**: 1 day to 1 week
  - **Low**: > 1 week

### Change Failure Rate
- Count the number of `incident` events in the last 30 days
- Divide by the number of `deployment` events × 100
- Classification:
  - **Elite**: 0-5%
  - **High**: 5-10%
  - **Medium**: 10-15%
  - **Low**: > 15%

### Mean Time to Recovery (MTTR)
- For each `recovery` event, use its `mttr_minutes` field
- Take the **median** of all MTTR values
- Classification:
  - **Elite**: < 1 hour (60 min)
  - **High**: < 1 day (1440 min)
  - **Medium**: < 1 week (10080 min)
  - **Low**: > 1 week

3. Display the results in a formatted table like this:

```
╔══════════════════════════════════════════════════════════════════╗
║                    DORA Metrics Summary                         ║
║                    Last 30 days                                 ║
╠══════════════════════════════╦═══════════════╦═══════════════════╣
║ Metric                       ║ Value         ║ Classification    ║
╠══════════════════════════════╬═══════════════╬═══════════════════╣
║ Deployment Frequency         ║ X.X/day       ║ Elite/High/Med/Low║
║ Lead Time for Changes        ║ Xh Xm        ║ Elite/High/Med/Low║
║ Change Failure Rate          ║ X.X%          ║ Elite/High/Med/Low║
║ Mean Time to Recovery        ║ Xh Xm        ║ Elite/High/Med/Low║
╚══════════════════════════════╩═══════════════╩═══════════════════╝
```

4. Also show a brief summary:
   - Total events tracked
   - Number of commits, deployments, incidents, recoveries
   - Any open (unresolved) incidents
