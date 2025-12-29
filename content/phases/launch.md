# Phase 4: Agent Launcher & Progress Management

Launches agents, tracks progress, and provides dynamic re-evaluation during sprints.

## When to Use

- After Phase 3 completes (agent prompts ready)
- When checking agent progress
- When re-evaluating and adjusting agent tasks mid-sprint

## Two Main Functions

### Function 1: Initial Launch

Provides ready-to-copy agent prompts from Phase 3.

```python
from workflow.core.workflow_state import WorkflowState

ws = WorkflowState("path/to/project")
state = ws.load()

agents = state.get('agents', [])

print(f"🚀 Launching {len(agents)} Agents\n")
print("Copy each prompt below to a separate Claude chat:\n")
print("="*60)

for agent in agents:
    print(f"\n💬 Agent {agent['id']} - {agent['role']}")
    print(f"\nYou are Agent {agent['id']}: {agent['role']}")
    print(f"Repository: {state.get('repo_url', 'github.com/user/repo')}")
    print(f"Read and follow: AGENT_PROMPTS/{agent['id']}_{role_filename}.md")
    print(f"START NOW")
    print("-"*60)
    
    # Update agent status
    ws.update_agent(agent['id'], status='in_progress')

print("\n➡️  Agents work for 30-60 minutes")
print("➡️  Then ask each: 'Give me a progress report'")
print("➡️  Paste reports back here for evaluation")
```

### Function 2: Progress Check & Re-Evaluation

Analyzes agent progress reports and generates updated prompts.

```
# User pastes 3-4 agent progress reports

Agent 1:
✅ Done: Added database indexes, 600ms → 150ms
🔄 Working on: Connection pooling
⏭️ Next: Cache layer

Agent 2:
✅ Done: Input validation on all endpoints
⚠️ Blocked by: Need database schema for User table
⏭️ Next: XSS prevention

Agent 3:
✅ Done: Unit tests for auth module (80% coverage)
🔄 Working on: Integration tests
⏭️ Next: E2E tests
```

**Analysis:**
```
📊 Progress Analysis:

Agent 1: ✅ Ahead of schedule - adding bonus task
Agent 2: ⚠️ Blocked - redirecting to XSS work  
Agent 3: ✅ Good progress - continue current path
```

**Updated Prompts:**
```
🔄 Updated Prompts for Next 60 Minutes:

💬 Agent 1 (Updated):
Continue backend optimization.
✅ Indexes done, ✅ Connection pooling in progress
NEW: Add Redis cache layer for frequently-accessed data
Files: app/cache.py (create), app/routes.py (modify)
Time: 60 min

💬 Agent 2 (Redirected):
Security hardening - focus on XSS prevention
Skip User table work (unblocked Agent 1 instead)
NEW: Add output escaping and CSP headers
Files: app/templates/*.html, app/middleware.py
Time: 60 min

💬 Agent 3 (Continue):
Testing infrastructure - good progress
Continue with integration tests
Files: tests/integration/test_*.py
Aim for 70% overall coverage
Time: 60 min
```

## Progress Report Template

Provide this template to agents:

```markdown
## Agent [N] - [30/60] min check-in

✅ Done:
- Task 1
- Task 2

🔄 Working on:
- Current task (X% complete)

⚠️ Blocked by:
- [Issue if any, or "None"]

⏭️ Next:
- Planned next task

📎 PR: [link if created]
```

## Re-Evaluation Logic

| Status | Action |
|--------|--------|
| **Ahead** | Add stretch goal |
| **Blocked** | Provide workaround or redirect |
| **Behind** | Simplify scope or extend time |
| **Stuck** | Offer technical guidance |

## Sprint Durations

- **Short sprint**: 30 minutes (quick tasks)
- **Standard sprint**: 60 minutes (most common)
- **Long sprint**: 90 minutes (complex work)

Recommend sprints, don't mandate. Some agents finish early, others need more time.

## When Agents Are Done

```python
# All agents report completion
print("\n✅ All Agents Complete!")
print(" Agent 1: Backend optimization - PR #45")
print(" Agent 2: Security hardening - PR #46")
print(" Agent 3: Testing infrastructure - PR #47")

ws.update_phase(4, "phase_4_complete")
ws.complete_phase(4)

print("\n➡️  Next: Run phase5-integration to merge all PRs")
```

## State Management

Track agent status:
- `not_started` → Initial
- `in_progress` → Working
- `blocked` → Needs help
- `complete` → PR created

Update state after each sprint check-in.

## Key Principles

1. **Sprints not marathons** - 30-60 min check-ins
2. **Dynamic adjustment** - Redirect based on progress
3. **Unblock quickly** - Don't let agents wait
4. **Celebrate wins** - Note completed work
5. **Stay flexible** - Adapt to reality
