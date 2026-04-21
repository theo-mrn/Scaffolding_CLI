from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from forge.config.settings import settings
from forge.generators.dockerfile import generate_dockerfile
from forge.generators.gitignore import generate_gitignore
from forge.generators.readme import generate_readme
from forge.generators.terraform import generate_terraform
from forge.generators.structure import generate_structure
from forge.github.repo import create_github_repo
from forge.github.branch_protection import set_branch_protection
from forge.github.secrets import set_repo_secrets
from forge.github.errors import GitHubError

console = Console()


def run_scaffold(
    name: str,
    project_type: str,
    output_dir: Path,
    skip_github: bool,
    private: bool,
    ci_secrets: str,
) -> None:
    output_dir = _resolve_output_dir(output_dir)
    project_dir = output_dir / name

    # React: vite creates the directory itself — don't pre-create it
    if project_type != "react":
        try:
            project_dir.mkdir(parents=True)
        except OSError as e:
            console.print(f"[red]Error:[/red] Cannot create directory '{project_dir}': {e.strerror}")
            raise typer.Exit(1)

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), console=console) as progress:
        task = progress.add_task("Initialising project...", total=None)
        generate_structure(project_dir, project_type, name)
        progress.update(task, description="[green]✓[/green] Project initialised")

        task = progress.add_task("Generating Dockerfile...", total=None)
        generate_dockerfile(project_dir, project_type)
        progress.update(task, description="[green]✓[/green] Dockerfile generated")

        task = progress.add_task("Generating .gitignore...", total=None)
        generate_gitignore(project_dir, project_type)
        progress.update(task, description="[green]✓[/green] .gitignore generated")

        task = progress.add_task("Generating README.md...", total=None)
        generate_readme(project_dir, name, project_type)
        progress.update(task, description="[green]✓[/green] README.md generated")

        task = progress.add_task("Generating Terraform module...", total=None)
        generate_terraform(project_dir, name)
        progress.update(task, description="[green]✓[/green] Terraform module generated")

        task = progress.add_task("Initialising git repository...", total=None)
        _git_init(project_dir, name)
        progress.update(task, description="[green]✓[/green] Git repository initialised")

        repo_url: str | None = None

        if not skip_github and settings.github_token:
            try:
                task = progress.add_task("Creating GitHub repository...", total=None)
                repo_url = create_github_repo(name, private=private)
                progress.update(task, description=f"[green]✓[/green] GitHub repo created: {repo_url}")

                task = progress.add_task("Pushing initial commit...", total=None)
                _git_push(project_dir, repo_url)
                progress.update(task, description="[green]✓[/green] Initial commit pushed")

                task = progress.add_task("Setting branch protection rules...", total=None)
                set_branch_protection(name)
                progress.update(task, description="[green]✓[/green] Branch protection rules applied")

                if ci_secrets:
                    task = progress.add_task("Setting CI/CD secrets...", total=None)
                    set_repo_secrets(name, _parse_secrets(ci_secrets))
                    progress.update(task, description="[green]✓[/green] CI/CD secrets configured")
            except GitHubError as e:
                progress.stop()
                console.print(f"\n[red]Erreur GitHub :[/red] {e}")
                console.print("[dim]Le projet a été créé localement — configure le repo GitHub manuellement.[/dim]")
                repo_url = None

    # Summary printed after Progress context so it always appears last
    _print_summary(project_dir, project_type=project_type, repo_url=repo_url)


def _resolve_output_dir(output_dir: Path) -> Path:
    if output_dir == Path("."):
        return output_dir
    if output_dir.is_absolute() and not output_dir.exists():
        return Path.home() / Path(*output_dir.parts[1:])
    return output_dir


def _git_init(project_dir: Path, project_name: str) -> None:
    import subprocess

    subprocess.run(["git", "init", "-b", "main"], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", f"chore: initial scaffold for {project_name}"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )


def _git_push(project_dir: Path, repo_url: str) -> None:
    import subprocess

    subprocess.run(
        ["git", "remote", "add", "origin", repo_url],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "push", "-u", "origin", "main"],
        cwd=project_dir,
        check=True,
        capture_output=True,
    )


def _parse_secrets(raw: str) -> dict:
    secrets = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if "=" in pair:
            key, _, value = pair.partition("=")
            secrets[key.strip()] = value.strip()
    return secrets


_NEXT_STEPS: dict[str, list[str]] = {
    "python": [
        "source .venv/bin/activate",
        "python src/main.py",
    ],
    "fastapi": [
        "source .venv/bin/activate",
        "uvicorn src.main:app --reload",
    ],
    "node": [
        "npm start",
    ],
    "react": [
        "npm run dev",
    ],
    "go": [
        "go run cmd/main.go",
    ],
}


def _print_summary(project_dir: Path, project_type: str, repo_url: str | None = None) -> None:
    console.print(f"\n[bold green]✓ Project ready:[/bold green] {project_dir.resolve()}")
    if repo_url:
        console.print(f"[bold green]✓ GitHub:[/bold green]        {repo_url}")
    console.print("\n[dim]Next steps:[/dim]")
    console.print(f"  cd {project_dir.resolve()}")
    for step in _NEXT_STEPS.get(project_type, []):
        console.print(f"  {step}")
