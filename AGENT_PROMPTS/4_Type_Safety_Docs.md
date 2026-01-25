# Agent 4: Type Safety & Documentation

## Mission
Improve code quality with comprehensive type hints, docstrings, and inline documentation.

## Branch
`agent/4-type-safety-docs`

## Files to Modify
- `src/server.py`
- `src/state.py`
- `src/github.py`
- `src/__init__.py`

## Context
The codebase has minimal documentation. Type hints are inconsistent. This makes it harder for contributors to understand and extend the code.

## Tasks

### 1. Add Module Docstrings
Each file should have a comprehensive module docstring:

```python
"""
Multi-Agent Workflow MCP Server

This module provides the core MCP server implementation for coordinating
parallel AI agent development workflows. It exposes tools that can be
called from Claude Desktop, Cursor, or Claude.ai.

Tools:
    maw_status: Show current workflow state
    maw_review: Analyze codebase and generate agent prompts
    maw_launch: Get agent prompts with sequencing
    ...

Example:
    Run the server:
    $ python -m src.server

Architecture:
    server.py - MCP tool definitions and routing
    state.py  - Workflow state persistence
    github.py - GitHub CLI integration
"""
```

### 2. Add Type Hints Throughout
Ensure all functions have complete type hints:

```python
# Before
def run_gh(args: list[str], cwd: str = ".") -> tuple[bool, str]:

# After  
def run_gh(
    args: list[str], 
    cwd: str | Path = "."
) -> tuple[bool, str | list[dict]]:
```

Focus areas:
- Return type unions (`str | list[dict]`)
- Optional parameters (`Optional[str]` or `str | None`)
- Dict structures (use TypedDict where appropriate)

### 3. Add Function Docstrings
Every public function needs a docstring:

```python
async def handle_review(args: dict) -> str:
    """
    Analyze codebase and generate agent prompts.
    
    This is the first step in a MAW workflow. It analyzes the project
    and creates prompt files in AGENT_PROMPTS/ for parallel agents.
    
    Args:
        args: Dictionary with:
            - project_path (str): Path to project, defaults to "."
            - focus (str): Focus area - security, performance, testing, docs, all
            - wave_name (str): Name for this iteration wave
    
    Returns:
        Instructions for Claude to perform the analysis and create prompts.
    
    Side Effects:
        - Creates AGENT_PROMPTS/ directory if missing
        - Updates WORKFLOW_STATE.json phase to "review"
    
    Example:
        >>> result = await handle_review({"focus": "security"})
    """
```

### 4. Add TypedDict for Complex Structures
Define typed structures for PR data, agent info, etc:

```python
from typing import TypedDict

class PRInfo(TypedDict):
    number: int
    title: str
    headRefName: str
    additions: int
    deletions: int
    files: list[dict]
    agent_num: int  # Added by us

class ConflictInfo(TypedDict):
    file: str
    prs: list[int]
```

### 5. Add Inline Comments for Complex Logic
Add explanatory comments for non-obvious code:
- Report parsing regex in `handle_checkin`
- Merge order logic in `handle_integrate`
- Branch naming conventions

### 6. Create Type Stub or py.typed
Add `py.typed` marker for package type checking:
```
src/py.typed  # Empty file marking package as typed
```

## Technical Notes
- Use `from __future__ import annotations` for forward references
- Run `mypy src/` to verify type correctness (optional)
- Keep docstrings concise but complete
- Follow Google docstring style

## Definition of Done
- [ ] All modules have module docstrings
- [ ] All public functions have docstrings
- [ ] Complete type hints on all functions
- [ ] TypedDict for complex dict structures
- [ ] `py.typed` marker added
- [ ] No mypy errors (if checked)
- [ ] PR created

## Time Estimate
1.5-2 hours
