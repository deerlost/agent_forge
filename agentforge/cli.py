import json
import logging
import sys
from pathlib import Path

import click

from agentforge.core.config import load_config
from agentforge.core.checkpoint import CheckpointManager
from agentforge.core.cost_tracker import CostTracker
from agentforge.core.orchestrator import Orchestrator


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
@click.option("--config-dir", default="config", type=click.Path(), help="Config directory")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("-v", "--verbose", is_flag=True, help="Verbose logging")
def run(prd, profile, backend, auto, config_dir, output_dir, verbose):
    """Generate an application from a PRD document."""
    setup_logging(verbose)
    config_path = Path(config_dir)
    project_yaml = Path("agentforge.yaml")
    project_config_path = project_yaml if project_yaml.exists() else None
    config = load_config(config_path, project_config_path=project_config_path)
    config.profile = profile
    if not config.project_name:
        config.project_name = Path(prd).stem
    project_output = Path(output_dir) / config.project_name
    click.echo(f"AgentForge v0.1.0")
    click.echo(f"Project: {config.project_name}")
    click.echo(f"Profile: {profile}")
    click.echo(f"PRD: {prd}")
    click.echo(f"Output: {project_output}")
    click.echo()
    orch = Orchestrator(config=config, output_dir=project_output, prd_path=prd, auto_mode=auto)
    orch.run()


@main.command()
@click.option("--project", required=True, help="Project name to resume")
@click.option("--output-dir", default="output", type=click.Path(), help="Output directory")
@click.option("--config-dir", default="config", type=click.Path(), help="Config directory")
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
    config = load_config(Path(config_dir))
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
def profiles():
    """List available service profiles."""
    profiles_dir = Path("profiles")
    if not profiles_dir.exists():
        click.echo("No profiles directory found.")
        return
    click.echo("Available profiles:")
    for f in sorted(profiles_dir.glob("*.yaml")):
        click.echo(f"  - {f.stem}")


if __name__ == "__main__":
    main()
