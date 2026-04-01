import json
import pytest
from pathlib import Path
from agentforge.core.checkpoint import CheckpointManager
from agentforge.models.state import OrchestratorState, Checkpoint


class TestCheckpointManager:
    def test_save_and_load(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.SPRINTING,
            current_sprint="S002",
            completed_sprints=["S001"],
        )
        mgr.save(cp)
        loaded = mgr.load()
        assert loaded is not None
        assert loaded.project_name == "Test"
        assert loaded.status == OrchestratorState.SPRINTING
        assert loaded.current_sprint == "S002"
        assert loaded.completed_sprints == ["S001"]

    def test_load_returns_none_when_no_checkpoint(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        assert mgr.load() is None

    def test_exists(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        assert not mgr.exists()
        cp = Checkpoint(project_name="Test", profile="web-app")
        mgr.save(cp)
        assert mgr.exists()

    def test_update_state(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        cp = Checkpoint(project_name="Test", profile="web-app")
        mgr.save(cp)
        mgr.update(status=OrchestratorState.ANALYZING)
        loaded = mgr.load()
        assert loaded.status == OrchestratorState.ANALYZING

    def test_update_sprint_progress(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.SPRINTING,
            current_sprint="S001",
        )
        mgr.save(cp)
        mgr.complete_sprint("S001")
        loaded = mgr.load()
        assert "S001" in loaded.completed_sprints
        assert loaded.current_sprint is None

    def test_record_failure(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state")
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.SPRINTING,
            current_sprint="S001",
        )
        mgr.save(cp)
        mgr.record_failure("API timeout")
        loaded = mgr.load()
        assert loaded.failed_attempts == 1
        assert loaded.error == "API timeout"
        assert loaded.status == OrchestratorState.PAUSED

    def test_record_failure_blocks_after_max(self, tmp_project):
        mgr = CheckpointManager(tmp_project / "state", max_retries=3)
        cp = Checkpoint(
            project_name="Test",
            profile="web-app",
            status=OrchestratorState.SPRINTING,
            current_sprint="S001",
            failed_attempts=2,
        )
        mgr.save(cp)
        mgr.record_failure("third failure")
        loaded = mgr.load()
        assert loaded.failed_attempts == 3
        assert loaded.status == OrchestratorState.BLOCKED
