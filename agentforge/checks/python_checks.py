"""Python quality checkers (Ruff, Mypy)."""

import logging
import subprocess
import time
from pathlib import Path

from agentforge.checks.base import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class RuffChecker(BaseChecker):
    """Run Ruff linter on Python code."""

    def __init__(self, config: dict):
        super().__init__("ruff", config)
        self.timeout = config.get("timeout", 60)

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = ["ruff", "check", "."]

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.time() - start_time

            errors = []
            warnings = []

            if result.returncode != 0:
                # Parse ruff output: file:line:col: code message
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    # Ruff format: path/file.py:10:5: E501 Line too long
                    if ":" in line and any(c.isdigit() for c in line):
                        errors.append(line)

                # Capture stderr if no structured errors found
                if not errors and result.stderr.strip():
                    errors.append(result.stderr.strip()[:500])

            passed = result.returncode == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Run 'ruff check . --fix' to auto-fix some issues"

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout + result.stderr,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"Ruff check timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["Ruff not found. Install with: pip install ruff"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="pip install ruff",
            )


class MypyChecker(BaseChecker):
    """Run Mypy type checker on Python code."""

    def __init__(self, config: dict):
        super().__init__("mypy", config)
        self.timeout = config.get("timeout", 60)

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = ["mypy", ".", "--ignore-missing-imports"]

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.time() - start_time

            errors = []
            warnings = []

            if result.returncode != 0:
                # Parse mypy output: file.py:line: error: message
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ": error:" in line:
                        errors.append(line)
                    elif ": warning:" in line or ": note:" in line:
                        warnings.append(line)

                # Capture stderr if no structured errors found
                if not errors and result.stderr.strip():
                    errors.append(result.stderr.strip()[:500])

            passed = result.returncode == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Fix type errors in the reported files. Add type annotations where missing."

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout + result.stderr,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"Mypy check timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["Mypy not found. Install with: pip install mypy"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="pip install mypy",
            )
