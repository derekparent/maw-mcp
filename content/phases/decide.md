# Phase 6: Iteration Decision

Analyzes current state and recommends deploy, iterate, or add features.

## When to Use

- After Phase 5 (integration complete)
- After Phase 5.5 (audit complete)
- When deciding next steps
- End of each iteration

## What This Phase Does

1. Reviews what was accomplished
2. Checks for remaining issues
3. Evaluates quality and completeness
4. Provides clear recommendation
5. If iterating: kicks off Phase 3 for next round

## Decision Framework

```python
from workflow.core.workflow_state import WorkflowState

ws = WorkflowState("path/to/project")
state = ws.load()

print("🎯 Iteration Decision Analysis\n")

# Analyze completed work
completed_agents = [a for a in state['agents'] if a['status'] == 'complete']
print(f"✅ Completed: {len(completed_agents)} improvements")

# Check quality indicators
quality_score = 8  # Based on audit
deployment_ready = True  # Based on tests/issues

print(f"\n📊 Quality Score: {quality_score}/10")
print(f"🚀 Deployment Ready: {'Yes' if deployment_ready else 'No'}")
```

## Decision Criteria

### ✅ Deploy When:
- All tests passing
- No critical issues
- Quality score ≥7/10
- Audit passed (if ran Phase 5.5)
- User requirements met

### ⚠️ Fix Then Deploy When:
- Minor bugs found
- Security issues present
- Performance problems
- Test gaps identified

### 🔄 Iterate (Phase 3 Again) When:
- Quality score <7/10
- Major refactoring needed
- Architecture issues
- Technical debt high
- More improvements identified

### ➕ Add Features When:
- Core functionality solid
- Quality high
- User requests features
- Ready to expand scope

## Starting New Iteration

If recommending iteration:

```python
# Increment iteration counter
state['iteration'] += 1

# Reset phase to 3
state['phase'] = 3
state['status'] = 'starting_iteration_' + str(state['iteration'])

# Clear agent list for fresh start
state['agents'] = []

ws.save(state)

print(f"\n🔄 Starting Iteration {state['iteration']}")
print("\n➡️  Next: Run phase3-codex-review")
print("   This will identify the next set of improvements")
```

## Deployment Guidance

If recommending deploy:

```bash
# Staging deployment
git checkout dev
git pull origin dev
# Deploy to staging environment
# Run smoke tests
# Monitor for issues

# Production deployment (after staging verified)
git checkout main
git merge dev
git push origin main
# Deploy to production
# Monitor closely
# Have rollback plan ready
```

## Iteration History Tracking

Track iterations in state:

```json
{
  "iteration": 2,
  "iteration_history": [
    {
      "iteration": 1,
      "improvements": 4,
      "completed_at": "2025-11-17T10:00:00Z",
      "outcome": "deployed"
    },
    {
      "iteration": 2,
      "improvements": 3,
      "completed_at": "2025-11-17T16:00:00Z",
      "outcome": "iterating"
    }
  ]
}
```

## Success Metrics

Track across iterations:
- Improvements per iteration
- Time per iteration
- Quality score trend
- Bug count trend
- Test coverage trend

## Output Format

```markdown
# Iteration {N} Decision

## What Was Accomplished
- ✅ Improvement 1
- ✅ Improvement 2
- ✅ Improvement 3

## Current State
- Quality Score: 8/10
- Test Coverage: 78%
- Known Issues: 2 minor
- Deployment Ready: Yes

## Recommendation: DEPLOY ✅

### Deployment Plan
1. Deploy to staging
2. Run smoke tests
3. Monitor for 24h
4. Deploy to production

### Post-Deployment
- Monitor error rates
- Track performance metrics
- Gather user feedback
```

## State Update

```python
# For deploy
ws.update_phase(6, "deployed")
ws.complete_phase(6)

# For iterate
state['iteration'] += 1
state['phase'] = 3
state['agents'] = []
ws.save(state)
# → Run phase3-codex-review
```

## Next Steps Summary

| Decision | Next Action |
|----------|-------------|
| Deploy | `git merge dev` → deploy → monitor |
| Fix First | Address issues → then deploy |
| Iterate | Run phase3-codex-review (Iteration N+1) |
| Add Features | Run phase3-codex-review with feature focus |
