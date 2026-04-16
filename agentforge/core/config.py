from pathlib import Path
from typing import Any, Optional
import yaml
from pydantic import BaseModel, Field, PrivateAttr
from agentforge.models.agent import AgentConfig


class OrchestratorConfig(BaseModel):
    max_sprint_retries: int = 3
    max_reviewer_rounds: int = 5
    context_reset_strategy: str = "full"


class HumanCheckpointsConfig(BaseModel):
    after_analysis: bool = True
    after_planning: bool = True
    sprint_interval: int = 0
    after_final_qa: bool = True


class RequirementReviewConfig(BaseModel):
    enabled: bool = False


class TimeoutsConfig(BaseModel):
    agent_max_minutes: int = 30
    sprint_max_minutes: int = 60
    total_max_hours: int = 8


class CostConfig(BaseModel):
    max_total_cost: float = 200.0
    warn_threshold: float = 150.0


class AppConfig(BaseModel):
    project_name: str = ""
    profile: str = ""
    domain_prompt: Optional[str] = None
    default_engine: str = "claude-cli"
    knowledge_dir: Optional[str] = None
    output_dir: Optional[str] = None
    orchestrator: OrchestratorConfig = Field(default_factory=OrchestratorConfig)
    human_checkpoints: HumanCheckpointsConfig = Field(default_factory=HumanCheckpointsConfig)
    requirement_review: RequirementReviewConfig = Field(default_factory=RequirementReviewConfig)
    timeouts: TimeoutsConfig = Field(default_factory=TimeoutsConfig)
    cost: CostConfig = Field(default_factory=CostConfig)
    _agents_raw: dict[str, Any] = PrivateAttr(default_factory=dict)

    def get_agent_config(self, dotted_key: str) -> AgentConfig:
        parts = dotted_key.split(".")
        node = self._agents_raw
        for part in parts:
            if part not in node:
                raise KeyError(f"Agent config not found: {dotted_key}")
            node = node[part]
        return AgentConfig.model_validate(node)


def _deep_merge(base: dict, override: dict) -> dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_dir: Path, project_config_path: Optional[Path] = None) -> AppConfig:
    defaults_path = config_dir / "defaults.yaml"
    orch_path = config_dir / "orchestrator.yaml"
    agents_path = config_dir / "agents.yaml"

    defaults_data = {}
    if defaults_path.exists():
        with open(defaults_path) as f:
            raw = yaml.safe_load(f) or {}
            defaults_data = raw.get("defaults", raw)

    orch_data = {}
    if orch_path.exists():
        with open(orch_path) as f:
            orch_data = yaml.safe_load(f) or {}

    agents_data = {}
    if agents_path.exists():
        with open(agents_path) as f:
            agents_data = yaml.safe_load(f) or {}

    merged = {}
    merged["orchestrator"] = orch_data.get("orchestrator", {})
    merged["human_checkpoints"] = orch_data.get("human_checkpoints", defaults_data.get("human_checkpoints", {}))
    merged["requirement_review"] = orch_data.get("requirement_review", defaults_data.get("requirement_review", {}))
    merged["timeouts"] = orch_data.get("timeouts", {})
    merged["cost"] = defaults_data.get("cost", {})
    merged["default_engine"] = agents_data.get("execution", {}).get("default_engine", "claude-cli")

    if project_config_path and project_config_path.exists():
        with open(project_config_path) as f:
            project_data = yaml.safe_load(f) or {}
        project_info = project_data.get("project", {})
        merged["project_name"] = project_info.get("name", "")
        merged["domain_prompt"] = project_info.get("domain_prompt")
        merged["knowledge_dir"] = project_info.get("knowledge_dir")
        merged["output_dir"] = project_info.get("output_dir")
        merged["profile"] = project_data.get("profile", "")
        if "orchestrator" in project_data:
            orch_override = project_data["orchestrator"]
            if "human_checkpoints" in orch_override:
                merged["human_checkpoints"] = _deep_merge(
                    merged["human_checkpoints"], orch_override["human_checkpoints"]
                )

    config = AppConfig.model_validate(merged)
    config._agents_raw = agents_data.get("agents", {})
    return config
