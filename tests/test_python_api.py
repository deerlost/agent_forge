"""Tests for the public Python API."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from agentforge import AgentForge
from agentforge.models.agent import AgentResult
from agentforge.models.state import OrchestratorState


@pytest.fixture
def api_project(tmp_path):
    """Create minimal project structure for API testing."""
    # Config dir
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    import yaml
    (config_dir / "defaults.yaml").write_text(yaml.dump({"defaults": {
        "max_sprint_retries": 2, "max_reviewer_rounds": 2,
        "human_checkpoints": {"after_analysis": False, "after_planning": False, "sprint_interval": 0, "after_final_qa": False},
        "requirement_review": {"enabled": False},
        "cost": {"max_total_cost": 50, "warn_threshold": 40},
    }}))
    (config_dir / "orchestrator.yaml").write_text(yaml.dump({
        "orchestrator": {"max_sprint_retries": 2, "max_reviewer_rounds": 2},
        "human_checkpoints": {"after_analysis": False, "after_planning": False, "sprint_interval": 0, "after_final_qa": False},
        "requirement_review": {"enabled": False},
        "timeouts": {"agent_max_minutes": 5, "sprint_max_minutes": 10, "total_max_hours": 1},
    }))
    (config_dir / "agents.yaml").write_text(yaml.dump({
        "execution": {"default_engine": "claude-cli"},
        "agents": {
            "analyst": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
            "planner": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
            "generators": {
                "api": {"engine": "claude-cli", "model": "sonnet", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
                "ui": {"engine": "claude-cli", "model": "sonnet", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
            },
            "reviewers": {
                "api_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read"], "prompt_file": ""},
                "ui_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read"], "prompt_file": ""},
            },
            "evaluator": {"engine": "claude-cli", "model": "opus", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Bash"], "prompt_file": ""},
        },
    }))

    # PRD
    prd = tmp_path / "test.md"
    prd.write_text("# Test PRD\n\nBuild a hello world app.")

    return tmp_path, config_dir, prd


class TestAgentForgeAPI:
    def test_create_instance(self, api_project):
        tmp_path, config_dir, prd = api_project
        forge = AgentForge(
            prd_path=str(prd),
            profile="web-app",
            config_dir=str(config_dir),
            output_dir=str(tmp_path / "output"),
        )
        assert forge is not None
        assert forge.config.project_name == "test"

    def test_config_overrides(self, api_project):
        tmp_path, config_dir, prd = api_project
        forge = AgentForge(
            prd_path=str(prd),
            profile="web-app",
            config_dir=str(config_dir),
            output_dir=str(tmp_path / "output"),
            config_overrides={"cost.max_total_cost": 100},
        )
        assert forge.config.cost.max_total_cost == 100

    def test_event_callback(self, api_project):
        tmp_path, config_dir, prd = api_project
        forge = AgentForge(
            prd_path=str(prd),
            config_dir=str(config_dir),
            output_dir=str(tmp_path / "output"),
        )
        events = []

        @forge.on("sprint_completed")
        def on_sprint(sprint_id, result):
            events.append(sprint_id)

        forge._emit("sprint_completed", sprint_id="S001", result={})
        assert "S001" in events

    def test_run_with_mocked_cli(self, api_project):
        tmp_path, config_dir, prd = api_project
        forge = AgentForge(
            prd_path=str(prd),
            config_dir=str(config_dir),
            output_dir=str(tmp_path / "output"),
        )
        output_dir = Path(tmp_path / "output" / "test")

        def mock_run_agent(**kwargs):
            prompt = kwargs.get("prompt", "")
            if "Analyze" in prompt or "PRD" in prompt:
                (output_dir / "state" / "requirement_spec.json").write_text(json.dumps({
                    "project_name": "Test", "modules": [], "non_functional": {}, "ambiguities": [],
                }))
                return AgentResult(output="done", cost=1.0, exit_code=0)
            if "plan" in prompt.lower():
                (output_dir / "state" / "plan.json").write_text(json.dumps({
                    "tech_stack": {}, "data_model": [], "api_contract": [],
                    "sprints": [{"id": "S001", "name": "Init", "type": "backend", "features": [],
                                 "depends_on": [], "contract": {"done_criteria": ["works"], "test_scenarios": ["test"]}}],
                }))
                return AgentResult(output="done", cost=2.0, exit_code=0)
            return AgentResult(output="OK", cost=0.5, exit_code=0)

        forge._orchestrator.cli_executor = MagicMock()
        forge._orchestrator.cli_executor.run_agent.side_effect = mock_run_agent

        forge.run()
        assert forge._orchestrator.state == OrchestratorState.COMPLETED

    def test_analyze_only(self, api_project):
        tmp_path, config_dir, prd = api_project
        forge = AgentForge(
            prd_path=str(prd),
            config_dir=str(config_dir),
            output_dir=str(tmp_path / "output"),
        )
        output_dir = Path(tmp_path / "output" / "test")

        def mock_analyst(**kwargs):
            (output_dir / "state" / "requirement_spec.json").write_text(json.dumps({
                "project_name": "Test", "modules": [{"id": "M001", "name": "Auth", "priority": "P0", "features": []}],
                "non_functional": {}, "ambiguities": [],
            }))
            return AgentResult(output="done", cost=1.0, exit_code=0)

        forge._orchestrator.cli_executor = MagicMock()
        forge._orchestrator.cli_executor.run_agent.side_effect = mock_analyst

        spec = forge.analyze()
        assert spec is not None
        assert spec["project_name"] == "Test"
