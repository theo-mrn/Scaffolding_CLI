from __future__ import annotations

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore[no-redef]
import tomli_w
from pathlib import Path

_CONFIG_PATH = Path.home() / ".config" / "forge" / "config.toml"


def load_stored_token() -> str:
    if not _CONFIG_PATH.exists():
        return ""
    try:
        with open(_CONFIG_PATH, "rb") as f:
            data = tomllib.load(f)
        return data.get("github", {}).get("token", "")
    except Exception:
        return ""


def save_token(token: str) -> None:
    _CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict = {}
    if _CONFIG_PATH.exists():
        try:
            with open(_CONFIG_PATH, "rb") as f:
                existing = tomllib.load(f)
        except Exception:
            pass
    existing.setdefault("github", {})["token"] = token
    with open(_CONFIG_PATH, "wb") as f:
        tomli_w.dump(existing, f)
