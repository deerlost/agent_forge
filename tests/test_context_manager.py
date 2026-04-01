import json
import pytest
from agentforge.core.context_manager import ContextManager


class TestContextManager:
    def test_build_first_handoff(self, tmp_project, sample_plan):
        mgr = ContextManager(tmp_project / "state")
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S001", completed_sprints=[], file_manifest=[], key_decisions=[], known_issues=[])
        assert handoff["tech_stack"] == sample_plan["tech_stack"]
        assert handoff["current_sprint"]["id"] == "S001"
        assert handoff["recent_sprints"] == []
        assert handoff["file_manifest"] == []

    def test_build_handoff_with_history(self, tmp_project, sample_plan):
        mgr = ContextManager(tmp_project / "state")
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S002", completed_sprints=["S001"], file_manifest=[{"path": "src/auth.py", "sprint": "S001", "summary": "Auth module"}], key_decisions=["Use JWT for auth"], known_issues=[])
        assert handoff["current_sprint"]["id"] == "S002"
        assert len(handoff["file_manifest"]) == 1
        assert handoff["key_decisions"] == ["Use JWT for auth"]

    def test_recent_sprints_rolling_window(self, tmp_project, sample_plan):
        for i in range(3, 6):
            sample_plan["sprints"].append({"id": f"S00{i}", "name": f"Sprint {i}", "type": "backend", "features": [], "depends_on": [], "contract": {"done_criteria": [], "test_scenarios": []}})
        mgr = ContextManager(tmp_project / "state", recent_window=3)
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S005", completed_sprints=["S001", "S002", "S003", "S004"], file_manifest=[], key_decisions=[], known_issues=[])
        assert len(handoff["recent_sprints"]) == 3
        recent_ids = [s["id"] for s in handoff["recent_sprints"]]
        assert recent_ids == ["S002", "S003", "S004"]

    def test_file_manifest_limit(self, tmp_project, sample_plan):
        mgr = ContextManager(tmp_project / "state", max_files=3)
        files = [{"path": f"src/file{i}.py", "sprint": "S001", "summary": f"File {i}"} for i in range(10)]
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S001", completed_sprints=[], file_manifest=files, key_decisions=[], known_issues=[])
        assert len(handoff["file_manifest"]) == 3

    def test_save_and_load_handoff(self, tmp_project, sample_plan):
        mgr = ContextManager(tmp_project / "state")
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S001", completed_sprints=[], file_manifest=[], key_decisions=[], known_issues=[])
        mgr.save_handoff("S001", handoff)
        loaded = mgr.load_handoff("S001")
        assert loaded is not None
        assert loaded["current_sprint"]["id"] == "S001"

    def test_load_nonexistent_handoff(self, tmp_project):
        mgr = ContextManager(tmp_project / "state")
        assert mgr.load_handoff("S999") is None

    def test_format_as_prompt(self, tmp_project, sample_plan):
        mgr = ContextManager(tmp_project / "state")
        handoff = mgr.build_handoff(plan=sample_plan, current_sprint_id="S001", completed_sprints=[], file_manifest=[], key_decisions=[], known_issues=[])
        prompt = mgr.format_as_prompt(handoff)
        assert "Handoff" in prompt
        assert "S001" in prompt
        assert "```json" in prompt
