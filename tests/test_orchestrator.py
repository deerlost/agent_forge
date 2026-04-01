import json
import pytest
from unittest.mock import MagicMock, patch, call

from agentforge.core.orchestrator import Orchestrator
from agentforge.core.config import AppConfig, HumanCheckpointsConfig, OrchestratorConfig, RequirementReviewConfig, TimeoutsConfig, CostConfig
from agentforge.core.checkpoint import CheckpointManager
from agentforge.core.cli_executor import CLIExecutor
from agentforge.core.cost_tracker import CostTracker
from agentforge.core.human_gate import HumanGate, GateType, GateResult
from agentforge.core.context_manager import ContextManager
from agentforge.models.state import OrchestratorState, Checkpoint
from agentforge.models.agent import AgentResult, AgentConfig


@pytest.fixture
def mock_config():
    config = AppConfig(
        project_name="TestProject",
        profile="web-app",
        orchestrator=OrchestratorConfig(max_sprint_retries=3, max_reviewer_rounds=5),
        human_checkpoints=HumanCheckpointsConfig(
            after_analysis=False, after_planning=False, sprint_interval=0, after_final_qa=False,
        ),
        requirement_review=RequirementReviewConfig(enabled=False),
        timeouts=TimeoutsConfig(agent_max_minutes=30, sprint_max_minutes=60),
        cost=CostConfig(max_total_cost=200, warn_threshold=150),
    )
    # We need to set _agents_raw so get_agent_config works
    config._agents_raw = {
        "analyst": {"engine": "claude-cli", "model": "opus", "max_turns": 20, "timeout_minutes": 15, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
        "planner": {"engine": "claude-cli", "model": "opus", "max_turns": 30, "timeout_minutes": 20, "allowed_tools": ["Read", "Write"], "prompt_file": ""},
        "generators": {
            "ui": {"engine": "claude-cli", "model": "sonnet", "max_turns": 100, "timeout_minutes": 30, "allowed_tools": ["Read", "Write", "Edit", "Bash"], "prompt_file": ""},
            "api": {"engine": "claude-cli", "model": "sonnet", "max_turns": 100, "timeout_minutes": 30, "allowed_tools": ["Read", "Write", "Edit", "Bash"], "prompt_file": ""},
        },
        "reviewers": {
            "ui_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 20, "timeout_minutes": 15, "allowed_tools": ["Read"], "prompt_file": ""},
            "api_reviewer": {"engine": "claude-cli", "model": "opus", "max_turns": 20, "timeout_minutes": 15, "allowed_tools": ["Read"], "prompt_file": ""},
        },
        "evaluator": {"engine": "claude-cli", "model": "opus", "max_turns": 50, "timeout_minutes": 30, "allowed_tools": ["Read", "Bash"], "prompt_file": ""},
    }
    return config


@pytest.fixture
def orchestrator(tmp_project, mock_config):
    return Orchestrator(config=mock_config, output_dir=tmp_project, prd_path="docs/test.md")


class TestOrchestratorInit:
    def test_initial_state(self, orchestrator):
        assert orchestrator.state == OrchestratorState.INIT

    def test_creates_output_dirs(self, orchestrator, tmp_project):
        assert (tmp_project / "state").exists()
        assert (tmp_project / "state" / "sprints").exists()
        assert (tmp_project / "workspace").exists()
        assert (tmp_project / "logs").exists()


class TestOrchestratorStateTransitions:
    def test_transition_init_to_analyzing(self, orchestrator):
        orchestrator._transition(OrchestratorState.ANALYZING)
        assert orchestrator.state == OrchestratorState.ANALYZING

    def test_checkpoint_saved_on_transition(self, orchestrator):
        orchestrator._transition(OrchestratorState.ANALYZING)
        cp = orchestrator.checkpoint_mgr.load()
        assert cp is not None
        assert cp.status == OrchestratorState.ANALYZING


class TestOrchestratorRunAgent:
    def test_run_agent_delegates_to_executor(self, orchestrator):
        orchestrator.cli_executor = MagicMock(spec=CLIExecutor)
        orchestrator.cli_executor.run_agent.return_value = AgentResult(output="analysis complete", cost=3.0, exit_code=0)

        result = orchestrator._run_agent(agent_key="analyst", prompt="Analyze the PRD")
        assert result.is_success
        orchestrator.cli_executor.run_agent.assert_called_once()

    def test_run_agent_tracks_cost(self, orchestrator):
        orchestrator.cli_executor = MagicMock(spec=CLIExecutor)
        orchestrator.cli_executor.run_agent.return_value = AgentResult(output="done", cost=5.0, exit_code=0)
        orchestrator.cost_tracker = MagicMock(spec=CostTracker)

        orchestrator._run_agent(agent_key="analyst", prompt="test")
        orchestrator.cost_tracker.record.assert_called_once()
        orchestrator.cost_tracker.check_limit.assert_called_once()


class TestOrchestratorResume:
    def test_resume_from_checkpoint(self, tmp_project, mock_config):
        state_dir = tmp_project / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "sprints").mkdir(exist_ok=True)
        cp = Checkpoint(project_name="TestProject", profile="web-app", status=OrchestratorState.PLANNING)
        CheckpointManager(state_dir).save(cp)

        orch = Orchestrator(config=mock_config, output_dir=tmp_project, prd_path="docs/test.md")
        assert orch.state == OrchestratorState.PLANNING

    def test_resume_completed_project(self, tmp_project, mock_config):
        state_dir = tmp_project / "state"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "sprints").mkdir(exist_ok=True)
        cp = Checkpoint(project_name="TestProject", profile="web-app", status=OrchestratorState.COMPLETED)
        CheckpointManager(state_dir).save(cp)

        orch = Orchestrator(config=mock_config, output_dir=tmp_project, prd_path="docs/test.md")
        assert orch.state == OrchestratorState.COMPLETED
