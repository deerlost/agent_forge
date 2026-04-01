import logging
import shutil
from pathlib import Path

logger = logging.getLogger(__name__)

TEMPLATE_MAP = {
    "vue3": ("ui/vue3", "frontend"),
    "react": ("ui/react", "frontend"),
    "fastapi": ("api/fastapi", "backend"),
    "spring-boot": ("api/spring-boot", "backend"),
    "go-gin": ("api/go-gin", "backend"),
    "docker": ("infra/docker", "infra"),
    "k8s": ("infra/k8s", "infra"),
    "celery": ("scheduler/celery", "scheduler"),
    "xxl-job": ("scheduler/xxl-job", "scheduler"),
    "python-algo": ("algorithm/python-algo", "algorithm"),
}


class TemplateCopier:
    def __init__(self, templates_dir: Path):
        self.templates_dir = templates_dir

    def _find_template(self, name: str) -> tuple[Path, str]:
        if name in TEMPLATE_MAP:
            subdir, target_name = TEMPLATE_MAP[name]
            source = self.templates_dir / subdir
            if source.exists():
                return source, target_name
        for category_dir in self.templates_dir.iterdir():
            if category_dir.is_dir():
                template_dir = category_dir / name
                if template_dir.exists():
                    category_targets = {"ui": "frontend", "api": "backend", "infra": "infra"}
                    target = category_targets.get(category_dir.name, name)
                    return template_dir, target
        raise FileNotFoundError(f"Template not found: {name}")

    def copy_template(self, name: str, workspace: Path) -> Path:
        source, target_name = self._find_template(name)
        target = workspace / target_name
        if target.exists():
            logger.info(f"Target directory {target} already exists, skipping copy")
            return target
        logger.info(f"Copying template {name} -> {target}")
        shutil.copytree(source, target)
        return target

    def copy_templates(self, names: list[str], workspace: Path) -> list[Path]:
        paths = []
        for name in names:
            try:
                path = self.copy_template(name, workspace)
                paths.append(path)
            except FileNotFoundError:
                logger.warning(f"Template {name} not found, skipping")
        return paths

    def list_templates(self) -> list[str]:
        available = []
        for category_dir in self.templates_dir.iterdir():
            if category_dir.is_dir():
                for template_dir in category_dir.iterdir():
                    if template_dir.is_dir():
                        available.append(template_dir.name)
        return sorted(available)
