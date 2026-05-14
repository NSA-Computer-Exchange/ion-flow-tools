from pathlib import Path
from typing import Optional


WORKSPACE_ROOT = Path("workspace")

STATE_DIR = Path.home() / ".ionflow"
STATE_DIR.mkdir(exist_ok=True)

CURRENT_FILE = STATE_DIR / "current_workspace.json"


def list_workspaces():
    return sorted([
        p.name for p in WORKSPACE_ROOT.iterdir()
        if p.is_dir()
    ])


def set_current_workspace(name: str):
    ws_path = WORKSPACE_ROOT / name
    if not ws_path.exists():
        raise ValueError(f"Workspace not found: {name}")

    CURRENT_FILE.write_text(name.strip(), encoding="utf-8")


def get_current_workspace() -> Optional[str]:
    if not CURRENT_FILE.exists():
        return None
    return CURRENT_FILE.read_text(encoding="utf-8").strip()


def require_current_workspace() -> str:
    ws = get_current_workspace()
    if not ws:
        raise RuntimeError("No current workspace set. Use: ionflow workspace set <name>")
    return ws