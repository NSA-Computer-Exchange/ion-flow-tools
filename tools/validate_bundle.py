from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

from tools.parse_dataflow_xml import parse_dataflow_xml
from tools.bundle import build_bundle_manifest
from tools.workspace import (
    get_current_workspace,
    get_current_manifest,
    current_flow_xml_path,
    workspace_path,
)


def _artifact_names_by_type(manifest: Dict[str, Any], artifact_type: str) -> List[str]:
    return sorted(
        {
            a.get("name", "")
            for a in manifest.get("artifacts", [])
            if a.get("artifact_type") == artifact_type and a.get("name")
        }
    )


def validate_bundle(
    dataflow_xml: str | Path,
    exports_root: str | Path = "exports",
) -> Dict[str, Any]:
    parsed = parse_dataflow_xml(dataflow_xml)
    manifest = build_bundle_manifest(exports_root)

    available = {
        "workflows": _artifact_names_by_type(manifest, "workflow"),
        "connection_points": _artifact_names_by_type(manifest, "connection_point"),
        "scripts": _artifact_names_by_type(manifest, "script"),
        "mappings": _artifact_names_by_type(manifest, "mapping"),
    }

    referenced = parsed.get("dependencies", {})

    missing = {
        "workflows": sorted(set(referenced.get("workflows", [])) - set(available["workflows"])),
        "connection_points": [],
        "scripts": [],
        "mappings": [],
    }

    resolved = {
        "workflows": sorted(set(referenced.get("workflows", [])) & set(available["workflows"])),
        "connection_points": sorted(referenced.get("connection_points", [])),
        "scripts": sorted(referenced.get("scripts", [])),
        "mappings": sorted(referenced.get("mappings", [])),
    }

    return {
        "flow": parsed.get("name", ""),
        "referenced": referenced,
        "available": available,
        "resolved": resolved,
        "missing": missing,
    }


def validate_current_workspace_bundle() -> dict:
    current = get_current_workspace()
    manifest = get_current_manifest()
    flow_path = current_flow_xml_path()

    if not current or not manifest or not flow_path:
        raise ValueError("No current workspace is selected.")

    workspace_root = workspace_path(current)

    result = validate_bundle(
        dataflow_xml=flow_path,
        exports_root=workspace_root / "exports",
    )
    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) not in {2, 3}:
        print("Usage: python -m tools.validate_bundle <dataflow-xml> [exports-root]")
        raise SystemExit(1)

    dataflow_xml = sys.argv[1]
    exports_root = sys.argv[2] if len(sys.argv) == 3 else "exports"

    result = validate_bundle(dataflow_xml, exports_root)
    print(json.dumps(result, indent=4))