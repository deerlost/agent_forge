"""Quality gate engine that orchestrates checker execution.

Runs checks in priority order (fast -> medium -> slow) and
short-circuits on fast check failures.
"""

import logging
from pathlib import Path
from typing import Optional

from agentforge.checks.base import BaseChecker, CheckResult

logger = logging.getLogger(__name__)

# Speed tiers for ordering execution
SPEED_TIERS: dict[str, str] = {
    "ruff": "fast",
    "eslint": "fast",
    "prettier": "fast",
    "tsc": "medium",
    "mypy": "medium",
}

TIER_ORDER = ["fast", "medium", "slow"]


class QualityGate:
    """Orchestrates quality check execution with fail-fast semantics.

    Runs checkers grouped by speed tier. If any 'fast' checker fails,
    remaining tiers are skipped to provide rapid feedback.
    """

    def __init__(self, workspace: Path, config: dict):
        self.workspace = workspace
        self.config = config
        self.enabled = config.get("enabled", True)
        self.max_retries = config.get("max_retries", 2)
        self.checkers: list[BaseChecker] = []

        if self.enabled:
            self._init_checkers()

    def _init_checkers(self) -> None:
        """Initialize checkers based on config."""
        checks_config = self.config.get("checks", {})

        # Frontend checks
        frontend_config = checks_config.get("frontend", {})
        if frontend_config.get("eslint", {}).get("enabled", False):
            from agentforge.checks.frontend import ESLintChecker
            self.checkers.append(ESLintChecker(frontend_config.get("eslint", {})))

        if frontend_config.get("tsc", {}).get("enabled", False):
            from agentforge.checks.frontend import TypeScriptChecker
            self.checkers.append(TypeScriptChecker(frontend_config.get("tsc", {})))

        if frontend_config.get("prettier", {}).get("enabled", False):
            from agentforge.checks.frontend import PrettierChecker
            self.checkers.append(PrettierChecker(frontend_config.get("prettier", {})))

        # Python checks
        python_config = checks_config.get("python", {})
        if python_config.get("ruff", {}).get("enabled", False):
            from agentforge.checks.python_checks import RuffChecker
            self.checkers.append(RuffChecker(python_config.get("ruff", {})))

        if python_config.get("mypy", {}).get("enabled", False):
            from agentforge.checks.python_checks import MypyChecker
            self.checkers.append(MypyChecker(python_config.get("mypy", {})))

        logger.info(f"Initialized {len(self.checkers)} quality checkers")

    def _group_by_tier(self) -> dict[str, list[BaseChecker]]:
        """Group checkers by speed tier."""
        tiers: dict[str, list[BaseChecker]] = {tier: [] for tier in TIER_ORDER}

        for checker in self.checkers:
            tier = SPEED_TIERS.get(checker.name, "slow")
            tiers[tier].append(checker)

        return tiers

    def run_checks(self) -> tuple[bool, list[CheckResult]]:
        """Run all enabled checks with fail-fast on fast tier.

        Returns:
            (all_passed, results) tuple
        """
        if not self.enabled:
            logger.info("Quality gate disabled, skipping checks")
            return True, []

        if not self.checkers:
            logger.warning("No checkers configured")
            return True, []

        tiers = self._group_by_tier()
        all_results: list[CheckResult] = []
        fast_tier_failed = False

        for tier in TIER_ORDER:
            tier_checkers = tiers[tier]
            if not tier_checkers:
                continue

            logger.info(f"Running {tier} tier checks ({len(tier_checkers)} checkers)")

            for checker in tier_checkers:
                logger.info(f"Running {checker.name}...")
                result = checker.run(self.workspace)
                all_results.append(result)

                if not result.passed:
                    logger.warning(
                        f"{checker.name} failed: {len(result.errors)} error(s), "
                        f"{len(result.warnings)} warning(s)"
                    )
                    if tier == "fast":
                        fast_tier_failed = True
                else:
                    logger.info(f"{checker.name} passed ({result.duration_seconds:.2f}s)")

            # Fail-fast: if any fast check failed, skip remaining tiers
            if tier == "fast" and fast_tier_failed:
                logger.warning("Fast tier checks failed, skipping remaining tiers")
                break

        all_passed = all(r.passed for r in all_results)
        return all_passed, all_results

    def format_feedback(self, results: list[CheckResult]) -> str:
        """Format check results as feedback for Generator Agent.

        Args:
            results: List of check results

        Returns:
            Human-readable feedback string
        """
        if not results:
            return "No quality checks were run."

        lines = ["## Quality Check Results\n"]

        failed = [r for r in results if not r.passed]
        passed = [r for r in results if r.passed]

        if passed:
            lines.append(f"✓ {len(passed)} check(s) passed\n")

        if failed:
            lines.append(f"✗ {len(failed)} check(s) failed:\n")
            for result in failed:
                lines.append(result.format_for_agent())
                lines.append("")

        return "\n".join(lines)
