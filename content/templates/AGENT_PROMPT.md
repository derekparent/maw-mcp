# Agent [N]: [Role Name]

## Mission
[One sentence: What specific improvement to make]

## Branch
`agent/[N]-[slug]`

## Context
[2-3 sentences: Why this matters, what problem it solves]

## Files to Modify
- `path/to/file1.py` - [What changes]
- `path/to/file2.py` - [What changes]
- `path/to/new_file.py` - [Create: purpose]

## Tasks
1. [ ] [Specific task with measurable outcome]
2. [ ] [Specific task with measurable outcome]
3. [ ] [Specific task with measurable outcome]

## Definition of Done
- [ ] [Primary deliverable]
- [ ] Tests added/updated
- [ ] No linting errors
- [ ] PR created with descriptive title
- [ ] Completion report provided (see below)

## Time Estimate
[X] hours

## Dependencies
- **Depends on:** [Agent N or "None"]
- **Blocks:** [Agent N or "None"]

## Notes
[Any gotchas, edge cases, or context the agent should know]

---

## START NOW

Read this file, create branch `agent/[N]-[slug]`, implement, create PR.

---

## DISCIPLINE RULES

### Test-Driven Development

RED → GREEN → REFACTOR. No exceptions.

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. Test takes 30 seconds. |
| "I'll test after" | Tests added after prove nothing. They pass by definition. |
| "Already manually tested" | No record, can't re-run, doesn't count. |
| "Code already written" | Delete it. Start over with the test. |
| "Hard to test" | Hard to test = bad design. Listen to the friction. |
| "Just a prototype" | First code sets the pattern. Do it right now. |

**Wrote code before the test? Delete it. Start with the test.**

### Debugging: The 3-Attempt Rule

If you've tried 3+ fixes without success: **STOP.**

You're treating symptoms, not root cause. Go back to basics:

1. **Reproduce** - Can you trigger it reliably? Minimal repro case.
2. **Isolate** - Binary search. Add logging. Which component?
3. **Trace backward** - Start at symptom, walk back to root cause.
4. **Fix the root** - Write a failing test for the ROOT cause, then fix.

Red flags that mean you're guessing:
- "Let me try one more thing"
- Fix works but you're not sure why
- Fix causes a different failure

### Verification Before Completion

**Claims without fresh evidence = lies.**

Before claiming ANY task complete:
1. **Identify** - What command proves this claim?
2. **Run** - Execute the command FRESH (in this session)
3. **Read** - Full output, check exit code, count pass/fail
4. **Include** - Put the evidence in your completion report

❌ "Tests pass, task complete"  
✅ "Ran `pytest tests/ -v`, 12/12 passed, output below. Task complete."

Your completion report will be verified. Don't waste everyone's time.

---

## COMPLETION REPORT FORMAT

When you finish, provide this report for the coordinator:

```markdown
## Agent [N] Completion Report

**Status:** ✅ Complete | ⚠️ Partial | ❌ Blocked
**Branch:** `agent/[N]-[slug]`
**PR:** #[number] or [link]

### What Was Done
- [Completed task 1]
- [Completed task 2]
- [Completed task 3]

### Files Changed
| File | Change |
|------|--------|
| path/to/file.py | Created (X lines) |
| path/to/other.py | Modified (+X/-Y lines) |

### Tests
- **Added:** [N] new tests
- **Status:** All passing | X failing
- **Coverage:** [file] [X]%

### API/Endpoints Affected
- `GET /api/endpoint` - [new/modified/tested]
- `POST /api/endpoint` - [new/modified/tested]

### Database Changes
- [New model/migration or "None"]

### Environment/Config
- [New env vars needed or "None"]

### Notes for Integration
- [Merge order dependencies]
- [Potential conflicts with other agents]
- [Things to watch for]

### Time Spent
[X] hours (estimate was [Y]h)
```
