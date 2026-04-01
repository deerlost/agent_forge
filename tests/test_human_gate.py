import pytest
from unittest.mock import patch
from agentforge.core.human_gate import HumanGate, GateType, GateResult
from agentforge.core.config import HumanCheckpointsConfig


class TestHumanGate:
    def test_gate_type_values(self):
        assert GateType.AFTER_ANALYSIS.value == "after_analysis"
        assert GateType.AFTER_PLANNING.value == "after_planning"
        assert GateType.SPRINT_INTERVAL.value == "sprint_interval"
        assert GateType.AFTER_FINAL_QA.value == "after_final_qa"
        assert GateType.AMBIGUITY.value == "ambiguity"

    def test_should_pause_after_analysis(self):
        config = HumanCheckpointsConfig(after_analysis=True)
        gate = HumanGate(config)
        assert gate.should_pause(GateType.AFTER_ANALYSIS)

    def test_should_not_pause_when_disabled(self):
        config = HumanCheckpointsConfig(after_planning=False)
        gate = HumanGate(config)
        assert not gate.should_pause(GateType.AFTER_PLANNING)

    def test_sprint_interval_zero_means_disabled(self):
        config = HumanCheckpointsConfig(sprint_interval=0)
        gate = HumanGate(config)
        assert not gate.should_pause_at_sprint(3)

    def test_sprint_interval_triggers(self):
        config = HumanCheckpointsConfig(sprint_interval=3)
        gate = HumanGate(config)
        assert not gate.should_pause_at_sprint(1)
        assert not gate.should_pause_at_sprint(2)
        assert gate.should_pause_at_sprint(3)
        assert not gate.should_pause_at_sprint(4)
        assert gate.should_pause_at_sprint(6)

    def test_auto_mode_disables_all(self):
        config = HumanCheckpointsConfig(after_analysis=True, after_planning=True, after_final_qa=True)
        gate = HumanGate(config, auto_mode=True)
        assert not gate.should_pause(GateType.AFTER_ANALYSIS)
        assert not gate.should_pause(GateType.AFTER_PLANNING)
        assert not gate.should_pause(GateType.AFTER_FINAL_QA)

    def test_ambiguity_gate_always_pauses_unless_auto(self):
        config = HumanCheckpointsConfig()
        gate = HumanGate(config)
        assert gate.should_pause(GateType.AMBIGUITY)
        gate_auto = HumanGate(config, auto_mode=True)
        assert not gate_auto.should_pause(GateType.AMBIGUITY)

    @patch("builtins.input", return_value="y")
    def test_wait_for_approval_yes(self, mock_input):
        config = HumanCheckpointsConfig()
        gate = HumanGate(config)
        result = gate.wait_for_human(GateType.AFTER_PLANNING, context={"sprint_count": 5})
        assert result.approved

    @patch("builtins.input", return_value="n")
    def test_wait_for_approval_no(self, mock_input):
        config = HumanCheckpointsConfig()
        gate = HumanGate(config)
        result = gate.wait_for_human(GateType.AFTER_PLANNING, context={})
        assert not result.approved

    def test_register_callback(self):
        config = HumanCheckpointsConfig()
        gate = HumanGate(config)
        callback_called = {}
        def my_callback(gate_type, context):
            callback_called["type"] = gate_type
            return True
        gate.register_callback(my_callback)
        result = gate.wait_for_human(GateType.AFTER_PLANNING, context={})
        assert callback_called["type"] == GateType.AFTER_PLANNING
        assert result.approved
