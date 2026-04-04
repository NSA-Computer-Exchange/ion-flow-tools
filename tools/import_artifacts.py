from __future__ import annotations

from pathlib import Path
import shutil


ARTIFACT_DIR_MAP = {
    "workflows": "workflows",
    "connection_points": "connection_points",
    "scripts": "scripts",
    "mappings": "mappings",
}


def import_artifact_file(
    workspace_root: Path,
    artifact_type: str,
    source_file: str | Path,
    dest_name: str | None = None,
) -> Path:
    source_file = Path(source_file).expanduser().resolve()
    if not source_file.exists():
        raise FileNotFoundError(f"Artifact file not found: {source_file}")

    if artifact_type not in ARTIFACT_DIR_MAP:
        raise ValueError(f"Unsupported artifact type: {artifact_type}")

    dest_dir = workspace_root / "exports" / ARTIFACT_DIR_MAP[artifact_type]
    dest_dir.mkdir(parents=True, exist_ok=True)

    filename = dest_name or source_file.name
    dest_path = dest_dir / filename
    shutil.copy2(source_file, dest_path)
    return dest_path