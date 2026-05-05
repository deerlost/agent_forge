"""Quality gate checks base module.

Defines the core abstractions for quality checks (lint, type check, format, etc.)
that run after code generation to provide fast, deterministic feedback.
"""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class CheckSeverity(str, Enum):
    """Severity level of a check failure."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class CheckResult(BaseModel):
    """Result of running a quality check."""

    checker: str = Field(..., description="Name of the checker (eslint, tsc, checkstyle, etc.)")
    passed: bool = Field(..., description="Whether the check passed")
    errors: list[str] = Field(default_factory=list, description="Human-readable error messages")
    warnings: list[str] = Field(default_factory=list, description="Warning messages")
    raw_output: str = Field(default="", description="Raw command output")
    fix_hint: str = Field(default="", description="Hint for Generator to fix issues")
    duration_seconds: float = Field(default=0.0, description="Execution time")
    exit_code: int = Field(default=0, description="Command exit code")

    def format_for_agent(self) -> str:
        """Format check result as feedback for Generator Agent."""
        if self.passed:
            return f"✓ {self.checker} passed"

        lines = [f"✗ {self.checker} failed with {len(self.errors)} error(s)"]

        # Show first 10 errors to avoid overwhelming the agent
        for i, error in enumerate(self.errors[:10], 1):
            lines.append(f"  {i}. {error}")

        if len(self.errors) > 10:
            lines.append(f"  ... and {len(self.errors) - 10} more errors")

        if self.fix_hint:
            lines.append(f"\nFix hint: {self.fix_hint}")

        return "\n".join(lines)


class BaseChecker:
    """Abstract base class for quality checkers."""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config

    def run(self, workspace: Path) -> CheckResult:
        """Run the check and return result.

        Args:
            workspace: Path to the workspace directory

        Returns:
            CheckResult with pass/fail status and error details
        """
        raise NotImplementedError("Subclasses must implement run()")

    def can_auto_fix(self) -> bool:
        """Whether this checker supports automatic fixing."""
        return False

    def auto_fix(self, workspace: Path) -> CheckResult:
        """Attempt to automatically fix issues.

        Returns:
            CheckResult after attempting fixes
        """
        raise NotImplementedError("Auto-fix not supported")
