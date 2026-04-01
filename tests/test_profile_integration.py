"""Integration test: verify profile loading and template copying in orchestrator."""
import json
import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock

from agentforge.core.config import (
    AppConfig, OrchestratorConfig, HumanCheckpointsConfig,
    RequirementReviewConfig, TimeoutsConfig, CostConfig,
)
from agentforge.core.orchestrator import Orchestrator
from agentforge.models.state import OrchestratorState


@pytest.fixture
def full_project(tmp_path):
    """Create a project with profiles, templates, and agents directories."""
    # Profile
    profiles_dir = tmp_path / "profiles"
    profiles_dir.mkdir()
    (profiles_dir / "web-app.yaml").write_text(yaml.dump({
        "name": "web-app",
        "description": "Full-stack web app",
        "generators": ["ui", "api"],
        "reviewers": ["ui_reviewer", "api_reviewer"],
        "evaluator_strategies": ["api_test"],
        "templates": ["vue3", "fastapi"],
        "sprint_types": ["frontend", "backend", "fullstack"],
    }))

    # Templates
    vue_dir = tmp_path / "templates" / "ui" / "vue3"
    vue_dir.mkdir(parents=True)
    (vue_dir / "package.json").write_text('{"name": "frontend"}')
    vue_src = vue_dir / "src"
    vue_src.mkdir()
    (vue_src / "main.ts").write_text("import vue")

    api_dir = tmp_path / "templates" / "api" / "fastapi"
    api_dir.mkdir(parents=True)
    (api_dir / "pyproject.toml").write_text('[project]\nname = "backend"')
    app_dir = api_dir / "app"
    app_dir.mkdir()
    (app_dir / "main.py").write_text("from fastapi import FastAPI")

    # Output dir
    output_dir = tmp_path / "output" / "test"
    return tmp_path, output_dir


@pytest.fixture
def integration_config():
    config = AppConfig(
        project_name="Test",
        profile="web-app",
        orchestrator=OrchestratorConfig(max_sprint_retries=2, max_reviewer_rounds=2),
        human_checkpoints=HumanCheckpointsConfig(
            after_analysis=False, after_planning=False,
            sprint_interval=0, after_final_qa=False,
        ),
        requirement_review=RequirementReviewConfig(enabled=False),
        timeouts=TimeoutsConfig(agent_max_minutes=5),
        cost=CostConfig(max_total_cost=50),
    )
    config._agents_raw = {
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
    }
    return config


class TestProfileIntegration:
    def test_templates_copied_on_init(self, full_project, integration_config):
        base_dir, output_dir = full_project
        orch = Orchestrator(
            config=integration_config,
            output_dir=output_dir,
            prd_path="test.md",
            auto_mode=True,
            profiles_dir=base_dir / "profiles",
            templates_dir=base_dir / "templates",
        )
        assert (output_dir / "workspace" / "frontend" / "package.json").exists()
        assert (output_dir / "workspace" / "frontend" / "src" / "main.ts").exists()
        assert (output_dir / "workspace" / "backend" / "pyproject.toml").exists()
        assert (output_dir / "workspace" / "backend" / "app" / "main.py").exists()

    def test_profile_loaded(self, full_project, integration_config):
        base_dir, output_dir = full_project
        orch = Orchestrator(
            config=integration_config,
            output_dir=output_dir,
            prd_path="test.md",
            profiles_dir=base_dir / "profiles",
            templates_dir=base_dir / "templates",
        )
        assert orch.profile is not None
        assert orch.profile.name == "web-app"
        assert "ui" in orch.profile.generators

    def test_no_profile_dir_still_works(self, full_project, integration_config):
        _, output_dir = full_project
        orch = Orchestrator(
            config=integration_config,
            output_dir=output_dir,
            prd_path="test.md",
        )
        assert orch.profile is None
        assert orch.state == OrchestratorState.INIT

    def test_templates_not_overwritten(self, full_project, integration_config):
        base_dir, output_dir = full_project
        # Pre-create frontend with custom content
        frontend_dir = output_dir / "workspace" / "frontend"
        frontend_dir.mkdir(parents=True)
        (frontend_dir / "package.json").write_text('{"custom": true}')

        orch = Orchestrator(
            config=integration_config,
            output_dir=output_dir,
            prd_path="test.md",
            profiles_dir=base_dir / "profiles",
            templates_dir=base_dir / "templates",
        )
        content = (output_dir / "workspace" / "frontend" / "package.json").read_text()
        assert "custom" in content
