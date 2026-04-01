import pytest
import yaml
from pathlib import Path
from agentforge.core.profile import Profile, load_profile, load_profiles_from_string, merge_profiles

@pytest.fixture
def profiles_dir(tmp_path):
    web_app = {"name": "web-app", "description": "Full-stack web application", "generators": ["ui", "api"], "reviewers": ["ui_reviewer", "api_reviewer"], "evaluator_strategies": ["playwright", "api_test"], "templates": ["vue3", "fastapi"], "sprint_types": ["frontend", "backend", "fullstack"]}
    (tmp_path / "web-app.yaml").write_text(yaml.dump(web_app))
    scheduler = {"name": "scheduler", "description": "Scheduling service", "generators": ["scheduler", "api"], "reviewers": ["scheduler_reviewer", "api_reviewer"], "evaluator_strategies": ["api_test", "schedule_test"], "templates": ["celery", "fastapi"], "sprint_types": ["job_definition", "api"]}
    (tmp_path / "scheduler.yaml").write_text(yaml.dump(scheduler))
    return tmp_path

class TestProfile:
    def test_load_single_profile(self, profiles_dir):
        profile = load_profile("web-app", profiles_dir)
        assert profile.name == "web-app"
        assert "ui" in profile.generators
        assert "api" in profile.generators
        assert "vue3" in profile.templates

    def test_load_missing_profile_raises(self, profiles_dir):
        with pytest.raises(FileNotFoundError):
            load_profile("nonexistent", profiles_dir)

    def test_merge_two_profiles(self, profiles_dir):
        p1 = load_profile("web-app", profiles_dir)
        p2 = load_profile("scheduler", profiles_dir)
        merged = merge_profiles([p1, p2])
        assert "ui" in merged.generators
        assert "scheduler" in merged.generators
        assert "api" in merged.generators
        assert merged.generators.count("api") == 1
        assert "ui_reviewer" in merged.reviewers
        assert "scheduler_reviewer" in merged.reviewers
        assert "vue3" in merged.templates
        assert "celery" in merged.templates
        assert merged.templates.count("fastapi") == 1
        assert "frontend" in merged.sprint_types
        assert "job_definition" in merged.sprint_types

    def test_profile_from_comma_string(self, profiles_dir):
        profiles = load_profiles_from_string("web-app,scheduler", profiles_dir)
        assert len(profiles) == 2

    def test_profile_generators_for_sprint_type(self, profiles_dir):
        profile = load_profile("web-app", profiles_dir)
        gens = profile.generators_for_sprint_type("fullstack")
        assert "api" in gens
        assert "ui" in gens
        gens = profile.generators_for_sprint_type("backend")
        assert "api" in gens
        assert "ui" not in gens
        gens = profile.generators_for_sprint_type("frontend")
        assert "ui" in gens
        assert "api" not in gens
