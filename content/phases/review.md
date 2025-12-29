# Phase 3: Codex Review & Agent Prompt Generation

Analyzes codebase, identifies 3-5 high-impact improvements, creates specialized agent roles, and generates ready-to-use agent prompts.

## When to Use

- **Primary entry point for existing projects**
- After Phase 2 (for new projects)
- Start of each iteration
- User requests code review or improvements

## What This Phase Does

1. Deep codebase analysis
2. Identifies 3-5 high-impact improvements
3. Determines optimal agent count (usually 3-4)
4. Creates specialized agent roles
5. Generates agent prompt files in AGENT_PROMPTS/
6. Updates workflow state
7. Provides copy-paste prompts for Phase 4

## Workflow

```python
from workflow.core.workflow_state import WorkflowState
import os

ws = WorkflowState("path/to/project")
state = ws.load()

# Analyze codebase comprehensively
# Look for:
# - Performance bottlenecks
# - Security issues
# - Code quality problems
# - Missing features
# - Technical debt
# - Test coverage gaps
# - Documentation needs

# Determine agent count (3-5 based on scope)
# Simple project → 3 agents
# Medium project → 4 agents  
# Complex project → 5 agents

# Create agent roles tailored to improvements
# Examples:
# - Backend Performance Engineer
# - Security Hardening Specialist
# - Testing Infrastructure Engineer
# - UI/UX Modernization Engineer
# - Documentation Writer

# Create AGENT_PROMPTS directory
os.makedirs("AGENT_PROMPTS", exist_ok=True)

# Generate prompt files
# AGENT_PROMPTS/1_Backend_Performance.md
# AGENT_PROMPTS/2_Security_Hardening.md
# etc.
```

## Agent Prompt Template

Each agent prompt file should be SHORT and self-contained:

```markdown
# Agent [N]: [Role Name]

## Mission
[One sentence: What specific improvement to make]

## Repository
- URL: github.com/user/repo
- Branch: improve/[N]-[short-description]

## Your Task
[2-3 sentences describing the specific problem and target outcome]

## Approach
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Files to Modify
- path/to/file1.py
- path/to/file2.py
- config.py

## Time Estimate
2-3 hours

## Definition of Done
- [ ] [Specific deliverable 1]
- [ ] [Specific deliverable 2]
- [ ] PR created with descriptive title
- [ ] Tests pass

## START NOW
```

## Analysis Focus Areas

### 1. Performance
- Slow queries
- Large file operations
- Memory leaks
- N+1 problems

### 2. Security
- Input validation
- Authentication issues
- SQL injection risks
- XSS vulnerabilities

### 3. Code Quality
- Duplicate code
- Complex functions
- Missing error handling
- Poor naming

### 4. Testing
- Coverage gaps
- Missing integration tests
- No edge case tests

### 5. Documentation
- Missing README sections
- No API docs
- Unclear setup

## Agent Count Decision

**3 Agents** (2-4 hours total):
- 1-2 high-impact improvements each
- Clear, non-overlapping domains
- Example: Backend, Frontend, Testing

**4 Agents** (3-5 hours total):
- Standard for most projects
- More specialized roles
- Example: Performance, Security, UI, Docs

**5 Agents** (4-6 hours total):
- Complex projects only
- Highly specialized roles
- Example: Backend, Frontend, Security, Testing, Docs

**Avoid 6+ agents** - coordination overhead exceeds benefits

## Prompt Quality Standards

Each agent prompt must include:
- Clear role and responsibility
- Specific improvement goal
- Files to modify
- Time estimate (1-3 hours)
- Definition of done
- Branch naming convention

Keep prompts under 200 words - details go in AGENT_PROMPTS/ files.

## State Update

```python
# Add agents to state
for i in range(1, agent_count + 1):
    ws.add_agent(i, agent_roles[i], "not_started")

ws.update_phase(3, "phase_3_complete")
ws.complete_phase(3)
```

## Output

At the end of Phase 3, provide:

1. **Summary of improvements identified**
2. **Agent role assignments**
3. **AGENT_PROMPTS/ directory** with markdown files
4. **Copy-paste prompts** for Phase 4:

```
✅ Phase 3 Complete!
📋 4 improvements identified
🤖 4 agent prompts created in AGENT_PROMPTS/

➡️ Next: Start 4 Claude Code sessions with these prompts:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💬 Agent 1 Prompt:
You are Agent 1: Backend Performance Engineer
Repository: https://github.com/user/repo
Read and follow: AGENT_PROMPTS/1_Backend_Performance.md
START NOW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Repeat for agents 2, 3, 4...]
```
