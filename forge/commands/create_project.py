from __future__ import annotations

from enum import Enum
from pathlib import Path

import typer

from forge.commands.scaffold import console, run_scaffold

app = typer.Typer(help="Create a new project with company standards.")


class ProjectType(str, Enum):
    python = "python"
    node = "node"
    react = "react"
    go = "go"
    fastapi = "fastapi"


@app.callback(invoke_without_command=True)
def create_project(
    name: str = typer.Option(..., "--name", "-n", help="Project name"),
    project_type: ProjectType = typer.Option(..., "--type", "-t", help="Project type"),
    output_dir: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
    skip_github: bool = typer.Option(False, "--skip-github", help="Skip GitHub repo creation"),
    private: bool = typer.Option(True, "--private/--public", help="GitHub repo visibility"),
    ci_secrets: str = typer.Option(
        "", "--secrets", help="Comma-separated CI secrets (KEY=VALUE,...)"
    ),
) -> None:
    """Scaffold a new project with Dockerfile, .gitignore, Terraform, and GitHub setup."""
    project_dir = output_dir / name
    if project_dir.exists():
        console.print(f"[red]Error:[/red] Directory '{project_dir}' already exists.")
        raise typer.Exit(1)

    run_scaffold(
        name=name,
        project_type=project_type.value,
        output_dir=output_dir,
        skip_github=skip_github,
        private=private,
        ci_secrets=ci_secrets,
    )
