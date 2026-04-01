import pytest
from agentforge.models.state import OrchestratorState, Checkpoint
from agentforge.models.agent import AgentResult, AgentConfig
from agentforge.models.sprint import Sprint, SprintContract
from agentforge.models.plan import Plan, RequirementSpec, Module, Feature


class TestOrchestratorState:
    def test_all_states_exist(self):
        assert OrchestratorState.INIT.value == "INIT"
        assert OrchestratorState.ANALYZING.value == "ANALYZING"
        assert OrchestratorState.REVIEWING_REQ.value == "REVIEWING_REQ"
        assert OrchestratorState.PLANNING.value == "PLANNING"
        assert OrchestratorState.SPRINTING.value == "SPRINTING"
        assert OrchestratorState.SPRINT_EVALUATING.value == "SPRINT_EVALUATING"
        assert OrchestratorState.CONTEXT_RESET.value == "CONTEXT_RESET"
        assert OrchestratorState.FINAL_QA.value == "FINAL_QA"
        assert OrchestratorState.COMPLETED.value == "COMPLETED"
        assert OrchestratorState.WAITING_HUMAN.value == "WAITING_HUMAN"
        assert OrchestratorState.PAUSED.value == "PAUSED"
        assert OrchestratorState.BLOCKED.value == "BLOCKED"


class TestCheckpoint:
    def test_create_checkpoint(self):
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.SPRINTING,
            current_sprint="S002",
            current_agent="ui_generator",
            completed_sprints=["S001"],
        )
        assert cp.project_name == "Test"
        assert cp.status == OrchestratorState.SPRINTING
        assert cp.failed_attempts == 0
        assert cp.error is None

    def test_checkpoint_serialization(self):
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.INIT,
        )
        data = cp.model_dump()
        assert data["status"] == "INIT"
        restored = Checkpoint.model_validate(data)
        assert restored.status == OrchestratorState.INIT


class TestAgentResult:
    def test_create_result(self):
        r = AgentResult(
            output="done",
            files_changed=["src/main.py"],
            token_usage={"prompt": 100, "completion": 50},
            cost=0.5,
            exit_code=0,
        )
        assert r.is_success

    def test_failed_result(self):
        r = AgentResult(
            output="error",
            files_changed=[],
            token_usage={},
            cost=0.1,
            exit_code=1,
        )
        assert not r.is_success


class TestAgentConfig:
    def test_create_config(self):
        c = AgentConfig(
            engine="claude-cli",
            model="opus",
            max_turns=20,
            timeout_minutes=15,
            allowed_tools=["Read", "Write"],
            prompt_file="agents/analyst/prompts/system.md",
        )
        assert c.engine == "claude-cli"
        assert "Read" in c.allowed_tools


class TestSprint:
    def test_create_sprint(self):
        s = Sprint(
            id="S001",
            name="Auth module",
            type="fullstack",
            features=["F001"],
            depends_on=[],
            contract=SprintContract(
                done_criteria=["Login works"],
                test_scenarios=["Test login"],
            ),
        )
        assert s.id == "S001"
        assert s.type == "fullstack"
        assert len(s.contract.done_criteria) == 1


class TestPlan:
    def test_create_plan_from_dict(self, sample_plan):
        plan = Plan.model_validate(sample_plan)
        assert len(plan.sprints) == 2
        assert plan.sprints[0].id == "S001"
        assert plan.tech_stack["frontend"] == "vue3 + vite"


class TestRequirementSpec:
    def test_create_spec_from_dict(self, sample_requirement_spec):
        spec = RequirementSpec.model_validate(sample_requirement_spec)
        assert spec.project_name == "Test Project"
        assert len(spec.modules) == 1
        assert spec.modules[0].features[0].id == "F001"
        assert not spec.has_ambiguities

    def test_spec_with_ambiguities(self):
        spec = RequirementSpec(
            project_name="Test",
            modules=[],
            non_functional={},
            ambiguities=[
                {"id": "A001", "description": "unclear", "needs_human": True}
            ],
        )
        assert spec.has_ambiguities
