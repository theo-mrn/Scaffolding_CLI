from __future__ import annotations

from pathlib import Path

import typer

from forge.commands.scaffold import console
from forge.config.settings import settings
from forge.config.store import load_stored_token, save_token
from forge.github.secrets import set_repo_secrets
from forge.github.errors import GitHubError

app = typer.Typer(help="Add a secret to a GitHub repo and the local .env file.")


@app.callback(invoke_without_command=True)
def add_secret(
    repo: str = typer.Option(..., "--repo", "-r", help="GitHub repo name"),
    key: str = typer.Option(..., "--key", "-k", help="Secret name"),
    value: str = typer.Option(..., "--value", "-v", help="Secret value", hide_input=True),
    env_file: Path = typer.Option(Path(".env"), "--env-file", help="Path to local .env file"),
    skip_github: bool = typer.Option(False, "--skip-github", help="Only update local .env"),
) -> None:
    """Add a secret to GitHub Actions and the local .env file."""

    # --- Local .env ---
    _write_env(env_file, key, value)
    console.print(f"[green]✓[/green] Added {key} to {env_file}")

    if skip_github:
        return

    # --- GitHub ---
    if not settings.github_token:
        settings.github_token = load_stored_token()
    if not settings.github_token:
        token = typer.prompt("  GitHub token", hide_input=True)
        settings.github_token = token
        save_token(token)

    try:
        set_repo_secrets(repo, {key: value})
        console.print(f"[green]✓[/green] Added {key} to GitHub repo '{repo}'")
    except GitHubError as e:
        console.print(f"[red]GitHub error:[/red] {e}")
        raise typer.Exit(1)


def _write_env(env_file: Path, key: str, value: str) -> None:
    lines: list[str] = []

    if env_file.exists():
        lines = env_file.read_text().splitlines()

    # Update existing key or append
    key_found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}=") or line.startswith(f"{key} ="):
            lines[i] = f"{key}={value}"
            key_found = True
            break

    if not key_found:
        lines.append(f"{key}={value}")

    env_file.write_text("\n".join(lines) + "\n")
