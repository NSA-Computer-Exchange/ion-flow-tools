from pathlib import Path
import json


def _safe_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


def _extract_script_code(script_obj):
    if not isinstance(script_obj, dict):
        return None

    if script_obj.get("scriptCode"):
        return script_obj.get("scriptCode")

    decoded = script_obj.get("decoded")
    if isinstance(decoded, dict):
        return decoded.get("scriptCode")

    for key in ("script", "data", "content"):
        value = script_obj.get(key)
        if isinstance(value, dict) and value.get("scriptCode"):
            return value.get("scriptCode")

    return None


def save_readable_artifacts(normalized: dict, enriched: dict, markdown_text: str, output_dir="output"):
    flow_name = _safe_name(normalized.get("name", "UnnamedDataflow"))
    base = Path(output_dir) / flow_name / "readable"

    folders = {
        "root": base,
        "scripts": base / "scripts",
        "connection_points": base / "connection_points",
        "mappings": base / "mappings",
        "workflows": base / "workflows",
        "metadata": base / "metadata",
    }

    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    saved = []

    flow_json = folders["root"] / "flow.json"
    flow_json.write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    saved.append(flow_json)

    enriched_json = folders["root"] / "enriched.json"
    enriched_json.write_text(json.dumps(enriched, indent=2), encoding="utf-8")
    saved.append(enriched_json)

    md_file = folders["root"] / f"{flow_name}.md"
    md_file.write_text(markdown_text, encoding="utf-8")
    saved.append(md_file)

    dependencies_file = folders["metadata"] / "dependencies.json"
    dependencies_file.write_text(
        json.dumps(normalized.get("dependencies", {}), indent=2),
        encoding="utf-8"
    )
    saved.append(dependencies_file)

    artifacts = normalized.get("artifacts", {})

    for name, obj in artifacts.get("scripts", {}).items():
        code = _extract_script_code(obj)
        if code:
            out_file = folders["scripts"] / f"{_safe_name(name)}.py"
            out_file.write_text(code, encoding="utf-8")
            saved.append(out_file)

    for name, obj in artifacts.get("connection_points", {}).items():
        out_file = folders["connection_points"] / f"{_safe_name(name)}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    for name, obj in artifacts.get("mappings", {}).items():
        out_file = folders["mappings"] / f"{_safe_name(name)}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    for name, obj in artifacts.get("workflows", {}).items():
        out_file = folders["workflows"] / f"{_safe_name(name)}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    return saved


def save_deployable_artifacts(flow_name: str, deploy_bundle: dict, output_dir="output"):
    safe_flow = _safe_name(flow_name)
    base = Path(output_dir) / safe_flow / "deploy"

    folders = {
        "dataflow": base / "dataflow",
        "scripts": base / "scripts",
        "connection_points": base / "connection_points",
        "mappings": base / "mappings",
        "workflows": base / "workflows",
        "activation_policies": base / "activation_policies",
    }

    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    saved = []

    dataflow_xml = deploy_bundle.get("dataflow_xml")
    if dataflow_xml:
        out_file = folders["dataflow"] / f"{safe_flow}.xml"
        out_file.write_text(dataflow_xml, encoding="utf-8")
        saved.append(out_file)

    for name, content in deploy_bundle.get("scripts", {}).items():
        out_file = folders["scripts"] / f"{_safe_name(name)}.json"
        if isinstance(content, str):
            out_file.write_text(content, encoding="utf-8")
        else:
            out_file.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
        saved.append(out_file)

    for name, content in deploy_bundle.get("connection_points", {}).items():
        out_file = folders["connection_points"] / f"{_safe_name(name)}.xml"
        out_file.write_text(content, encoding="utf-8")
        saved.append(out_file)

    for name, content in deploy_bundle.get("mappings", {}).items():
        out_file = folders["mappings"] / f"{_safe_name(name)}.xml"
        out_file.write_text(content, encoding="utf-8")
        saved.append(out_file)

    for name, content in deploy_bundle.get("workflows", {}).items():
        out_file = folders["workflows"] / f"{_safe_name(name)}.xml"
        out_file.write_text(content, encoding="utf-8")
        saved.append(out_file)

    for name, content in deploy_bundle.get("activation_policies", {}).items():
        out_file = folders["activation_policies"] / f"{_safe_name(name)}.xml"
        out_file.write_text(content, encoding="utf-8")
        saved.append(out_file)

    manifest = {
        "flow": flow_name,
        "deployable": {
            "dataflow_xml": bool(deploy_bundle.get("dataflow_xml")),
            "scripts": sorted(list(deploy_bundle.get("scripts", {}).keys())),
            "connection_points": sorted(list(deploy_bundle.get("connection_points", {}).keys())),
            "mappings": sorted(list(deploy_bundle.get("mappings", {}).keys())),
            "workflows": sorted(list(deploy_bundle.get("workflows", {}).keys())),
            "activation_policies": sorted(list(deploy_bundle.get("activation_policies", {}).keys())),
        },
    }

    manifest_file = base / "manifest.json"
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    saved.append(manifest_file)

    return saved
