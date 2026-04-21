from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

console = Console()

_ENV_EXAMPLE = "# Add your environment variables here\n# PORT=3000\n"


def generate_structure(project_dir: Path, project_type: str, project_name: str) -> None:
    generators = {
        "python": _init_python,
        "fastapi": _init_fastapi,
        "node": _init_node,
        "react": _init_react,
        "go": _init_go,
    }
    fn = generators.get(project_type)
    if fn:
        fn(project_dir, project_name)


def _run(cmd: list[str], cwd: Path) -> None:
    try:
        subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode().strip() if e.stderr else ""
        label = " ".join(cmd[:2])
        msg = f"'{label}' failed (exit {e.returncode})"
        if stderr:
            msg += f"\n  {stderr}"
        console.print(f"[red]Error:[/red] {msg}")
        raise typer.Exit(1)


def _require(binary: str) -> None:
    if not shutil.which(binary):
        console.print(f"[red]Error:[/red] '{binary}' is not installed or not in PATH.")
        raise typer.Exit(1)


def _write_env_example(project_dir: Path, extras: str = "") -> None:
    (project_dir / ".env.example").write_text(_ENV_EXAMPLE + extras)
    (project_dir / ".env").write_text(_ENV_EXAMPLE + extras)


def _init_python(project_dir: Path, project_name: str) -> None:
    _require("python3")
    src = project_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text(
        "import os\nfrom dotenv import load_dotenv\n\nload_dotenv()\n\n"
        f'def main() -> None:\n    print("Hello from {project_name}!")\n\n\n'
        'if __name__ == "__main__":\n    main()\n'
    )
    (project_dir / "requirements.txt").write_text("python-dotenv>=1.0.0\n")
    _write_env_example(project_dir)
    _run(["python3", "-m", "venv", ".venv"], cwd=project_dir)
    pip = project_dir / ".venv" / "bin" / "pip"
    _run([str(pip), "install", "-r", "requirements.txt", "-q"], cwd=project_dir)


def _init_fastapi(project_dir: Path, project_name: str) -> None:
    _require("python3")
    src = project_dir / "src"
    (src / "routers").mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text(
        "import os\nfrom dotenv import load_dotenv\nfrom fastapi import FastAPI\n\n"
        "load_dotenv()\n\n"
        f'app = FastAPI(title="{project_name}")\n\n\n'
        '@app.get("/health")\ndef health() -> dict:\n    return {"status": "ok"}\n'
    )
    (project_dir / "requirements.txt").write_text(
        "fastapi>=0.110.0\nuvicorn[standard]>=0.29.0\npython-dotenv>=1.0.0\n"
    )
    _write_env_example(project_dir)
    _run(["python3", "-m", "venv", ".venv"], cwd=project_dir)
    pip = project_dir / ".venv" / "bin" / "pip"
    _run([str(pip), "install", "-r", "requirements.txt", "-q"], cwd=project_dir)


def _init_node(project_dir: Path, project_name: str) -> None:
    _require("npm")
    src = project_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "index.js").write_text(
        'require("dotenv").config();\n'
        'const express = require("express");\n\n'
        "const app = express();\n"
        "const PORT = process.env.PORT || 3000;\n\n"
        'app.use(express.json());\n\n'
        'app.get("/health", (req, res) => {\n'
        '  res.json({ status: "ok" });\n'
        "});\n\n"
        "app.listen(PORT, () => {\n"
        f'  console.log(`{project_name} running on port ${{PORT}}`);\n'
        "});\n"
    )
    _run(["npm", "init", "-y"], cwd=project_dir)
    pkg_path = project_dir / "package.json"
    pkg = json.loads(pkg_path.read_text())
    pkg["scripts"] = {"start": "node src/index.js", "dev": "node --watch src/index.js"}
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n")
    _write_env_example(project_dir, "PORT=3000\n")
    _run(["npm", "install", "express", "dotenv"], cwd=project_dir)


def _init_react(project_dir: Path, project_name: str) -> None:
    _require("npm")
    parent = project_dir.parent
    _run(
        ["npm", "create", "vite@latest", project_name, "--", "--template", "react"],
        cwd=parent,
    )
    _write_env_example(project_dir, "VITE_API_URL=http://localhost:3000\n")
    _run(["npm", "install"], cwd=project_dir)


def _init_go(project_dir: Path, project_name: str) -> None:
    _require("go")
    cmd_dir = project_dir / "cmd"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "main.go").write_text(
        'package main\n\nimport (\n'
        '\t"encoding/json"\n'
        '\t"log"\n'
        '\t"net/http"\n'
        '\t"os"\n\n'
        '\t"github.com/joho/godotenv"\n'
        ')\n\n'
        'func main() {\n'
        '\t_ = godotenv.Load()\n\n'
        '\tport := os.Getenv("PORT")\n'
        '\tif port == "" {\n'
        '\t\tport = "8080"\n'
        '\t}\n\n'
        '\thttp.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {\n'
        '\t\tw.Header().Set("Content-Type", "application/json")\n'
        '\t\tjson.NewEncoder(w).Encode(map[string]string{"status": "ok"})\n'
        '\t})\n\n'
        f'\tlog.Printf("{project_name} listening on :%s", port)\n'
        '\tlog.Fatal(http.ListenAndServe(":"+port, nil))\n'
        '}\n'
    )
    _write_env_example(project_dir, "PORT=8080\n")
    _run(["go", "mod", "init", f"github.com/your-org/{project_name}"], cwd=project_dir)
    _run(["go", "get", "github.com/joho/godotenv"], cwd=project_dir)
    _run(["go", "mod", "tidy"], cwd=project_dir)
