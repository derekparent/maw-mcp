# Agent Coordination

## Launch Sequence

### Wave 1: Foundation (Run First)
| Agent | Role | Branch | Dependency |
|-------|------|--------|------------|
| 1 | Testing Infrastructure | `agent/1-testing-infrastructure` | None |

**Why first:** Tests establish a safety net before any refactoring. Other agents can verify their changes don't break existing behavior.

### Wave 2: Parallel Execution
These agents can run **simultaneously** after Agent 1 creates the test infrastructure:

| Agent | Role | Branch | Dependency |
|-------|------|--------|------------|
| 2 | Error Handling | `agent/2-error-handling` | Agent 1 |
| 4 | Type Safety & Docs | `agent/4-type-safety-docs` | Agent 1 |

**Why parallel:** These agents modify different aspects of the code with minimal overlap.

### Wave 3: Final
| Agent | Role | Branch | Dependency |
|-------|------|--------|------------|
| 3 | Code Modularity | `agent/3-code-modularity` | Agents 1, 2, 4 |

**Why last:** Refactoring into modules is safest after tests exist, error handling is solid, and types/docs are in place.

## File Overlap Analysis

| File | Agent 1 | Agent 2 | Agent 3 | Agent 4 |
|------|---------|---------|---------|---------|
| `src/server.py` | ❌ | ✅ Modify | ✅ Major | ✅ Docs |
| `src/state.py` | ❌ | ✅ Modify | ❌ | ✅ Docs |
| `src/github.py` | ❌ | ✅ Modify | ❌ | ✅ Docs |
| `tests/*` | ✅ Create | ❌ | ❌ | ❌ |
| `src/handlers/*` | ❌ | ❌ | ✅ Create | ❌ |
| `pyproject.toml` | ✅ Update | ❌ | ❌ | ❌ |

**Potential Conflicts:**
- `src/server.py` modified by Agents 2, 3, 4
- Recommendation: Merge in order 4 → 2 → 3 (docs first, then error handling, then refactor)

## Integration Order

1. **Agent 1** (Testing) - Merge first, establishes CI baseline
2. **Agent 4** (Type Safety) - Low risk, adds docs without changing behavior  
3. **Agent 2** (Error Handling) - Medium risk, modifies behavior but tests exist
4. **Agent 3** (Modularity) - Higher risk, major refactor but now has safety net

## Communication Protocol

If agents encounter blocking issues:
1. Document the blocker in PR description
2. Create a `WIP:` PR early
3. Note files that may conflict with other agents

## Success Criteria

All PRs must:
- [ ] Pass existing tests (once Agent 1 completes)
- [ ] Include any new tests for new functionality
- [ ] Have no merge conflicts with main
- [ ] Be reviewed before merge
