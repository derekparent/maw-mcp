"""
Pytest fixtures for MAW MCP Server tests
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.state import WorkflowState, AgentInfo, WaveInfo


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory"""
    project = tmp_path / "test_project"
    project.mkdir()
    return project


@pytest.fixture
def sample_workflow_state(tmp_project: Path) -> WorkflowState:
    """Create a sample workflow state"""
    return WorkflowState(
        project=tmp_project.name,
        project_path=str(tmp_project),
        phase="launch",
        iteration=1,
        status="launching",
        review_complete=True,
        wave=WaveInfo(
            number=1,
            name="Foundation",
            agents=[1, 2, 3],
            status="in_progress"
        ),
        agents=[
            AgentInfo(
                id=1,
                role="Testing Infrastructure",
                slug="testing-infrastructure",
                branch="agent/1-testing-infrastructure",
                status="in_progress",
                wave=1
            ),
            AgentInfo(
                id=2,
                role="Security Hardening",
                slug="security-hardening",
                branch="agent/2-security-hardening",
                status="not_started",
                wave=1
            ),
            AgentInfo(
                id=3,
                role="Documentation",
                slug="documentation",
                branch="agent/3-documentation",
                status="complete",
                pr_number=42,
                wave=1
            ),
        ],
        created_at="2025-01-01T00:00:00+00:00",
        last_updated="2025-01-02T00:00:00+00:00",
    )


@pytest.fixture
def state_file_content() -> dict:
    """Sample WORKFLOW_STATE.json content"""
    return {
        "project": "test_project",
        "project_path": "/tmp/test_project",
        "phase": "idle",
        "iteration": 0,
        "status": "not_started",
        "tech_stack": None,
        "review_complete": False,
        "wave": None,
        "agents": [],
        "history": [],
        "created_at": "2025-01-01T00:00:00+00:00",
        "last_updated": "2025-01-01T00:00:00+00:00",
    }


@pytest.fixture
def mock_gh_success():
    """Mock successful gh CLI calls"""
    with patch("src.github.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="[]",
            stderr=""
        )
        yield mock_run


@pytest.fixture
def mock_gh_not_found():
    """Mock gh CLI not installed"""
    with patch("src.github.subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("gh")
        yield mock_run


@pytest.fixture
def mock_gh_timeout():
    """Mock gh CLI timeout"""
    import subprocess
    with patch("src.github.subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="gh", timeout=30)
        yield mock_run


@pytest.fixture
def sample_prs() -> list[dict]:
    """Sample PR data from GitHub API"""
    return [
        {
            "number": 1,
            "title": "Agent 1: Testing Infrastructure",
            "headRefName": "agent/1-testing-infrastructure",
            "body": "Testing infrastructure changes",
            "additions": 100,
            "deletions": 10,
            "files": [
                {"path": "tests/test_state.py"},
                {"path": "tests/conftest.py"},
                {"path": "pyproject.toml"},
            ],
            "author": {"login": "agent1"},
            "url": "https://github.com/test/repo/pull/1",
            "agent_num": 1
        },
        {
            "number": 2,
            "title": "Agent 2: Security Hardening",
            "headRefName": "agent/2-security-hardening",
            "body": "Security improvements",
            "additions": 50,
            "deletions": 5,
            "files": [
                {"path": "src/server.py"},
                {"path": "src/auth.py"},
            ],
            "author": {"login": "agent2"},
            "url": "https://github.com/test/repo/pull/2",
            "agent_num": 2
        },
        {
            "number": 3,
            "title": "Agent 3: Documentation",
            "headRefName": "agent/3-documentation",
            "body": "Docs update",
            "additions": 200,
            "deletions": 20,
            "files": [
                {"path": "README.md"},
                {"path": "docs/setup.md"},
            ],
            "author": {"login": "agent3"},
            "url": "https://github.com/test/repo/pull/3",
            "agent_num": 3
        },
    ]


@pytest.fixture
def sample_prs_with_conflicts() -> list[dict]:
    """Sample PRs with file conflicts"""
    return [
        {
            "number": 1,
            "title": "Agent 1",
            "headRefName": "agent/1-test",
            "files": [
                {"path": "src/server.py"},
                {"path": "tests/test_server.py"},
            ],
            "agent_num": 1
        },
        {
            "number": 2,
            "title": "Agent 2",
            "headRefName": "agent/2-test",
            "files": [
                {"path": "src/server.py"},  # Conflict!
                {"path": "src/other.py"},
            ],
            "agent_num": 2
        },
    ]


@pytest.fixture
def agent_prompts_dir(tmp_project: Path) -> Path:
    """Create AGENT_PROMPTS directory with sample prompts"""
    prompts_dir = tmp_project / "AGENT_PROMPTS"
    prompts_dir.mkdir()

    # Create sample agent prompt files
    (prompts_dir / "1_Testing_Infrastructure.md").write_text("""# Agent 1: Testing Infrastructure

## Mission
Build test coverage for the MAW-MCP server.

## Branch
`agent/1-testing-infrastructure`

## Files to Modify
- tests/test_state.py
- tests/conftest.py

## Tasks
1. Create test directory structure
2. Write unit tests

## Definition of Done
- [ ] Tests pass
- [ ] PR created
""")

    (prompts_dir / "2_Security_Hardening.md").write_text("""# Agent 2: Security Hardening

## Mission
Improve security of the server.

## Branch
`agent/2-security-hardening`

## Files to Modify
- src/server.py

## Tasks
1. Add input validation

## Definition of Done
- [ ] Tests pass
- [ ] PR created
""")

    (prompts_dir / "COORDINATION.md").write_text("""# Coordination

1. Agent 1 runs first
2. Agents 2+ run in parallel
""")

    return prompts_dir
