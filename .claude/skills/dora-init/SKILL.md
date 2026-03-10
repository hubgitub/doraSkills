# /dora-init

Initializes DORA metrics tracking in the current project (with team support).

## Instructions

When the user runs `/dora-init`, perform the following steps:

1. Check if `.claude/hooks/dora-tracker.sh` already exists in the current project. If it does, inform the user that DORA tracking is already set up.

2. If not already set up:
   - Copy the hook script from DoraSkills to the current project:
     - Copy `.claude/hooks/dora-tracker.sh` to the target project's `.claude/hooks/`
     - Make it executable
   - Merge or create `.claude/settings.json` in the target project with the PostToolUse hook configuration for Bash that runs the dora-tracker.sh script (async: true)
   - Create the `data/events/` directory if it doesn't exist
   - Also create a `.gitkeep` file in `data/events/` so the directory is tracked by Git
   - If a legacy `data/dora-events.json` file exists, offer to migrate its events into the new `data/events/` structure (split by author)

3. Display a summary of what was set up and list available commands:

```
DORA Metrics tracking initialized! (Team Mode)

Available commands:
  /dora-status        - View current DORA metrics summary (all team members)
  /dora-dashboard     - Generate an interactive HTML dashboard with team stats
  /dora-log-deploy    - Manually log a deployment (e.g., /dora-log-deploy production v2.1.0)
  /dora-log-incident  - Log an incident (e.g., /dora-log-incident API down - critical)
  /dora-log-recovery  - Log incident recovery (e.g., /dora-log-recovery evt_003)

Team features:
  - Each team member's events are stored in data/events/{username}.json
  - All metrics aggregate data from all team members
  - The dashboard shows per-contributor breakdown
  - Commit and merge safely via Git (no merge conflicts)

Automatic tracking:
  - Git commits are automatically tracked via hooks
  - Docker/K8s deployment commands are automatically detected
  - Jira IDs are extracted from commit messages (e.g., PROJ-123)

Data is stored in: data/events/
```
