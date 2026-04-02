import json
import pytest
from pathlib import Path
from agentforge.learning.extractor import Extractor

@pytest.fixture
def run_state(tmp_path):
    """Create a simulated run state directory with review/QA results."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    sprints_dir = state_dir / "sprints"
    sprints_dir.mkdir()

    # Sprint S001 review: passed first try (good pattern source)
    (sprints_dir / "S001_review.json").write_text(json.dumps({
        "sprint_id": "S001",
        "passed": True,
        "score": 4.5,
        "dimensions": {"completeness": {"score": 5, "notes": "All criteria met"}, "code_quality": {"score": 4, "notes": "Clean code"}},
        "issues": [],
    }))

    # Sprint S002 review: failed, needed revisions (antipattern source)
    (sprints_dir / "S002_review.json").write_text(json.dumps({
        "sprint_id": "S002",
        "passed": False,
        "score": 2.5,
        "dimensions": {"completeness": {"score": 3, "notes": "Missing validation"}, "architecture": {"score": 2, "notes": "Business logic in controller"}},
        "issues": [
            {"severity": "high", "file": "controller.py", "description": "Business logic in controller instead of service layer"},
            {"severity": "medium", "file": "schema.py", "description": "Missing input validation"},
        ],
    }))

    # Final QA
    (state_dir / "final_qa.json").write_text(json.dumps({
        "passed": True,
        "overall_score": 3.8,
        "bugs": [{"severity": "medium", "description": "Pagination empty on page 2"}],
    }))

    # Plan (to know sprint types)
    (state_dir / "plan.json").write_text(json.dumps({
        "sprints": [
            {"id": "S001", "name": "Auth", "type": "fullstack"},
            {"id": "S002", "name": "Users", "type": "backend"},
        ]
    }))

    return state_dir


class TestExtractor:
    def test_extract_from_run(self, run_state):
        extractor = Extractor()
        result = extractor.extract(run_state, profile="web-app")
        assert len(result["patterns"]) > 0
        assert len(result["antipatterns"]) > 0

    def test_high_score_sprint_generates_pattern(self, run_state):
        extractor = Extractor()
        result = extractor.extract(run_state, profile="web-app")
        patterns = result["patterns"]
        # S001 scored 4.5, should generate a pattern
        assert any("S001" in p.get("context", "") or p.get("score_impact", 0) > 0 for p in patterns)

    def test_failed_review_generates_antipattern(self, run_state):
        extractor = Extractor()
        result = extractor.extract(run_state, profile="web-app")
        antipatterns = result["antipatterns"]
        assert any("controller" in ap.get("antipattern", "").lower() for ap in antipatterns)

    def test_bugs_generate_antipatterns(self, run_state):
        extractor = Extractor()
        result = extractor.extract(run_state, profile="web-app")
        antipatterns = result["antipatterns"]
        assert any("pagination" in ap.get("antipattern", "").lower() or "page" in ap.get("antipattern", "").lower() for ap in antipatterns)

    def test_empty_state_returns_empty(self, tmp_path):
        state_dir = tmp_path / "empty_state"
        state_dir.mkdir()
        (state_dir / "sprints").mkdir()
        extractor = Extractor()
        result = extractor.extract(state_dir, profile="web-app")
        assert result["patterns"] == []
        assert result["antipatterns"] == []
