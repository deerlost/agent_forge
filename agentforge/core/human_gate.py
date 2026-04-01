import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional
from agentforge.core.config import HumanCheckpointsConfig

logger = logging.getLogger(__name__)


class GateType(str, Enum):
    AFTER_ANALYSIS = "after_analysis"
    AFTER_PLANNING = "after_planning"
    SPRINT_INTERVAL = "sprint_interval"
    AFTER_FINAL_QA = "after_final_qa"
    AMBIGUITY = "ambiguity"


@dataclass
class GateResult:
    approved: bool
    feedback: str = ""


class HumanGate:
    def __init__(self, config: HumanCheckpointsConfig, auto_mode: bool = False):
        self.config = config
        self.auto_mode = auto_mode
        self._callback: Optional[Callable] = None

    def register_callback(self, callback: Callable[[GateType, dict], bool]) -> None:
        self._callback = callback

    def should_pause(self, gate_type: GateType) -> bool:
        if self.auto_mode:
            return False
        mapping = {
            GateType.AFTER_ANALYSIS: self.config.after_analysis,
            GateType.AFTER_PLANNING: self.config.after_planning,
            GateType.AFTER_FINAL_QA: self.config.after_final_qa,
            GateType.AMBIGUITY: True,
        }
        return mapping.get(gate_type, False)

    def should_pause_at_sprint(self, sprint_number: int) -> bool:
        if self.auto_mode or self.config.sprint_interval == 0:
            return False
        return sprint_number % self.config.sprint_interval == 0

    def wait_for_human(self, gate_type: GateType, context: dict[str, Any]) -> GateResult:
        logger.info(f"Human gate triggered: {gate_type.value}")
        if self._callback:
            approved = self._callback(gate_type, context)
            return GateResult(approved=approved)
        print(f"\n{'='*60}")
        print(f"  Human checkpoint: {gate_type.value}")
        print(f"{'='*60}")
        if context:
            for key, value in context.items():
                print(f"  {key}: {value}")
        print()
        response = input("  Continue? (y/n): ").strip().lower()
        return GateResult(approved=response in ("y", "yes", ""))
