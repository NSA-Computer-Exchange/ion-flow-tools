from __future__ import annotations
from tools.extract_embedded import extract_embedded_artifacts

from pathlib import Path
from datetime import datetime
import json
import shutil
import re


PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = PROJECT_ROOT / "workspace"
SESSION_FILE = WORKSPACE_ROOT / ".current_workspace.json"


def _slugify(value: str) -> str:
    value = value.strip()
    value = re.sub(r"[^\w\s-]", "", value)
    value = re.sub(r"[\s-]+", "_", value)
    return value or "workspace"


def workspace_path(name: str) -> Path:
    return WORKSPACE_ROOT / _slugify(name)


def manifest_path(name: str) -> Path:
    return workspace_path(name) / "manifest.json"


def ensure_workspace_dirs(name: str) -> Path:
    root = workspace_path(name)

    dirs = [
        root / "exports" / "dataflows",
        root / "exports" / "workflows",
        root / "exports" / "connection_points",
        root / "exports" / "scripts",
        root / "exports" / "mappings",
        root / "artifacts" / "normalized",
        root / "artifacts" / "docs",
        root / "artifacts" / "diagrams",
        root / "artifacts" / "bundles",
    ]

    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    return root


def load_manifest(name: str) -> dict | None:
    path = manifest_path(name)
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return None
            return json.loads(content)
    except json.JSONDecodeError:
        return None


def save_manifest(name: str, manifest: dict) -> Path:
    root = ensure_workspace_dirs(name)
    path = root / "manifest.json"
    temp_path = root / "manifest.json.tmp"

    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")

    with temp_path.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    temp_path.replace(path)
    return path


def list_workspaces() -> list[str]:
    if not WORKSPACE_ROOT.exists():
        return []

    results = []
    for item in WORKSPACE_ROOT.iterdir():
        if item.is_dir() and (item / "manifest.json").exists():
            results.append(item.name)

    return sorted(results)


def get_current_workspace() -> str | None:
    if not SESSION_FILE.exists():
        return None

    try:
        with SESSION_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("workspace_name")
    except Exception:
        return None


def set_current_workspace(name: str) -> None:
    WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    with SESSION_FILE.open("w", encoding="utf-8") as f:
        json.dump({"workspace_name": name}, f, indent=2)


def get_current_manifest() -> dict | None:
    current = get_current_workspace()
    if not current:
        return None
    return load_manifest(current)


def stage_dataflow(xml_path: str | Path, workspace_name: str | None = None) -> dict:
    xml_path = Path(xml_path).expanduser().resolve()
    if not xml_path.exists():
        raise FileNotFoundError(f"XML file not found: {xml_path}")

    flow_name = xml_path.stem
    workspace_name = workspace_name or flow_name

    root = ensure_workspace_dirs(workspace_name)
    dest = root / "exports" / "dataflows" / xml_path.name
    shutil.copy2(xml_path, dest)

    extracted = extract_embedded_artifacts(dest, root / "exports")

    now = datetime.now().isoformat(timespec="seconds")

    existing = load_manifest(workspace_name) or {}
    manifest = {
        "workspace_name": workspace_name,
        "flow_name": flow_name,
        "source_file": str(xml_path),
        "current_flow": str(Path("exports") / "dataflows" / xml_path.name),
        "created_at": existing.get("created_at", now),
        "updated_at": now,
        "extracted_artifacts": extracted,
    }

    save_manifest(workspace_name, manifest)
    set_current_workspace(workspace_name)

    return {
        "workspace_name": workspace_name,
        "workspace_root": str(root),
        "flow_name": flow_name,
        "staged_flow_path": str(dest),
        "manifest_path": str(root / "manifest.json"),
    }


def current_flow_xml_path() -> Path | None:
    manifest = get_current_manifest()
    current = get_current_workspace()

    if not manifest or not current:
        return None

    rel = manifest.get("current_flow")
    if not rel:
        return None

    return workspace_path(current) / rel

