from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json


def build_bundle_manifest(exports_root: str | Path = "exports") -> Dict[str, Any]:
    exports_root = Path(exports_root)

    artifacts: List[Dict[str, Any]] = []

    workflows_dir = exports_root / "workflows"
    if workflows_dir.exists():
        for path in sorted(workflows_dir.glob("*.xml")):
            artifacts.append(
                {
                    "artifact_type": "workflow",
                    "name": path.stem,
                    "path": str(path),
                }
            )

    connection_points_dir = exports_root / "connection_points"
    if connection_points_dir.exists():
        for path in sorted(connection_points_dir.glob("*.xml")):
            artifacts.append(
                {
                    "artifact_type": "connection_point",
                    "name": path.stem,
                    "path": str(path),
                }
            )

    scripts_dir = exports_root / "scripts"
    if scripts_dir.exists():
        for path in sorted(scripts_dir.glob("*.json")):
            artifacts.append(
                {
                    "artifact_type": "script",
                    "name": _extract_script_name(path),
                    "path": str(path),
                }
            )

    mappings_dir = exports_root / "mappings"
    if mappings_dir.exists():
        for path in sorted(mappings_dir.glob("*.xml")):
            artifacts.append(
                {
                    "artifact_type": "mapping",
                    "name": _mapping_name_from_file(path),
                    "path": str(path),
                }
            )

    return {
        "exports_root": str(exports_root),
        "artifacts": artifacts,
    }


def _extract_script_name(path: Path) -> str:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        return (
            data.get("name")
            or data.get("scriptName")
            or data.get("id")
            or path.stem
        )
    except Exception:
        return path.stem


def _mapping_name_from_file(path: Path) -> str:
    return path.stem


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m tools.bundle <exports-folder>")
        raise SystemExit(1)

    manifest = build_bundle_manifest(sys.argv[1])
    print(json.dumps(manifest, indent=2))