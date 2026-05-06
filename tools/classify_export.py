from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import xml.etree.ElementTree as ET


def _local_name(tag: str) -> str:
    """Strip namespace from an XML tag."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _safe_find_text(elem: ET.Element, child_name: str, default: str = "") -> str:
    """Find direct child by local name and return its text."""
    for child in list(elem):
        if _local_name(child.tag) == child_name:
            return (child.text or "").strip()
    return default


def _has_child(elem: ET.Element, child_name: str) -> bool:
    for child in list(elem):
        if _local_name(child.tag) == child_name:
            return True
    return False


def classify_export(xml_path: str | Path) -> Dict[str, Any]:
    """
    Inspect an exported ION XML file and classify its artifact type.

    Returns a normalized summary dict.
    """
    xml_path = Path(xml_path)

    tree = ET.parse(xml_path)
    root = tree.getroot()
    root_name = _local_name(root.tag)

    result: Dict[str, Any] = {
        "file_path": str(xml_path),
        "root_tag": root_name,
        "artifact_type": "unknown",
        "name": "",
    }

    # DocumentFlows wrapper can contain different artifact sets
    if root_name == "DocumentFlows":

        # Dataflow export
        if _has_child(root, "DocumentFlow"):
            docflow = None
            for child in list(root):
                if _local_name(child.tag) == "DocumentFlow":
                    docflow = child
                    break

            if docflow is not None:
                result["artifact_type"] = "dataflow"
                result["name"] = _safe_find_text(docflow, "Name")
                result["description"] = _safe_find_text(docflow, "Description")
                result["flow_type"] = _safe_find_text(docflow, "Type")
                result["last_updated_by"] = _safe_find_text(docflow, "LastUpdatedBy")
                result["last_updated_on"] = _safe_find_text(docflow, "LastUpdatedOn")
                return result

        # Connection point export
        if _has_child(root, "ConnectionPoints"):
            cps = None
            for child in list(root):
                if _local_name(child.tag) == "ConnectionPoints":
                    cps = child
                    break

            if cps is not None:
                cp = None
                for child in list(cps):
                    if _local_name(child.tag) == "ConnectionPoint":
                        cp = child
                        break

                result["artifact_type"] = "connection_point"
                if cp is not None:
                    result["name"] = _safe_find_text(cp, "Name")
                return result

        return result

    if root_name in {"Workflow", "Workflows", "WorkflowDefinitions"}:
        result["artifact_type"] = "workflow"

        if root_name == "Workflow":
            result["name"] = _safe_find_text(root, "Name")
            return result

        if root_name == "Workflows":
            wf = None
            for child in list(root):
                if _local_name(child.tag) == "Workflow":
                    wf = child
                    break
            if wf is not None:
                result["name"] = _safe_find_text(wf, "Name")
            return result

        if root_name == "WorkflowDefinitions":
            wf = None
            for child in list(root):
                if _local_name(child.tag) in {"WorkflowDefinition", "Workflow"}:
                    wf = child
                    break
            if wf is not None:
                result["name"] = _safe_find_text(wf, "Name")
            return result

    if root_name in {"ConnectionPoint", "ConnectionPoints"}:
        result["artifact_type"] = "connection_point"

        if root_name == "ConnectionPoint":
            result["name"] = _safe_find_text(root, "Name")
        else:
            cp = None
            for child in list(root):
                if _local_name(child.tag) == "ConnectionPoint":
                    cp = child
                    break
            if cp is not None:
                result["name"] = _safe_find_text(cp, "Name")

        return result

    if root_name in {"Mapping", "Mappings"}:
        result["artifact_type"] = "mapping"
        return result

    if root_name in {"Monitor", "Monitors"}:
        result["artifact_type"] = "monitor"
        return result

    if root_name in {"ActivationPolicy", "ActivationPolicies"}:
        result["artifact_type"] = "activation_policy"
        return result

    if root_name in {"Script", "Scripts"}:
        result["artifact_type"] = "script"
        return result

    return result

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m tools.classify_export <xml-file>")
        raise SystemExit(1)

    summary = classify_export(sys.argv[1])
    print(json.dumps(summary, indent=2))
