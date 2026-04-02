"""Public Python API for AgentForge."""
import json
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from agentforge.core.config import AppConfig, load_config
from agentforge.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class AgentForge:
    """High-level API for running AgentForge pipelines.

    Usage:
        forge = AgentForge(prd_path="./docs/prd.md", profile="web-app")
        forge.run()

        # Or step-by-step:
        spec = forge.analyze()
        plan = forge.plan(spec)
        forge.execute(plan)

        # Event callbacks:
        @forge.on("sprint_completed")
        def on_sprint(sprint_id, result):
            print(f"Sprint {sprint_id} done")
    """

    def __init__(
        self,
        prd_path: str,
        profile: str = "web-app",
        config_dir: str = "config",
        output_dir: str = "output",
        config_overrides: Optional[dict[str, Any]] = None,
        auto_mode: bool = True,
        profiles_dir: Optional[str] = None,
        templates_dir: Optional[str] = None,
    ):
        self._prd_path = prd_path
        self._config_dir = Path(config_dir)
        self._output_dir = Path(output_dir)
        self._callbacks: dict[str, list[Callable]] = {}

        # Load config
        project_yaml = Path("agentforge.yaml")
        project_config_path = project_yaml if project_yaml.exists() else None
        self.config = load_config(self._config_dir, project_config_path=project_config_path)
        self.config.profile = profile

        # Apply overrides
        if config_overrides:
            self._apply_overrides(config_overrides)

        # Derive project name from PRD filename if not set
        if not self.config.project_name:
            self.config.project_name = Path(prd_path).stem

        # Resolve directories
        project_output = self._output_dir / self.config.project_name
        p_dir = Path(profiles_dir) if profiles_dir else Path("profiles")
        t_dir = Path(templates_dir) if templates_dir else Path("templates")

        # Create orchestrator
        self._orchestrator = Orchestrator(
            config=self.config,
            output_dir=project_output,
            prd_path=prd_path,
            auto_mode=auto_mode,
            profiles_dir=p_dir if p_dir.exists() else None,
            templates_dir=t_dir if t_dir.exists() else None,
        )

    def _apply_overrides(self, overrides: dict[str, Any]) -> None:
        """Apply dotted-key overrides to config. E.g. 'cost.max_total_cost': 100."""
        for key, value in overrides.items():
            parts = key.split(".")
            obj = self.config
            for part in parts[:-1]:
                obj = getattr(obj, part)
            setattr(obj, parts[-1], value)

    def on(self, event: str) -> Callable:
        """Register an event callback. Use as decorator."""
        def decorator(func: Callable) -> Callable:
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(func)
            return func
        return decorator

    def _emit(self, event: str, **kwargs) -> None:
        """Emit an event to registered callbacks."""
        for callback in self._callbacks.get(event, []):
            callback(**kwargs)

    def run(self) -> None:
        """Run the full pipeline: analyze -> plan -> sprints -> QA."""
        self._orchestrator.run()

    def analyze(self) -> Optional[dict]:
        """Run only the analysis phase. Returns requirement_spec."""
        self._orchestrator._run_analysis()
        return self._orchestrator.requirement_spec

    def plan(self, spec: Optional[dict] = None) -> Optional[dict]:
        """Run only the planning phase. Returns plan."""
        if self._orchestrator.state.value not in ("PLANNING", "INIT", "ANALYZING"):
            self._orchestrator._transition(
                __import__("agentforge.models.state", fromlist=["OrchestratorState"]).OrchestratorState.PLANNING
            )
        self._orchestrator._run_planning()
        return self._orchestrator.plan

    def execute(self, plan: Optional[dict] = None) -> None:
        """Execute sprints and final QA using the loaded plan."""
        if plan:
            self._orchestrator.plan = plan
        self._orchestrator._run_sprints()
        self._orchestrator._run_final_qa()
