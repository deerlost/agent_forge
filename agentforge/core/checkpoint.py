import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from agentforge.models.state import Checkpoint, OrchestratorState


class CheckpointManager:
    def __init__(self, state_dir: Path, max_retries: int = 3):
        self.state_dir = state_dir
        self.max_retries = max_retries
        self._path = state_dir / "checkpoint.json"

    def exists(self) -> bool:
        return self._path.exists()

    def save(self, checkpoint: Checkpoint) -> None:
        checkpoint.timestamp = datetime.utcnow()
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(checkpoint.model_dump_json(indent=2), encoding="utf-8")

    def load(self) -> Optional[Checkpoint]:
        if not self._path.exists():
            return None
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return Checkpoint.model_validate(data)

    def update(self, **kwargs) -> Checkpoint:
        cp = self.load()
        if cp is None:
            raise RuntimeError("No checkpoint to update")
        for key, value in kwargs.items():
            setattr(cp, key, value)
        self.save(cp)
        return cp

    def complete_sprint(self, sprint_id: str) -> Checkpoint:
        cp = self.load()
        if cp is None:
            raise RuntimeError("No checkpoint to update")
        if sprint_id not in cp.completed_sprints:
            cp.completed_sprints.append(sprint_id)
        cp.current_sprint = None
        cp.failed_attempts = 0
        cp.error = None
        self.save(cp)
        return cp

    def record_failure(self, error: str) -> Checkpoint:
        cp = self.load()
        if cp is None:
            raise RuntimeError("No checkpoint to update")
        cp.failed_attempts += 1
        cp.error = error
        if cp.failed_attempts >= self.max_retries:
            cp.status = OrchestratorState.BLOCKED
        else:
            cp.status = OrchestratorState.PAUSED
        self.save(cp)
        return cp
