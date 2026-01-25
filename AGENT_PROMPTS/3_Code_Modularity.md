# Agent 3: Code Modularity & Refactoring

## Mission
Refactor the large `server.py` into smaller, focused modules to improve maintainability and testability.

## Branch
`agent/3-code-modularity`

## Files to Modify/Create
- `src/server.py` (reduce size)
- `src/handlers/__init__.py` (create)
- `src/handlers/status.py` (create)
- `src/handlers/review.py` (create)
- `src/handlers/launch.py` (create)
- `src/handlers/checkin.py` (create)
- `src/handlers/integrate.py` (create)
- `src/handlers/lifecycle.py` (create - setup, clean, decide)
- `src/handlers/learning.py` (create - learn, patterns)

## Context
`server.py` is 1300+ lines with some very large handlers:
- `handle_checkin()`: 220+ lines
- `handle_integrate()`: 300+ lines

This makes the code hard to navigate, test, and maintain.

## Tasks

### 1. Create Handler Module Structure
```
src/
├── __init__.py
├── server.py          # Slim: just MCP setup and routing
├── state.py           # No changes
├── github.py          # No changes
└── handlers/
    ├── __init__.py    # Export all handlers
    ├── status.py      # handle_status
    ├── review.py      # handle_review
    ├── launch.py      # handle_launch
    ├── checkin.py     # handle_checkin (largest)
    ├── integrate.py   # handle_integrate (largest)
    ├── lifecycle.py   # setup, clean, decide
    └── learning.py    # learn, patterns
```

### 2. Extract Handlers to Modules
Move each handler function to its own module:

```python
# src/handlers/status.py
from ..state import load_state, format_status, suggest_next_step

async def handle_status(args: dict) -> str:
    """Show current workflow state"""
    ...
```

### 3. Slim Down server.py
After extraction, `server.py` should only contain:
- Server initialization
- Tool definitions (list_tools)
- Tool routing (call_tool)
- Resource definitions
- Main entry point

Target: < 300 lines

### 4. Extract Helper Functions
Move shared utilities:
- `slugify()` → `src/utils.py`
- Report parsing logic from `handle_checkin` → `src/parsers.py`

### 5. Update Imports
Ensure all imports work correctly:
```python
# src/handlers/__init__.py
from .status import handle_status
from .review import handle_review
# ... etc

# src/server.py
from .handlers import (
    handle_status, handle_review, handle_launch,
    handle_checkin, handle_integrate, handle_decide,
    handle_learn, handle_patterns, handle_setup, handle_clean
)
```

## Technical Notes
- Preserve all existing behavior exactly
- Keep function signatures identical
- Test manually after each extraction
- Run `python -m src.server` to verify no import errors

## Definition of Done
- [ ] `src/handlers/` module created with 7+ files
- [ ] `server.py` reduced to < 300 lines
- [ ] All tools work identically to before
- [ ] No circular import issues
- [ ] MCP server starts without errors
- [ ] PR created

## Time Estimate
2-2.5 hours
