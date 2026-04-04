from pathlib import Path
import base64
import json
import xml.etree.ElementTree as ET


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _find_first(root, local_name: str):
    for elem in root.iter():
        if _local_name(elem.tag) == local_name:
            return elem
    return None


def _find_all(root, local_name: str):
    found = []
    for elem in root.iter():
        if _local_name(elem.tag) == local_name:
            found.append(elem)
    return found


def _to_xml_string(elem) -> str:
    return ET.tostring(elem, encoding="unicode")


def _wrap_xml(root_tag: str, inner_xml: str) -> str:
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<{root_tag}>\n{inner_xml}\n</{root_tag}>\n'


def _safe_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


def _decode_script_payload(encoded_text: str):
    """
    Scripts in native export XML are base64-encoded JSON.
    Return both decoded JSON object and pretty JSON text.
    """
    decoded = base64.b64decode(encoded_text).decode("utf-8")
    obj = json.loads(decoded)
    pretty = json.dumps(obj, indent=2, ensure_ascii=False)
    return obj, pretty


def build_deploy_bundle_from_export_xml(xml_path: str) -> dict:
    """
    Build a deploy bundle from a native ION dataflow export XML.

    Returns:
    {
      "flow_name": "...",
      "dataflow_xml": "...",              # full original export file
      "scripts": {name: json_obj},
      "connection_points": {name: xml_string},
      "mappings": {},
      "workflows": {},
      "activation_policies": {}
    }
    """
    xml_file = Path(xml_path)
    raw_xml = xml_file.read_text(encoding="utf-8")

    root = ET.fromstring(raw_xml)

    # Flow name
    flow_name = "UnnamedDataflow"
    docflow = _find_first(root, "DocumentFlow")
    if docflow is not None:
        name_elem = _find_first(docflow, "Name")
        if name_elem is not None and name_elem.text:
            flow_name = name_elem.text.strip()

    bundle = {
        "flow_name": flow_name,
        "dataflow_xml": raw_xml,
        "scripts": {},
        "connection_points": {},
        "mappings": {},
        "workflows": {},
        "activation_policies": {},
    }

    # Scripts
    scripts_parent = _find_first(root, "Scripts")
    if scripts_parent is not None:
        for script_elem in list(scripts_parent):
            if _local_name(script_elem.tag) != "Script":
                continue

            script_name = script_elem.attrib.get("Name", "UnnamedScript")
            encoded_text = (script_elem.text or "").strip()
            if not encoded_text:
                continue

            try:
                script_obj, _pretty_json = _decode_script_payload(encoded_text)
                bundle["scripts"][script_name] = script_obj
            except Exception as exc:
                bundle["scripts"][script_name] = {
                    "error": f"Unable to decode script export: {exc}",
                    "raw": encoded_text
                }

    # Connection Points
    cps_parent = _find_first(root, "ConnectionPoints")
    if cps_parent is not None:
        for cp_elem in list(cps_parent):
            if _local_name(cp_elem.tag) != "ConnectionPoint":
                continue

            name_elem = _find_first(cp_elem, "Name")
            cp_name = name_elem.text.strip() if name_elem is not None and name_elem.text else "UnnamedConnectionPoint"

            # Save each CP wrapped in its own ConnectionPoints root
            cp_xml = _wrap_xml("ConnectionPoints", _to_xml_string(cp_elem))
            bundle["connection_points"][cp_name] = cp_xml

    # Optional future sections if present in export XML
    # Mapping(s)
    mappings_parent = _find_first(root, "Mappings")
    if mappings_parent is not None:
        for map_elem in list(mappings_parent):
            if _local_name(map_elem.tag) != "Mapping":
                continue

            name_elem = _find_first(map_elem, "Name")
            map_name = name_elem.text.strip() if name_elem is not None and name_elem.text else "UnnamedMapping"
            map_xml = _wrap_xml("Mappings", _to_xml_string(map_elem))
            bundle["mappings"][map_name] = map_xml

    # Workflow(s)
    workflows_parent = _find_first(root, "Workflows")
    if workflows_parent is not None:
        for wf_elem in list(workflows_parent):
            if _local_name(wf_elem.tag) != "Workflow":
                continue

            name_elem = _find_first(wf_elem, "Name")
            wf_name = name_elem.text.strip() if name_elem is not None and name_elem.text else "UnnamedWorkflow"
            wf_xml = _wrap_xml("Workflows", _to_xml_string(wf_elem))
            bundle["workflows"][wf_name] = wf_xml

    # Activation Policies
    aps_parent = _find_first(root, "ActivationPolicies")
    if aps_parent is not None:
        for ap_elem in list(aps_parent):
            if _local_name(ap_elem.tag) != "ActivationPolicy":
                continue

            name_elem = _find_first(ap_elem, "Name")
            ap_name = name_elem.text.strip() if name_elem is not None and name_elem.text else "UnnamedActivationPolicy"
            ap_xml = _wrap_xml("ActivationPolicies", _to_xml_string(ap_elem))
            bundle["activation_policies"][ap_name] = ap_xml

    return bundle

def build_deploy_bundle_from_xml_string(xml_string):

    root = ET.fromstring(xml_string)

    bundle = {
        "dataflow_xml": xml_string,
        "scripts": {},
        "connection_points": {},
        "mappings": {},
        "workflows": {},
        "activation_policies": {},
    }

    # same parsing logic as before

    return bundle
