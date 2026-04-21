from __future__ import annotations

from pathlib import Path


def detect_project_type(project_dir: Path) -> str | None:
    """Detect project type by inspecting files in the directory."""

    if (project_dir / "go.mod").exists():
        return "go"

    if (project_dir / "package.json").exists():
        pkg = (project_dir / "package.json").read_text()
        if "vite" in pkg and "react" in pkg:
            return "react"
        return "node"

    if (project_dir / "requirements.txt").exists():
        reqs = (project_dir / "requirements.txt").read_text().lower()
        if "fastapi" in reqs:
            return "fastapi"
        return "python"

    if (project_dir / "pyproject.toml").exists():
        content = (project_dir / "pyproject.toml").read_text().lower()
        if "fastapi" in content:
            return "fastapi"
        return "python"

    return None
