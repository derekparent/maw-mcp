# Agent 1: Testing Infrastructure

## Mission
Build comprehensive test coverage for the MAW-MCP server to ensure reliability and enable safe refactoring.

## Branch
`agent/1-testing-infrastructure`

## Files to Modify/Create
- `tests/__init__.py` (create)
- `tests/conftest.py` (create)
- `tests/test_server.py` (create)
- `tests/test_state.py` (create)
- `tests/test_github.py` (create)
- `pyproject.toml` (update test config)

## Context
The codebase currently has **zero tests** despite pytest being in dev dependencies. This is a critical gap for an MCP server that coordinates development workflows.

## Tasks

### 1. Set Up Test Infrastructure
- Create `tests/` directory with proper structure
- Add `conftest.py` with fixtures for:
  - Temporary project directories
  - Mock workflow states
  - GitHub CLI mocking

### 2. Unit Tests for State Management (`test_state.py`)
- Test `WorkflowState.empty()` creates valid state
- Test `load_state()` handles missing file
- Test `load_state()` handles corrupt JSON
- Test `save_state()` writes valid JSON
- Test `format_status()` output formatting
- Test `suggest_next_step()` for all phases

### 3. Unit Tests for GitHub Integration (`test_github.py`)
- Test `run_gh()` handles missing CLI
- Test `run_gh()` handles timeouts
- Test `get_agent_prs()` filters correctly
- Test `detect_conflicts()` finds overlapping files
- Test `format_pr_dashboard()` output formatting
- Mock subprocess calls (don't hit real GitHub)

### 4. Integration Tests for MCP Tools (`test_server.py`)
- Test `handle_status()` returns valid output
- Test `handle_review()` creates AGENT_PROMPTS dir
- Test `handle_setup()` creates all files
- Test `handle_clean()` removes correct files
- Test `slugify()` edge cases

### 5. Update pyproject.toml
- Add pytest configuration
- Configure coverage settings
- Add test markers for unit vs integration

## Technical Notes
- Use `pytest-asyncio` for async handler tests
- Use `tmp_path` fixture for file system tests
- Mock `subprocess.run` for GitHub CLI calls
- Keep tests fast (< 5 seconds total)

## Definition of Done
- [ ] `tests/` directory with 4 test files
- [ ] At least 80% code coverage
- [ ] All tests pass with `pytest -v`
- [ ] No external dependencies (mocked GitHub)
- [ ] PR created with test results in description

## Time Estimate
2-3 hours
