from pathlib import Path

from jinja2 import Environment, PackageLoader


def generate_terraform(project_dir: Path, project_name: str) -> None:
    tf_dir = project_dir / "terraform"
    tf_dir.mkdir()

    env = _jinja_env()
    ctx = {"project_name": project_name}

    (tf_dir / "main.tf").write_text(env.get_template("terraform_main.tf.j2").render(**ctx))
    (tf_dir / "variables.tf").write_text(
        env.get_template("terraform_variables.tf.j2").render(**ctx)
    )
    (tf_dir / "outputs.tf").write_text(
        env.get_template("terraform_outputs.tf.j2").render(**ctx)
    )


def _jinja_env() -> Environment:
    return Environment(
        loader=PackageLoader("forge", "config/templates"),
        keep_trailing_newline=True,
    )
