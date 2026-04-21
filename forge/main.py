import typer
from forge.commands.create_project import app as create_project_app
from forge.commands.init import app as init_app

app = typer.Typer(
    name="forge",
    help="Scaffold new projects with company standards.",
    no_args_is_help=True,
)

app.add_typer(init_app, name="init")
app.add_typer(create_project_app, name="create-project")

if __name__ == "__main__":
    app()
