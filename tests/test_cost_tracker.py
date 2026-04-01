import json
import pytest
from agentforge.core.cost_tracker import CostTracker, CostLimitExceeded
from agentforge.models.agent import AgentResult

class TestCostTracker:
    def test_record_cost(self, tmp_project):
        tracker = CostTracker(tmp_project / "state", max_cost=200, warn_threshold=150)
        result = AgentResult(output="ok", token_usage={"prompt": 1000, "completion": 500}, cost=3.50, exit_code=0)
        tracker.record("analyst", result, sprint_id=None)
        data = tracker.get_summary()
        assert data["total_cost"] == 3.50
        assert data["by_agent"]["analyst"]["cost"] == 3.50
        assert data["by_agent"]["analyst"]["calls"] == 1

    def test_record_multiple_agents(self, tmp_project):
        tracker = CostTracker(tmp_project / "state", max_cost=200, warn_threshold=150)
        tracker.record("analyst", AgentResult(output="ok", cost=3.0, exit_code=0))
        tracker.record("planner", AgentResult(output="ok", cost=5.0, exit_code=0))
        tracker.record("analyst", AgentResult(output="ok", cost=2.0, exit_code=0))
        data = tracker.get_summary()
        assert data["total_cost"] == 10.0
        assert data["by_agent"]["analyst"]["cost"] == 5.0
        assert data["by_agent"]["analyst"]["calls"] == 2
        assert data["by_agent"]["planner"]["calls"] == 1

    def test_record_with_sprint(self, tmp_project):
        tracker = CostTracker(tmp_project / "state", max_cost=200, warn_threshold=150)
        tracker.record("ui_generator", AgentResult(output="ok", cost=10.0, exit_code=0), sprint_id="S001")
        data = tracker.get_summary()
        assert data["by_sprint"]["S001"]["cost"] == 10.0

    def test_cost_limit_exceeded(self, tmp_project):
        tracker = CostTracker(tmp_project / "state", max_cost=10, warn_threshold=8)
        tracker.record("agent", AgentResult(output="ok", cost=11.0, exit_code=0))
        with pytest.raises(CostLimitExceeded):
            tracker.check_limit()

    def test_persistence(self, tmp_project):
        tracker1 = CostTracker(tmp_project / "state", max_cost=200, warn_threshold=150)
        tracker1.record("analyst", AgentResult(output="ok", cost=5.0, exit_code=0))
        tracker2 = CostTracker(tmp_project / "state", max_cost=200, warn_threshold=150)
        data = tracker2.get_summary()
        assert data["total_cost"] == 5.0
