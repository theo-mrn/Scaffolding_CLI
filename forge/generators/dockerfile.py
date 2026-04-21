from pathlib import Path

from jinja2 import Environment, PackageLoader


def generate_dockerfile(project_dir: Path, project_type: str) -> None:
    env = _jinja_env()
    template = env.get_template(f"{project_type}.Dockerfile.j2")
    (project_dir / "Dockerfile").write_text(template.render())


def _jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("forge", "config/templates"),
        keep_trailing_newline=True,
    )
