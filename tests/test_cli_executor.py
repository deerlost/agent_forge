import json
import pytest
from unittest.mock import patch, MagicMock
from agentforge.core.cli_executor import CLIExecutor
from agentforge.models.agent import AgentResult


class TestCLIExecutor:
    def test_build_command_basic(self):
        executor = CLIExecutor()
        cmd = executor._build_command(prompt="Do something", model="opus", allowed_tools=["Read", "Write"], max_turns=20)
        assert "claude" in cmd
        assert "--print" in cmd
        assert "--model" in cmd
        idx = cmd.index("--model")
        assert cmd[idx + 1] == "opus"
        assert "--max-turns" in cmd
        assert "--output-format" in cmd

    def test_build_command_with_system_prompt(self):
        executor = CLIExecutor()
        cmd = executor._build_command(prompt="Do something", model="sonnet", allowed_tools=["Read"], max_turns=10, system_prompt="You are an analyst")
        assert "--system-prompt" in cmd

    def test_build_command_with_append_prompt(self):
        executor = CLIExecutor()
        cmd = executor._build_command(prompt="Do something", model="opus", allowed_tools=[], max_turns=10, append_prompt="Handoff data here")
        assert "--append-system-prompt" in cmd

    def test_build_command_allowed_tools(self):
        executor = CLIExecutor()
        cmd = executor._build_command(prompt="Do something", model="opus", allowed_tools=["Read", "Write", "Bash"], max_turns=10)
        assert "--allowedTools" in cmd
        idx = cmd.index("--allowedTools")
        assert cmd[idx + 1] == "Read,Write,Bash"

    def test_parse_json_output(self):
        executor = CLIExecutor()
        mock_result = MagicMock()
        mock_result.stdout = json.dumps({"result": "Task completed", "usage": {"prompt": 500, "completion": 200}, "cost": 1.23})
        mock_result.returncode = 0
        result = executor._parse_result(mock_result)
        assert isinstance(result, AgentResult)
        assert result.output == "Task completed"
        assert result.cost == 1.23
        assert result.is_success

    def test_parse_non_json_output(self):
        executor = CLIExecutor()
        mock_result = MagicMock()
        mock_result.stdout = "Plain text output from Claude"
        mock_result.returncode = 0
        result = executor._parse_result(mock_result)
        assert result.output == "Plain text output from Claude"
        assert result.is_success

    def test_parse_failed_result(self):
        executor = CLIExecutor()
        mock_result = MagicMock()
        mock_result.stdout = "Error occurred"
        mock_result.returncode = 1
        result = executor._parse_result(mock_result)
        assert not result.is_success
        assert result.exit_code == 1

    @patch("subprocess.run")
    def test_run_agent_calls_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(stdout=json.dumps({"result": "done", "cost": 0.5}), returncode=0)
        executor = CLIExecutor()
        result = executor.run_agent(prompt="Analyze this PRD", workspace="/tmp/test", model="opus", allowed_tools=["Read", "Write"], max_turns=20, timeout_minutes=15)
        mock_run.assert_called_once()
        call_args = mock_run.call_args
        assert call_args.kwargs["cwd"] == "/tmp/test"
        assert call_args.kwargs["timeout"] == 15 * 60
        assert result.is_success

    @patch("subprocess.run")
    def test_run_agent_timeout_handling(self, mock_run):
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="claude", timeout=900)
        executor = CLIExecutor()
        result = executor.run_agent(prompt="Long task", workspace="/tmp/test", model="opus", allowed_tools=[], max_turns=100, timeout_minutes=15)
        assert not result.is_success
        assert result.exit_code == -1
        assert "timeout" in result.output.lower()
