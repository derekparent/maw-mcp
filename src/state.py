"""
Workflow State Management
Handles WORKFLOW_STATE.json read/write operations
"""
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Optional
from pydantic import BaseModel


class WaveInfo(BaseModel):
    """Tracks wave-based iteration"""
    number: int = 1
    name: str = ""
    agents: list[int] = []
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: str = "not_started"


class AgentInfo(BaseModel):
    """Tracks individual agent status"""
    id: int
    role: str
    slug: str  # URL-safe short name for branch
    branch: str  # Full branch name
    status: str = "not_started"  # not_started, in_progress, complete, blocked
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    pr_number: Optional[int] = None
    wave: int = 1


class WorkflowState(BaseModel):
    """Complete workflow state for a project"""
    project: str
    project_path: str
    phase: str = "idle"  # idle, review, launch, integrate, decide
    iteration: int = 0
    status: str = "not_started"
    tech_stack: Optional[str] = None
    review_complete: bool = False
    mode: str = "parallel"  # "parallel" | "sequential"
    current_task_index: int = 0  # For sequential mode: which task is next
    wave: Optional[WaveInfo] = None
    agents: list[AgentInfo] = []
    history: list[dict[str, Any]] = []
    created_at: str = ""
    last_updated: str = ""

    @classmethod
    def empty(cls, project_path: Path) -> "WorkflowState":
        """Create empty state for new project"""
        now = datetime.now(UTC).isoformat()
        return cls(
            project=project_path.name,
            project_path=str(project_path),
            created_at=now,
            last_updated=now,
        )


STATE_FILE = "WORKFLOW_STATE.json"


def load_state(project_path: str = ".") -> WorkflowState:
    """Load state from project, create if doesn't exist"""
    path = Path(project_path).resolve()
    state_file = path / STATE_FILE
    
    if not state_file.exists():
        return WorkflowState.empty(path)
    
    try:
        data = json.loads(state_file.read_text())
        return WorkflowState(**data)
    except (json.JSONDecodeError, Exception) as e:
        print(f"⚠️ Corrupt state file, creating fresh: {e}")
        return WorkflowState.empty(path)


def save_state(state: WorkflowState, project_path: str = ".") -> None:
    """Save state to project"""
    path = Path(project_path).resolve()
    state_file = path / STATE_FILE
    
    state.last_updated = datetime.now(UTC).isoformat()
    state_file.write_text(json.dumps(state.model_dump(), indent=2))


def format_status(state: WorkflowState) -> str:
    """Format state for display"""
    lines = [
        f"📊 {state.project}",
        f"Phase: {state.phase} | Iteration: {state.iteration}",
        f"Status: {state.status}",
    ]
    
    if state.wave:
        lines.append(f"Wave: {state.wave.number} - {state.wave.name} ({state.wave.status})")
    
    if state.review_complete:
        lines.append("✅ Review complete - ready for launch")
    
    # Show sequential mode status
    if state.mode == "sequential":
        lines.append(f"🔢 Sequential mode: task {state.current_task_index + 1} next")
    
    # Agent status
    if state.agents:
        complete = [a for a in state.agents if a.status == "complete"]
        active = [a for a in state.agents if a.status == "in_progress"]
        waiting = [a for a in state.agents if a.status == "not_started"]
        
        lines.append("")
        if complete:
            lines.append(f"✅ Complete: {len(complete)} agents")
            for a in complete:
                pr = f" (PR #{a.pr_number})" if a.pr_number else ""
                lines.append(f"   {a.id}. {a.role}{pr}")
        
        if active:
            lines.append(f"🔄 Active: {len(active)} agents")
            for a in active:
                lines.append(f"   {a.id}. {a.role} → {a.branch}")
        
        if waiting:
            lines.append(f"⏳ Waiting: {len(waiting)} agents")
    
    return "\n".join(lines)


def suggest_next_step(state: WorkflowState) -> str:
    """Suggest next action based on current state"""
    phase = state.phase
    
    if phase == "idle" or state.status == "not_started":
        return "→ Run maw_review to analyze codebase and generate agent prompts"
    
    if phase == "review" and state.review_complete:
        return "→ Run maw_launch to get agent prompts and launch sequence"
    
    if phase == "review":
        return "→ Review AGENT_PROMPTS/, then run maw_launch"
    
    if phase == "launch":
        agents = state.agents
        incomplete = [a for a in agents if a.status != "complete"]
        if incomplete:
            return f"→ {len(incomplete)} agents still working. Run maw_checkin with progress reports."
        return "→ All agents complete! Run maw_integrate for merge guidance"
    
    if phase == "integrate":
        return "→ Complete test plan, then run maw_decide"
    
    if phase == "decide":
        return "→ Deploy, iterate (run maw_review), or add features"
    
    if "complete" in state.status:
        return "→ Workflow complete. Run maw_review for next iteration."
    
    return f"→ Continue {phase} phase (status: {state.status})"
