"""Resource path resolver.

Lookup order for config/agents/templates/profiles:
  1. Working directory (local overrides)
  2. AgentForge package installation directory (built-in defaults)

This means users never need to copy framework resources.
They only create local files when they want to override defaults.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Package root: agentforge/ (where __init__.py lives)
# Resources are siblings: config/, agents/, templates/, profiles/
_PACKAGE_DIR = Path(__file__).parent.parent  # agentforge/agentforge/ -> agentforge/
_INSTALL_DIR = _PACKAGE_DIR.parent           # agentforge/ -> project root containing config/ etc.


def resolve_dir(name: str, local_override: str | None = None) -> Path | None:
    """Resolve a resource directory by name.

    Args:
        name: directory name (config, agents, templates, profiles)
        local_override: explicit path from CLI argument

    Returns:
        Path if found, None if not found anywhere.

    Lookup order:
        1. local_override (if provided and exists)
        2. ./{name} (current working directory)
        3. {install_dir}/{name} (AgentForge installation directory)
    """
    def _has_content(d: Path) -> bool:
        """Check if directory exists and has at least one file."""
        return d.exists() and d.is_dir() and any(d.iterdir())

    # 1. Explicit override
    if local_override:
        p = Path(local_override)
        if _has_content(p):
            logger.debug(f"Resource '{name}': using explicit path {p}")
            return p

    # 2. Current working directory
    local = Path.cwd() / name
    if _has_content(local):
        logger.debug(f"Resource '{name}': using local {local}")
        return local

    # 3. Installation directory
    installed = _INSTALL_DIR / name
    if _has_content(installed):
        logger.debug(f"Resource '{name}': using installed {installed}")
        return installed

    logger.debug(f"Resource '{name}': not found")
    return None


def resolve_config_dir(local_override: str | None = None) -> Path:
    """Resolve config directory. Falls back to built-in defaults."""
    result = resolve_dir("config", local_override)
    if result is None:
        # Last resort: return install dir config (may not exist)
        return _INSTALL_DIR / "config"
    return result


def resolve_agents_dir(local_override: str | None = None) -> Path | None:
    return resolve_dir("agents", local_override)


def resolve_templates_dir(local_override: str | None = None) -> Path | None:
    return resolve_dir("templates", local_override)


def resolve_profiles_dir(local_override: str | None = None) -> Path | None:
    return resolve_dir("profiles", local_override)


def resolve_knowledge_dir(local_override: str | None = None) -> Path:
    """Knowledge dir: always in CWD (never from install dir, it's user data)."""
    if local_override:
        return Path(local_override)
    return Path.cwd() / "knowledge"


def get_install_dir() -> Path:
    """Return the AgentForge installation root directory."""
    return _INSTALL_DIR
