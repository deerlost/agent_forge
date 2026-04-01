import json
import logging
from pathlib import Path
from agentforge.models.agent import AgentResult

logger = logging.getLogger(__name__)


class CostLimitExceeded(Exception):
    def __init__(self, current_cost: float):
        self.current_cost = current_cost
        super().__init__(f"Cost limit exceeded: ${current_cost:.2f}")


class CostTracker:
    def __init__(self, state_dir: Path, max_cost: float = 200, warn_threshold: float = 150):
        self.state_dir = state_dir
        self.max_cost = max_cost
        self.warn_threshold = warn_threshold
        self._path = state_dir / "cost_tracking.json"
        self._data = self._load()

    def _load(self) -> dict:
        if self._path.exists():
            return json.loads(self._path.read_text(encoding="utf-8"))
        return {"total_cost": 0.0, "total_tokens": {"prompt": 0, "completion": 0}, "by_agent": {}, "by_sprint": {}}

    def _save(self) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def record(self, agent_name: str, result: AgentResult, sprint_id: str | None = None) -> None:
        self._data["total_cost"] += result.cost
        self._data["total_tokens"]["prompt"] += result.token_usage.get("prompt", 0)
        self._data["total_tokens"]["completion"] += result.token_usage.get("completion", 0)
        if agent_name not in self._data["by_agent"]:
            self._data["by_agent"][agent_name] = {"cost": 0.0, "calls": 0}
        self._data["by_agent"][agent_name]["cost"] += result.cost
        self._data["by_agent"][agent_name]["calls"] += 1
        if sprint_id:
            if sprint_id not in self._data["by_sprint"]:
                self._data["by_sprint"][sprint_id] = {"cost": 0.0}
            self._data["by_sprint"][sprint_id]["cost"] += result.cost
        self._save()

    def check_limit(self) -> None:
        if self._data["total_cost"] >= self.max_cost:
            raise CostLimitExceeded(self._data["total_cost"])
        if self._data["total_cost"] >= self.warn_threshold:
            logger.warning(f"Cost warning: ${self._data['total_cost']:.2f}")

    def get_summary(self) -> dict:
        return self._data.copy()
