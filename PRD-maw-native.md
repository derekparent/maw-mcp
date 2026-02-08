# PRD: MAW Native — Multi-Agent Workflow for Claude Code

**Version**: 0.1.0-draft
**Author**: DP
**Date**: 2026-02-07
**Status**: Draft
**Parent Project**: maw-mcp
**Relationship**: New project branching from maw-mcp concepts; does not replace maw-mcp

---

## 1. Problem Statement

maw-mcp works — it coordinates parallel AI agents effectively. But it requires:

1. **Manual agent spawning** — copy-paste prompts into separate Cursor/Claude Code windows
2. **No inter-agent communication** — agents can't talk to each other or the hub
3. **External state tracking** — WORKFLOW_STATE.json managed via MCP tool calls
4. **Manual check-ins** — hub must poll GitHub PRs or parse pasted reports
5. **No permission bypass** — each agent instance prompts for permissions independently

Claude Code now has **native agent teams** and **custom subagents** that solve all of these:
- Automatic agent spawning with `TeamCreate` + `Task`
- Direct inter-agent messaging via `SendMessage`
- Shared task lists with dependency tracking
- `bypassPermissions` mode for autonomous operation
- Split-pane or in-process display modes

**MAW Native** ports the orchestration intelligence from maw-mcp's 10 tools into Claude Code's native agent/team primitives, creating a fully autonomous multi-agent development workflow that runs inside a single Claude Code session.

---

## 2. Goals

| Goal | Metric |
|------|--------|
| Zero manual copy-paste | Agents spawn and receive prompts automatically |
| Autonomous operation | Full workflow runs with `bypassPermissions` — no permission prompts |
| Preserve MAW phases | Same proven lifecycle: review → launch → integrate → decide |
| Inter-agent coordination | Agents message each other when blocked or when work overlaps |
| Faster iteration | Eliminate overhead of switching windows, parsing reports |
| Learning continuity | Capture learnings across sessions via persistent memory |

### Non-Goals

- Replace maw-mcp (it remains useful for cross-tool orchestration)
- Support non-Claude Code environments
- Build a UI/dashboard (Claude Code's terminal is the UI)

---

## 3. Architecture

### 3.1 Component Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code Session                     │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │             MAW Lead Agent (Orchestrator)              │  │
│  │  - Runs the workflow state machine                     │  │
│  │  - Creates worktrees + team, spawns teammates          │  │
│  │  - Assigns tasks, monitors, escalates blockers to user │  │
│  │  - Merges worktrees, makes deploy/iterate decisions    │  │
│  │  - Permission mode: delegate                           │  │
│  └──────────┬────────────────────────────┬───────────────┘  │
│             │      Shared Task List      │                   │
│     ┌───────┴──────┬──────────┬──────────┴──────┐           │
│     ▼              ▼          ▼                  ▼           │
│  ┌──────┐    ┌──────────┐  ┌──────┐      ┌──────────┐      │
│  │Impl 1│    │Impl 2    │  │Tester│      │Reviewer  │      │
│  │      │◄──►│          │  │      │      │          │      │
│  └──┬───┘    └────┬─────┘  └──┬───┘      └────┬─────┘      │
│     │             │           │                │             │
│  ../maw-wt-1  ../maw-wt-2  ../maw-wt-3   ../maw-wt-4      │
│  (worktree)   (worktree)   (worktree)    (worktree)         │
│     │             │           │                │             │
│     └─────────────┴───────────┴────────────────┘             │
│              Each agent has its own git worktree             │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Agent Definitions (`.claude/agents/`)

Six custom subagents, defined as markdown files with YAML frontmatter:

#### `maw-lead.md` — Orchestrator (Team Lead)

```yaml
name: maw-lead
description: >
  Multi-Agent Workflow orchestrator. Use when the user wants to run a
  parallel development workflow — review codebase, spawn agents, coordinate
  work, integrate results, and decide next steps. Invoke with "maw",
  "launch agents", "multi-agent", or "parallel workflow".
model: opus
permissionMode: bypassPermissions
tools: Task(maw-implementer, maw-tester, maw-reviewer, maw-fixer), Read, Grep, Glob, Bash
memory: user
skills:
  - maw-orchestration
```

> **Why `bypassPermissions` instead of `delegate`?** The lead needs `Bash` for git worktree creation, merges, and test runs during integration. `delegate` mode restricts to coordination-only tools, which would block the integration phase. The user can manually toggle to delegate mode (Shift+Tab) during the launch phase if they want the lead to focus purely on coordination. `bypassPermissions` is inherited from `--dangerously-skip-permissions` anyway.

> **Why `memory: user`?** The lead accumulates cross-project orchestration patterns — merge order heuristics, common failure modes, task decomposition strategies. These are valuable across all projects, not just one. Implementers use `memory: project` because their knowledge (code patterns, test conventions) is project-specific.

**System prompt responsibilities:**
- Run the 6-phase workflow state machine (setup → review → launch → integrate → decide → learn)
- Analyze codebase and decompose into 3-5 parallel tasks (standalone) or read maw-mcp analysis (hybrid mode)
- Create git worktrees for each agent
- Create team via `TeamCreate`, spawn teammates via `Task` with detailed prompts
- Create and assign tasks via `TaskCreate` / `TaskUpdate`
- Monitor progress via `TaskList` and teammate messages
- Escalate blockers to user when agents can't self-resolve
- Merge worktrees, run tests, synthesize results
- Make deploy/iterate decisions
- Capture learnings to persistent memory
- Check for CLAUDE.md in target repo; generate minimal one if missing

#### `maw-implementer.md` — Autonomous Coder

```yaml
name: maw-implementer
description: >
  Autonomous code implementer. Writes code until done or blocked.
  Can choose patterns, refactor, fix linting. Stops and messages
  lead if hitting architectural ambiguity or security decisions.
model: sonnet
permissionMode: bypassPermissions
tools: Read, Write, Edit, Bash, Grep, Glob
memory: project
```

**System prompt responsibilities:**
- Receive task from lead, work autonomously
- Create feature branch, implement changes
- Run tests before claiming done
- Message lead only if: tests fail twice, architecture-changing ambiguity, touching auth/payments/security
- Mark task complete via `TaskUpdate` when done

#### `maw-tester.md` — Test Writer & Runner

```yaml
name: maw-tester
description: >
  Writes and runs tests for implemented features. Creates unit tests,
  integration tests, and edge case coverage. Validates implementations
  meet acceptance criteria.
model: sonnet
permissionMode: bypassPermissions
tools: Read, Write, Edit, Bash, Grep, Glob
memory: project
```

**System prompt responsibilities:**
- Write comprehensive tests for assigned code
- Run full test suite, report results
- Message implementer directly if tests reveal bugs
- Block on missing dependencies or broken test infra
- Include test output as evidence when marking complete

#### `maw-reviewer.md` — Code Quality Gate

```yaml
name: maw-reviewer
description: >
  Reviews code for quality, security, and best practices. Reads
  implementation and tests, provides structured feedback. Verdict:
  approved or changes-requested.
model: sonnet
permissionMode: bypassPermissions
tools: Read, Grep, Glob, Bash
memory: project
```

**System prompt responsibilities:**
- Review implementation + tests together
- Check: no secrets, input validation, error handling, naming, duplication
- Provide structured feedback (critical / warning / suggestion)
- Verdict: "approved" or "changes-requested" with specifics
- Message implementer directly with change requests
- Wait for both implementation AND tests before reviewing

#### `maw-researcher.md` — Read-Only Explorer (v0.2)

> **Deferred to v0.2.** The built-in `Explore` subagent handles most read-only codebase research. The lead can spawn Explore directly for pre-review analysis. A custom researcher becomes valuable when you need persistent memory of codebase patterns across sessions.

```yaml
name: maw-researcher
description: >
  Deep codebase research and analysis. Explores architecture,
  dependencies, patterns. Reports findings without modifying code.
  Use for pre-review analysis or investigation tasks.
model: haiku
permissionMode: dontAsk
tools: Read, Grep, Glob, Bash
memory: user
```

#### `maw-fixer.md` — Targeted Bug Fixer

```yaml
name: maw-fixer
description: >
  Targeted debugger and fixer. Receives change requests from reviewer,
  implements fixes, re-runs tests. Lightweight agent for iteration loops.
model: sonnet
permissionMode: bypassPermissions
tools: Read, Write, Edit, Bash, Grep, Glob
memory: project
```

**System prompt responsibilities:**
- Receive change requests from reviewer
- Implement minimal fixes
- Re-run affected tests
- Message reviewer when fixes are ready for re-review

---

### 3.3 Workflow State Machine

The lead agent manages the workflow through 6 phases. State is tracked in the lead's context and the shared task list — no external state file needed.

```
┌───────┐     ┌────────┐     ┌────────┐     ┌───────────┐     ┌────────┐     ┌───────┐
│ SETUP │────►│ REVIEW │────►│ LAUNCH │────►│ INTEGRATE │────►│ DECIDE │────►│ LEARN │
└───────┘     └────────┘     └────────┘     └───────────┘     └────────┘     └───────┘
                  ▲                                                │
                  └────────────────────────────────────────────────┘
                                    (iterate)
```

| Phase | What the Lead Does | Native Primitives Used |
|-------|-------------------|----------------------|
| **Setup** | Analyze repo structure, identify improvement areas | `Glob`, `Grep`, `Read` |
| **Review** | Decompose work into 3-5 parallel tasks with acceptance criteria | `TaskCreate`, dependency graph via `addBlockedBy` |
| **Launch** | Create team, spawn agents, assign tasks | `TeamCreate`, `Task` (spawn), `TaskUpdate` (assign) |
| **Integrate** | Monitor completion, detect file conflicts, plan merge order | `TaskList`, `SendMessage`, `Bash` (git operations) |
| **Decide** | Assess results: deploy, iterate, or add features | `TaskList` (review outcomes), `SendMessage` (broadcast) |
| **Learn** | Capture learnings to persistent memory | Memory files in `~/.claude/agent-memory/maw-lead/` |

### 3.4 Task Dependency Graph (Example)

```
Task 1: "Set up test infrastructure"        [no dependencies]
Task 2: "Implement error handling"           [blocked by Task 1]
Task 3: "Add type safety"                   [blocked by Task 1]
Task 4: "Refactor server module"            [blocked by Tasks 2, 3]
Task 5: "Review all changes"               [blocked by Task 4]
```

The lead creates this graph using `TaskCreate` + `TaskUpdate(addBlockedBy)`. Claude Code's native task system automatically unblocks tasks when dependencies complete.

### 3.5 Git Worktree Isolation

Each agent works in its own git worktree, eliminating file conflicts entirely. The lead scripts worktree setup during the launch phase.

**Worktree lifecycle:**

```bash
# Lead creates worktrees during launch (one per agent)
git worktree add ../maw-wt-agent-1 -b agent/1-testing-infrastructure
git worktree add ../maw-wt-agent-2 -b agent/2-error-handling
git worktree add ../maw-wt-agent-3 -b agent/3-type-safety

# Each agent's spawn prompt includes its worktree path
# Agent works entirely within its worktree — no conflicts possible

# Lead merges after integration
cd /original/repo
git merge agent/1-testing-infrastructure
git merge agent/2-error-handling
# ...

# Lead cleans up worktrees after merge
git worktree remove ../maw-wt-agent-1
git worktree remove ../maw-wt-agent-2
git worktree remove ../maw-wt-agent-3
```

**Why worktrees over branches-in-same-directory:**
- Agents can edit the same file in parallel without overwriting each other
- No `git stash` / `git checkout` gymnastics
- Each worktree is a full working copy — tests run independently
- Clean merge workflow: lead merges sequentially into main, resolving conflicts once

**Lead responsibilities:**
- Create worktrees before spawning agents
- Include worktree path in each agent's spawn prompt (e.g., "Your working directory is `../maw-wt-agent-1`")
- Clean up worktrees after integration or on `maw_clean`

**Large repo consideration:** Each worktree is a full working copy (minus `.git` objects, which are shared). On a large monorepo, 5 worktrees means 5x the working tree disk usage. For repos >1GB, the setup script should use sparse checkout to limit each worktree to only the directories that agent needs:

```bash
# Sparse worktree for an agent that only touches src/auth/
git worktree add --no-checkout ../maw-wt-agent-2 -b agent/2-auth-hardening
cd ../maw-wt-agent-2
git sparse-checkout set src/auth/ tests/test_auth/ pyproject.toml
git checkout
```

For typical repos (<100MB), full worktrees are fine — the overhead is negligible.

### 3.6 Review Modes: Standalone & Hybrid

maw-native works **standalone** (no dependencies) but is enhanced when maw-mcp is available.

#### Standalone Mode (default)

The lead agent runs its own codebase review using `Read`, `Grep`, `Glob`, and the orchestration skill's decomposition heuristics. The lead presents its analysis to the user, who reviews and approves before agents launch.

```
┌──────────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│   MAW Lead Agent     │     │     User Reviews     │     │   Native Agent Team  │
│                      │     │                      │     │                      │
│  Analyzes codebase   │────►│  Reads task list     │────►│  Lead spawns         │
│  Creates task list   │     │  Adjusts scope       │     │  teammates who       │
│  Proposes breakdown  │     │  Says "launch"       │     │  execute autonomously │
└──────────────────────┘     └─────────────────────┘     └──────────────────────┘
```

#### Hybrid Mode (when maw-mcp is available)

If maw-mcp is configured as an MCP server, the lead defers to its `maw_review` tool for analysis. This produces richer, more structured output (AGENT_PROMPTS/ files with acceptance criteria, file lists, time estimates) because maw-mcp has purpose-built analysis logic.

```
┌─────────────────────┐     ┌─────────────────────┐     ┌──────────────────────┐
│    maw-mcp (MCP)    │     │     User Reviews     │     │   Native Agent Team  │
│                     │     │                      │     │                      │
│  maw_review         │────►│  Reads AGENT_PROMPTS │────►│  maw-lead spawns     │
│  - analyzes code    │     │  Edits/approves      │     │  teammates who       │
│  - creates prompts  │     │  Adjusts scope       │     │  execute autonomously │
│  - writes tasks     │     │                      │     │                      │
└─────────────────────┘     └─────────────────────┘     └──────────────────────┘
```

**Detection logic:** The lead checks if `maw_review` MCP tool is available. If yes, uses it. If no, runs its own analysis. No user configuration needed.

**Why the human-in-the-loop review step matters regardless of mode:**
- Prevents wasted agent tokens on misaligned work
- Keeps the human where they add most value (deciding *what* to fix)
- Agents run autonomously where they add most value (doing the actual fixing)

---

## 4. Permission Model

### 4.1 Autonomous Mode (Primary)

The user launches Claude Code with:

```bash
claude --dangerously-skip-permissions
```

All teammates inherit this. No permission prompts. Full autonomy.

### 4.2 Supervised Mode (Alternative)

For users who want oversight:

```bash
claude
```

Each agent uses its defined `permissionMode`:
- Lead: `delegate` (coordination only, no code changes)
- Implementers/Testers/Fixers: `bypassPermissions` if pre-approved, otherwise `acceptEdits`
- Reviewer: `dontAsk` (read-only, auto-denies writes)
- Researcher: `dontAsk` (read-only)

### 4.3 Plan Approval Gate (Optional)

For critical work, the lead can spawn agents with plan approval required:

```
Spawn an implementer teammate to refactor the auth module.
Require plan approval before they make any changes.
```

The agent plans in read-only mode, submits plan to lead, lead approves/rejects, then agent implements.

---

## 5. Communication Patterns

### 5.1 Lead ↔ Teammate (Primary)

```
Lead → Implementer:  "Task assigned: implement error handling in src/server.py"
Implementer → Lead:  "Done. 4 files changed, 95% test coverage. PR ready."
Lead → Reviewer:     "Review implementer's work on branch agent/2-error-handling"
Reviewer → Lead:     "Changes requested: missing input validation on line 142"
```

### 5.2 Teammate ↔ Teammate (Direct)

```
Reviewer → Implementer: "Line 142 needs input validation. See my review notes."
Implementer → Reviewer: "Fixed. Re-review ready."
Tester → Implementer:   "test_edge_case fails — handler returns None instead of raising."
```

### 5.3 Broadcast (Rare)

```
Lead → All: "Blocking issue found in shared utility. Pause until resolved."
```

### 5.4 Shutdown Sequence

```
Lead → Each Teammate: shutdown_request
Teammate → Lead:      shutdown_response (approve)
Lead: TeamDelete (cleanup)
```

### 5.5 User Notifications: Blockers & Cost

Agents don't just talk to each other — they escalate to the **user** when it matters.

**Blocker escalation** — any agent can trigger a `Notification` hook that surfaces in the user's terminal:

```
Scenarios that trigger user notification:
- Agent blocked: tests fail twice, can't self-resolve
- Agent blocked: needs architectural decision (auth, DB schema, API contract)
- Agent blocked: touching security-sensitive code, needs human approval
- Lead blocked: merge conflict can't be auto-resolved
- Lead info: all tasks complete, ready for user decision
```

**How it works:**
- Agents message the lead with `[BLOCKER]` prefix
- Lead evaluates: can it resolve? If not, it messages the user directly
- `Notification` hook fires a system notification (macOS `osascript` or `terminal-notifier`)
- User sees: "MAW: Agent 2 blocked — auth module needs design decision"

**Cost awareness:**
- Lead tracks approximate agent count x turns as a proxy for token spend
- At configurable thresholds (e.g., 50 turns total, 100 turns total), lead messages user:
  "Checkpoint: ~50 agent turns completed. 3/5 tasks done. Continue?"
- User can: continue, pause, adjust scope, or shut down

**Implementation:**

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/notify-user.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/notify-user.sh
# Reads notification content from stdin, sends macOS notification
INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | jq -r '.message // "MAW agent needs attention"')
osascript -e "display notification \"$MESSAGE\" with title \"MAW Workflow\""
```

---

## 6. Skills & Hooks

### 6.1 MAW Orchestration Skill

The lead agent loads a skill that contains the full workflow protocol:

**`skills/maw-orchestration/SKILL.md`**

Contents:
- Phase definitions and transition rules
- Task decomposition heuristics (how to split work)
- Merge order logic (docs → tests → backend → frontend)
- Conflict detection patterns
- Decision framework (deploy vs iterate vs add features)
- Check-in contract (when agents should/shouldn't interrupt)
- Risk tiering (autonomous vs must-ask decisions)
- **Compaction survival protocol**: update `.maw-lead-state.json` every ~10 turns; after any compaction event, re-read the file + `TaskList` to restore orchestration context
- Cost checkpoint thresholds (default: notify user at 50 total turns, then every 25)

### 6.2 Hooks

#### `TeammateIdle` Hook

Runs when a teammate goes idle. Used to check if they actually completed their task:

```json
{
  "hooks": {
    "TeammateIdle": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/check-task-completion.sh"
          }
        ]
      }
    ]
  }
}
```

Script checks: did the teammate mark their task complete? If not, exit code 2 to keep them working.

#### `TaskCompleted` Hook

Runs when a task is marked complete. Validates that tests pass:

```json
{
  "hooks": {
    "TaskCompleted": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./scripts/validate-task-done.sh"
          }
        ]
      }
    ]
  }
}
```

Script checks: are tests passing? Is there a git diff? Exit code 2 to block completion if validation fails.

#### `PreCompact` Hook — State Persistence Across Compaction

**This is critical.** The lead agent orchestrating 5 agents across 100+ turns will inevitably hit context window compaction. When compaction fires, the lead could lose track of which agents are on which tasks, what the merge order should be, and what decisions have been made.

The `PreCompact` hook fires *before* compaction occurs. The lead uses this to serialize its orchestration state to a file, then re-reads it after compaction restores.

```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/save-lead-state.sh"
          }
        ]
      }
    ]
  }
}
```

```bash
#!/bin/bash
# scripts/save-lead-state.sh
# Serialize current orchestration state before context compaction
# The lead's system prompt includes instructions to re-read this file
# after compaction to restore awareness

STATE_FILE=".maw-lead-state.json"
cat > "$STATE_FILE" << 'TEMPLATE'
{
  "_note": "This file is auto-updated by PreCompact hook. Lead re-reads after compaction.",
  "phase": "UPDATE_ME",
  "agents": [],
  "tasks_complete": [],
  "tasks_in_progress": [],
  "tasks_blocked": [],
  "merge_order": [],
  "decisions_made": [],
  "turn_count": 0
}
TEMPLATE

echo "State template written to $STATE_FILE — lead will populate on next turn" >&2
```

**The lead's orchestration skill instructs it to:**
1. Maintain `.maw-lead-state.json` as a running state snapshot (updated every ~10 turns)
2. After any compaction event, re-read the file to restore orchestration context
3. Cross-reference with `TaskList` (which survives compaction) for ground truth

This gives the lead a durable memory that survives context window resets — the same pattern as persistent agent memory, but for ephemeral workflow state.

---

## 7. Mapping: maw-mcp Tools → MAW Native

This table shows how each of the 10 maw-mcp tools maps to native Claude Code primitives:

| maw-mcp Tool | MAW Native Equivalent | How |
|---|---|---|
| `maw_setup` | **Plugin install** | Install the maw-native plugin. Agent definitions, skills, hooks auto-discovered. |
| `maw_review` | **maw-mcp (hybrid)** | Still uses maw-mcp's `maw_review` MCP tool for analysis. User reviews output before launching. |
| `maw_launch` | **TeamCreate + Task + worktrees** | Lead creates worktrees, creates team, spawns teammates via `Task(maw-implementer, ...)`, assigns tasks. |
| `maw_checkin` | **Automatic messages** | Teammates message lead on completion. `TaskList` shows real-time status. No polling needed. |
| `maw_integrate` | **Lead + Bash** | Lead reads task outcomes, runs `git merge`, `pytest` via Bash. Merge order logic is in the skill. |
| `maw_decide` | **Lead decision logic** | Lead evaluates outcomes against decision framework in skill. Recommends deploy/iterate/add. |
| `maw_learn` | **Persistent memory** | Lead writes to `~/.claude/agent-memory/maw-lead/MEMORY.md`. Survives across sessions. |
| `maw_patterns` | **Memory files** | Lead reads from memory directory. Can create topic-specific files (e.g., `debugging.md`, `patterns.md`). |
| `maw_clean` | **TeamDelete + git** | Lead shuts down teammates, runs `TeamDelete`, optionally cleans branches via Bash. |
| `maw_status` | **TaskList + context** | Lead checks `TaskList` for real-time status. No separate state file needed. |

---

## 8. User Experience

### 8.1 Quick Start

```bash
# One-time setup: install the maw-native plugin

# Launch with full autonomy
claude --dangerously-skip-permissions --teammate-mode tmux

# Tell Claude what to do
> Review this codebase for code quality issues and fix them
```

What happens:
1. Lead analyzes codebase (standalone) or calls `maw_review` (if maw-mcp available)
2. Lead presents task breakdown to user
3. User reviews, adjusts scope, says "launch"
4. Lead creates git worktrees (one per agent)
5. Lead creates team, spawns 3-5 teammates
6. Each teammate works in its own worktree — no file conflicts
7. Lead monitors progress, escalates blockers to user (macOS notifications)
8. Lead merges worktrees into main when all tasks complete
9. Lead runs tests, reports results
10. User decides: deploy, iterate, or add features

### 8.2 Sequential Mode

For bandwidth-constrained environments:

```
> Review this codebase and work through improvements one at a time
```

Lead spawns one agent at a time, waits for completion, then spawns the next. Uses subagents instead of teams (lower overhead).

### 8.3 Focused Mode

```
> Launch agents to fix the security issues in src/auth/
```

Lead scopes review to specific area, creates targeted tasks.

### 8.4 User Intervention

At any point, the user can:
- Message any teammate directly (Shift+Up/Down in in-process mode)
- Override the lead's decisions
- Add/remove tasks from the shared task list
- Shut down specific teammates
- Switch between delegate and hands-on mode (Shift+Tab)

---

## 9. Project Structure

Distributed as a **Claude Code plugin** for easy installation.

```
maw-native/
├── .claude-plugin/
│   └── plugin.json               # Plugin metadata (name, version, description)
├── agents/
│   ├── maw-lead.md               # Orchestrator (team lead)
│   ├── maw-implementer.md        # Autonomous coder
│   ├── maw-tester.md             # Test writer & runner
│   ├── maw-reviewer.md           # Code quality gate
│   ├── maw-researcher.md         # Read-only explorer
│   └── maw-fixer.md              # Targeted bug fixer
├── skills/
│   └── maw-orchestration/
│       └── SKILL.md              # Full workflow protocol
├── commands/
│   ├── launch.md                 # /maw-launch — start agent team
│   ├── status.md                 # /maw-status — check progress
│   └── review.md                 # /maw-review — analyze codebase
├── hooks/
│   └── hooks.json                # TeammateIdle, TaskCompleted, PreCompact, Notification hooks
├── scripts/
│   ├── setup-worktrees.sh        # Create worktrees for agents (supports sparse checkout for large repos)
│   ├── cleanup-worktrees.sh      # Remove worktrees after integration (idempotent)
│   ├── maw-recover.sh            # Detect orphaned worktrees, report state for recovery
│   ├── save-lead-state.sh        # PreCompact hook — serialize orchestration state
│   ├── check-task-completion.sh  # TeammateIdle validation
│   ├── validate-task-done.sh     # TaskCompleted validation
│   └── notify-user.sh            # macOS notification for blockers/cost
├── CLAUDE.md                     # Plugin-level instructions
├── README.md                     # Documentation + quick start
└── examples/
    ├── wave-code-quality.md      # Example: code quality wave
    ├── wave-security.md          # Example: security hardening
    └── wave-feature.md           # Example: new feature development
```

### 9.1 Plugin Manifest

```json
{
  "name": "maw-native",
  "description": "Multi-Agent Workflow — orchestrate parallel Claude Code agents with autonomous execution, git worktree isolation, and human-in-the-loop review",
  "version": "0.1.0",
  "author": { "name": "DP" },
  "repository": "https://github.com/derekparent/maw-native",
  "keywords": ["multi-agent", "orchestration", "autonomous", "workflow", "agent-teams"]
}
```

### 9.2 What's NOT in this project

- No Python MCP server (agents are native markdown files)
- No WORKFLOW_STATE.json (state lives in task list + lead context)
- No `pyproject.toml` or `package.json` (no runtime dependencies)
- No `src/` directory (no application code to build)

This is a **configuration-as-code plugin**. The "code" is agent definitions, skills, hooks, shell scripts, and documentation.

### 9.3 Relationship to maw-mcp

maw-native is a **sibling project**, not a replacement:

| | maw-mcp | maw-native |
|---|---|---|
| **What it is** | MCP server (Python) | Claude Code plugin (markdown + shell) |
| **Review phase** | `maw_review` tool | Uses maw-mcp's `maw_review` (hybrid mode) |
| **Execution phase** | Manual copy-paste to agents | Native agent teams (autonomous) |
| **When to use** | Cross-tool orchestration, explicit state | Claude Code-native, fully autonomous |

In hybrid mode, maw-mcp handles analysis and maw-native handles execution. They complement each other.

---

## 10. Migration Path from maw-mcp

| Aspect | maw-mcp | maw-native |
|--------|---------|------------|
| **Runtime** | Python MCP server | Claude Code native agents |
| **Agent spawning** | Manual (copy-paste to Cursor) | Automatic (`Task` tool) |
| **Communication** | GitHub PRs + manual reports | Direct messaging (`SendMessage`) |
| **State** | WORKFLOW_STATE.json | Shared task list (`TaskCreate/TaskList`) |
| **Permissions** | Per-instance | `--dangerously-skip-permissions` inherits to all |
| **Learning** | PROJECT_LEARNINGS.md via MCP tool | Persistent agent memory |
| **Setup** | `maw_setup` tool call | Install plugin / copy agent files |
| **Dependencies** | Python 3.10+, gh CLI, MCP | Claude Code only |

### maw-mcp continues to be useful for:
- Orchestrating agents across different tools (Cursor + Claude Code + others)
- Environments where Claude Code agent teams aren't available
- Users who prefer explicit state files over implicit state

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Agent teams are experimental | Feature may change/break | Pin to known-working Claude Code version; keep maw-mcp as fallback |
| `bypassPermissions` is dangerous | Agents could delete files, push bad code | Hook validation scripts; reviewer agent as quality gate; git worktree isolation (never touches main directly) |
| Token cost scales with teammates | Expensive for large teams | Default to 3-5 agents max; sequential mode for cost-sensitive work; cost checkpoints |
| No session resumption for teams | Lost progress on disconnect | Worktrees persist on disk; recovery script reconstructs state. See Section 11.1 |
| Lead implements instead of delegating | Defeats purpose of team | Skill instructions reinforce delegation-first behavior; user can toggle delegate mode via Shift+Tab during launch phase |
| Teammate hangs / never completes | Blocks dependent tasks | Lead probes after N minutes of idle; TeammateIdle hook validates completion |

### 11.1 Error Recovery

**Problem:** Claude Code agent teams don't survive session restarts. If the session crashes, tmux disconnects, or the user's laptop sleeps, the team is gone — but git worktrees remain on disk.

**Recovery strategy:**

```bash
# scripts/maw-recover.sh — detect orphaned worktrees and report state
#!/bin/bash
PROJECT_DIR="${1:-.}"
echo "Scanning for MAW worktrees..."

for wt in ../maw-wt-*; do
  if [ -d "$wt" ]; then
    BRANCH=$(git -C "$wt" branch --show-current)
    STATUS=$(git -C "$wt" status --porcelain | wc -l | tr -d ' ')
    COMMITS=$(git -C "$wt" log main..HEAD --oneline | wc -l | tr -d ' ')
    echo "  $wt → branch: $BRANCH, uncommitted: $STATUS, commits ahead: $COMMITS"
  fi
done
```

**Recovery flow:**
1. User restarts Claude Code, says "recover" or "check worktrees"
2. Lead runs `maw-recover.sh` — discovers orphaned worktrees with their branch state
3. Lead reconstructs task list from worktree state (branch exists + commits = likely complete; uncommitted changes = was in-progress)
4. Lead spawns new teammates to continue incomplete work, or proceeds to integration for complete work
5. All scripts are **idempotent** — safe to run multiple times

**Timeout handling:**
- Lead tracks last message timestamp from each teammate (in context)
- If no message for ~5 minutes during active work: lead sends a probe message
- If teammate doesn't respond after probe: lead marks task as stalled, spawns maw-fixer or reassigns
- `TeammateIdle` hook catches premature idle (task not marked complete)

### 11.2 Cost Estimation

Rough estimates based on Claude Code pricing (Feb 2026):

| Mode | Agents | Est. Turns | Est. Input/Output | Notes |
|------|--------|------------|-------------------|-------|
| **Full parallel** | 4-5 | 100-200 total | ~2-5M input, ~500K-1M output | Fastest; highest cost |
| **Sequential** | 1-2 | 50-80 total | ~1-2M input, ~200K-400K output | Slower; ~40-60% cheaper |
| **Focused** (single area) | 2-3 | 30-50 total | ~500K-1M input, ~100K-300K output | Targeted; most efficient |

> Note: Actual costs depend heavily on codebase size, task complexity, and how many iterations the reviewer requests. These are order-of-magnitude estimates for a medium codebase (~10K LOC). The lead tracks turn count as a proxy and checkpoints with the user at configurable intervals.

**Cost tracking implementation:** The lead maintains a running turn count in its context window. The orchestration skill defines checkpoint thresholds (default: notify at 50 total turns, then every 25). At each checkpoint, the lead messages the user with progress + estimated remaining work. The user can continue, adjust scope, or stop. This is "mental bookkeeping" in the lead's context — there's no programmatic token counting API.

---

## 12. Success Criteria

### MVP (v0.1)

- [ ] Plugin scaffold (plugin.json, directory structure)
- [ ] 5 agent definitions in `agents/` (lead, implementer, tester, reviewer, fixer)
- [ ] Orchestration skill with full workflow protocol
- [ ] Git worktree setup/cleanup/recovery scripts (idempotent)
- [ ] Standalone review mode (lead analyzes codebase directly)
- [ ] Hybrid review mode (defers to maw-mcp's `maw_review` if available)
- [ ] `--dangerously-skip-permissions` enables fully autonomous operation
- [ ] Blocker notification script (macOS `osascript`)
- [ ] Lead checks for CLAUDE.md in target repo; generates minimal one if missing
- [ ] README with quick start guide
- [ ] Acceptance tests (see Section 12.1)

### v0.2

- [ ] maw-researcher agent (persistent memory for codebase patterns)
- [ ] Persistent memory captures learnings across sessions
- [ ] Cost checkpoint logic (turn counting with user prompts)
- [ ] TeammateIdle + TaskCompleted hook validation scripts
- [ ] Sequential mode via subagents (for bandwidth-limited use)
- [ ] Example waves (code quality, security, feature)
- [ ] Slash commands (`/maw-launch`, `/maw-status`, `/maw-review`)

### v1.0

- [ ] Battle-tested on 3+ real projects
- [ ] Refined agent prompts based on observed behavior
- [ ] Published to plugin marketplace
- [ ] Configurable agent roster (add/remove agent types)
- [ ] Recovery from mid-workflow crashes (auto-detect orphaned worktrees)

### 12.1 Acceptance Tests

**Test fixture:** A minimal Python repo with intentional issues, stored in `examples/test-fixture/`:

```
examples/test-fixture/
├── src/
│   ├── calculator.py    # Has a division-by-zero bug (line 15)
│   ├── auth.py          # Missing input validation (intentionally ambiguous — which pattern?)
│   └── utils.py         # No type hints, no docstrings
├── tests/
│   └── test_calculator.py  # 2 passing tests, missing edge cases
├── pyproject.toml
└── README.md
```

| # | Test | Concrete Steps | Pass Criteria |
|---|------|----------------|---------------|
| 1 | **Smoke test** | `cd examples/test-fixture && claude --dangerously-skip-permissions` → "Review and fix this codebase" | 2+ worktrees created at `../maw-wt-*`; agents commit on their branches; lead merges all to main; `pytest` passes; worktrees cleaned up |
| 2 | **Blocker escalation** | Same fixture. Agent assigned to fix `auth.py` encounters ambiguous auth pattern | Agent sends `[BLOCKER]` to lead → lead messages user → `osascript` notification fires (verify via `log show --predicate 'process == "osascript"' --last 1m`) |
| 3 | **Worktree isolation** | Assign agent-1 and agent-2 both tasks that modify `utils.py` | Each gets its own worktree; both modify `utils.py` independently; lead merges sequentially; final `utils.py` has both agents' changes |
| 4 | **Worktree cleanup** | After test 1 completes, run `./scripts/cleanup-worktrees.sh` twice | First run removes worktrees (exit 0); second run is no-op (exit 0, no errors); `git worktree list` shows only main |
| 5 | **Recovery** | Start test 1; after worktrees created and agents spawned, `kill -9` the Claude Code process | Restart Claude Code; say "recover"; `maw-recover.sh` reports worktree state; lead reconstructs tasks; workflow resumes or proceeds to merge |
| 6 | **Standalone review** | Remove maw-mcp from `.mcp.json`; run on test fixture | Lead analyzes codebase itself using Read/Grep/Glob; produces task breakdown; user approves; team launches normally |
| 7 | **Hybrid review** | Ensure maw-mcp in `.mcp.json`; run on test fixture | Lead calls `maw_review` MCP tool; produces AGENT_PROMPTS/; user reviews; says "launch"; team executes |
| 8 | **Sequential mode** | "Fix this codebase one task at a time" | No `TeamCreate`; lead spawns subagents sequentially; each completes before next starts; all tasks eventually done |
| 9 | **Reviewer gate** | Force reviewer to reject (e.g., implementer skips test for `divide(x, 0)`) | Reviewer sends change request → lead spawns fixer → fixer adds test → reviewer re-reviews → approves → lead merges |
| 10 | **PreCompact state persistence** | Run on a larger repo that forces context compaction (~100+ turns) | `.maw-lead-state.json` exists with current phase/agent state; after compaction, lead re-reads file and continues orchestrating without confusion |

---

## 13. Design Decisions (Resolved)

1. **Git worktrees** — Use worktrees. Each agent gets its own worktree for true isolation. Lead scripts worktree creation during launch phase. See [Section 3.5](#35-git-worktree-isolation).

2. **Team size** — 3-5 agents per wave. Matches maw-mcp's proven default.

3. **Distribution** — Claude Code plugin. Installable via the plugin system for easy onboarding. See [Section 9](#9-project-structure).

4. **Hybrid mode** — Standalone-first design. Lead runs its own review if maw-mcp isn't available. When maw-mcp IS available, the lead defers to `maw_review` for richer analysis. Either way, user reviews before agents launch. See [Section 3.6](#36-review-modes-standalone--hybrid).

5. **Cost guardrails + blocker notifications** — Lead tracks approximate token spend and notifies the user at thresholds. Agents escalate blockers to the user (not just to the lead) via a `Notification` hook. See [Section 5.5](#55-user-notifications-blockers--cost).

---

## Appendix A: Environment Setup

```bash
# Enable agent teams (required — experimental feature)
# Add to ~/.claude/settings.json:
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}

# Launch with full autonomy
claude --dangerously-skip-permissions

# Or with split panes (recommended for visibility)
claude --dangerously-skip-permissions --teammate-mode tmux
```

## Appendix B: Example Session Transcript (Hybrid Mode)

```
# PHASE 1: Review via maw-mcp (human-in-the-loop)
User: /maw-review focus="code quality"

maw-mcp (MCP tool):
  → Analyzing codebase...
  → Found 4 improvement areas:
    1. Missing test coverage (src/handlers/)
    2. Error handling gaps (src/server.py)
    3. Type safety issues (src/state.py)
    4. Documentation gaps (README, docstrings)
  → Created AGENT_PROMPTS/ with task breakdowns
  → "Review the prompts, then say 'launch' to start agents"

User: [reads AGENT_PROMPTS/, adjusts scope, removes task 4]
User: launch

# PHASE 2: Autonomous execution via native agent teams
Lead (maw-lead):
  → Setting up git worktrees...
    ../maw-wt-agent-1 → agent/1-testing-infrastructure
    ../maw-wt-agent-2 → agent/2-error-handling
    ../maw-wt-agent-3 → agent/3-type-safety
  → Creating team "maw-quality-wave"...
  → Spawning 3 teammates...
  → Creating tasks with dependencies:
    Task 1: "Add test infrastructure" (no deps) → impl-1 in ../maw-wt-agent-1
    Task 2: "Fix error handling" (blocked by 1) → impl-2 in ../maw-wt-agent-2
    Task 3: "Add type annotations" (blocked by 1) → impl-3 in ../maw-wt-agent-3

  [impl-1 completes Task 1 in its worktree, messages lead]
  [Tasks 2 and 3 automatically unblock]
  [impl-2 and impl-3 work in parallel — no conflicts, separate worktrees]

  [impl-2 hits a blocker: unclear auth pattern]
  impl-2 → Lead: "[BLOCKER] Auth module uses two patterns. Which to standardize on?"
  Lead → User: 🔔 "Agent 2 blocked — auth module needs design decision"
  User → impl-2: "Use the middleware pattern from src/auth/middleware.py"
  [impl-2 continues]

  [Both complete]
  [Lead spawns reviewer in ../maw-wt-agent-4]
  [Reviewer reviews all changes across worktrees]
  [Reviewer sends minor fix request to impl-2]
  [Lead spawns maw-fixer, fixer implements, reviewer approves]

# PHASE 3: Integration
Lead:
  → Checkpoint: ~45 agent turns completed. All tasks done. Proceeding to merge.
  → Merging worktrees into main:
    1. git merge agent/1-testing-infrastructure ✅
    2. git merge agent/2-error-handling ✅
    3. git merge agent/3-type-safety ✅
  → Running full test suite... 47 tests passing ✅
  → Cleaning up worktrees...
  → Recommendation: Deploy ✅
  → Learnings captured to memory

User: ship it
```
