import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from agentforge.cli import main


class TestCLI:
    def test_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "AgentForge" in result.output

    def test_run_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run", "--help"])
        assert result.exit_code == 0
        assert "--prd" in result.output
        assert "--profile" in result.output

    def test_run_missing_prd(self):
        runner = CliRunner()
        result = runner.invoke(main, ["run"])
        assert result.exit_code != 0

    def test_resume_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["resume", "--help"])
        assert result.exit_code == 0
        assert "--project" in result.output

    def test_status_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["status", "--help"])
        assert result.exit_code == 0

    def test_cost_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["cost", "--help"])
        assert result.exit_code == 0

    def test_profiles_list_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["profiles", "--help"])
        assert result.exit_code == 0
