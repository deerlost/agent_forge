from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrchestratorState(str, Enum):
    INIT = "INIT"
    ANALYZING = "ANALYZING"
    REVIEWING_REQ = "REVIEWING_REQ"
    PLANNING = "PLANNING"
    SPRINTING = "SPRINTING"
    SPRINT_EVALUATING = "SPRINT_EVALUATING"
    CONTEXT_RESET = "CONTEXT_RESET"
    FINAL_QA = "FINAL_QA"
    COMPLETED = "COMPLETED"
    WAITING_HUMAN = "WAITING_HUMAN"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"


class Checkpoint(BaseModel):
    project_name: str
    profile: str = ""
    status: OrchestratorState = OrchestratorState.INIT
    current_sprint: Optional[str] = None
    current_agent: Optional[str] = None
    completed_sprints: list[str] = Field(default_factory=list)
    failed_attempts: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
