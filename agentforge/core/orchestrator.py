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
from agentforge.learning.extractor import Extractor
from agentforge.learning.injector import KnowledgeInjector
from agentforge.learning.knowledge_base import KnowledgeBase, Pattern, AntiPattern
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
        knowledge_dir: Optional[Path] = None,
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

        # Learning engine
        self.knowledge_base: Optional[KnowledgeBase] = None
        self.injector: Optional[KnowledgeInjector] = None
        self.extractor = Extractor()
        if knowledge_dir:
            self.knowledge_base = KnowledgeBase(knowledge_dir)
            self.injector = KnowledgeInjector(self.knowledge_base)
            logger.info(f"Learning engine initialized from {knowledge_dir}")

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

    def _find_existing_state_file(self, name: str) -> Optional[Path]:
        """Search for existing state file. JSON preferred over MD."""
        search_dirs = [
            self.state_dir,                           # output/{project}/state/
            Path.cwd() / "state",                     # {cwd}/state/ (user-created)
        ]
        # JSON first (structured, framework can parse)
        for d in search_dirs:
            candidate = d / f"{name}.json"
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate
        # MD fallback (needs conversion)
        for d in search_dirs:
            candidate = d / f"{name}.md"
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate
        return None

    def _load_state_file(self, path: Path) -> Optional[dict]:
        """Load a state file. JSON parsed directly; MD triggers Agent conversion."""
        content = path.read_text(encoding="utf-8")
        if path.suffix == ".json":
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON: {path}")
                return None
        elif path.suffix == ".md":
            # MD file found — need to convert to JSON via Agent
            return self._convert_md_to_json(path)
        return None

    def _convert_md_to_json(self, md_path: Path) -> Optional[dict]:
        """Use Agent to convert an existing MD state file to JSON. Retries on invalid JSON."""
        md_abs = str(md_path.resolve())
        name = md_path.stem  # "requirement_spec" or "plan"
        json_path = self.state_dir / f"{name}.json"
        state_abs = str(self.state_dir.resolve())

        for attempt in range(3):
            if attempt == 0:
                logger.info(f"Converting {md_path.name} to JSON format...")
                prompt = (
                    f"Read the existing document at: {md_abs}\n\n"
                    f"Convert its content into valid JSON and write to: {state_abs}/{name}.json\n\n"
                    f"CRITICAL: Output must be valid JSON. Verify there are no trailing commas, "
                    f"unescaped quotes in strings, or missing delimiters. "
                    f"Keep ALL information from the original document."
                )
            else:
                # Read the broken JSON and ask Agent to fix it
                broken = json_path.read_text(encoding="utf-8") if json_path.exists() else ""
                logger.info(f"Fixing invalid JSON (attempt {attempt + 1})...")
                prompt = (
                    f"The file at {state_abs}/{name}.json contains invalid JSON. "
                    f"Fix it and overwrite the file. The JSON parse error was: {last_error}\n\n"
                    f"Read the file, fix the JSON syntax error, and write the corrected version back."
                )

            self._run_agent(
                agent_key="analyst" if "requirement" in name else "planner",
                prompt=prompt,
            )

            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text(encoding="utf-8"))
                    logger.info(f"Successfully converted {md_path.name} -> {name}.json")
                    return data
                except json.JSONDecodeError as e:
                    last_error = str(e)
                    logger.warning(f"Invalid JSON (attempt {attempt + 1}): {last_error}")

        logger.error(f"Failed to convert {md_path.name} to valid JSON after 3 attempts")
        return None

    def _generate_md_from_json(self, json_path: Path) -> None:
        """Generate a human-readable MD file from a JSON state file."""
        md_path = json_path.with_suffix(".md")
        if md_path.exists():
            return  # Don't overwrite existing MD

        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError):
            return

        name = json_path.stem
        lines = [f"# {data.get('project_name', name)}\n"]

        if name == "requirement_spec":
            for module in data.get("modules", []):
                lines.append(f"\n## {module.get('id', '')} - {module.get('name', '')} [{module.get('priority', '')}]\n")
                for feat in module.get("features", []):
                    lines.append(f"### {feat.get('id', '')} - {feat.get('description', '')}")
                    for ac in feat.get("acceptance_criteria", []):
                        lines.append(f"- {ac}")

        elif name == "plan":
            lines.append(f"\n## Tech Stack\n")
            for k, v in data.get("tech_stack", {}).items():
                lines.append(f"- **{k}**: {v}")
            lines.append(f"\n## Sprints\n")
            for sprint in data.get("sprints", []):
                lines.append(f"### {sprint.get('id', '')} [{sprint.get('type', '')}] {sprint.get('name', '')}")
                for c in sprint.get("contract", {}).get("done_criteria", []):
                    lines.append(f"- [ ] {c}")

        md_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Generated {md_path.name} from {json_path.name}")

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
            # Try multiple locations for prompt file
            prompt_path = None
            candidates = [
                Path(agent_config.prompt_file),                           # Relative to CWD
                Path.cwd() / agent_config.prompt_file,                    # Explicit CWD
            ]
            # Add install directory path
            from agentforge.core.resources import resolve_agents_dir
            agents_dir = resolve_agents_dir()
            if agents_dir:
                # prompt_file is like "agents/analyst/prompts/system.md"
                # agents_dir is like "/path/to/agentforge/agents"
                # Strip "agents/" prefix and join with agents_dir
                relative = agent_config.prompt_file
                if relative.startswith("agents/"):
                    relative = relative[len("agents/"):]
                candidates.append(agents_dir / relative)

            for candidate in candidates:
                if candidate.exists():
                    prompt_path = candidate
                    break

            if prompt_path:
                system_prompt = prompt_path.read_text(encoding="utf-8")
                logger.debug(f"Loaded system prompt from: {prompt_path}")
            else:
                logger.warning(f"System prompt not found: {agent_config.prompt_file}")

        # Inject learned experience into system prompt
        if self.injector and system_prompt:
            agent_short = agent_key.split(".")[-1]  # "generators.ui" -> "ui"
            experience = self.injector.inject(
                agent=agent_short,
                profile=self.config.profile,
            )
            if experience:
                system_prompt = system_prompt + "\n\n" + experience

        # All agents use absolute paths for workspace
        # Analyst/Planner work at project output root (access state/ + workspace/)
        # Generators work in workspace/ (where code lives)
        if agent_key in ("analyst", "planner", "evaluator", "requirement_reviewer"):
            work_dir = str(self.output_dir.resolve())
        else:
            work_dir = str(self.workspace_dir.resolve())

        result = self.cli_executor.run_agent(
            prompt=prompt,
            workspace=work_dir,
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

        # Resume from PAUSED/BLOCKED: reset failure counter and return to SPRINTING
        if self.state in (OrchestratorState.PAUSED, OrchestratorState.BLOCKED):
            cp = self.checkpoint_mgr.load()
            logger.info(f"Resuming from {self.state.value} (sprint: {cp.current_sprint}, failures: {cp.failed_attempts})")
            # Reset failure counter and set back to SPRINTING
            self.checkpoint_mgr.update(
                status=OrchestratorState.SPRINTING,
                failed_attempts=0,
                error=None,
            )
            self.state = OrchestratorState.SPRINTING

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

        # Check for existing analysis results (json or md)
        existing_spec = self._find_existing_state_file("requirement_spec")
        if existing_spec:
            logger.info(f"Found existing requirement spec: {existing_spec}")
            self.requirement_spec = self._load_state_file(existing_spec)
        else:
            prd_abs = str(Path(self.prd_path).resolve())
            state_abs = str(self.state_dir.resolve())
            prd_suffix = Path(self.prd_path).suffix.lower()
            file_hint = ""
            if prd_suffix == ".pdf":
                file_hint = "\n\nNote: This is a PDF file. Use the Read tool to read it (it supports PDF)."
            result = self._run_agent(
                agent_key="analyst",
                prompt=f"Analyze the PRD file at: {prd_abs}{file_hint}\n\nWrite output to: {state_abs}/requirement_spec.json",
            )

            if not result.is_success:
                self.checkpoint_mgr.record_failure(f"Analyst failed: {result.output}")
                return

            spec_path = self.state_dir / "requirement_spec.json"
            if spec_path.exists():
                self.requirement_spec = json.loads(spec_path.read_text(encoding="utf-8"))
                self._generate_md_from_json(spec_path)

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

        # Check for existing plan (json or md)
        existing_plan = self._find_existing_state_file("plan")
        if existing_plan:
            logger.info(f"Found existing plan: {existing_plan}")
            self.plan = self._load_state_file(existing_plan)
        else:
            state_abs = str(self.state_dir.resolve())
            result = self._run_agent(
                agent_key="planner",
                prompt=f"Read requirement spec from: {state_abs}/requirement_spec.json\n\nWrite technical plan to: {state_abs}/plan.json",
            )

            if not result.is_success:
                self.checkpoint_mgr.record_failure(f"Planner failed: {result.output}")
                return

            plan_path = self.state_dir / "plan.json"
            if plan_path.exists():
                self.plan = json.loads(plan_path.read_text(encoding="utf-8"))
                self._generate_md_from_json(plan_path)

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

        workspace_abs = str(self.workspace_dir.resolve())
        state_abs = str(self.state_dir.resolve())

        for gen_key, reviewer_key in generators:
            gen_result = self._run_agent(
                agent_key=gen_key,
                prompt=f"Implement sprint {sprint_id}: {sprint['name']}\n\nWorkspace directory: {workspace_abs}\nState directory: {state_abs}",
                sprint_id=sprint_id,
                append_prompt=handoff_prompt,
            )
            if not gen_result.is_success:
                self.checkpoint_mgr.record_failure(f"Generator {gen_key} failed for {sprint_id}")
                return False

            for round_num in range(self.config.orchestrator.max_reviewer_rounds):
                review_result = self._run_agent(
                    agent_key=f"reviewers.{reviewer_key}",
                    prompt=f"Review code for sprint {sprint_id}\n\nWorkspace directory: {workspace_abs}",
                    sprint_id=sprint_id,
                )
                if review_result.is_success:
                    break

                logger.info(f"Review round {round_num + 1} for {reviewer_key}: needs revision")
                gen_result = self._run_agent(
                    agent_key=gen_key,
                    prompt=f"Fix issues from review for sprint {sprint_id}:\n{review_result.output}\n\nWorkspace directory: {workspace_abs}",
                    sprint_id=sprint_id,
                    append_prompt=handoff_prompt,
                )
                if not gen_result.is_success:
                    self.checkpoint_mgr.record_failure(f"Generator {gen_key} fix failed for {sprint_id}")
                    return False

        return True

    def _run_final_qa(self) -> None:
        self._transition(OrchestratorState.FINAL_QA)
        workspace_abs = str(self.workspace_dir.resolve())
        state_abs = str(self.state_dir.resolve())
        result = self._run_agent(
            agent_key="evaluator",
            prompt=f"Run full application QA\n\nWorkspace directory: {workspace_abs}\nState directory: {state_abs}\nWrite QA results to: {state_abs}/final_qa.json",
        )

        qa_path = self.state_dir / "final_qa.json"
        qa_path.write_text(
            json.dumps({"output": result.output, "success": result.is_success}, indent=2),
            encoding="utf-8",
        )

        if self.human_gate.should_pause(GateType.AFTER_FINAL_QA):
            self.human_gate.wait_for_human(GateType.AFTER_FINAL_QA, context={"qa_passed": result.is_success})

        # Extract and persist learned experience
        self._extract_learning()

        self._transition(OrchestratorState.COMPLETED)

    def _extract_learning(self) -> None:
        """Extract patterns/antipatterns from this run and save to knowledge base."""
        if not self.knowledge_base:
            return

        try:
            result = self.extractor.extract(self.state_dir, profile=self.config.profile)

            for p_data in result.get("patterns", []):
                self.knowledge_base.add_pattern(Pattern.model_validate(p_data))

            for ap_data in result.get("antipatterns", []):
                self.knowledge_base.add_antipattern(AntiPattern.model_validate(ap_data))

            # Save project history for cross-project analysis
            history_dir = self.knowledge_base.knowledge_dir / "project_history"
            history_dir.mkdir(parents=True, exist_ok=True)
            cost_summary = self.cost_tracker.get_summary()
            history = {
                "project_name": self.config.project_name,
                "profile": self.config.profile,
                "total_cost": cost_summary.get("total_cost", 0),
                "total_sprints": len(self.checkpoint_mgr.load().completed_sprints) if self.checkpoint_mgr.load() else 0,
                "patterns_extracted": len(result.get("patterns", [])),
                "antipatterns_extracted": len(result.get("antipatterns", [])),
            }
            history_path = history_dir / f"{self.config.project_name}.json"
            history_path.write_text(
                json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            logger.info(
                f"Learning extracted: {len(result.get('patterns', []))} patterns, "
                f"{len(result.get('antipatterns', []))} antipatterns"
            )
        except Exception as e:
            logger.warning(f"Failed to extract learning: {e}")
