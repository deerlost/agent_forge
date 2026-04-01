import json
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Create a temporary project directory with standard structure."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    (state_dir / "sprints").mkdir()
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return tmp_path


@pytest.fixture
def sample_plan():
    """A minimal plan.json for testing."""
    return {
        "tech_stack": {
            "frontend": "vue3 + vite",
            "backend": "python + fastapi",
            "database": "postgresql",
        },
        "data_model": [
            {
                "entity": "User",
                "fields": [
                    {"name": "id", "type": "bigint", "pk": True},
                    {"name": "email", "type": "varchar(255)", "unique": True},
                ],
            }
        ],
        "api_contract": [
            {
                "method": "POST",
                "path": "/api/auth/login",
                "request": {"email": "string", "password": "string"},
                "response": {"token": "string"},
                "errors": [401],
            }
        ],
        "sprints": [
            {
                "id": "S001",
                "name": "Project init + Auth",
                "type": "fullstack",
                "features": ["F001"],
                "depends_on": [],
                "contract": {
                    "done_criteria": ["POST /api/auth/login returns JWT"],
                    "test_scenarios": ["Correct login succeeds"],
                },
            },
            {
                "id": "S002",
                "name": "User management",
                "type": "backend",
                "features": ["F002"],
                "depends_on": ["S001"],
                "contract": {
                    "done_criteria": ["GET /api/users returns list"],
                    "test_scenarios": ["List users returns paginated data"],
                },
            },
        ],
    }


@pytest.fixture
def sample_requirement_spec():
    """A minimal requirement_spec.json for testing."""
    return {
        "project_name": "Test Project",
        "modules": [
            {
                "id": "M001",
                "name": "Auth",
                "priority": "P0",
                "features": [
                    {
                        "id": "F001",
                        "description": "Email login",
                        "acceptance_criteria": ["Login works"],
                        "business_rules": [],
                        "ai_feature": False,
                    }
                ],
            }
        ],
        "non_functional": {},
        "ambiguities": [],
    }
