"""Java quality checkers (Checkstyle, ArchUnit)."""

import logging
import re
import subprocess
import time
from pathlib import Path

from agentforge.checks.base import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class CheckstyleChecker(BaseChecker):
    """Run Maven Checkstyle plugin."""

    def __init__(self, config: dict):
        super().__init__("checkstyle", config)
        self.timeout = config.get("timeout", 120)
        self.command = config.get("command", "mvn checkstyle:check")

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = self.command.split()

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

            # Parse Maven Checkstyle output
            # Format: [ERROR] path/to/File.java:[line,col]: message
            # or: [WARN] path/to/File.java:[line,col]: message
            error_pattern = re.compile(r"\[ERROR\]\s+(.+?\.java):\[(\d+),(\d+)\]:\s+(.+)")
            warn_pattern = re.compile(r"\[WARN\]\s+(.+?\.java):\[(\d+),(\d+)\]:\s+(.+)")

            output_lines = result.stdout.splitlines() + result.stderr.splitlines()
            for line in output_lines:
                error_match = error_pattern.search(line)
                if error_match:
                    file_path, line_num, col, message = error_match.groups()
                    errors.append(f"{file_path}:{line_num}:{col} - {message}")
                    continue

                warn_match = warn_pattern.search(line)
                if warn_match:
                    file_path, line_num, col, message = warn_match.groups()
                    warnings.append(f"{file_path}:{line_num}:{col} - {message}")

            # Check for build failure
            if result.returncode != 0 and not errors:
                # Maven build failed but no specific errors parsed
                if "BUILD FAILURE" in result.stdout or "BUILD FAILURE" in result.stderr:
                    errors.append("Maven Checkstyle build failed - check raw output")

            passed = result.returncode == 0 and len(errors) == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Fix Checkstyle violations in the reported Java files"

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout + "\n" + result.stderr,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"Checkstyle timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
                fix_hint="Consider reducing scope or increasing timeout",
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["Maven not found. Install Maven or check PATH"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="Install Maven: https://maven.apache.org/install.html",
            )


class ArchUnitChecker(BaseChecker):
    """Run ArchUnit architecture tests via Maven."""

    def __init__(self, config: dict):
        super().__init__("archunit", config)
        self.timeout = config.get("timeout", 180)
        self.command = config.get("command", "mvn test -Dtest=ArchitectureTest")

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        cmd = self.command.split()

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

            # Parse Maven test output for ArchUnit violations
            # ArchUnit failures appear as test failures with detailed violation messages
            output_lines = result.stdout.splitlines() + result.stderr.splitlines()

            # Look for test failures
            test_failure_pattern = re.compile(r"Tests run: (\d+), Failures: (\d+), Errors: (\d+)")
            archunit_violation_pattern = re.compile(r"Architecture Violation.*")

            in_failure_section = False
            for line in output_lines:
                # Detect test summary
                test_match = test_failure_pattern.search(line)
                if test_match:
                    _, failures, test_errors = test_match.groups()
                    if int(failures) > 0 or int(test_errors) > 0:
                        in_failure_section = True

                # Capture ArchUnit violation messages
                if "Architecture Violation" in line or "was violated" in line:
                    errors.append(line.strip())
                elif in_failure_section and line.strip() and not line.startswith("["):
                    # Capture detailed violation context
                    if any(keyword in line for keyword in ["depends on", "accesses", "should not"]):
                        errors.append(line.strip())

            # Check for build/test failure
            if result.returncode != 0 and not errors:
                if "BUILD FAILURE" in result.stdout or "BUILD FAILURE" in result.stderr:
                    errors.append("ArchUnit tests failed - check raw output for details")
                elif "No tests found" in result.stdout or "No tests found" in result.stderr:
                    warnings.append("No ArchUnit tests found - ensure ArchitectureTest.java exists")

            passed = result.returncode == 0 and len(errors) == 0
            fix_hint = ""
            if not passed:
                fix_hint = "Fix architecture violations: ensure domain layer doesn't depend on infrastructure"

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=result.stdout + "\n" + result.stderr,
                duration_seconds=duration,
                exit_code=result.returncode,
                fix_hint=fix_hint,
            )

        except subprocess.TimeoutExpired:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"ArchUnit tests timed out after {self.timeout} seconds"],
                duration_seconds=self.timeout,
                exit_code=-1,
                fix_hint="Consider reducing test scope or increasing timeout",
            )
        except FileNotFoundError:
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=["Maven not found. Install Maven or check PATH"],
                duration_seconds=0,
                exit_code=-1,
                fix_hint="Install Maven: https://maven.apache.org/install.html",
            )

