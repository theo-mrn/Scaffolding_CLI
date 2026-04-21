from pathlib import Path

from jinja2 import Environment, PackageLoader


def generate_gitignore(project_dir: Path, project_type: str) -> None:
    env = _jinja_env()
    template = env.get_template(f"{project_type}.gitignore.j2")
    (project_dir / ".gitignore").write_text(template.render())


def _jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("forge", "config/templates"),
        keep_trailing_newline=True,
    )
