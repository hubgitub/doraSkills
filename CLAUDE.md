# DoraSkills - DORA Metrics Tracking for Claude Code

## Project Overview

DoraSkills tracks the 4 DORA metrics in real-time via Claude Code hooks and skills:
- **Deployment Frequency** - How often code is deployed to production
- **Lead Time for Changes** - Time from commit to production deployment
- **Change Failure Rate** - % of deployments causing incidents
- **Mean Time to Recovery (MTTR)** - Time to recover from incidents

## Data Storage

All events are stored in `data/dora-events.json`. Event types: `commit`, `deployment`, `incident`, `recovery`.

## Available Skills

| Skill | Description |
|---|---|
| `/dora-init` | Initialize DORA tracking in a project |
| `/dora-status` | Display DORA metrics summary in terminal |
| `/dora-dashboard` | Generate interactive HTML dashboard |
| `/dora-log-deploy <env> <version>` | Manually log a deployment |
| `/dora-log-incident <desc> - <severity>` | Log an incident |
| `/dora-log-recovery [incident_id]` | Log a recovery |

## Automatic Tracking

The PostToolUse hook on Bash (`.claude/hooks/dora-tracker.sh`) automatically detects:
- `git commit` - Logs commit events with hash, message, author, branch, and extracted Jira IDs
- `docker push`, `docker-compose up`, `kubectl apply`, `kubectl rollout`, `helm upgrade` - Logs deployment events

## DORA Classification Thresholds

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| Deployment Frequency | >1/day | 1/day-1/week | 1/week-1/month | <1/month |
| Lead Time for Changes | <1h | 1h-1day | 1day-1week | >1week |
| Change Failure Rate | 0-5% | 5-10% | 10-15% | >15% |
| MTTR | <1h | <1day | <1week | >1week |

## Conventions

- Event IDs follow the format `evt_XXX` (zero-padded, incrementing)
- Timestamps are ISO 8601 in UTC (e.g., `2026-03-05T10:30:00Z`)
- Jira IDs are extracted from commit messages using the regex `[A-Z]+-\d+`
- The dashboard script uses only Python standard library (no pip dependencies)
- MTTR is calculated in minutes and stored in `mttr_minutes`
- Metrics are calculated over a rolling 30-day window
- Lead Time and MTTR use median (not mean) for robustness against outliers
