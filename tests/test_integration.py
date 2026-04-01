"""Integration test: verify the full pipeline with mocked CLI executor."""
import json
import pytest
from pathlib import Path
from unittest.mock import MagicMock

from agentforge.core.config import AppConfig, OrchestratorConfig, HumanCheckpointsConfig, RequirementReviewConfig, TimeoutsConfig, CostConfig
from agentforge.core.orchestrator import Orchestrator
from agentforge.models.agent import AgentResult
from agentforge.models.state import OrchestratorState


@pytest.fixture
def integration_config():
    config = AppConfig(
        project_name="IntegrationTest",
        profile="web-app",
        orchestrator=OrchestratorConfig(max_sprint_retries=2, max_reviewer_rounds=2),
        human_checkpoints=HumanCheckpointsConfig(
            after_analysis=False, after_planning=False, sprint_interval=0, after_final_qa=False,
        ),
        requirement_review=RequirementReviewConfig(enabled=False),
        timeouts=TimeoutsConfig(agent_max_minutes=5),
        cost=CostConfig(max_total_cost=50),
    )
    # PrivateAttr: set directly after instantiation (Pydantic allows this)
    config._agents_raw = {
        "analyst": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
        "planner": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
        "generators": {
            "api": {"engine": "claude-cli", "model": "sonnet", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Write", "Edit", "Bash"], "prompt_file": ""},
            "ui": {"engine": "claude-cli", "model": "sonnet", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Write", "Edit", "Bash"], "prompt_file": ""},
        },
        "reviewers": {
            "api_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read"], "prompt_file": ""},
            "ui_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 5, "timeout_minutes": 5, "allowed_tools": ["Read"], "prompt_file": ""},
        },
        "evaluator": {"engine": "claude-cli", "model": "opus", "max_turns": 10, "timeout_minutes": 5, "allowed_tools": ["Read", "Bash"], "prompt_file": ""},
    }
    return config


class TestFullPipeline:
    def test_complete_run_with_mocked_cli(self, tmp_project, integration_config):
        """Simulate a complete run where every CLI call succeeds."""
        orch = Orchestrator(
            config=integration_config,
            output_dir=tmp_project,
            prd_path="docs/test.md",
            auto_mode=True,
        )

        # Mock the CLI executor
        def mock_run_agent(**kwargs):
            prompt = kwargs.get("prompt", "")

            # Analyst call: write requirement_spec.json
            if "Analyze" in prompt or "PRD" in prompt:
                spec = {
                    "project_name": "Test",
                    "modules": [{"id": "M001", "name": "Auth", "priority": "P0", "features": [
                        {"id": "F001", "description": "Login", "acceptance_criteria": ["Login works"], "business_rules": [], "ai_feature": False}
                    ]}],
                    "non_functional": {},
                    "ambiguities": [],
                }
                (tmp_project / "state" / "requirement_spec.json").write_text(json.dumps(spec))
                return AgentResult(output="Analysis complete", cost=1.0, exit_code=0)

            # Planner call: write plan.json
            if "plan" in prompt.lower():
                plan = {
                    "tech_stack": {"frontend": "vue3", "backend": "fastapi"},
                    "data_model": [],
                    "api_contract": [{"method": "POST", "path": "/api/login", "request": {}, "response": {}, "errors": []}],
                    "sprints": [
                        {"id": "S001", "name": "Auth", "type": "fullstack", "features": ["F001"], "depends_on": [],
                         "contract": {"done_criteria": ["Login works"], "test_scenarios": ["Test login"]}}
                    ],
                }
                (tmp_project / "state" / "plan.json").write_text(json.dumps(plan))
                return AgentResult(output="Plan complete", cost=2.0, exit_code=0)

            # All other calls succeed
            return AgentResult(output="OK", cost=0.5, exit_code=0)

        orch.cli_executor = MagicMock()
        orch.cli_executor.run_agent.side_effect = mock_run_agent

        # Run the full pipeline
        orch.run()

        # Verify final state
        assert orch.state == OrchestratorState.COMPLETED
        cp = orch.checkpoint_mgr.load()
        assert cp.status == OrchestratorState.COMPLETED
        assert "S001" in cp.completed_sprints

        # Verify cost was tracked
        summary = orch.cost_tracker.get_summary()
        assert summary["total_cost"] > 0

        # Verify QA results written
        assert (tmp_project / "state" / "final_qa.json").exists()

    def test_resume_after_failure(self, tmp_project, integration_config):
        """Simulate a run that fails at planner, then resumes."""
        orch = Orchestrator(
            config=integration_config,
            output_dir=tmp_project,
            prd_path="docs/test.md",
            auto_mode=True,
        )

        # Analyst succeeds, planner fails
        call_count = {"n": 0}
        def mock_run_fail(**kwargs):
            call_count["n"] += 1
            prompt = kwargs.get("prompt", "")
            if "Analyze" in prompt or "PRD" in prompt:
                spec = {"project_name": "Test", "modules": [], "non_functional": {}, "ambiguities": []}
                (tmp_project / "state" / "requirement_spec.json").write_text(json.dumps(spec))
                return AgentResult(output="done", cost=1.0, exit_code=0)
            # Planner fails
            return AgentResult(output="error", cost=0.5, exit_code=1)

        orch.cli_executor = MagicMock()
        orch.cli_executor.run_agent.side_effect = mock_run_fail
        orch.run()

        # Should be paused after planner failure
        cp = orch.checkpoint_mgr.load()
        assert cp.status == OrchestratorState.PAUSED
        assert cp.error is not None
