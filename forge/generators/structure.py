from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import typer
from rich.console import Console

console = Console()


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
    subprocess.run(cmd, cwd=cwd, check=True, capture_output=True)


def _require(binary: str) -> None:
    if not shutil.which(binary):
        console.print(f"[red]Error:[/red] '{binary}' is not installed or not in PATH.")
        raise typer.Exit(1)


def _init_python(project_dir: Path, project_name: str) -> None:
    _require("python3")
    src = project_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text(
        f'def main() -> None:\n    print("Hello from {project_name}!")\n\n\nif __name__ == "__main__":\n    main()\n'
    )
    (project_dir / "requirements.txt").write_text("")
    _run(["python3", "-m", "venv", ".venv"], cwd=project_dir)


def _init_fastapi(project_dir: Path, project_name: str) -> None:
    _require("python3")
    src = project_dir / "src"
    (src / "routers").mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("")
    (src / "main.py").write_text(
        f'from fastapi import FastAPI\n\napp = FastAPI(title="{project_name}")\n\n\n@app.get("/health")\ndef health() -> dict:\n    return {{"status": "ok"}}\n'
    )
    requirements = project_dir / "requirements.txt"
    requirements.write_text("fastapi>=0.110.0\nuvicorn[standard]>=0.29.0\n")
    _run(["python3", "-m", "venv", ".venv"], cwd=project_dir)
    pip = project_dir / ".venv" / "bin" / "pip"
    _run([str(pip), "install", "-r", "requirements.txt", "-q"], cwd=project_dir)


def _init_node(project_dir: Path, project_name: str) -> None:
    _require("npm")
    src = project_dir / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "index.js").write_text(
        f'const http = require("http");\n\nconst PORT = process.env.PORT || 3000;\n\nconst server = http.createServer((req, res) => {{\n  if (req.url === "/health") {{\n    res.writeHead(200, {{ "Content-Type": "application/json" }});\n    res.end(JSON.stringify({{ status: "ok" }}));\n    return;\n  }}\n  res.writeHead(404);\n  res.end();\n}});\n\nserver.listen(PORT, () => {{\n  console.log(`{project_name} running on port ${{PORT}}`);\n}});\n'
    )
    _run(["npm", "init", "-y"], cwd=project_dir)
    # Overwrite package.json with proper scripts after npm init
    import json
    pkg_path = project_dir / "package.json"
    pkg = json.loads(pkg_path.read_text())
    pkg["scripts"] = {"start": "node src/index.js", "dev": "node --watch src/index.js"}
    pkg_path.write_text(json.dumps(pkg, indent=2) + "\n")
    _run(["npm", "install"], cwd=project_dir)


def _init_react(project_dir: Path, project_name: str) -> None:
    _require("npm")
    parent = project_dir.parent
    _run(
        ["npm", "create", "vite@latest", project_name, "--", "--template", "react"],
        cwd=parent,
    )
    _run(["npm", "install"], cwd=project_dir)


def _init_go(project_dir: Path, project_name: str) -> None:
    _require("go")
    cmd_dir = project_dir / "cmd"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "main.go").write_text(
        'package main\n\nimport (\n\t"encoding/json"\n\t"log"\n\t"net/http"\n\t"os"\n)\n\nfunc main() {\n\tport := os.Getenv("PORT")\n\tif port == "" {\n\t\tport = "8080"\n\t}\n\n\thttp.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {\n\t\tw.Header().Set("Content-Type", "application/json")\n\t\tjson.NewEncoder(w).Encode(map[string]string{"status": "ok"})\n\t})\n\n\tlog.Printf("' + project_name + ' listening on :%s", port)\n\tlog.Fatal(http.ListenAndServe(":"+port, nil))\n}\n'
    )
    _run(["go", "mod", "init", f"github.com/your-org/{project_name}"], cwd=project_dir)
    _run(["go", "mod", "tidy"], cwd=project_dir)
