import typer
from forge.commands.create_project import app as create_project_app
from forge.commands.init import app as init_app
from forge.commands.init_ci import app as init_ci_app
from forge.commands.list_types import app as list_types_app
from forge.commands.add_secret import app as add_secret_app

app = typer.Typer(
    name="forge",
    help="Scaffold new projects with company standards.",
    no_args_is_help=True,
)

app.add_typer(init_app, name="init")
app.add_typer(init_ci_app, name="init-ci")
app.add_typer(create_project_app, name="create-project")
app.add_typer(list_types_app, name="list-types")
app.add_typer(add_secret_app, name="add-secret")

if __name__ == "__main__":
    app()
