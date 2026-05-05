"""Architecture fitness checkers (DDD layer validation)."""

import ast
import logging
import time
from pathlib import Path
from typing import Optional

from agentforge.checks.base import BaseChecker, CheckResult

logger = logging.getLogger(__name__)


class PythonLayerChecker(BaseChecker):
    """Check Python DDD layer dependencies using AST analysis.

    Validates that domain layer does not import from infrastructure layer.
    """

    def __init__(self, config: dict):
        super().__init__("ddd_layer_check", config)
        self.timeout = config.get("timeout", 60)
        self.domain_dir = config.get("domain_dir", "domain")
        self.forbidden_imports = config.get("forbidden_imports", ["infrastructure"])

    def run(self, workspace: Path) -> CheckResult:
        start_time = time.time()
        errors = []
        warnings = []

        domain_path = workspace / self.domain_dir
        if not domain_path.exists():
            return CheckResult(
                checker=self.name,
                passed=True,
                warnings=[f"Domain directory '{self.domain_dir}' not found, skipping check"],
                duration_seconds=time.time() - start_time,
                exit_code=0,
            )

        try:
            # Scan all Python files in domain directory
            python_files = list(domain_path.rglob("*.py"))
            logger.info(f"Scanning {len(python_files)} Python files in {domain_path}")

            for py_file in python_files:
                violations = self._check_file_imports(py_file, workspace)
                errors.extend(violations)

                # Timeout check
                if time.time() - start_time > self.timeout:
                    warnings.append(f"Timeout reached, scanned {len(python_files)} files")
                    break

            duration = time.time() - start_time
            passed = len(errors) == 0
            fix_hint = ""
            if not passed:
                fix_hint = (
                    "Domain layer should not depend on infrastructure. "
                    "Use dependency inversion: define interfaces in domain, "
                    "implement in infrastructure."
                )

            return CheckResult(
                checker=self.name,
                passed=passed,
                errors=errors,
                warnings=warnings,
                raw_output=f"Scanned {len(python_files)} files in {domain_path}",
                duration_seconds=duration,
                exit_code=0 if passed else 1,
                fix_hint=fix_hint,
            )

        except Exception as e:
            logger.error(f"Error during Python layer check: {e}", exc_info=True)
            return CheckResult(
                checker=self.name,
                passed=False,
                errors=[f"Layer check failed: {str(e)}"],
                duration_seconds=time.time() - start_time,
                exit_code=-1,
            )

    def _check_file_imports(self, file_path: Path, workspace: Path) -> list[str]:
        """Check a single Python file for forbidden imports.

        Args:
            file_path: Path to Python file
            workspace: Workspace root path

        Returns:
            List of violation messages
        """
        violations = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))

            for node in ast.walk(tree):
                # Check 'import infrastructure' or 'import infrastructure.xxx'
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if self._is_forbidden_import(alias.name):
                            relative_path = file_path.relative_to(workspace)
                            violations.append(
                                f"{relative_path}:{node.lineno} - "
                                f"Domain layer imports forbidden module: {alias.name}"
                            )

                # Check 'from infrastructure import xxx'
                elif isinstance(node, ast.ImportFrom):
                    if node.module and self._is_forbidden_import(node.module):
                        relative_path = file_path.relative_to(workspace)
                        violations.append(
                            f"{relative_path}:{node.lineno} - "
                            f"Domain layer imports from forbidden module: {node.module}"
                        )

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")
        except Exception as e:
            logger.warning(f"Error parsing {file_path}: {e}")

        return violations

    def _is_forbidden_import(self, module_name: str) -> bool:
        """Check if module name matches forbidden imports.

        Args:
            module_name: Import module name (e.g., 'infrastructure.db')

        Returns:
            True if import is forbidden
        """
        for forbidden in self.forbidden_imports:
            if module_name == forbidden or module_name.startswith(f"{forbidden}."):
                return True
        return False


class JavaLayerChecker(BaseChecker):
    """Check Java DDD layer dependencies using ArchUnit.

    This is a wrapper around ArchUnitChecker for consistency.
    """

    def __init__(self, config: dict):
        super().__init__("java_layer_check", config)
        # Delegate to ArchUnitChecker
        from agentforge.checks.java import ArchUnitChecker
        self.archunit_checker = ArchUnitChecker(config)

    def run(self, workspace: Path) -> CheckResult:
        """Run ArchUnit checks via Maven."""
        result = self.archunit_checker.run(workspace)
        # Override checker name for clarity
        result.checker = self.name
        return result

