from __future__ import annotations

from pathlib import Path
from typing import Iterable

from tools.workspace import get_current_workspace, workspace_path


ARTIFACT_DIR_MAP = {
    "workflows": "workflows",
    "connection_points": "connection_points",
    "scripts": "scripts",
    "mappings": "mappings",
}

ARTIFACT_SUFFIXES = {
    "workflows": (".xml",),
    "connection_points": (".xml",),
    "scripts": (".json",),
    "mappings": (".xml",),
}


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def get_search_roots() -> list[Path]:
    roots = []
    project_root = get_project_root()

    roots.append(project_root / "exports")
    roots.append(project_root / "workspace")
    roots.append(project_root)

    current = get_current_workspace()
    if current:
        roots.append(workspace_path(current) / "exports")

    roots.append(Path.home() / "Downloads")

    seen = []
    for r in roots:
        r = r.expanduser().resolve()
        if r.exists() and r not in seen:
            seen.append(r)
    return seen


def _candidate_patterns(name: str, suffixes: tuple[str, ...]) -> list[str]:
    patterns = []
    for suffix in suffixes:
        patterns.append(f"{name}{suffix}")
        patterns.append(f"*{name}*{suffix}")
        patterns.append(f"*{name.replace('_', '*')}*{suffix}")
    return patterns


def find_artifact_candidates(
    artifact_type: str,
    artifact_name: str,
    extra_roots: Iterable[Path] | None = None,
    limit: int = 10,
) -> list[Path]:
    roots = get_search_roots()
    if extra_roots:
        for r in extra_roots:
            r = Path(r).expanduser().resolve()
            if r.exists() and r not in roots:
                roots.append(r)

    subdir = ARTIFACT_DIR_MAP.get(artifact_type, "")
    suffixes = ARTIFACT_SUFFIXES.get(artifact_type, (".xml", ".json"))

    found: list[Path] = []
    seen: set[Path] = set()

    for root in roots:
        candidates_bases = [root]
        if subdir and (root / subdir).exists():
            candidates_bases.insert(0, root / subdir)

        for base in candidates_bases:
            for pattern in _candidate_patterns(artifact_name, suffixes):
                for path in base.rglob(pattern):
                    resolved = path.resolve()
                    if resolved.is_file() and resolved not in seen:
                        seen.add(resolved)
                        found.append(resolved)
                        if len(found) >= limit:
                            return found

    return found