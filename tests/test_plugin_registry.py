import pytest
from pathlib import Path
from agentforge.core.plugin_registry import PluginRegistry

@pytest.fixture
def agents_dir(tmp_path):
    (tmp_path / "analyst" / "prompts").mkdir(parents=True)
    (tmp_path / "analyst" / "prompts" / "system.md").write_text("# Analyst")
    (tmp_path / "planner" / "prompts").mkdir(parents=True)
    (tmp_path / "planner" / "prompts" / "system.md").write_text("# Planner")
    (tmp_path / "generators" / "ui" / "prompts").mkdir(parents=True)
    (tmp_path / "generators" / "ui" / "prompts" / "vue_system.md").write_text("# UI Gen")
    (tmp_path / "generators" / "api" / "prompts").mkdir(parents=True)
    (tmp_path / "generators" / "api" / "prompts" / "fastapi_system.md").write_text("# API Gen")
    (tmp_path / "reviewers" / "ui_reviewer" / "prompts").mkdir(parents=True)
    (tmp_path / "reviewers" / "ui_reviewer" / "prompts" / "review_criteria.md").write_text("# UI Review")
    (tmp_path / "reviewers" / "api_reviewer" / "prompts").mkdir(parents=True)
    (tmp_path / "reviewers" / "api_reviewer" / "prompts" / "review_criteria.md").write_text("# API Review")
    (tmp_path / "evaluator" / "prompts").mkdir(parents=True)
    (tmp_path / "evaluator" / "prompts" / "global_qa.md").write_text("# Evaluator")
    return tmp_path

class TestPluginRegistry:
    def test_discover_all(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        assert "analyst" in registry.agents
        assert "planner" in registry.agents
        assert "ui" in registry.generators
        assert "api" in registry.generators
        assert "ui_reviewer" in registry.reviewers
        assert "api_reviewer" in registry.reviewers
        assert "evaluator" in registry.agents

    def test_get_prompt_path(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        path = registry.get_prompt_path("generators", "ui")
        assert path is not None
        assert path.exists()
        assert "vue_system" in path.name

    def test_get_prompt_path_missing(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        path = registry.get_prompt_path("generators", "go_api")
        assert path is None

    def test_validate_profile(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        # Use a simple mock object with generators and reviewers attributes
        class MockProfile:
            generators = ["ui", "api"]
            reviewers = ["ui_reviewer", "api_reviewer"]
        errors = registry.validate_profile(MockProfile())
        assert len(errors) == 0

    def test_validate_profile_missing_generator(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        class MockProfile:
            generators = ["ui", "go_api"]
            reviewers = ["ui_reviewer"]
        errors = registry.validate_profile(MockProfile())
        assert len(errors) > 0
        assert "go_api" in errors[0]

    def test_list_available(self, agents_dir):
        registry = PluginRegistry(agents_dir)
        registry.discover()
        available = registry.list_available()
        assert "generators" in available
        assert "ui" in available["generators"]
        assert "reviewers" in available
