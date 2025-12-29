# Phase 5: Integration & Merge

Reviews and safely merges all agent PRs with conflict detection and testing.

## Prerequisites

- Phase 4 complete (all agents finished)
- Each agent has created a PR
- WORKFLOW_STATE.json shows agents with status=complete

## Workflow Options

### Quick Merge (15-20 minutes)

For simple, low-risk merges:

```python
from workflow.core.workflow_state import WorkflowState

ws = WorkflowState("path/to/project")
state = ws.load()
agents = [a for a in state['agents'] if a['status'] == 'complete']

print(f"🔀 Quick Merge - {len(agents)} PRs")

# 1. List PRs
print("\n📋 Pull Requests:")
for agent in agents:
    print(f"  PR #{agent.get('pr_number')}: {agent['role']}")

# 2. Determine merge order (least risky first)
# - Docs/tests first
# - Backend before frontend
# - Independent before dependent

# 3. Merge each with checks
for pr_num in merge_order:
    print(f"\n Merging PR #{pr_num}...")
    # gh pr merge {pr_num} --squash --delete-branch
    # Run tests
    # Verify no breaks

ws.update_phase(5, "phase_5_complete")
ws.complete_phase(5)

print("\n✅ All PRs Merged!")
print("➡️  Next: Run phase5-quality-audit (recommended)")
print("➡️  Or: Run phase6-iteration to decide next steps")
```

### Comprehensive Integration (45-60 minutes)

For production or complex merges:

1. **Gather All PRs** (5 min) - List open PRs, note files modified, check CI status
2. **Review Each PR** (30 min) - Code quality, test coverage, documentation, conflicts
3. **Determine Merge Order** (10 min) - By dependencies, risk, conflicts
4. **Check for Conflicts** (5 min) - File overlap detection, resolution strategy
5. **Execute Merges** (30 min) - One at a time, test after each, rollback if issues
6. **Final Verification** (10 min) - Full test suite, manual testing, build verification
7. **Documentation** (5 min) - Update CHANGELOG, create release notes
8. **Next Steps** (5 min) - Deploy, iterate, or add features

## Merge Order Heuristics

**Merge first:**
1. Documentation-only changes
2. Test additions (no code changes)
3. Independent backend improvements
4. Frontend changes (depend on backend)
5. Integration changes (touch multiple areas)

**Watch for:**
- Multiple PRs modifying same file
- Database schema changes
- API contract changes
- Breaking changes

## Git Commands

```bash
# For each PR in order:
gh pr view {pr_num}              # Review
gh pr checks {pr_num}            # Check CI
gh pr merge {pr_num} --squash    # Merge
git checkout dev && git pull     # Update
pytest                           # Test
```

## Conflict Resolution

If conflicts detected:
1. Identify which files conflict
2. Determine if real conflict or just overlap
3. Suggest merge order to minimize conflicts
4. Provide resolution strategy

## Testing Requirements

After each merge:
- Run test suite
- Check for new failures
- Verify improvements work
- Test integration points

## Integration Report Template

```markdown
# Integration Summary

## PRs Merged
1. PR #45 - Backend Performance ✅
2. PR #46 - Security Hardening ✅  
3. PR #47 - Testing Infrastructure ✅

## Final Status
- Tests: ✅ All passing
- Build: ✅ Success
- Manual verification: ✅ Confirmed

## Issues Found
- [None OR list any issues]

## Next Steps
[Recommendation: Audit/Deploy/Iterate]
```

## State Update

```python
ws.update_phase(5, "phase_5_complete")
ws.complete_phase(5)
```

## Output

- All PRs reviewed
- Merge order determined
- PRs merged successfully
- Tests passing
- State updated
- Clear next step (phase5-quality-audit or phase6-iteration)
