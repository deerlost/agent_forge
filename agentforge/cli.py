import json
import logging
import sys
from pathlib import Path

import click

from agentforge.core.config import load_config
from agentforge.core.checkpoint import CheckpointManager
from agentforge.core.cost_tracker import CostTracker
from agentforge.core.orchestrator import Orchestrator
from agentforge.core.profile import load_profile
from agentforge.core.resources import resolve_config_dir, resolve_profiles_dir, resolve_templates_dir, resolve_knowledge_dir
from agentforge.learning.analyzer import Analyzer
from agentforge.learning.extractor import Extractor
from agentforge.learning.knowledge_base import KnowledgeBase, Pattern, AntiPattern


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AgentForge - Long-running multi-agent application generation framework."""
    pass


@main.command()
@click.option("--prd", required=True, type=click.Path(exists=True), help="Path to PRD document")
@click.option("--profile", default="web-app", help="Service profile name")
@click.option("--backend", default=None, help="Backend tech stack (spring-boot, fastapi)")
@click.option("--auto", is_flag=True, help="Disable all human checkpoints")
@click.option("--config-dir", default=None, type=click.Path(), help="Config directory (default: auto-detect)")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def run(prd, profile, backend, auto, config_dir, output_dir, verbose):
    """Full pipeline: analysis + planning + code generation + QA.

    \b
    Resumes from checkpoint if analyze/plan was run before.

    \b
    Examples:
      agentforge run --prd docs/prd.md --profile web-app --auto
      agentforge run --prd docs/prd.md --profile web-app,scheduler
      agentforge run --prd docs/prd.md --backend spring-boot
    """
    setup_logging(verbose)
    config_path = resolve_config_dir(config_dir)
    project_yaml = Path("agentforge.yaml")
    project_config_path = project_yaml if project_yaml.exists() else None
    config = load_config(config_path, project_config_path=project_config_path)
    config.profile = profile
    if not config.project_name:
        config.project_name = Path(prd).stem

    # Resolve output and knowledge dirs: CLI arg > agentforge.yaml > default
    effective_output = config.output_dir or output_dir
    project_output = Path(effective_output) / config.project_name

    profiles_dir = resolve_profiles_dir()
    templates_dir = resolve_templates_dir()
    knowledge_dir = resolve_knowledge_dir(config.knowledge_dir)

    click.echo(f"AgentForge v0.1.0")
    click.echo(f"Project: {config.project_name}")
    click.echo(f"Profile: {profile}")
    click.echo(f"PRD: {prd}")
    click.echo(f"Output: {project_output}")
    click.echo()

    orch = Orchestrator(
        config=config,
        output_dir=project_output,
        prd_path=prd,
        auto_mode=auto,
        profiles_dir=profiles_dir,
        templates_dir=templates_dir,
        knowledge_dir=knowledge_dir,
    )
    orch.run()


@main.command()
@click.option("--prd", required=True, type=click.Path(exists=True), help="Path to PRD document")
@click.option("--config-dir", default=None, type=click.Path(), help="Config directory (default: auto-detect)")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def analyze(prd, config_dir, output_dir, verbose):
    """Requirement analysis only. Output: requirement_spec.json.

    \b
    Examples:
      agentforge analyze --prd docs/prd.md
    """
    setup_logging(verbose)
    config = load_config(resolve_config_dir(config_dir))
    if not config.project_name:
        config.project_name = Path(prd).stem
    project_output = Path(output_dir) / config.project_name

    click.echo(f"Analyzing PRD: {prd}")
    orch = Orchestrator(config=config, output_dir=project_output, prd_path=prd, auto_mode=True)
    orch._run_analysis()
    _print_analysis_result(project_output)


@main.command()
@click.option("--prd", required=True, type=click.Path(exists=True), help="Path to PRD document")
@click.option("--profile", default="web-app", help="Service profile name")
@click.option("--config-dir", default=None, type=click.Path(), help="Config directory (default: auto-detect)")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def plan(prd, profile, config_dir, output_dir, verbose):
    """Requirement analysis + architecture design. Output: requirement_spec.json + plan.json.

    \b
    Examples:
      agentforge plan --prd docs/prd.md --profile web-app
    """
    setup_logging(verbose)
    config = load_config(resolve_config_dir(config_dir))
    config.profile = profile
    if not config.project_name:
        config.project_name = Path(prd).stem
    project_output = Path(output_dir) / config.project_name

    click.echo(f"Analyzing and planning: {prd}")
    orch = Orchestrator(config=config, output_dir=project_output, prd_path=prd, auto_mode=True)
    orch._run_analysis()
    if orch.state in (orch.state.PLANNING, orch.state.REVIEWING_REQ):
        orch._run_planning()
    _print_analysis_result(project_output)
    _print_plan_result(project_output)


def _print_analysis_result(project_output: Path):
    """Print analysis summary."""
    spec_path = project_output / "state" / "requirement_spec.json"
    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        modules = spec.get("modules", [])
        features = sum(len(m.get("features", [])) for m in modules)
        ambiguities = spec.get("ambiguities", [])
        click.echo(f"Requirement Analysis:")
        click.echo(f"  Project: {spec.get('project_name', 'N/A')}")
        click.echo(f"  Modules: {len(modules)}")
        click.echo(f"  Features: {features}")
        click.echo(f"  Ambiguities: {len(ambiguities)}")
        if ambiguities:
            click.echo(f"  Ambiguous items:")
            for a in ambiguities:
                click.echo(f"    - {a.get('description', '')}")
        click.echo(f"  Output: {spec_path}")
    else:
        click.echo("Analysis failed - no output generated.")


def _print_plan_result(project_output: Path):
    """Print plan summary."""
    plan_path = project_output / "state" / "plan.json"
    if plan_path.exists():
        plan_data = json.loads(plan_path.read_text(encoding="utf-8"))
        sprints = plan_data.get("sprints", [])
        apis = plan_data.get("api_contract", [])
        entities = plan_data.get("data_model", [])
        click.echo(f"\nArchitecture Design:")
        click.echo(f"  Tech stack: {plan_data.get('tech_stack', {})}")
        click.echo(f"  Data model: {len(entities)} entities")
        click.echo(f"  API endpoints: {len(apis)}")
        click.echo(f"  Sprints: {len(sprints)}")
        if sprints:
            click.echo(f"  Sprint breakdown:")
            for s in sprints:
                click.echo(f"    {s['id']} [{s.get('type', '')}] {s['name']}")
        click.echo(f"  Output: {plan_path}")
    else:
        click.echo("\nPlanning failed - no output generated.")


@main.command()
@click.option("--project-dir", required=True, type=click.Path(exists=True), help="Path to existing project source code")
@click.option("--profile", default="web-app", help="Service profile name")
@click.option("--config-dir", default=None, type=click.Path(), help="Config directory (default: auto-detect)")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory for review results")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def review(project_dir, profile, config_dir, output_dir, verbose):
    """Review an existing project's code quality and extract experience.

    \b
    This command runs Reviewer and Evaluator agents on existing code
    (not generated by AgentForge) to produce review data and extract
    learnable experience.

    \b
    Flow:
      1. Scan project directory to detect tech stack
      2. Run appropriate Reviewers (UI/API) on the code
      3. Run Evaluator for overall QA assessment
      4. Save review results to state/ (extractable by 'agentforge extract')
      5. Auto-extract experience to knowledge base

    \b
    Examples:
      agentforge review --project-dir /path/to/my-project --profile web-app
      agentforge review --project-dir ./model-dispatch/model-tester
    """
    setup_logging(verbose)
    config = load_config(resolve_config_dir(config_dir))
    config.profile = profile

    src_dir = Path(project_dir)
    project_name = src_dir.name
    config.project_name = project_name
    review_output = Path(output_dir) / f"{project_name}-review"

    # Create state directories
    state_dir = review_output / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    sprints_dir = state_dir / "sprints"
    sprints_dir.mkdir(exist_ok=True)
    (review_output / "logs").mkdir(exist_ok=True)

    click.echo(f"AgentForge Code Review")
    click.echo(f"Project: {project_name}")
    click.echo(f"Source: {src_dir}")
    click.echo(f"Profile: {profile}")
    click.echo(f"Output: {review_output}")
    click.echo()

    # Detect tech stack by scanning files
    has_frontend = any(src_dir.rglob("*.vue")) or any(src_dir.rglob("*.tsx")) or any(src_dir.rglob("*.jsx"))
    has_python = any(src_dir.rglob("*.py"))
    has_java = any(src_dir.rglob("*.java"))
    has_js = any(src_dir.rglob("*.js"))

    click.echo(f"Detected:")
    if has_frontend:
        click.echo(f"  Frontend: Vue/React")
    if has_python:
        click.echo(f"  Backend: Python")
    if has_java:
        click.echo(f"  Backend: Java")
    if has_js and not has_frontend:
        click.echo(f"  JavaScript")
    click.echo()

    from agentforge.core.cli_executor import CLIExecutor
    executor = CLIExecutor()

    review_count = 0

    # Run backend reviewer
    if has_python or has_java:
        click.echo("Running backend code review...")
        agent_config = config.get_agent_config("reviewers.api_reviewer")
        result = executor.run_agent(
            prompt=f"Review all backend code in this project directory. Check architecture, security, code quality. Output your review as JSON with fields: passed, score, dimensions, issues, suggestions.",
            workspace=str(src_dir),
            model=agent_config.model,
            allowed_tools=agent_config.allowed_tools,
            max_turns=agent_config.max_turns,
            timeout_minutes=agent_config.timeout_minutes,
        )
        # Save as sprint review
        review_data = {
            "sprint_id": "REVIEW_BACKEND",
            "passed": result.is_success,
            "score": 3.5,
            "dimensions": {"architecture": {"score": 3, "notes": ""}, "security": {"score": 3, "notes": ""}, "code_quality": {"score": 3, "notes": ""}},
            "issues": [],
            "raw_output": result.output,
        }
        # Try to parse structured output from agent
        try:
            parsed = json.loads(result.output)
            if isinstance(parsed, dict):
                review_data.update({k: v for k, v in parsed.items() if k in ("passed", "score", "dimensions", "issues", "suggestions")})
        except (json.JSONDecodeError, TypeError):
            pass

        (sprints_dir / "REVIEW_BACKEND_review.json").write_text(
            json.dumps(review_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        review_count += 1
        click.echo(f"  Backend review: score={review_data.get('score', 'N/A')}")

    # Run frontend reviewer
    if has_frontend or (has_js and not has_python and not has_java):
        click.echo("Running frontend code review...")
        agent_config = config.get_agent_config("reviewers.ui_reviewer")
        result = executor.run_agent(
            prompt=f"Review all frontend code in this project directory. Check component quality, best practices, UI quality. Output your review as JSON with fields: passed, score, dimensions, issues, suggestions.",
            workspace=str(src_dir),
            model=agent_config.model,
            allowed_tools=agent_config.allowed_tools,
            max_turns=agent_config.max_turns,
            timeout_minutes=agent_config.timeout_minutes,
        )
        review_data = {
            "sprint_id": "REVIEW_FRONTEND",
            "passed": result.is_success,
            "score": 3.5,
            "dimensions": {"completeness": {"score": 3, "notes": ""}, "ui_quality": {"score": 3, "notes": ""}, "code_quality": {"score": 3, "notes": ""}},
            "issues": [],
            "raw_output": result.output,
        }
        try:
            parsed = json.loads(result.output)
            if isinstance(parsed, dict):
                review_data.update({k: v for k, v in parsed.items() if k in ("passed", "score", "dimensions", "issues", "suggestions")})
        except (json.JSONDecodeError, TypeError):
            pass

        (sprints_dir / "REVIEW_FRONTEND_review.json").write_text(
            json.dumps(review_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        review_count += 1
        click.echo(f"  Frontend review: score={review_data.get('score', 'N/A')}")

    # Run overall evaluator
    click.echo("Running overall QA assessment...")
    agent_config = config.get_agent_config("evaluator")
    result = executor.run_agent(
        prompt=f"Review this entire project for overall quality. Assess functionality, design quality, code quality, and product depth. Output as JSON with fields: passed, overall_score, dimensions, bugs, improvement_suggestions.",
        workspace=str(src_dir),
        model=agent_config.model,
        allowed_tools=agent_config.allowed_tools,
        max_turns=agent_config.max_turns,
        timeout_minutes=agent_config.timeout_minutes,
    )
    qa_data = {
        "passed": result.is_success,
        "overall_score": 3.5,
        "dimensions": {},
        "bugs": [],
        "improvement_suggestions": [],
        "raw_output": result.output,
    }
    try:
        parsed = json.loads(result.output)
        if isinstance(parsed, dict):
            qa_data.update({k: v for k, v in parsed.items() if k in ("passed", "overall_score", "dimensions", "bugs", "improvement_suggestions")})
    except (json.JSONDecodeError, TypeError):
        pass

    (state_dir / "final_qa.json").write_text(
        json.dumps(qa_data, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    click.echo(f"  Overall QA: score={qa_data.get('overall_score', 'N/A')}")

    # Auto-extract experience
    click.echo()
    click.echo("Extracting experience...")
    from agentforge.learning.extractor import Extractor
    from agentforge.learning.knowledge_base import KnowledgeBase, Pattern, AntiPattern
    extractor = Extractor()
    extracted = extractor.extract(state_dir, profile=profile)
    patterns = extracted.get("patterns", [])
    antipatterns = extracted.get("antipatterns", [])

    kdir = Path("knowledge")
    kb = KnowledgeBase(kdir)
    for p in patterns:
        kb.add_pattern(Pattern.model_validate(p))
    for ap in antipatterns:
        kb.add_antipattern(AntiPattern.model_validate(ap))

    click.echo(f"  Patterns extracted: {len(patterns)}")
    click.echo(f"  Anti-patterns extracted: {len(antipatterns)}")
    click.echo()
    click.echo(f"Review complete!")
    click.echo(f"  Review data: {state_dir}")
    click.echo(f"  Knowledge base: {kdir}")
    click.echo(f"  Run 'agentforge learn' to see accumulated knowledge")


@main.command()
@click.option("--project", required=True, help="Project name to resume")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("--config-dir", default=None, type=click.Path(), help="Config directory (default: auto-detect)")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def resume(project, output_dir, config_dir, verbose):
    """Resume a paused or failed run from checkpoint."""
    setup_logging(verbose)
    project_output = Path(output_dir) / project
    state_dir = project_output / "state"
    cp_mgr = CheckpointManager(state_dir)
    cp = cp_mgr.load()
    if cp is None:
        click.echo(f"No checkpoint found for project: {project}")
        sys.exit(1)
    click.echo(f"Resuming project: {project}")
    click.echo(f"State: {cp.status.value}")
    click.echo(f"Completed sprints: {cp.completed_sprints}")
    config = load_config(resolve_config_dir(config_dir))
    config.project_name = cp.project_name
    config.profile = cp.profile
    orch = Orchestrator(config=config, output_dir=project_output, prd_path="")
    orch.run()


@main.command()
@click.option("--project", required=True, help="Project name")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
def status(project, output_dir):
    """View the current status of a project run."""
    state_dir = Path(output_dir) / project / "state"
    cp_mgr = CheckpointManager(state_dir)
    cp = cp_mgr.load()
    if cp is None:
        click.echo(f"No run found for project: {project}")
        return
    click.echo(f"Project: {cp.project_name}")
    click.echo(f"Profile: {cp.profile}")
    click.echo(f"Status: {cp.status.value}")
    click.echo(f"Current sprint: {cp.current_sprint or 'N/A'}")
    click.echo(f"Completed: {cp.completed_sprints}")
    click.echo(f"Failed attempts: {cp.failed_attempts}")
    if cp.error:
        click.echo(f"Last error: {cp.error}")
    click.echo(f"Last updated: {cp.timestamp}")


@main.command()
@click.option("--project", required=True, help="Project name")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
def cost(project, output_dir):
    """View cost report for a project."""
    state_dir = Path(output_dir) / project / "state"
    tracker = CostTracker(state_dir)
    data = tracker.get_summary()
    click.echo(f"Cost Report: {project}")
    click.echo(f"{'='*40}")
    click.echo(f"Total cost: ${data['total_cost']:.2f}")
    click.echo(f"Total tokens: prompt={data['total_tokens']['prompt']}, completion={data['total_tokens']['completion']}")
    click.echo()
    if data["by_agent"]:
        click.echo("By Agent:")
        for agent, info in data["by_agent"].items():
            click.echo(f"  {agent}: ${info['cost']:.2f} ({info['calls']} calls)")
    if data["by_sprint"]:
        click.echo()
        click.echo("By Sprint:")
        for sprint, info in data["by_sprint"].items():
            click.echo(f"  {sprint}: ${info['cost']:.2f}")


@main.command()
@click.option("--details", is_flag=True, help="Show profile details")
def profiles(details):
    """List available service profiles."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        click.echo("No profiles directory found.")
        return
    click.echo("Available profiles:")
    for f in sorted(profiles_dir.glob("*.yaml")):
        name = f.stem
        if details:
            try:
                profile = load_profile(name, profiles_dir)
                click.echo(f"\n  {name}: {profile.description}")
                click.echo(f"    Generators: {', '.join(profile.generators)}")
                click.echo(f"    Reviewers:  {', '.join(profile.reviewers)}")
                click.echo(f"    Templates:  {', '.join(profile.templates)}")
                click.echo(f"    Sprint types: {', '.join(profile.sprint_types)}")
            except Exception:
                click.echo(f"  - {name} (error loading)")
        else:
            click.echo(f"  - {name}")


@main.command()
@click.option("--analyze", is_flag=True, help="Run cross-project trend analysis")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def learn(analyze, knowledge_dir):
    """View or analyze learned knowledge from past runs."""
    kdir = Path(knowledge_dir)
    if not kdir.exists():
        click.echo("No knowledge directory found. Run projects first to build knowledge.")
        return

    kb = KnowledgeBase(kdir)
    patterns = kb.get_patterns()
    antipatterns = kb.get_antipatterns()
    pending = kb.get_pending()
    pending_count = len(pending["patterns"]) + len(pending["antipatterns"])

    click.echo(f"Knowledge Base Summary")
    click.echo(f"{'='*40}")
    click.echo(f"Approved patterns: {len(patterns)}")
    click.echo(f"Approved anti-patterns: {len(antipatterns)}")
    if pending_count > 0:
        click.echo(f"Pending approval: {pending_count}")

    if analyze:
        click.echo()
        analyzer = Analyzer(kdir)
        click.echo(analyzer.format_report())


@main.command("extract")
@click.option("--state-dir", required=True, type=click.Path(exists=True), help="Path to project state/ directory")
@click.option("--profile", default="web-app", help="Profile name to tag extracted knowledge")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def extract(state_dir, profile, knowledge_dir):
    """Extract learning from an existing project's state directory.

    Use this to import experience from projects that were NOT run by AgentForge,
    or from old AgentForge runs.

    The state directory must contain:
      - sprints/*_review.json (sprint review results)
      - final_qa.json (optional, global QA results)
      - plan.json (optional, for sprint type mapping)

    Example:
      agentforge extract --state-dir output/old-project/state --profile web-app
    """
    kdir = Path(knowledge_dir)
    sdir = Path(state_dir)

    # Check for required files
    sprints_dir = sdir / "sprints"
    review_files = list(sprints_dir.glob("*_review.json")) if sprints_dir.exists() else []
    qa_file = sdir / "final_qa.json"

    if not review_files and not qa_file.exists():
        click.echo("No review or QA files found. Expected:")
        click.echo(f"  {sprints_dir}/*_review.json")
        click.echo(f"  {sdir}/final_qa.json")
        click.echo()
        click.echo("See 'agentforge extract --help' for required file format.")
        return

    click.echo(f"Extracting from: {sdir}")
    click.echo(f"  Sprint reviews: {len(review_files)}")
    click.echo(f"  Final QA: {'found' if qa_file.exists() else 'not found'}")
    click.echo(f"  Profile: {profile}")
    click.echo()

    # Extract
    extractor = Extractor()
    result = extractor.extract(sdir, profile=profile)

    patterns = result.get("patterns", [])
    antipatterns = result.get("antipatterns", [])

    click.echo(f"Extracted: {len(patterns)} patterns, {len(antipatterns)} anti-patterns")

    if not patterns and not antipatterns:
        click.echo("Nothing to save.")
        return

    # Save to knowledge base
    kb = KnowledgeBase(kdir)
    for p_data in patterns:
        kb.add_pattern(Pattern.model_validate(p_data))
    for ap_data in antipatterns:
        kb.add_antipattern(AntiPattern.model_validate(ap_data))

    click.echo(f"Saved to: {kdir}")
    click.echo()
    click.echo("Knowledge base updated:")
    click.echo(f"  Total patterns: {len(kb.get_patterns())}")
    click.echo(f"  Total anti-patterns: {len(kb.get_antipatterns())}")


@main.command("add-pattern")
@click.argument("text")
@click.option("--agent", default="", help="Agent name (ui, api, scheduler...)")
@click.option("--profile", default="web-app", help="Profile name")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def add_pattern(text, agent, profile, knowledge_dir):
    """Add a successful pattern to the knowledge base.

    Examples:
      agentforge add-pattern "Vue 表单使用 v-model + computed setter" --agent ui
      agentforge add-pattern "API 统一返回 {code, data, message} 格式" --agent api
      agentforge add-pattern "使用 Pinia 管理认证状态" --agent ui --profile web-app
    """
    kb = KnowledgeBase(Path(knowledge_dir))
    kb.add_pattern(Pattern(pattern=text, agent=agent, profile=profile, frequency=1))
    click.echo(f"Pattern added: {text}")
    click.echo(f"  Agent: {agent or '(all)'}, Profile: {profile}")


@main.command("add-antipattern")
@click.argument("text")
@click.option("--fix", default="", help="Recommended fix")
@click.option("--agent", default="", help="Agent name (ui, api, scheduler...)")
@click.option("--profile", default="web-app", help="Profile name")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def add_antipattern(text, fix, agent, profile, knowledge_dir):
    """Add an anti-pattern (common mistake) to the knowledge base.

    Examples:
      agentforge add-antipattern "Controller 中直接写业务逻辑" --fix "使用 Service 层" --agent api
      agentforge add-antipattern "前端硬编码 API 地址" --fix "使用环境变量" --agent ui
      agentforge add-antipattern "不处理分页空数据状态" --fix "始终处理空状态展示" --agent ui
    """
    kb = KnowledgeBase(Path(knowledge_dir))
    kb.add_antipattern(AntiPattern(antipattern=text, fix=fix, agent=agent, profile=profile, frequency=1))
    click.echo(f"Anti-pattern added: {text}")
    if fix:
        click.echo(f"  Fix: {fix}")
    click.echo(f"  Agent: {agent or '(all)'}, Profile: {profile}")


@main.command("import-rules")
@click.argument("file", type=click.Path(exists=True))
@click.option("--profile", default="web-app", help="Profile name")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def import_rules(file, profile, knowledge_dir):
    """Batch import patterns and anti-patterns from a YAML/JSON file.

    File format (YAML):

      patterns:
        - pattern: "使用 Pinia 管理状态"
          agent: ui
        - pattern: "API 统一返回格式"
          agent: api

      antipatterns:
        - antipattern: "Controller 里写业务逻辑"
          fix: "使用 Service 层"
          agent: api
        - antipattern: "不处理空数据状态"
          fix: "始终处理空状态展示"
          agent: ui

    Example:
      agentforge import-rules team-rules.yaml --profile web-app
    """
    import yaml as _yaml

    file_path = Path(file)
    content = file_path.read_text(encoding="utf-8")

    if file_path.suffix in (".yaml", ".yml"):
        data = _yaml.safe_load(content) or {}
    elif file_path.suffix == ".json":
        data = json.loads(content)
    else:
        click.echo(f"Unsupported file format: {file_path.suffix} (use .yaml or .json)")
        return

    kb = KnowledgeBase(Path(knowledge_dir))
    p_count = 0
    ap_count = 0

    for p in data.get("patterns", []):
        kb.add_pattern(Pattern(
            pattern=p.get("pattern", ""),
            agent=p.get("agent", ""),
            profile=profile,
            frequency=p.get("frequency", 1),
        ))
        p_count += 1

    for ap in data.get("antipatterns", []):
        kb.add_antipattern(AntiPattern(
            antipattern=ap.get("antipattern", ""),
            fix=ap.get("fix", ""),
            agent=ap.get("agent", ""),
            profile=profile,
            frequency=ap.get("frequency", 1),
        ))
        ap_count += 1

    click.echo(f"Imported from {file_path.name}:")
    click.echo(f"  Patterns: {p_count}")
    click.echo(f"  Anti-patterns: {ap_count}")
    click.echo(f"  Profile: {profile}")


@main.command("pending")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def pending(knowledge_dir):
    """List all pending knowledge items awaiting approval."""
    kdir = Path(knowledge_dir)
    if not kdir.exists():
        click.echo("No knowledge directory found.")
        return

    kb = KnowledgeBase(kdir)
    items = kb.get_pending()

    p_list = items["patterns"]
    ap_list = items["antipatterns"]

    if not p_list and not ap_list:
        click.echo("No pending items.")
        return

    if p_list:
        click.echo(f"Pending patterns ({len(p_list)}):")
        for i, p in enumerate(p_list, 1):
            click.echo(f"  {i}. [{p.agent}] {p.pattern}")
            if p.submitted_by:
                click.echo(f"     submitted by: {p.submitted_by}, project: {p.source_project}")

    if ap_list:
        click.echo(f"\nPending anti-patterns ({len(ap_list)}):")
        for i, ap in enumerate(ap_list, 1):
            click.echo(f"  {i}. [{ap.agent}] {ap.antipattern}")
            if ap.fix:
                click.echo(f"     fix: {ap.fix}")
            if ap.submitted_by:
                click.echo(f"     submitted by: {ap.submitted_by}, project: {ap.source_project}")

    click.echo(f"\nUse 'agentforge approve \"<text>\"' or 'agentforge reject \"<text>\"' to review.")


@main.command("approve")
@click.argument("text")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def approve_cmd(text, knowledge_dir):
    """Approve a pending knowledge item by its text."""
    kb = KnowledgeBase(Path(knowledge_dir))
    if kb.approve(text):
        click.echo(f"Approved: {text}")
    else:
        click.echo(f"Not found or not pending: {text}")


@main.command("reject")
@click.argument("text")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def reject_cmd(text, knowledge_dir):
    """Reject a pending knowledge item by its text."""
    kb = KnowledgeBase(Path(knowledge_dir))
    if kb.reject(text):
        click.echo(f"Rejected: {text}")
    else:
        click.echo(f"Not found or not pending: {text}")


@main.command("approve-all")
@click.option("--knowledge-dir", default="knowledge", type=click.Path(), help="Knowledge directory")
def approve_all_cmd(knowledge_dir):
    """Approve all pending knowledge items."""
    kb = KnowledgeBase(Path(knowledge_dir))
    items = kb.get_pending()
    count = 0
    for p in items["patterns"]:
        kb.approve(p.pattern)
        count += 1
    for ap in items["antipatterns"]:
        kb.approve(ap.antipattern)
        count += 1

    if count:
        click.echo(f"Approved {count} items.")
    else:
        click.echo("No pending items.")


if __name__ == "__main__":
    main()
