from __future__ import annotations

from pathlib import Path

import questionary
import typer

from forge.commands.scaffold import console, run_scaffold
from forge.config.settings import settings
from forge.config.store import load_stored_token, save_token

app = typer.Typer(help="Interactively scaffold a new project.")

PROJECT_TYPES = ["python", "node", "react", "go", "fastapi"]


@app.callback(invoke_without_command=True)
def init(
    output_dir: Path = typer.Option(Path("."), "--output", "-o", help="Output directory"),
) -> None:
    """Interactively create a new project — asks for everything step by step."""
    console.print("\n[bold]forge[/bold] — new project setup\n")

    name = typer.prompt("  Project name")

    project_type = questionary.select(
        "  Project type",
        choices=PROJECT_TYPES,
    ).ask()

    if not project_type:
        raise typer.Exit(0)

    private = typer.confirm("  Private repository?", default=True)
    setup_github = typer.confirm("  Set up GitHub? (create repo, branch protection)", default=True)

    ci_secrets = ""
    docker = False
    sonar = False
    docker_secrets: dict = {}

    if setup_github:
        if not settings.github_token:
            settings.github_token = load_stored_token()
        if not settings.github_token:
            token = typer.prompt("  GitHub token", hide_input=True)
            settings.github_token = token
            save_token(token)
            console.print("  [dim]Token saved to ~/.config/forge/config.toml[/dim]")

        docker = typer.confirm("  Enable Docker build & push in CI?", default=False)
        if docker:
            docker_username = typer.prompt("  Docker username")
            docker_password = typer.prompt("  Docker password/token", hide_input=True)
            docker_secrets = {
                "DOCKER_USERNAME": docker_username,
                "DOCKER_PASSWORD": docker_password,
            }

        sonar = typer.confirm("  Enable SonarCloud? (requires SONAR_TOKEN)", default=False)
        if sonar:
            sonar_token = typer.prompt("  SonarCloud token", hide_input=True)
            docker_secrets["SONAR_TOKEN"] = sonar_token

    skip_github = not setup_github

    console.print()

    run_scaffold(
        name=name,
        project_type=project_type,
        output_dir=output_dir,
        skip_github=skip_github,
        private=private,
        ci_secrets=ci_secrets,
        docker=docker,
        sonar=sonar,
        docker_secrets=docker_secrets,
    )
