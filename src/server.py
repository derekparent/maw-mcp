"""
Multi-Agent Workflow MCP Server

Provides tools to coordinate parallel AI agent development workflows.
Works with Cursor, Claude Code, and Claude.ai.
"""
import json
import re
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import AnyUrl

from .state import (
    WorkflowState, AgentInfo, WaveInfo,
    load_state, save_state, format_status, suggest_next_step
)
from .github import (
    get_agent_prs, detect_conflicts, format_pr_dashboard,
    get_local_branches, run_gh
)

# Server setup
server = Server("maw-mcp")

# =============================================================================
# FOCUS RESOLUTION - Natural Language to Focus Area
# =============================================================================

# Shortcuts map common terms to canonical focus areas
FOCUS_SHORTCUTS = {
    # UI/UX
    "ui": "ui", "ux": "ui", "design": "ui", "styling": "ui",
    "look": "ui", "appearance": "ui", "layout": "ui", "responsive": "ui",
    "prettier": "ui", "ugly": "ui", "clean up": "ui", "css": "ui",
    "tailwind": "ui", "colors": "ui", "fonts": "ui", "mobile": "ui",
    "touch": "ui", "buttons": "ui", "forms": "ui",
    
    # API
    "api": "api", "endpoints": "api", "routes": "api", "rest": "api",
    "graphql": "api", "requests": "api", "responses": "api",
    
    # Data
    "data": "data", "database": "data", "db": "data", "schema": "data",
    "queries": "data", "sql": "data", "models": "data", "migrations": "data",
    "sqlite": "data", "postgres": "data", "mysql": "data",
    
    # Performance
    "performance": "performance", "speed": "performance", "slow": "performance",
    "fast": "performance", "optimize": "performance", "caching": "performance",
    "memory": "performance", "cpu": "performance", "latency": "performance",
    
    # Testing
    "testing": "testing", "tests": "testing", "coverage": "testing",
    "tdd": "testing", "unit tests": "testing", "pytest": "testing",
    "integration tests": "testing", "e2e": "testing",
    
    # Security
    "security": "security", "auth": "security", "secure": "security",
    "vulnerabilities": "security", "secrets": "security", "passwords": "security",
    "injection": "security", "xss": "security", "csrf": "security",
    
    # Documentation
    "docs": "docs", "documentation": "docs", "readme": "docs", 
    "comments": "docs", "docstrings": "docs", "api docs": "docs",
    
    # Architecture/Code Quality
    "architecture": "architecture", "structure": "architecture",
    "refactor": "architecture", "clean code": "architecture",
    "separation": "architecture", "modules": "architecture",
    "organization": "architecture",
    
    # Error Handling
    "errors": "errors", "error handling": "errors", "exceptions": "errors",
    "logging": "errors", "debugging": "errors", "crashes": "errors",
    
    # DX (Developer Experience)
    "dx": "dx", "setup": "dx", "tooling": "dx", "config": "dx",
    "developer": "dx", "onboarding": "dx",
}

# Detailed descriptions for each canonical focus area
FOCUS_DESCRIPTIONS = {
    "ui": "User interface, styling, responsiveness, UX patterns, visual design, mobile layout, touch targets, accessibility",
    "api": "API design, endpoints, request/response handling, REST conventions, error responses, versioning",
    "data": "Database schema, queries, data flow, migrations, ORM usage, data integrity, relationships",
    "performance": "Speed optimization, caching, memory usage, query optimization, lazy loading, bundle size",
    "testing": "Test coverage, test quality, edge cases, unit tests, integration tests, test organization",
    "security": "Authentication, authorization, input validation, secrets handling, injection prevention, CSRF/XSS",
    "docs": "README quality, inline comments, API documentation, setup guides, architecture docs",
    "architecture": "Code structure, separation of concerns, modularity, dependency management, design patterns",
    "errors": "Error handling, exception management, logging, user-facing error messages, recovery strategies",
    "dx": "Developer experience, setup process, tooling, configuration, local development workflow",
    "all": "Comprehensive analysis across all areas",
}

# Paths to check for goals document
GOAL_DOC_PATHS = [
    "GOALS.md",
    ".maw/goals.md",
    "docs/GOALS.md",
    ".github/GOALS.md",
]


def resolve_focus(raw_input: str) -> tuple[str, str]:
    """
    Resolve natural language input to a focus area.
    
    Returns:
        tuple: (canonical_focus_or_raw, description)
        - If matched: (canonical_name, FOCUS_DESCRIPTIONS[canonical])
        - If not matched: (raw_input, raw_input) - LLM interprets directly
    """
    if not raw_input:
        return ("all", FOCUS_DESCRIPTIONS["all"])
    
    normalized = raw_input.lower().strip()
    
    # Check exact shortcuts first
    if normalized in FOCUS_SHORTCUTS:
        canonical = FOCUS_SHORTCUTS[normalized]
        return (canonical, FOCUS_DESCRIPTIONS[canonical])
    
    # Check if any shortcut is contained in the input
    for shortcut, canonical in FOCUS_SHORTCUTS.items():
        if shortcut in normalized:
            return (canonical, FOCUS_DESCRIPTIONS[canonical])
    
    # No match - pass through raw input for LLM interpretation
    return (raw_input, raw_input)


def load_repo_goals(project_path: str) -> Optional[str]:
    """
    Load goals document from repo if it exists.
    
    Returns:
        Optional[str]: Content of goals file, or None if not found
    """
    path = Path(project_path).resolve()
    
    for goal_path in GOAL_DOC_PATHS:
        full_path = path / goal_path
        if full_path.exists():
            return full_path.read_text()
    
    return None


# =============================================================================
# SETUP CHECK - Ensure MAW is initialized before use
# =============================================================================

def check_maw_setup(project_path: str) -> tuple[bool, str]:
    """
    Check if MAW has been set up in this repo.
    
    Returns:
        tuple: (is_setup, message)
        - If setup: (True, "")
        - If not: (False, helpful message about running maw_setup)
    """
    path = Path(project_path).resolve()
    
    required_files = [
        ("WORKFLOW_STATE.json", "workflow state tracking"),
        ("MAW_README.md", "MAW documentation and examples"),
    ]
    
    missing = []
    for filename, description in required_files:
        if not (path / filename).exists():
            missing.append(f"- {filename} ({description})")
    
    if missing:
        return (False, f"""## ⚠️ MAW Not Set Up

This repo hasn't been initialized for MAW workflow.

**Missing:**
{chr(10).join(missing)}

**Run `maw_setup` first** to create:
- MAW_README.md - How to use MAW (keep this for reference!)
- WORKFLOW_STATE.json - Tracks your workflow progress
- GOALS.md - Your project priorities (customize this)
- PROJECT_LEARNINGS.md - Capture insights as you go
- AGENT_PROMPTS/ - Where agent tasks go

All files are gitignored by default.""")
    
    return (True, "")


# =============================================================================
# FILE TEMPLATES - Created by maw_setup
# =============================================================================

MAW_README_TEMPLATE = '''# MAW Workflow Guide

This repo uses MAW (Multi-Agent Workflow) to coordinate parallel AI development.

## Quick Reference

| Command | What It Does |
|---------|--------------|
| `maw_status` | Where am I? What's next? |
| `maw_review` | Analyze code, create agent tasks |
| `maw_launch` | Get copy-paste prompts for agents |
| `maw_launch next=true` | Sequential mode: one task at a time |
| `maw_checkin` | Check agent progress (auto-fetches PRs) |
| `maw_integrate` | Get merge order + test checklist |
| `maw_decide` | Deploy, iterate, or move on? |
| `maw_clean` | Reset for next iteration |

## Typical Session

```
1. maw_review focus="ui"     # Analyze, create agent prompts
2. [Review AGENT_PROMPTS/]   # Sanity check before launching
3. maw_launch                # Get prompts for each agent
4. [Run agents in parallel]  # Paste into Cursor/Claude Code windows
5. maw_checkin               # See who's done
6. maw_integrate             # Merge order + tests
7. [Merge PRs, run tests]
8. maw_decide                # Ship it or iterate?
```

## Focus Options

Use shortcuts or natural language:

| Shortcut | Covers |
|----------|--------|
| `ui` | styling, layout, forms, mobile, UX |
| `api` | endpoints, routes, requests |
| `data` | database, schema, queries |
| `performance` | speed, caching, optimization |
| `testing` | coverage, unit tests, e2e |
| `security` | auth, validation, secrets |
| `docs` | readme, comments, guides |
| `errors` | error handling, logging |

Or just describe it:
```
maw_review focus="make the checkout flow less confusing"
maw_review focus="error messages are unhelpful"
```

## Files in This Repo

| File | Purpose | Edit? |
|------|---------|-------|
| `MAW_README.md` | This guide | No |
| `GOALS.md` | Your priorities - MAW reads this | **Yes!** |
| `WORKFLOW_STATE.json` | Current phase/progress | No (auto) |
| `PROJECT_LEARNINGS.md` | Session notes | Optional |
| `AGENT_PROMPTS/` | Generated agent tasks | Review only |

## Best Practices

1. **Review before launch** - Always check AGENT_PROMPTS/ before running agents
2. **Keep GOALS.md updated** - MAW uses it to prioritize
3. **One iteration at a time** - Complete the cycle before starting another
4. **Capture learnings** - Use `maw_learn` when you hit something tricky

## When to Use Sequential Mode

Can't run multiple agents? Use `maw_launch next=true`:
- Returns one task at a time
- Call again to get the next task
- State persists across sessions

Good for small projects or limited compute.

## When NOT to Use MAW

- Single-file changes
- Quick fixes (< 30 min)

Just do those directly.

## Troubleshooting

**"MAW Not Set Up" error**
Run `maw_setup` - you're in a repo that wasn't initialized.

**Agents stepping on each other**
Check COORDINATION.md - some agents need to go first.

**Merge conflicts**
`maw_integrate` warns about these. Merge one at a time, rebase after each.

---
*Generated by maw_setup. Keep this file for reference.*
'''

GOALS_TEMPLATE = '''# Project Goals

MAW reads this file to prioritize what to work on.
Update this as your priorities change!

## Active Focus
<!-- What you're working on NOW - MAW prioritizes these -->
- 

## Backlog  
<!-- Coming up next - MAW considers these secondary -->
- 

## Not Now
<!-- Explicitly deprioritized - MAW skips unless critical -->
- 

## Long-term Vision
<!-- Where is this project going? Helps MAW understand context -->


---
*Tip: Be specific. "Fix UI" is vague. "Mobile touch targets too small on inventory page" is actionable.*
'''

LEARNINGS_TEMPLATE = '''# Project Learnings

Capture insights as you work. Use `maw_learn` to add entries, or edit directly.

---

'''
CONTENT_DIR = Path(__file__).parent.parent / "content"


def slugify(text: str) -> str:
    """Convert text to URL-safe slug"""
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')[:30]


# =============================================================================
# TOOL: maw_status
# =============================================================================
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="maw_status",
            description="Show current workflow state and recommended next action",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {
                        "type": "string",
                        "description": "Path to project (default: current directory)",
                        "default": "."
                    }
                }
            }
        ),
        Tool(
            name="maw_review",
            description="Analyze codebase, identify improvements, generate agent prompts. PAUSES for your review before agents can be launched. Checks for GOALS.md to prioritize findings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "focus": {
                        "type": "string",
                        "description": "Focus area - use shortcuts (ui, api, data, security, testing, docs, performance, architecture, errors, dx) or natural language (e.g., 'make forms less janky', 'error handling is weak')"
                    },
                    "wave_name": {
                        "type": "string",
                        "description": "Name for this wave of improvements (e.g., 'Foundation & Security')"
                    }
                }
            }
        ),
        Tool(
            name="maw_launch",
            description="Get agent prompts with branch names and launch sequence. Use next=true for sequential single-agent mode.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "agent_id": {
                        "type": "integer",
                        "description": "Get prompt for specific agent only"
                    },
                    "next": {
                        "type": "boolean",
                        "description": "Sequential mode: get only the next unstarted task (default: false, returns all)",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="maw_checkin",
            description="Check agent progress. Auto-fetches from GitHub PRs, or paste reports manually.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "reports": {
                        "type": "string",
                        "description": "Optional: paste reports manually (auto-fetches from GitHub if omitted)"
                    },
                    "auto": {
                        "type": "boolean",
                        "description": "Auto-fetch from GitHub PRs (default: true)",
                        "default": True
                    }
                }
            }
        ),
        Tool(
            name="maw_integrate",
            description="Get merge order, test plan, and integration checklist",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."}
                }
            }
        ),
        Tool(
            name="maw_decide",
            description="Get recommendation to deploy, iterate, or add features",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."}
                }
            }
        ),
        Tool(
            name="maw_learn",
            description="Capture learnings from current session to PROJECT_LEARNINGS.md",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "learning": {
                        "type": "string",
                        "description": "What you learned (or leave blank for guided capture)"
                    },
                    "promote": {
                        "type": "boolean",
                        "description": "Also add to central UNIVERSAL_PATTERNS.md",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="maw_patterns",
            description="Search or browse accumulated patterns from UNIVERSAL_PATTERNS.md",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search term (leave blank to list all)"
                    }
                }
            }
        ),
        Tool(
            name="maw_setup",
            description="Initialize a repo for MAW workflow. Creates AGENT_PROMPTS/, WORKFLOW_STATE.json, updates .gitignore",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."}
                }
            }
        ),
        Tool(
            name="maw_clean",
            description="Clean up after iteration. Removes old agent prompts, resets state, optionally deletes branches",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "delete_branches": {
                        "type": "boolean",
                        "description": "Also delete local agent/* branches",
                        "default": False
                    },
                    "delete_remote": {
                        "type": "boolean",
                        "description": "Also delete remote agent/* branches",
                        "default": False
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Route tool calls to handlers"""
    handlers = {
        "maw_status": handle_status,
        "maw_review": handle_review,
        "maw_launch": handle_launch,
        "maw_checkin": handle_checkin,
        "maw_integrate": handle_integrate,
        "maw_decide": handle_decide,
        "maw_learn": handle_learn,
        "maw_patterns": handle_patterns,
        "maw_setup": handle_setup,
        "maw_clean": handle_clean,
    }
    
    handler = handlers.get(name)
    if not handler:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]
    
    result = await handler(arguments)
    return [TextContent(type="text", text=result)]


# =============================================================================
# HANDLERS
# =============================================================================

async def handle_status(args: dict) -> str:
    """Show current workflow state"""
    project_path = args.get("project_path", ".")
    state = load_state(project_path)
    
    status = format_status(state)
    next_step = suggest_next_step(state)
    
    return f"{status}\n\n{next_step}"


async def handle_review(args: dict) -> str:
    """Review: Analyze and generate agent prompts"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    raw_focus = args.get("focus", "all")
    wave_name = args.get("wave_name", "")
    
    state = load_state(project_path)
    path = Path(project_path).resolve()
    
    # Create AGENT_PROMPTS directory
    prompts_dir = path / "AGENT_PROMPTS"
    prompts_dir.mkdir(exist_ok=True)
    
    # Resolve focus - handles natural language
    focus_name, focus_description = resolve_focus(raw_focus)
    
    # Load repo goals if they exist
    repo_goals = load_repo_goals(project_path)
    
    # Build the goals context section
    goals_section = ""
    if repo_goals:
        goals_section = f"""
### Repository Goals (from GOALS.md)

The repository has a goals document. Use it to prioritize findings:

```
{repo_goals}
```

**Priority Rules:**
1. Items under "Active Focus" or "Current" are highest priority
2. Items under "Backlog" or "Next" are secondary
3. Items under "Not Now" or "Deferred" should be skipped unless critical
4. The --focus flag (if provided) overrides these defaults
"""
    
    # Build focus context section
    if focus_name == "all":
        focus_section = "**Focus:** All areas (comprehensive analysis)"
    elif focus_name == raw_focus:
        # Custom/natural language focus - pass through to LLM
        focus_section = f"""**Focus:** Custom focus requested

User said: "{raw_focus}"

Interpret this and prioritize findings related to this goal.
Deprioritize or omit unrelated findings unless they are critical issues."""
    else:
        # Matched a canonical focus area
        focus_section = f"""**Focus:** {focus_name.upper()}

{focus_description}

Prioritize findings in this area. Include critical issues from other areas, 
but deprioritize or omit non-critical findings unrelated to {focus_name}."""
    
    analysis_prompt = f"""
## Review: Codebase Analysis

Analyze this codebase and identify 3-5 high-impact improvements.

{focus_section}

**Wave:** {wave_name or "Wave 1"}
{goals_section}

### Analysis Areas
1. **Performance** - Slow queries, memory issues, N+1 problems
2. **Security** - Auth, validation, injection risks
3. **Code Quality** - Duplication, complexity, error handling
4. **Testing** - Coverage gaps, missing integration tests
5. **Documentation** - README, API docs, setup guides

### Output Required

For each improvement, create a file in `AGENT_PROMPTS/`:

```
AGENT_PROMPTS/
├── 1_Backend_Engineer.md
├── 2_Security_Hardening.md
├── 3_Testing_Infrastructure.md
├── COORDINATION.md
└── README.md
```

### Agent Prompt Template

Each agent file must include:

```markdown
# Agent N: [Role Name]

## Mission
[One sentence goal]

## Branch
`agent/N-[slug]`

## Files to Modify
- path/to/file1.py
- path/to/file2.py

## Tasks
1. [Specific task]
2. [Specific task]

## Definition of Done
- [ ] [Deliverable]
- [ ] Tests pass
- [ ] PR created

## Time Estimate
[X] hours
```

### Launch Sequence

Specify in COORDINATION.md:
- Which agent(s) run first
- Which can run in parallel
- Dependencies between agents

### After Creating Prompts

Update WORKFLOW_STATE.json:
- Set phase: 3
- Set review_complete: true
- Add agents array with id, role, slug, branch for each

Then tell the user: "Review AGENT_PROMPTS/ before running maw_launch"
"""
    
    # Update state
    state.phase = "review"
    state.status = "reviewing"
    if wave_name:
        state.wave = WaveInfo(number=state.iteration + 1, name=wave_name)
    save_state(state, project_path)
    
    return analysis_prompt


async def handle_launch(args: dict) -> str:
    """Launch: Get agent prompts with sequencing"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    agent_id = args.get("agent_id")
    next_only = args.get("next", False)
    
    state = load_state(project_path)
    path = Path(project_path).resolve()
    prompts_dir = path / "AGENT_PROMPTS"
    
    if not state.review_complete:
        return """⚠️ Review not complete.

Run maw_review first to:
1. Analyze the codebase
2. Generate agent prompts in AGENT_PROMPTS/
3. Set review_complete in state

Then you can run maw_launch."""
    
    if not prompts_dir.exists():
        return f"⚠️ AGENT_PROMPTS/ not found at {prompts_dir}"
    
    # Read agent prompts
    prompt_files = sorted(prompts_dir.glob("[0-9]_*.md"))
    if not prompt_files:
        return "⚠️ No agent prompt files found (expected: 1_Role.md, 2_Role.md, etc.)"
    
    # =========================================================================
    # SEQUENTIAL MODE: Return one task at a time
    # =========================================================================
    if next_only:
        state.mode = "sequential"
        total_tasks = len(prompt_files)
        
        # Check if all tasks are done
        if state.current_task_index >= total_tasks:
            return f"""## ✅ All {total_tasks} Tasks Complete

You've worked through all agent tasks sequentially.

**Next steps:**
- Run `maw_clean` to reset for a new iteration
- Run `maw_review` to identify more improvements
- Or you're done! 🎉"""
        
        # Get current task
        current_file = prompt_files[state.current_task_index]
        agent_num = int(current_file.name.split("_")[0])
        content = current_file.read_text()
        role = current_file.stem.split("_", 1)[1].replace("_", " ")
        
        # Extract branch from content or generate
        branch_match = re.search(r'`(agent/\d+-[^`]+)`', content)
        branch = branch_match.group(1) if branch_match else f"agent/{agent_num}-{slugify(role)}"
        
        lines = [
            f"## 🔢 Task {state.current_task_index + 1} of {total_tasks}",
            "",
            f"### Agent {agent_num}: {role}",
            f"**Branch:** `{branch}`",
            "",
            "```",
            f"You are Agent {agent_num}: {role}",
            f"Branch: {branch}",
            f"Read and implement: AGENT_PROMPTS/{current_file.name}",
            "Create PR when done.",
            "START NOW",
            "```",
            "",
            "---",
            "",
            f"*Run `maw_launch next=true` again for the next task ({total_tasks - state.current_task_index - 1} remaining)*",
        ]
        
        # Increment for next time
        state.current_task_index += 1
        state.phase = "launch"
        state.status = "launching"
        save_state(state, project_path)
        
        return "\n".join(lines)
    
    # =========================================================================
    # PARALLEL MODE: Return all tasks (existing behavior)
    # =========================================================================
    state.mode = "parallel"
    
    # Build launch output
    lines = ["## 🚀 Agent Launch Sequence\n"]
    
    # Read COORDINATION.md for sequence info
    coord_file = prompts_dir / "COORDINATION.md"
    if coord_file.exists():
        lines.append("### Launch Order")
        lines.append(coord_file.read_text())
        lines.append("")
    else:
        lines.append("### Launch Order")
        lines.append("1. Agent 1 - Run first (~20 min)")
        lines.append("2. Agents 2+ - Run in parallel after Agent 1 creates base\n")
    
    lines.append("---\n")
    lines.append("### Agent Prompts\n")
    lines.append("Copy each prompt to a separate Cursor/Claude Code session:\n")
    
    for pf in prompt_files:
        agent_num = int(pf.name.split("_")[0])
        
        if agent_id and agent_num != agent_id:
            continue
        
        content = pf.read_text()
        role = pf.stem.split("_", 1)[1].replace("_", " ")
        
        # Extract branch from content or generate
        branch_match = re.search(r'`(agent/\d+-[^`]+)`', content)
        branch = branch_match.group(1) if branch_match else f"agent/{agent_num}-{slugify(role)}"
        
        lines.append(f"#### Agent {agent_num}: {role}")
        lines.append(f"**Branch:** `{branch}`")
        lines.append("")
        lines.append("```")
        lines.append(f"You are Agent {agent_num}: {role}")
        lines.append(f"Branch: {branch}")
        lines.append(f"Read and implement: AGENT_PROMPTS/{pf.name}")
        lines.append("Create PR when done.")
        lines.append("START NOW")
        lines.append("```")
        lines.append("")
    
    # Update state
    state.phase = "launch"
    state.status = "launching"
    save_state(state, project_path)
    
    return "\n".join(lines)


async def handle_checkin(args: dict) -> str:
    """Checkin: Evaluate progress and provide guidance"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    reports = args.get("reports", "")
    auto_fetch = args.get("auto", True)  # Auto-fetch from GitHub by default
    
    # If no reports provided, try to fetch from GitHub
    if not reports and auto_fetch:
        success, prs = get_agent_prs(project_path)
        
        if success and prs:
            conflicts = detect_conflicts(prs)
            return format_pr_dashboard(prs, conflicts)
        elif success and not prs:
            # No agent PRs found - check for local branches
            local_branches = get_local_branches(project_path)
            agent_branches = [b for b in local_branches if b.startswith("agent/")]
            
            if agent_branches:
                lines = ["## 📊 Agent Status\n"]
                lines.append("### Local Branches (no PRs yet)")
                lines.append("These agent branches exist but don't have PRs:\n")
                for branch in agent_branches:
                    lines.append(f"- `{branch}`")
                lines.append("\nAgents should create PRs when done.")
                lines.append("\nOr paste completion reports manually below.")
                return "\n".join(lines)
            else:
                return """## Agent Check-in

No agent PRs or branches found.

**Options:**
1. Wait for agents to create PRs (they'll appear automatically)
2. Paste completion reports manually:

```
Agent 1 Done.
✓ [What they did]
PR: #N or URL

Agent 2 Done.
...
```"""
        else:
            # GitHub fetch failed - fall back to manual
            return f"""## Agent Check-in

⚠️ Couldn't fetch from GitHub: {prs}

**Fallback:** Paste completion reports manually:

```
Agent 1 Done.
✓ [What they did]  
PR: #N or URL

Agent 2 Done.
...
```"""
    
    # Manual reports provided - parse them
    if not reports:
        return """## Agent Check-in

Paste completion reports from each agent, or just run `maw_checkin` to auto-fetch from GitHub PRs."""

    # Parse completion reports
    lines = ["## 📊 Agent Status Dashboard\n"]
    
    # Extract agent statuses
    agent_blocks = re.split(r'## Agent \d+ Completion Report', reports)
    agent_headers = re.findall(r'## Agent (\d+) Completion Report', reports)
    
    complete = []
    partial = []
    blocked = []
    prs = []
    all_files = []
    all_endpoints = []
    all_tests = {"added": 0, "passing": True}
    integration_notes = []
    
    for i, header in enumerate(agent_headers):
        block = agent_blocks[i + 1] if i + 1 < len(agent_blocks) else ""
        agent_num = int(header)
        
        # Extract status
        status_match = re.search(r'\*\*Status:\*\*\s*(.*)', block)
        status = status_match.group(1).strip() if status_match else "Unknown"
        
        # Extract PR
        pr_match = re.search(r'\*\*PR:\*\*\s*#?(\d+|.*)', block)
        pr = pr_match.group(1).strip() if pr_match else None
        
        # Extract branch
        branch_match = re.search(r'\*\*Branch:\*\*\s*`([^`]+)`', block)
        branch = branch_match.group(1) if branch_match else f"agent/{agent_num}-unknown"
        
        # Categorize
        if "Complete" in status or "✅" in status:
            complete.append((agent_num, branch, pr))
        elif "Partial" in status or "⚠️" in status:
            partial.append((agent_num, branch, pr))
        elif "Blocked" in status or "❌" in status:
            blocked.append((agent_num, branch, pr))
        
        if pr and pr not in ["None", "N/A", ""]:
            prs.append((agent_num, pr))
        
        # Extract files changed
        files_section = re.search(r'### Files Changed\s*\n\|[^\n]+\n\|[^\n]+\n((?:\|[^\n]+\n)*)', block)
        if files_section:
            for file_line in files_section.group(1).strip().split('\n'):
                parts = file_line.split('|')
                if len(parts) >= 3:
                    all_files.append(parts[1].strip())
        
        # Extract endpoints
        endpoints_section = re.search(r'### API/Endpoints Affected\s*\n((?:- [^\n]+\n)*)', block)
        if endpoints_section:
            for ep_line in endpoints_section.group(1).strip().split('\n'):
                if ep_line.startswith('- '):
                    all_endpoints.append(ep_line[2:].strip())
        
        # Extract test count
        tests_match = re.search(r'\*\*Added:\*\*\s*(\d+)', block)
        if tests_match:
            all_tests["added"] += int(tests_match.group(1))
        if "failing" in block.lower():
            all_tests["passing"] = False
        
        # Extract integration notes
        notes_section = re.search(r'### Notes for Integration\s*\n((?:- [^\n]+\n)*)', block)
        if notes_section:
            for note_line in notes_section.group(1).strip().split('\n'):
                if note_line.startswith('- '):
                    integration_notes.append(f"Agent {agent_num}: {note_line[2:]}")
    
    # Build summary
    total = len(complete) + len(partial) + len(blocked)
    lines.append(f"### Summary")
    lines.append(f"| Status | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| ✅ Complete | {len(complete)} |")
    lines.append(f"| ⚠️ Partial | {len(partial)} |")
    lines.append(f"| ❌ Blocked | {len(blocked)} |")
    lines.append(f"| **Total** | **{total}** |")
    lines.append("")
    
    # Agent details
    if complete:
        lines.append("### ✅ Complete")
        for agent_num, branch, pr in complete:
            pr_text = f" → PR #{pr}" if pr else ""
            lines.append(f"- Agent {agent_num}: `{branch}`{pr_text}")
        lines.append("")
    
    if partial:
        lines.append("### ⚠️ Partial (needs attention)")
        for agent_num, branch, pr in partial:
            lines.append(f"- Agent {agent_num}: `{branch}`")
        lines.append("")
    
    if blocked:
        lines.append("### ❌ Blocked (needs resolution)")
        for agent_num, branch, pr in blocked:
            lines.append(f"- Agent {agent_num}: `{branch}`")
        lines.append("")
    
    # PRs ready for review
    if prs:
        lines.append("### 📋 PRs Ready")
        for agent_num, pr in prs:
            lines.append(f"- PR #{pr} (Agent {agent_num})")
        lines.append("")
    
    # Files changed aggregate
    if all_files:
        lines.append("### 📁 Files Changed (all agents)")
        for f in sorted(set(all_files)):
            lines.append(f"- `{f}`")
        lines.append("")
    
    # Endpoints affected
    if all_endpoints:
        lines.append("### 🔌 Endpoints Affected")
        for ep in sorted(set(all_endpoints)):
            lines.append(f"- {ep}")
        lines.append("")
    
    # Test summary
    lines.append("### 🧪 Tests")
    lines.append(f"- New tests added: {all_tests['added']}")
    lines.append(f"- Status: {'✅ All passing' if all_tests['passing'] else '❌ Some failing'}")
    lines.append("")
    
    # Integration notes
    if integration_notes:
        lines.append("### ⚠️ Integration Notes")
        for note in integration_notes:
            lines.append(f"- {note}")
        lines.append("")
    
    # Next steps
    lines.append("---")
    lines.append("")
    if blocked:
        lines.append("### 🚨 Action Required")
        lines.append("Resolve blocked agents before proceeding to integration.")
        lines.append("")
    elif partial:
        lines.append("### ⏳ Waiting")
        lines.append("Wait for partial agents to complete, or run another check-in in 30 min.")
        lines.append("")
    elif complete and len(complete) == total:
        lines.append("### ✅ Ready for Integration")
        lines.append("All agents complete! Run `maw_integrate` for merge guidance.")
        lines.append("")
    
    return "\n".join(lines)


async def handle_integrate(args: dict) -> str:
    """Integrate: Merge guidance with test plan"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    state = load_state(project_path)
    path = Path(project_path).resolve()
    
    lines = ["## Integrate\n"]
    
    # Try to fetch PRs from GitHub first
    gh_success, prs = get_agent_prs(project_path)
    gh_conflicts = detect_conflicts(prs) if gh_success and prs else []
    
    # Collect file info from GitHub PRs or AGENT_PROMPTS
    prompts_dir = path / "AGENT_PROMPTS"
    agents_info = []
    all_files = set()
    all_endpoints = set()
    has_db_changes = False
    has_env_changes = False
    
    # If we have GitHub PRs, use that data
    if gh_success and prs:
        for pr in prs:
            agent_num = pr.get("agent_num", 0)
            branch = pr.get("headRefName", "")
            role = branch.replace(f"agent/{agent_num}-", "").replace("-", " ").title()
            agents_info.append((agent_num, role, pr.get("number")))
            
            for f in pr.get("files", []):
                file_path = f.get("path", str(f)) if isinstance(f, dict) else str(f)
                all_files.add(file_path)
                
                # Check for DB/env indicators
                if any(x in file_path.lower() for x in ['migration', 'model', 'database', 'db']):
                    has_db_changes = True
                if any(x in file_path.lower() for x in ['config', 'env', '.env']):
                    has_env_changes = True
    
    # Fall back to AGENT_PROMPTS if no GitHub data
    elif prompts_dir.exists():
        for pf in sorted(prompts_dir.glob("[0-9]_*.md")):
            agent_num = int(pf.name.split("_")[0])
            role = pf.stem.split("_", 1)[1].replace("_", " ")
            content = pf.read_text()
            
            files_section = re.search(r'## Files to Modify\s*\n((?:- [^\n]+\n)*)', content)
            if files_section:
                for line in files_section.group(1).strip().split('\n'):
                    if line.startswith('- '):
                        file_path = re.match(r'- `?([^`\s]+)', line)
                        if file_path:
                            all_files.add(file_path.group(1))
            
            agents_info.append((agent_num, role, None))  # No PR number
            
            if 'migration' in content.lower() or 'database' in content.lower():
                has_db_changes = True
            if 'env' in content.lower() or 'config' in content.lower():
                has_env_changes = True
    
    # Detect endpoint files
    for f in all_files:
        if 'route' in f.lower() or 'api' in f.lower() or 'endpoint' in f.lower():
            all_endpoints.add(f)
    
    # Pre-merge checklist
    lines.append("### Pre-Merge Checklist")
    lines.append("- [ ] All agents report complete (run `maw_checkin`)")
    lines.append("- [ ] All PRs created and passing CI")
    if gh_conflicts:
        lines.append(f"- [ ] ⚠️ **{len(gh_conflicts)} file conflicts** - merge carefully (see below)")
    else:
        lines.append("- [ ] No merge conflicts detected")
    if has_db_changes:
        lines.append("- [ ] Database backup created")
        lines.append("- [ ] Migration tested on staging")
    if has_env_changes:
        lines.append("- [ ] New environment variables documented")
        lines.append("- [ ] .env.example updated")
    lines.append("")
    
    # Conflict warnings
    if gh_conflicts:
        lines.append("### ⚠️ File Conflicts Detected")
        lines.append("These files are modified by multiple PRs:\n")
        lines.append("| File | PRs |")
        lines.append("|------|-----|")
        for c in gh_conflicts:
            pr_list = ", ".join(f"#{n}" for n in c["prs"])
            lines.append(f"| `{c['file']}` | {pr_list} |")
        lines.append("")
        lines.append("**Merge one at a time, rebasing after each.**")
        lines.append("")
    
    # Merge order
    lines.append("### Recommended Merge Order\n")
    
    # Categorize agents by type for merge order
    docs_agents = []
    test_agents = []
    backend_agents = []
    frontend_agents = []
    other_agents = []
    
    for item in agents_info:
        agent_num = item[0]
        role = item[1]
        pr_num = item[2] if len(item) > 2 else None
        role_lower = role.lower()
        
        agent_entry = (agent_num, role, pr_num)
        if 'doc' in role_lower or 'writer' in role_lower or 'deploy' in role_lower:
            docs_agents.append(agent_entry)
        elif 'test' in role_lower or 'qa' in role_lower or 'integration' in role_lower:
            test_agents.append(agent_entry)
        elif 'backend' in role_lower or 'api' in role_lower or 'security' in role_lower or 'database' in role_lower or 'logging' in role_lower:
            backend_agents.append(agent_entry)
        elif 'frontend' in role_lower or 'ui' in role_lower or 'interface' in role_lower or 'offline' in role_lower:
            frontend_agents.append(agent_entry)
        else:
            other_agents.append(agent_entry)
    
    merge_order = 1
    merge_sequence = []  # Track order for commands
    
    if docs_agents:
        lines.append(f"**{merge_order}. Documentation** (lowest risk)")
        for agent_num, role, pr_num in docs_agents:
            pr_text = f" → PR #{pr_num}" if pr_num else ""
            lines.append(f"   - Agent {agent_num}: {role}{pr_text}")
            if pr_num:
                merge_sequence.append(pr_num)
        merge_order += 1
    
    if test_agents:
        lines.append(f"**{merge_order}. Tests** (low risk, improves safety)")
        for agent_num, role, pr_num in test_agents:
            pr_text = f" → PR #{pr_num}" if pr_num else ""
            lines.append(f"   - Agent {agent_num}: {role}{pr_text}")
            if pr_num:
                merge_sequence.append(pr_num)
        merge_order += 1
    
    if backend_agents:
        lines.append(f"**{merge_order}. Backend/Infrastructure**")
        for agent_num, role, pr_num in backend_agents:
            pr_text = f" → PR #{pr_num}" if pr_num else ""
            lines.append(f"   - Agent {agent_num}: {role}{pr_text}")
            if pr_num:
                merge_sequence.append(pr_num)
        merge_order += 1
    
    if frontend_agents:
        lines.append(f"**{merge_order}. Frontend/UI** (after backend stable)")
        for agent_num, role, pr_num in frontend_agents:
            pr_text = f" → PR #{pr_num}" if pr_num else ""
            lines.append(f"   - Agent {agent_num}: {role}{pr_text}")
            if pr_num:
                merge_sequence.append(pr_num)
        merge_order += 1
    
    if other_agents:
        lines.append(f"**{merge_order}. Other**")
        for agent_num, role, pr_num in other_agents:
            pr_text = f" → PR #{pr_num}" if pr_num else ""
            lines.append(f"   - Agent {agent_num}: {role}{pr_text}")
            if pr_num:
                merge_sequence.append(pr_num)
    
    lines.append("")
    
    # Merge commands with actual PR numbers
    lines.append("### Merge Commands\n")
    
    if merge_sequence:
        lines.append("```bash")
        lines.append("# Merge in this order:")
        for pr_num in merge_sequence:
            lines.append(f"gh pr merge {pr_num} --squash && git pull && pytest")
        lines.append("```")
    else:
        lines.append("```bash")
        lines.append("# For each PR in order:")
        lines.append("gh pr view <number>           # Review changes")
        lines.append("gh pr checks <number>         # Verify CI passes")
        lines.append("gh pr merge <number> --squash # Merge")
        lines.append("git pull                      # Update local")
        lines.append("pytest                        # Run tests")
        lines.append("```")
    lines.append("")
    
    # =========================================================================
    # COMPREHENSIVE TEST PLAN
    # =========================================================================
    lines.append("---\n")
    lines.append("## 🧪 Pre-Integration Test Plan\n")
    lines.append("Run these tests after all merges, before deploying.\n")
    
    # Health check
    lines.append("### Health Check")
    lines.append("| Test | Expected | Status |")
    lines.append("|------|----------|--------|")
    lines.append("| App starts without errors | Clean startup | ☐ |")
    lines.append("| GET /api/health (or /) | 200 OK | ☐ |")
    lines.append("| Database connection | Connected | ☐ |")
    lines.append("")
    
    # API Endpoints
    if all_endpoints or all_files:
        lines.append("### API Endpoints")
        lines.append("| Endpoint | Method | Test | Status |")
        lines.append("|----------|--------|------|--------|")
        
        # Generate endpoint tests based on files changed
        endpoint_tests = []
        for f in sorted(all_files):
            if 'route' in f.lower() or 'api' in f.lower():
                endpoint_tests.append(f"| Routes in `{f}` | Various | Smoke test all endpoints | ☐ |")
            elif 'auth' in f.lower():
                endpoint_tests.append("| /auth/login | POST | Valid credentials → 200 | ☐ |")
                endpoint_tests.append("| /auth/login | POST | Invalid credentials → 401 | ☐ |")
                endpoint_tests.append("| /auth/logout | POST | Clears session → 200 | ☐ |")
            elif 'user' in f.lower():
                endpoint_tests.append("| /api/users | GET | Returns user list | ☐ |")
                endpoint_tests.append("| /api/users/:id | GET | Returns user or 404 | ☐ |")
        
        if endpoint_tests:
            for test in endpoint_tests:
                lines.append(test)
        else:
            lines.append("| (endpoints from agent work) | - | Verify all new/changed endpoints | ☐ |")
        lines.append("")
    
    # Web Views
    lines.append("### Web Views (if applicable)")
    lines.append("| Page | Expected | Status |")
    lines.append("|------|----------|--------|")
    lines.append("| / (home) | Loads, HTTP 200 | ☐ |")
    lines.append("| All navigation links | Work correctly | ☐ |")
    lines.append("| Forms submit | No JS errors | ☐ |")
    lines.append("")
    
    # Edge Cases based on what was changed
    lines.append("### Edge Cases")
    lines.append("| Test | Expected | Status |")
    lines.append("|------|----------|--------|")
    if has_db_changes:
        lines.append("| Empty database | Handles gracefully | ☐ |")
        lines.append("| Large dataset | Performance acceptable | ☐ |")
    lines.append("| Invalid input | Returns 400, not 500 | ☐ |")
    lines.append("| Missing required fields | Clear error message | ☐ |")
    lines.append("| Unauthorized access | Returns 401/403 | ☐ |")
    lines.append("")
    
    # Automated tests
    lines.append("### Automated Tests")
    lines.append("```bash")
    lines.append("# Run full test suite")
    lines.append("pytest -v")
    lines.append("")
    lines.append("# With coverage")
    lines.append("pytest --cov=src --cov-report=html")
    lines.append("")
    lines.append("# Specific test files from agent work")
    for f in sorted(all_files):
        if 'test' in f.lower():
            lines.append(f"pytest {f}")
    lines.append("```")
    lines.append("")
    
    # Post-merge verification
    lines.append("### Post-Merge Verification")
    lines.append("| Check | Status |")
    lines.append("|-------|--------|")
    lines.append("| All tests passing | ☐ |")
    lines.append("| No new linting errors | ☐ |")
    lines.append("| App runs locally | ☐ |")
    lines.append("| Manual smoke test | ☐ |")
    if has_db_changes:
        lines.append("| Database migrations applied | ☐ |")
    if has_env_changes:
        lines.append("| Environment variables set | ☐ |")
    lines.append("")
    
    # Bugs found section (template)
    lines.append("### Bugs Found")
    lines.append("| Severity | Issue | Location | Status |")
    lines.append("|----------|-------|----------|--------|")
    lines.append("| - | (none yet) | - | - |")
    lines.append("")
    
    lines.append("---\n")
    lines.append("### After All Tests Pass")
    lines.append("Run `maw_decide` to determine: deploy, iterate, or add features.")
    
    # Update state
    state.phase = "integrate"
    state.status = "integrating"
    save_state(state, project_path)
    
    return "\n".join(lines)


async def handle_decide(args: dict) -> str:
    """Decide: Deploy/iterate/add decision"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    state = load_state(project_path)
    
    return f"""## Decide: What's Next?

### Current State
- Project: {state.project}
- Iteration: {state.iteration}
- Agents completed: {len([a for a in state.agents if a.status == 'complete'])}

### Decision Framework

| Condition | Recommendation |
|-----------|----------------|
| All tests pass, no critical issues | ✅ **Deploy** |
| Minor issues found | ⚠️ **Fix then deploy** |
| Quality score < 7/10, major refactoring needed | 🔄 **Iterate** (run maw_review again) |
| Core solid, users request features | ➕ **Add features** (new iteration) |

### Questions to Answer

1. Are all tests passing?
2. Any critical security issues?
3. Performance acceptable?
4. Documentation up to date?
5. Ready for real users?

### If Deploying

```bash
# Staging first
git checkout main
git pull
# Deploy to staging
# Run smoke tests
# Monitor for 24h

# Then production
# Deploy to production
# Monitor closely
```

### If Iterating

Run `maw_review` with focus on remaining issues.
This starts a new iteration with fresh agent prompts.

### Update State

After deciding, update WORKFLOW_STATE.json:
- If deployed: status = "deployed"
- If iterating: iteration += 1, run maw_review"""


async def handle_learn(args: dict) -> str:
    """Capture learnings"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    learning = args.get("learning", "")
    promote = args.get("promote", False)
    
    path = Path(project_path).resolve()
    learnings_file = path / "PROJECT_LEARNINGS.md"
    
    if not learning:
        return """## Capture Learnings

What did you learn this session? Consider:

- Bugs that took >10 minutes to solve
- Patterns that worked well
- Tools with non-obvious behavior
- Mistakes to avoid next time

Run maw_learn again with your learning:

```
maw_learn learning="[Your learning here]" promote=false
```

Set promote=true to also add to central UNIVERSAL_PATTERNS.md"""
    
    # Append to project learnings
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    entry = f"\n### {timestamp}\n{learning}\n"
    
    if learnings_file.exists():
        content = learnings_file.read_text()
        learnings_file.write_text(content + entry)
    else:
        learnings_file.write_text(f"# Project Learnings\n{entry}")
    
    result = f"✅ Added to PROJECT_LEARNINGS.md"
    
    if promote:
        patterns_file = CONTENT_DIR / "UNIVERSAL_PATTERNS.md"
        example_file = CONTENT_DIR / "UNIVERSAL_PATTERNS.example.md"
        
        # Create from example if doesn't exist
        if not patterns_file.exists() and example_file.exists():
            patterns_file.write_text(example_file.read_text())
        
        if patterns_file.exists():
            content = patterns_file.read_text()
            patterns_file.write_text(content + f"\n---\n\n### From {path.name}\n**Date:** {timestamp}\n\n{learning}\n")
            result += "\n✅ Also added to UNIVERSAL_PATTERNS.md"
    
    return result


async def handle_patterns(args: dict) -> str:
    """Search or browse patterns"""
    query = args.get("query", "").lower()
    
    patterns_file = CONTENT_DIR / "UNIVERSAL_PATTERNS.md"
    example_file = CONTENT_DIR / "UNIVERSAL_PATTERNS.example.md"
    
    # Create from example if doesn't exist
    if not patterns_file.exists():
        if example_file.exists():
            patterns_file.write_text(example_file.read_text())
        else:
            return "⚠️ UNIVERSAL_PATTERNS.md not found. Run `maw_learn promote=true` to start capturing patterns."
    
    content = patterns_file.read_text()
    
    if not query:
        # Return table of contents
        lines = ["## Universal Patterns\n"]
        for line in content.split("\n"):
            if line.startswith("### "):
                lines.append(f"- {line[4:]}")
        lines.append("\n\nRun `maw_patterns query=\"keyword\"` to search.")
        return "\n".join(lines)
    
    # Search for matching sections
    sections = content.split("### ")
    matches = []
    
    for section in sections[1:]:  # Skip header
        if query in section.lower():
            # Get just the title and first few lines
            lines = section.split("\n")
            title = lines[0]
            preview = "\n".join(lines[1:10])
            matches.append(f"### {title}\n{preview}...")
    
    if not matches:
        return f"No patterns found matching '{query}'"
    
    return f"## Patterns matching '{query}'\n\n" + "\n\n---\n\n".join(matches)


async def handle_setup(args: dict) -> str:
    """Initialize repo for MAW workflow with all required files"""
    project_path = args.get("project_path", ".")
    path = Path(project_path).resolve()
    
    lines = ["## MAW Setup\n"]
    created = []
    skipped = []
    
    # 1. Create MAW_README.md - the reference guide
    readme_file = path / "MAW_README.md"
    if not readme_file.exists():
        readme_file.write_text(MAW_README_TEMPLATE)
        created.append("MAW_README.md - Your MAW reference guide")
    else:
        skipped.append("MAW_README.md (exists)")
    
    # 2. Create GOALS.md - user's priorities
    goals_file = path / "GOALS.md"
    if not goals_file.exists():
        goals_file.write_text(GOALS_TEMPLATE)
        created.append("GOALS.md - **Edit this with your priorities!**")
    else:
        skipped.append("GOALS.md (exists)")
    
    # 3. Create WORKFLOW_STATE.json
    state_file = path / "WORKFLOW_STATE.json"
    if not state_file.exists():
        state = WorkflowState.empty(path)
        save_state(state, project_path)
        created.append("WORKFLOW_STATE.json - Workflow tracking")
    else:
        skipped.append("WORKFLOW_STATE.json (exists)")
    
    # 4. Create PROJECT_LEARNINGS.md
    learnings_file = path / "PROJECT_LEARNINGS.md"
    if not learnings_file.exists():
        learnings_file.write_text(LEARNINGS_TEMPLATE)
        created.append("PROJECT_LEARNINGS.md - Session notes")
    else:
        skipped.append("PROJECT_LEARNINGS.md (exists)")
    
    # 5. Create AGENT_PROMPTS directory
    prompts_dir = path / "AGENT_PROMPTS"
    if not prompts_dir.exists():
        prompts_dir.mkdir()
        (prompts_dir / ".gitkeep").touch()
        created.append("AGENT_PROMPTS/ - Agent task files go here")
    else:
        skipped.append("AGENT_PROMPTS/ (exists)")
    
    # 6. Update .gitignore with all MAW files
    gitignore = path / ".gitignore"
    maw_ignores = [
        "",
        "# MAW workflow (auto-generated, don't commit)",
        "MAW_README.md",
        "GOALS.md",
        "WORKFLOW_STATE.json",
        "PROJECT_LEARNINGS.md",
        "AGENT_PROMPTS/",
    ]
    
    gitignore_updated = False
    if gitignore.exists():
        content = gitignore.read_text()
        # Check if any MAW entries are missing
        missing_entries = [e for e in maw_ignores if e and e not in content and not e.startswith("#")]
        if missing_entries:
            gitignore.write_text(content.rstrip() + "\n" + "\n".join(maw_ignores) + "\n")
            gitignore_updated = True
            created.append(f".gitignore (added {len(missing_entries)} entries)")
    else:
        gitignore.write_text("\n".join(maw_ignores) + "\n")
        gitignore_updated = True
        created.append(".gitignore (created)")
    
    if not gitignore_updated and gitignore.exists():
        skipped.append(".gitignore (already has MAW entries)")
    
    # Build output
    if created:
        lines.append("### ✅ Created")
        for item in created:
            lines.append(f"- {item}")
        lines.append("")
    
    if skipped:
        lines.append("### ⏭️ Skipped (already exist)")
        for item in skipped:
            lines.append(f"- {item}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    lines.append("### 📋 Next Steps")
    lines.append("")
    lines.append("1. **Edit GOALS.md** - Add your current priorities")
    lines.append("2. **Read MAW_README.md** - Quick reference for all commands")
    lines.append("3. **Run `maw_review`** - Analyze codebase and create agent tasks")
    lines.append("")
    lines.append("💡 *All MAW files are gitignored. They're for your local workflow only.*")
    
    return "\n".join(lines)


async def handle_clean(args: dict) -> str:
    """Clean up after iteration"""
    project_path = args.get("project_path", ".")
    
    # Check if MAW is set up
    is_setup, setup_msg = check_maw_setup(project_path)
    if not is_setup:
        return setup_msg
    
    delete_branches = args.get("delete_branches", False)
    delete_remote = args.get("delete_remote", False)
    
    path = Path(project_path).resolve()
    lines = ["## MAW Clean\n"]
    cleaned = []
    
    # Delete AGENT_PROMPTS contents (keep directory)
    prompts_dir = path / "AGENT_PROMPTS"
    if prompts_dir.exists():
        count = 0
        for f in prompts_dir.glob("*.md"):
            f.unlink()
            count += 1
        if count:
            cleaned.append(f"AGENT_PROMPTS/ ({count} files)")
    
    # Reset WORKFLOW_STATE.json
    state_file = path / "WORKFLOW_STATE.json"
    if state_file.exists():
        state = WorkflowState.empty(path)
        state.iteration = 0  # Reset iteration count
        save_state(state, project_path)
        cleaned.append("WORKFLOW_STATE.json (reset to idle)")
    
    # Delete local agent branches
    if delete_branches:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "branch", "--list", "agent/*"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            branches = [b.strip().lstrip("* ") for b in result.stdout.strip().split("\n") if b.strip()]
            
            for branch in branches:
                subprocess.run(
                    ["git", "branch", "-D", branch],
                    cwd=project_path,
                    capture_output=True
                )
            
            if branches:
                cleaned.append(f"Local branches ({len(branches)}): {', '.join(branches)}")
        except Exception as e:
            lines.append(f"⚠️ Could not delete local branches: {e}")
    
    # Delete remote agent branches
    if delete_remote:
        import subprocess
        try:
            result = subprocess.run(
                ["git", "branch", "-r", "--list", "origin/agent/*"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            remote_branches = [b.strip().replace("origin/", "") for b in result.stdout.strip().split("\n") if b.strip()]
            
            for branch in remote_branches:
                subprocess.run(
                    ["git", "push", "origin", "--delete", branch],
                    cwd=project_path,
                    capture_output=True
                )
            
            if remote_branches:
                cleaned.append(f"Remote branches ({len(remote_branches)}): {', '.join(remote_branches)}")
        except Exception as e:
            lines.append(f"⚠️ Could not delete remote branches: {e}")
    
    if cleaned:
        lines.append("### Cleaned")
        for item in cleaned:
            lines.append(f"- 🗑️ {item}")
    else:
        lines.append("✅ Nothing to clean")
    
    lines.append("")
    lines.append("### What's Preserved")
    lines.append("- PROJECT_LEARNINGS.md (valuable history)")
    lines.append("- Git commit history")
    lines.append("- Merged PR changes in main branch")
    
    if not delete_branches:
        lines.append("")
        lines.append("💡 To also delete branches, run with `delete_branches=true`")
    
    if not delete_remote:
        lines.append("💡 To also delete remote branches, run with `delete_remote=true`")
    
    lines.append("")
    lines.append("### Ready for Next Iteration")
    lines.append("Run `maw_review` to start fresh analysis")
    
    return "\n".join(lines)


# =============================================================================
# RESOURCES
# =============================================================================

@server.list_resources()
async def list_resources():
    """List available phase guides"""
    from mcp.types import Resource
    
    resources = []
    phases_dir = CONTENT_DIR / "phases"
    
    if phases_dir.exists():
        for f in sorted(phases_dir.glob("*.md")):
            resources.append(Resource(
                uri=AnyUrl(f"file://{f}"),
                name=f.stem,
                description=f"Phase guide: {f.stem}",
                mimeType="text/markdown"
            ))
    
    return resources


@server.read_resource()
async def read_resource(uri: AnyUrl) -> str:
    """Read a phase guide"""
    path = Path(str(uri).replace("file://", ""))
    if path.exists():
        return path.read_text()
    return f"Resource not found: {uri}"


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the MCP server"""
    import asyncio
    from mcp.server.stdio import stdio_server
    
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
