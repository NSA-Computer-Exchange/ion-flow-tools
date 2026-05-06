from __future__ import annotations

from pathlib import Path
import base64
import xml.etree.ElementTree as ET


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child(elem: ET.Element, name: str):
    for child in list(elem):
        if _local_name(child.tag) == name:
            return child
    return None


def _children(elem: ET.Element, name: str):
    return [child for child in list(elem) if _local_name(child.tag) == name]


def _safe_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def extract_embedded_artifacts(xml_path: str | Path, exports_root: str | Path) -> dict:
    xml_path = Path(xml_path)
    exports_root = Path(exports_root)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    result = {
        "connection_points": [],
        "scripts": [],
        "mappings_bundle_found": False,
    }

    # Scripts
    scripts_root = _child(root, "Scripts")
    if scripts_root is not None:
        for script in _children(scripts_root, "Script"):
            name = script.attrib.get("Name", "").strip()
            encoded = (script.text or "").strip()

            if not name or not encoded:
                continue

            try:
                decoded = base64.b64decode(encoded).decode("utf-8")
            except Exception:
                continue

            out_path = exports_root / "scripts" / f"{name}.json"
            _safe_write_text(out_path, decoded)
            result["scripts"].append(str(out_path))

    # Connection points
    cps_root = _child(root, "ConnectionPoints")
    if cps_root is not None:
        for cp in _children(cps_root, "ConnectionPoint"):
            name_elem = _child(cp, "Name")
            name = (name_elem.text or "").strip() if name_elem is not None and name_elem.text else ""
            if not name:
                continue

            cp_xml = ET.tostring(cp, encoding="unicode")
            out_path = exports_root / "connection_points" / f"{name}.xml"
            _safe_write_text(out_path, cp_xml)
            result["connection_points"].append(str(out_path))

    # Mappings exists
    mappings_root = _child(root, "Mappings")
    if mappings_root is not None:
        result["mappings_bundle_found"] = True

    return result
