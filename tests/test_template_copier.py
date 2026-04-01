import pytest
from pathlib import Path
from agentforge.core.template_copier import TemplateCopier

@pytest.fixture
def templates_dir(tmp_path):
    vue_dir = tmp_path / "ui" / "vue3"
    vue_dir.mkdir(parents=True)
    (vue_dir / "package.json").write_text('{"name": "frontend"}')
    (vue_dir / "vite.config.ts").write_text("export default {}")
    src_dir = vue_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.ts").write_text("import { createApp } from 'vue'")

    api_dir = tmp_path / "api" / "fastapi"
    api_dir.mkdir(parents=True)
    (api_dir / "pyproject.toml").write_text('[project]\nname = "backend"')
    app_dir = api_dir / "app"
    app_dir.mkdir()
    (app_dir / "main.py").write_text("from fastapi import FastAPI")

    docker_dir = tmp_path / "infra" / "docker"
    docker_dir.mkdir(parents=True)
    (docker_dir / "docker-compose.yaml").write_text("version: '3.8'")
    (docker_dir / "Dockerfile.frontend").write_text("FROM node:20")
    (docker_dir / "Dockerfile.backend").write_text("FROM python:3.11")
    return tmp_path

class TestTemplateCopier:
    def test_copy_ui_template(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        copier = TemplateCopier(templates_dir)
        copier.copy_template("vue3", workspace)
        assert (workspace / "frontend" / "package.json").exists()
        assert (workspace / "frontend" / "src" / "main.ts").exists()

    def test_copy_api_template(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        copier = TemplateCopier(templates_dir)
        copier.copy_template("fastapi", workspace)
        assert (workspace / "backend" / "pyproject.toml").exists()
        assert (workspace / "backend" / "app" / "main.py").exists()

    def test_copy_docker_template(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        copier = TemplateCopier(templates_dir)
        copier.copy_template("docker", workspace)
        assert (workspace / "infra" / "docker-compose.yaml").exists()

    def test_copy_all_templates_for_profile(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        copier = TemplateCopier(templates_dir)
        copier.copy_templates(["vue3", "fastapi", "docker"], workspace)
        assert (workspace / "frontend" / "package.json").exists()
        assert (workspace / "backend" / "pyproject.toml").exists()
        assert (workspace / "infra" / "docker-compose.yaml").exists()

    def test_skip_if_already_exists(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        (workspace / "frontend").mkdir()
        (workspace / "frontend" / "package.json").write_text('{"custom": true}')
        copier = TemplateCopier(templates_dir)
        copier.copy_template("vue3", workspace)
        content = (workspace / "frontend" / "package.json").read_text()
        assert "custom" in content

    def test_missing_template_raises(self, templates_dir, tmp_path):
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        copier = TemplateCopier(templates_dir)
        with pytest.raises(FileNotFoundError):
            copier.copy_template("nonexistent", workspace)

    def test_list_available_templates(self, templates_dir):
        copier = TemplateCopier(templates_dir)
        available = copier.list_templates()
        assert "vue3" in available
        assert "fastapi" in available
        assert "docker" in available
