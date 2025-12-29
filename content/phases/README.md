# Workflow Phases

These guides provide detailed instructions for each phase of the multi-agent workflow.

## Phases

| Phase | Description | Tool |
|-------|-------------|------|
| **Review** | Analyze codebase, identify improvements, generate agent prompts | `maw_review` |
| **Launch** | Get copy-paste prompts with branch names, launch agents | `maw_launch` |
| **Integrate** | Merge PRs in order, run test plan, resolve conflicts | `maw_integrate` |
| **Decide** | Deploy, iterate, or add features | `maw_decide` |

## Flow

```
idle → review → launch → integrate → decide
          ↑                             ↓
          └─────────────────────────────┘
                    (iterate)
```

## Supporting Tools

| Tool | Purpose |
|------|---------|
| `maw_status` | Show current state, suggest next action |
| `maw_checkin` | Aggregate agent progress reports |
| `maw_learn` | Capture learnings to PROJECT_LEARNINGS.md |
| `maw_patterns` | Search accumulated patterns |
