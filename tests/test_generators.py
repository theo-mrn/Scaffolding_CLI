from pathlib import Path
from unittest.mock import patch

import pytest

from forge.generators.dockerfile import generate_dockerfile
from forge.generators.gitignore import generate_gitignore
from forge.generators.readme import generate_readme
from forge.generators.terraform import generate_terraform
from forge.generators.structure import generate_structure


@pytest.fixture()
def project_dir(tmp_path: Path) -> Path:
    d = tmp_path / "my-project"
    d.mkdir()
    return d


def test_generate_dockerfile_creates_file(project_dir: Path) -> None:
    generate_dockerfile(project_dir, "python")
    dockerfile = project_dir / "Dockerfile"
    assert dockerfile.exists()
    content = dockerfile.read_text()
    assert "FROM python" in content
    assert "WORKDIR /app" in content


def test_generate_gitignore_creates_file(project_dir: Path) -> None:
    generate_gitignore(project_dir, "python")
    gitignore = project_dir / ".gitignore"
    assert gitignore.exists()
    content = gitignore.read_text()
    assert "__pycache__" in content
    assert ".venv" in content


def test_generate_readme_contains_project_name(project_dir: Path) -> None:
    generate_readme(project_dir, "my-project", "python")
    readme = project_dir / "README.md"
    assert readme.exists()
    content = readme.read_text()
    assert "my-project" in content
    assert "python" in content


def test_generate_terraform_creates_module(project_dir: Path) -> None:
    generate_terraform(project_dir, "my-project")
    tf_dir = project_dir / "terraform"
    assert (tf_dir / "main.tf").exists()
    assert (tf_dir / "variables.tf").exists()
    assert (tf_dir / "outputs.tf").exists()
    assert "my-project" in (tf_dir / "variables.tf").read_text()


@patch("forge.generators.structure._run")
def test_generate_structure_python(mock_run, project_dir: Path) -> None:
    generate_structure(project_dir, "python", "my-project")
    assert (project_dir / "src" / "main.py").exists()
    assert (project_dir / "requirements.txt").exists()
    assert "my-project" in (project_dir / "src" / "main.py").read_text()
    mock_run.assert_called()


@patch("forge.generators.structure._run")
def test_generate_structure_fastapi(mock_run, project_dir: Path) -> None:
    generate_structure(project_dir, "fastapi", "my-api")
    assert (project_dir / "src" / "main.py").exists()
    assert (project_dir / "requirements.txt").exists()
    content = (project_dir / "src" / "main.py").read_text()
    assert "FastAPI" in content
    assert "my-api" in content


@patch("forge.generators.structure._run")
def test_generate_structure_node(mock_run, project_dir: Path) -> None:
    import json
    # simulate npm init -y creating package.json
    (project_dir / "package.json").write_text(json.dumps({"name": "my-project", "version": "1.0.0"}))
    generate_structure(project_dir, "node", "my-project")
    assert (project_dir / "src" / "index.js").exists()
    pkg = json.loads((project_dir / "package.json").read_text())
    assert "start" in pkg["scripts"]
    mock_run.assert_called()


@patch("forge.generators.structure._run")
def test_generate_structure_react(mock_run, project_dir: Path) -> None:
    # vite creates the dir — simulate it
    project_dir.mkdir(parents=True, exist_ok=True)
    generate_structure(project_dir, "react", "my-app")
    mock_run.assert_called()


@patch("forge.generators.structure._run")
@patch("forge.generators.structure.shutil.which", return_value="/usr/local/bin/go")
def test_generate_structure_go(mock_which, mock_run, project_dir: Path) -> None:
    generate_structure(project_dir, "go", "my-service")
    assert (project_dir / "cmd" / "main.go").exists()
    content = (project_dir / "cmd" / "main.go").read_text()
    assert "my-service" in content
    mock_run.assert_called()
