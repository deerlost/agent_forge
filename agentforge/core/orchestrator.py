import json
import logging
from pathlib import Path
from typing import Any, Optional

from agentforge.core.checkpoint import CheckpointManager
from agentforge.core.cli_executor import CLIExecutor
from agentforge.core.config import AppConfig
from agentforge.core.context_manager import ContextManager
from agentforge.core.cost_tracker import CostTracker
from agentforge.core.human_gate import GateType, HumanGate
from agentforge.core.profile import Profile, load_profile, load_profiles_from_string, merge_profiles
from agentforge.core.template_copier import TemplateCopier
from agentforge.models.agent import AgentResult
from agentforge.models.state import Checkpoint, OrchestratorState

logger = logging.getLogger(__name__)


class Orchestrator:
    def __init__(
        self,
        config: AppConfig,
        output_dir: Path,
        prd_path: str,
        auto_mode: bool = False,
        profiles_dir: Optional[Path] = None,
        templates_dir: Optional[Path] = None,
    ):
        self.config = config
        self.output_dir = Path(output_dir)
        self.prd_path = prd_path
        self.state_dir = self.output_dir / "state"
        self.workspace_dir = self.output_dir / "workspace"
        self.logs_dir = self.output_dir / "logs"

        # Ensure directories
        self.state_dir.mkdir(parents=True, exist_ok=True)
        (self.state_dir / "sprints").mkdir(exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.checkpoint_mgr = CheckpointManager(self.state_dir, max_retries=config.orchestrator.max_sprint_retries)
        self.cli_executor = CLIExecutor()
        self.cost_tracker = CostTracker(self.state_dir, max_cost=config.cost.max_total_cost, warn_threshold=config.cost.warn_threshold)
        self.human_gate = HumanGate(config.human_checkpoints, auto_mode=auto_mode)
        self.context_mgr = ContextManager(self.state_dir)

        # Load profile and copy templates
        self.profile: Optional[Profile] = None
        if profiles_dir and config.profile:
            try:
                profile_names = config.profile
                if "," in profile_names:
                    profiles = load_profiles_from_string(profile_names, profiles_dir)
                    self.profile = merge_profiles(profiles)
                else:
                    self.profile = load_profile(profile_names, profiles_dir)
                logger.info(f"Loaded profile: {self.profile.name}")
            except FileNotFoundError:
                logger.warning(f"Profile '{config.profile}' not found in {profiles_dir}")

        if templates_dir and self.profile:
            copier = TemplateCopier(templates_dir)
            copier.copy_templates(self.profile.templates, self.workspace_dir)
            logger.info(f"Templates copied to workspace")

        # Runtime state
        self.plan: Optional[dict] = None
        self.requirement_spec: Optional[dict] = None
        self.file_manifest: list[dict] = []
        self.key_decisions: list[str] = []
        self.known_issues: list[dict] = []

        # Resume or init
        existing_cp = self.checkpoint_mgr.load()
        if existing_cp:
            self.state = existing_cp.status
            self._load_existing_state(existing_cp)
            logger.info(f"Resumed from checkpoint: {self.state.value}")
        else:
            self.state = OrchestratorState.INIT
            self.checkpoint_mgr.save(Checkpoint(
                project_name=config.project_name,
                profile=config.profile,
                status=OrchestratorState.INIT,
            ))

    def _load_existing_state(self, cp: Checkpoint) -> None:
        plan_path = self.state_dir / "plan.json"
        if plan_path.exists():
            self.plan = json.loads(plan_path.read_text(encoding="utf-8"))

        spec_path = self.state_dir / "requirement_spec.json"
        if spec_path.exists():
            self.requirement_spec = json.loads(spec_path.read_text(encoding="utf-8"))

        if cp.completed_sprints:
            last_sprint = cp.completed_sprints[-1]
            handoff = self.context_mgr.load_handoff(last_sprint)
            if handoff:
                self.file_manifest = handoff.get("file_manifest", [])
                self.key_decisions = handoff.get("key_decisions", [])
                self.known_issues = handoff.get("known_issues", [])

    def _transition(self, new_state: OrchestratorState, **kwargs) -> None:
        logger.info(f"State transition: {self.state.value} -> {new_state.value}")
        self.state = new_state
        self.checkpoint_mgr.update(status=new_state, **kwargs)

    def _run_agent(
        self,
        agent_key: str,
        prompt: str,
        sprint_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        append_prompt: Optional[str] = None,
    ) -> AgentResult:
        agent_config = self.config.get_agent_config(agent_key)

        if system_prompt is None and agent_config.prompt_file:
            prompt_path = Path(agent_config.prompt_file)
            if prompt_path.exists():
                system_prompt = prompt_path.read_text(encoding="utf-8")

        result = self.cli_executor.run_agent(
            prompt=prompt,
            workspace=str(self.workspace_dir),
            model=agent_config.model,
            allowed_tools=agent_config.allowed_tools,
            max_turns=agent_config.max_turns,
            timeout_minutes=agent_config.timeout_minutes,
            system_prompt=system_prompt,
            append_prompt=append_prompt,
        )

        self.cost_tracker.record(agent_key, result, sprint_id=sprint_id)
        self.cost_tracker.check_limit()

        return result

    def run(self) -> None:
        logger.info(f"Starting AgentForge run: {self.config.project_name}")

        if self.state == OrchestratorState.COMPLETED:
            logger.info("Project already completed.")
            return

        if self.state in (OrchestratorState.INIT, OrchestratorState.ANALYZING):
            self._run_analysis()

        if self.state == OrchestratorState.REVIEWING_REQ:
            self._run_requirement_review()

        if self.state == OrchestratorState.PLANNING:
            self._run_planning()

        if self.state in (OrchestratorState.SPRINTING, OrchestratorState.SPRINT_EVALUATING, OrchestratorState.CONTEXT_RESET):
            self._run_sprints()

        if self.state == OrchestratorState.FINAL_QA:
            self._run_final_qa()

        logger.info("AgentForge run completed.")

    def _run_analysis(self) -> None:
        self._transition(OrchestratorState.ANALYZING)
        result = self._run_agent(agent_key="analyst", prompt=f"Analyze the PRD file at: {self.prd_path}")

        if not result.is_success:
            self.checkpoint_mgr.record_failure(f"Analyst failed: {result.output}")
            return

        spec_path = self.state_dir / "requirement_spec.json"
        if spec_path.exists():
            self.requirement_spec = json.loads(spec_path.read_text(encoding="utf-8"))

        ambiguities = (self.requirement_spec or {}).get("ambiguities", [])
        human_ambiguities = [a for a in ambiguities if a.get("needs_human")]
        if human_ambiguities and self.human_gate.should_pause(GateType.AMBIGUITY):
            self.human_gate.wait_for_human(GateType.AMBIGUITY, context={"ambiguities": human_ambiguities})

        if self.human_gate.should_pause(GateType.AFTER_ANALYSIS):
            self.human_gate.wait_for_human(
                GateType.AFTER_ANALYSIS,
                context={"modules": len((self.requirement_spec or {}).get("modules", []))},
            )

        if self.config.requirement_review.enabled:
            self._transition(OrchestratorState.REVIEWING_REQ)
        else:
            self._transition(OrchestratorState.PLANNING)

    def _run_requirement_review(self) -> None:
        for round_num in range(3):
            result = self._run_agent(agent_key="requirement_reviewer", prompt="Review the requirement_spec.json")
            if result.is_success:
                break
            logger.warning(f"Requirement review round {round_num + 1} failed")
        self._transition(OrchestratorState.PLANNING)

    def _run_planning(self) -> None:
        self._transition(OrchestratorState.PLANNING)
        result = self._run_agent(agent_key="planner", prompt="Create a technical plan based on requirement_spec.json")

        if not result.is_success:
            self.checkpoint_mgr.record_failure(f"Planner failed: {result.output}")
            return

        plan_path = self.state_dir / "plan.json"
        if plan_path.exists():
            self.plan = json.loads(plan_path.read_text(encoding="utf-8"))

        if self.human_gate.should_pause(GateType.AFTER_PLANNING):
            sprint_count = len((self.plan or {}).get("sprints", []))
            self.human_gate.wait_for_human(GateType.AFTER_PLANNING, context={"sprint_count": sprint_count})

        self._transition(OrchestratorState.SPRINTING)

    def _run_sprints(self) -> None:
        if not self.plan:
            logger.error("No plan loaded, cannot run sprints")
            return

        sprints = self.plan.get("sprints", [])
        cp = self.checkpoint_mgr.load()
        completed = set(cp.completed_sprints if cp else [])
        sprint_number = len(completed)

        for sprint in sprints:
            sprint_id = sprint["id"]
            if sprint_id in completed:
                continue

            sprint_number += 1
            logger.info(f"Starting sprint {sprint_id}: {sprint['name']}")
            self.checkpoint_mgr.update(status=OrchestratorState.SPRINTING, current_sprint=sprint_id)

            handoff = self.context_mgr.build_handoff(
                plan=self.plan,
                current_sprint_id=sprint_id,
                completed_sprints=list(completed),
                file_manifest=self.file_manifest,
                key_decisions=self.key_decisions,
                known_issues=self.known_issues,
            )
            handoff_prompt = self.context_mgr.format_as_prompt(handoff)

            success = self._run_sprint_generators(sprint, handoff_prompt)
            if not success:
                return

            self._transition(OrchestratorState.SPRINT_EVALUATING)
            eval_result = self._run_agent(
                agent_key="evaluator",
                prompt=f"Evaluate sprint {sprint_id}",
                sprint_id=sprint_id,
            )

            if not eval_result.is_success:
                cp = self.checkpoint_mgr.load()
                if cp and cp.failed_attempts >= self.config.orchestrator.max_sprint_retries:
                    return
                self.checkpoint_mgr.record_failure(f"Sprint {sprint_id} eval failed")
                continue

            self.context_mgr.save_handoff(sprint_id, handoff)
            self.checkpoint_mgr.complete_sprint(sprint_id)
            completed.add(sprint_id)
            self._transition(OrchestratorState.CONTEXT_RESET)
            logger.info(f"Sprint {sprint_id} completed, context reset")

            if self.human_gate.should_pause_at_sprint(sprint_number):
                self.human_gate.wait_for_human(
                    GateType.SPRINT_INTERVAL,
                    context={"sprint_number": sprint_number, "sprint_id": sprint_id},
                )

        self._transition(OrchestratorState.FINAL_QA)

    def _run_sprint_generators(self, sprint: dict, handoff_prompt: str) -> bool:
        sprint_id = sprint["id"]
        sprint_type = sprint.get("type", "fullstack")

        generators = []
        if sprint_type in ("backend", "fullstack"):
            generators.append(("generators.api", "api_reviewer"))
        if sprint_type in ("frontend", "fullstack"):
            generators.append(("generators.ui", "ui_reviewer"))

        for gen_key, reviewer_key in generators:
            gen_result = self._run_agent(
                agent_key=gen_key,
                prompt=f"Implement sprint {sprint_id}: {sprint['name']}",
                sprint_id=sprint_id,
                append_prompt=handoff_prompt,
            )
            if not gen_result.is_success:
                self.checkpoint_mgr.record_failure(f"Generator {gen_key} failed for {sprint_id}")
                return False

            for round_num in range(self.config.orchestrator.max_reviewer_rounds):
                review_result = self._run_agent(
                    agent_key=f"reviewers.{reviewer_key}",
                    prompt=f"Review code for sprint {sprint_id}",
                    sprint_id=sprint_id,
                )
                if review_result.is_success:
                    break

                logger.info(f"Review round {round_num + 1} for {reviewer_key}: needs revision")
                gen_result = self._run_agent(
                    agent_key=gen_key,
                    prompt=f"Fix issues from review for sprint {sprint_id}:\n{review_result.output}",
                    sprint_id=sprint_id,
                    append_prompt=handoff_prompt,
                )
                if not gen_result.is_success:
                    self.checkpoint_mgr.record_failure(f"Generator {gen_key} fix failed for {sprint_id}")
                    return False

        return True

    def _run_final_qa(self) -> None:
        self._transition(OrchestratorState.FINAL_QA)
        result = self._run_agent(agent_key="evaluator", prompt="Run full application QA")

        qa_path = self.state_dir / "final_qa.json"
        qa_path.write_text(
            json.dumps({"output": result.output, "success": result.is_success}, indent=2),
            encoding="utf-8",
        )

        if self.human_gate.should_pause(GateType.AFTER_FINAL_QA):
            self.human_gate.wait_for_human(GateType.AFTER_FINAL_QA, context={"qa_passed": result.is_success})

        self._transition(OrchestratorState.COMPLETED)
