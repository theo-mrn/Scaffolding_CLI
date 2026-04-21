import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(help="List available project types.")

console = Console()

_TYPES = [
    ("python", "Python app with venv + python-dotenv"),
    ("fastapi", "FastAPI REST API with uvicorn + python-dotenv"),
    ("node",    "Node.js app with Express + dotenv"),
    ("react",   "React app scaffolded with Vite"),
    ("go",      "Go app with net/http + godotenv"),
]


@app.callback(invoke_without_command=True)
def list_types() -> None:
    """Show all supported project types."""
    table = Table(show_header=True, header_style="bold")
    table.add_column("Type", style="bold cyan", min_width=10)
    table.add_column("Description")

    for name, description in _TYPES:
        table.add_row(name, description)

    console.print()
    console.print(table)
    console.print()
    console.print("[dim]Usage:[/dim]  forge init")
    console.print("[dim]       forge create-project --name mon-api --type fastapi[/dim]")
