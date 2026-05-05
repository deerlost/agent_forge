"""Frontend quality checkers (ESLint, TypeScript, Prettier)."""

import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

from agentforge.checks.base import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class ESLintChecker(BaseChecker):
    """Run ESLint on TypeScript and Vue files."""

    def __init__(self, config: dict):
        super().__init__("eslint", config)
        self.timeout = config.get("timeout", 60)

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = ["npx", "eslint", ".", "--ext", ".ts,.vue", "--format", "json"]

        try:
            result = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            duration = time.time() - start_time

            # ESLint returns exit code 1 when there are linting errors
            # Exit code 0 means no errors, exit code 2 means fatal error
            if result.returncode == 2:
                return CheckResult(
                    checker=self.name,
                    passed=False,
                    errors=[f"ESLint fatal error: {result.stderr}"],
                    raw_output=result.stderr,
                    duration_seconds=duration,
                    exit_code=result.returncode,
                    fix_hint="Check if ESLint is installed: npm install --save-dev eslint",
                )

            errors = []
            warnings = []

            try:
                # Parse JSON output
                if result.stdout.strip():
                    lint_results = json.loads(result.stdout)
                    for file_result in lint_results:
                        file_path = file_result.get("filePath", "")
                        messages = file_result.get("messages", [])
                        for msg in messages:
                            severity = msg.get("severity", 1)
                            line = msg.get("line", 0)
                            col = msg.get("column", 0)
                            rule = msg.get("ruleId", "")
                            message = msg.get("message", "")

                            error_text = f"{file_path}:{line}:{col} - {message} ({rule})"

                            if severity == 2:  # Error
                                errors.append(error_text)
                            elif severity == 1:  # Warning
                                warnings.append(error_text)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse ESLint JSON output")
                if result.stdout:
                    errors.append(f"ESLint output parsing failed: {result.stdout[:200]}")

            passed = len(errors) == 0 and result.returncode == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Run 'npx eslint . --ext .ts,.vue --fix' to auto-fix some issues"

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"ESLint timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
                fix_hint="Consider reducing the scope or increasing timeout",
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["ESLint not found. Install with: npm install --save-dev eslint"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="npm install --save-dev eslint @typescript-eslint/parser @typescript-eslint/eslint-plugin",
            )


class TypeScriptChecker(BaseChecker):
    """Run vue-tsc type checking."""

    def __init__(self, config: dict):
        super().__init__("tsc", config)
        self.timeout = config.get("timeout", 60)

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = ["npx", "vue-tsc", "--noEmit"]

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
                # Parse tsc text output: file(line,col): error TSxxxx: message
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    if ": error TS" in line:
                        errors.append(line)
                    elif ": warning " in line:
                        warnings.append(line)

                # If no structured errors found, capture raw output
                if not errors and result.stdout.strip():
                    errors.append(result.stdout.strip()[:500])
                if not errors and result.stderr.strip():
                    errors.append(result.stderr.strip()[:500])

            passed = result.returncode == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Fix TypeScript type errors in the reported files"

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
                errors=[f"TypeScript check timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["vue-tsc not found. Install with: npm install --save-dev vue-tsc"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="npm install --save-dev vue-tsc typescript",
            )


class PrettierChecker(BaseChecker):
    """Run Prettier format check."""

    def __init__(self, config: dict):
        super().__init__("prettier", config)
        self.timeout = config.get("timeout", 60)
        self.glob_pattern = config.get("glob", "src/**/*.{ts,vue}")

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = ["npx", "prettier", "--check", self.glob_pattern]

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
            if result.returncode != 0:
                # Prettier lists unformatted files on stdout
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line and not line.startswith("Checking"):
                        errors.append(f"Not formatted: {line}")

                if not errors and result.stderr.strip():
                    errors.append(result.stderr.strip()[:500])

            passed = result.returncode == 0
            fix_hint = ""
            if not passed:
                fix_hint = f"Run 'npx prettier --write \"{self.glob_pattern}\"' to auto-format"

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                raw_output=result.stdout + result.stderr,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"Prettier check timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["Prettier not found. Install with: npm install --save-dev prettier"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="npm install --save-dev prettier",
            )
