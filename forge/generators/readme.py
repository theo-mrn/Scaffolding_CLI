from pathlib import Path

from jinja2 import Environment, PackageLoader


def generate_readme(project_dir: Path, project_name: str, project_type: str) -> None:
    env = _jinja_env()
    template = env.get_template("readme.j2")
    (project_dir / "README.md").write_text(
        template.render(project_name=project_name, project_type=project_type)
    )


def _jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("forge", "config/templates"),
        keep_trailing_newline=True,
    )
