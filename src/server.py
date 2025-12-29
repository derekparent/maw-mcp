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
            description="Analyze codebase, identify improvements, generate agent prompts. PAUSES for your review before agents can be launched.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "focus": {
                        "type": "string",
                        "description": "Optional focus area: security, performance, testing, docs, all"
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
            description="Get agent prompts with branch names and launch sequence",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_path": {"type": "string", "default": "."},
                    "agent_id": {
                        "type": "integer",
                        "description": "Get prompt for specific agent only"
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
    focus = args.get("focus", "all")
    wave_name = args.get("wave_name", "")
    
    state = load_state(project_path)
    path = Path(project_path).resolve()
    
    # Create AGENT_PROMPTS directory
    prompts_dir = path / "AGENT_PROMPTS"
    prompts_dir.mkdir(exist_ok=True)
    
    # This is where the actual analysis would happen
    # For now, return instructions for the LLM to do the analysis
    
    analysis_prompt = f"""
## Review: Codebase Analysis

Analyze this codebase and identify 3-5 high-impact improvements.

**Focus:** {focus}
**Wave:** {wave_name or "Wave 1"}

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
    agent_id = args.get("agent_id")
    
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
        if patterns_file.exists():
            content = patterns_file.read_text()
            patterns_file.write_text(content + f"\n---\n\n### From {path.name}\n**Date:** {timestamp}\n\n{learning}\n")
            result += "\n✅ Also added to UNIVERSAL_PATTERNS.md"
    
    return result


async def handle_patterns(args: dict) -> str:
    """Search or browse patterns"""
    query = args.get("query", "").lower()
    
    patterns_file = CONTENT_DIR / "UNIVERSAL_PATTERNS.md"
    if not patterns_file.exists():
        return "⚠️ UNIVERSAL_PATTERNS.md not found"
    
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
