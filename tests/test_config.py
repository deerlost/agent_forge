import pytest
import yaml
from pathlib import Path
from agentforge.core.config import AppConfig, load_config

@pytest.fixture
def config_dir(tmp_path):
    defaults = {
        "defaults": {
            "max_sprint_retries": 3,
            "max_reviewer_rounds": 5,
            "context_reset_strategy": "full",
            "agent_timeout_minutes": 30,
            "sprint_timeout_minutes": 60,
            "total_timeout_hours": 8,
            "human_checkpoints": {
                "after_analysis": True,
                "after_planning": True,
                "sprint_interval": 0,
                "after_final_qa": True,
            },
            "requirement_review": {"enabled": False},
            "cost": {"max_total_cost": 200, "warn_threshold": 150},
        }
    }
    (tmp_path / "defaults.yaml").write_text(yaml.dump(defaults))
    orch = {
        "orchestrator": {"max_sprint_retries": 3, "max_reviewer_rounds": 5, "context_reset_strategy": "full"},
        "human_checkpoints": {"after_analysis": True, "after_planning": True, "sprint_interval": 0, "after_final_qa": True},
        "requirement_review": {"enabled": False},
        "timeouts": {"agent_max_minutes": 30, "sprint_max_minutes": 60, "total_max_hours": 8},
    }
    (tmp_path / "orchestrator.yaml").write_text(yaml.dump(orch))
    agents = {
        "execution": {"default_engine": "claude-cli"},
        "agents": {
            "analyst": {"engine": "claude-cli", "model": "opus", "max_turns": 20, "timeout_minutes": 15, "allowed_tools": ["Read", "Write", "Glob"], "prompt_file": "agents/analyst/prompts/system.md"},
            "generators": {"ui": {"engine": "claude-cli", "model": "sonnet", "max_turns": 100, "timeout_minutes": 30, "allowed_tools": ["Read", "Write", "Edit", "Bash", "Glob", "Grep"], "prompt_file": "agents/generators/ui/prompts/vue_system.md"}},
            "reviewers": {"ui_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 20, "timeout_minutes": 15, "allowed_tools": ["Read", "Glob", "Grep", "Bash"], "prompt_file": "agents/reviewers/ui_reviewer/prompts/review_criteria.md"}},
            "evaluator": {"engine": "claude-cli", "model": "opus", "max_turns": 50, "timeout_minutes": 30, "allowed_tools": ["Read", "Bash", "Glob", "Grep"], "prompt_file": "agents/evaluator/prompts/global_qa.md"},
        },
    }
    (tmp_path / "agents.yaml").write_text(yaml.dump(agents))
    return tmp_path

class TestLoadConfig:
    def test_load_from_directory(self, config_dir):
        config = load_config(config_dir)
        assert config.orchestrator.max_sprint_retries == 3
        assert config.human_checkpoints.after_analysis is True
        assert config.requirement_review.enabled is False
        assert config.timeouts.agent_max_minutes == 30
        assert config.cost.max_total_cost == 200

    def test_agent_config_loaded(self, config_dir):
        config = load_config(config_dir)
        assert config.default_engine == "claude-cli"
        analyst = config.get_agent_config("analyst")
        assert analyst.model == "opus"
        assert "Read" in analyst.allowed_tools

    def test_generator_config(self, config_dir):
        config = load_config(config_dir)
        ui_gen = config.get_agent_config("generators.ui")
        assert ui_gen.model == "sonnet"
        assert ui_gen.max_turns == 100

    def test_reviewer_config(self, config_dir):
        config = load_config(config_dir)
        reviewer = config.get_agent_config("reviewers.ui_reviewer")
        assert reviewer.model == "opus"
        assert "Write" not in reviewer.allowed_tools

    def test_missing_agent_raises(self, config_dir):
        config = load_config(config_dir)
        with pytest.raises(KeyError):
            config.get_agent_config("nonexistent")

    def test_project_override(self, config_dir, tmp_path):
        project_config = {
            "project": {"name": "TestProject", "domain_prompt": "./prompts/domain.md"},
            "profile": "web-app",
            "orchestrator": {"human_checkpoints": {"after_planning": False}},
        }
        project_yaml = tmp_path / "agentforge.yaml"
        project_yaml.write_text(yaml.dump(project_config))
        config = load_config(config_dir, project_config_path=project_yaml)
        assert config.project_name == "TestProject"
        assert config.human_checkpoints.after_planning is False
        assert config.human_checkpoints.after_analysis is True
