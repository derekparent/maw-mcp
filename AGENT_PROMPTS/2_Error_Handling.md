# Agent 2: Error Handling & Input Validation

## Mission
Add robust error handling and input validation throughout the codebase to prevent silent failures and security issues.

## Branch
`agent/2-error-handling`

## Files to Modify
- `src/server.py`
- `src/state.py`
- `src/github.py`

## Context
Current error handling is minimal. Many operations can fail silently or with cryptic messages. Path traversal and input validation are not consistently implemented.

## Tasks

### 1. Input Validation in Server Handlers
Add validation for all tool arguments in `server.py`:

```python
# Example pattern to apply
def validate_project_path(path: str) -> Path:
    """Validate and resolve project path safely"""
    resolved = Path(path).resolve()
    if not resolved.exists():
        raise ValueError(f"Project path does not exist: {path}")
    if not resolved.is_dir():
        raise ValueError(f"Project path is not a directory: {path}")
    return resolved
```

Apply to:
- `handle_status()`
- `handle_review()`
- `handle_launch()`
- `handle_checkin()`
- `handle_integrate()`
- `handle_learn()`
- `handle_setup()`
- `handle_clean()`

### 2. Path Security in State Module
Update `src/state.py`:
- Validate paths don't escape project directory
- Handle permission errors gracefully
- Add specific exceptions for state errors

```python
class StateError(Exception):
    """Base exception for state operations"""
    pass

class StateCorruptError(StateError):
    """State file is corrupt or invalid"""
    pass
```

### 3. Subprocess Safety in GitHub Module
Update `src/github.py`:
- Validate inputs before subprocess calls
- Add timeout handling with clear messages
- Sanitize branch names in output

```python
def validate_branch_name(branch: str) -> str:
    """Ensure branch name is safe"""
    if not re.match(r'^[a-zA-Z0-9/_-]+$', branch):
        raise ValueError(f"Invalid branch name: {branch}")
    return branch
```

### 4. Graceful Error Messages
Replace generic errors with helpful messages:
- "gh CLI not found" → Include installation instructions
- "Timeout" → Suggest retry or check network
- "Permission denied" → Suggest checking file ownership

### 5. Add Logging (Optional but Recommended)
- Add basic logging for debugging
- Log errors with stack traces
- Keep logs minimal in normal operation

## Technical Notes
- Don't break existing behavior
- Use custom exceptions with clear messages
- Return user-friendly errors via TextContent
- Test error paths manually

## Definition of Done
- [ ] All handlers validate inputs before use
- [ ] Path traversal prevented in all file operations
- [ ] Subprocess calls sanitize inputs
- [ ] Error messages are actionable
- [ ] No silent failures
- [ ] PR created

## Time Estimate
1.5-2 hours
