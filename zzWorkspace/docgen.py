from pathlib import Path
from zzWorkspace.diagram import generate_mermaid
import json

def _fmt_doc_mappings(step):
    mappings = step.get("documentMappings", [])
    if not mappings:
        return "None"

    lines = []
    for m in mappings:
        src = f"{m.get('inputDocument', '')} ({m.get('inputDocumentType', '')})"
        dst = f"{m.get('outputDocument', '')} ({m.get('outputDocumentType', '')})"
        lines.append(f"- {src} -> {dst}")
    return "\n".join(lines)


def _fmt_activity_docs(step):
    docs = step.get("activityDocuments", [])
    if not docs:
        return "None"

    lines = []
    for d in docs:
        noun = d.get("noun", "")
        verb = d.get("verb", "")
        dtype = d.get("documentType", "")
        label = f"{noun}"
        if verb:
            label = f"{verb}.{noun}"
        lines.append(f"- {label} [{dtype}]")
    return "\n".join(lines)


def _fmt_step(step, index):
    lines = [
        f"### {index}. {step.get('name', 'Unnamed Step')}",
        f"- Type: {step.get('type')}",
        f"- Activity Type: {step.get('activityType')}",
    ]

    if step.get("scriptName"):
        lines.append(f"- Script: `{step['scriptName']}`")

    if step.get("ionApiConnectionPoint"):
        lines.append(f"- ION API Connection Point: `{step['ionApiConnectionPoint']}`")

    if step.get("applicationConnectionPoints"):
        lines.append(f"- Application Connection Point: `{step['applicationConnectionPoints']}`")

    lines.append("- Documents:")
    lines.append(_fmt_activity_docs(step))

    lines.append("- Document Mappings:")
    lines.append(_fmt_doc_mappings(step))

    merge_mappings = step.get("mergeComponentMappings", [])
    if merge_mappings:
        lines.append("- Merge Mappings:")
        for mm in merge_mappings:
            attrs = mm.get("mergeComponentAttributes", [])
            for attr in attrs:
                lines.append(
                    f"  - {attr.get('name')} <- {attr.get('documentName')} {attr.get('path')}"
                )

    return "\n".join(lines)


def _extract_script_code(script_obj):
    """
    Supports either:
    - direct script API payload with scriptCode
    - wrapped shape if you later enrich/transform it
    """
    if not isinstance(script_obj, dict):
        return None

    if "scriptCode" in script_obj:
        return script_obj.get("scriptCode")

    decoded = script_obj.get("decoded")
    if isinstance(decoded, dict):
        return decoded.get("scriptCode")

    return None


def _summarize_script(script_name, script_code):
    """
    Lightweight heuristic summary for now.
    Later this can be replaced with AI-generated summaries.
    """
    if not script_code:
        return "No script source available."

    code_lower = script_code.lower()

    hints = []

    if "json.loads" in code_lower or "json.dumps" in code_lower:
        hints.append("parses or builds JSON")
    if "elementtree" in code_lower or "et.fromstring" in code_lower:
        hints.append("parses XML content")
    if "pid" in code_lower:
        hints.append("extracts or works with IDM document PIDs")
    if "emailmessage" in code_lower or '"to"' in code_lower or '"subject"' in code_lower:
        hints.append("builds an email request payload")
    if "items/search" in code_lower or "query" in code_lower:
        hints.append("prepares data for a search/query operation")
    if "orderby" in code_lower or "latest" in script_name.lower():
        hints.append("selects the latest matching result")

    if not hints:
        return "Custom transformation or orchestration logic."

    return "This script " + ", ".join(hints) + "."


def _fmt_script_section(script_name, script_obj):
    script_code = _extract_script_code(script_obj)
    summary = _summarize_script(script_name, script_code)

    lines = [
        f"### {script_name}",
        f"- Summary: {summary}",
    ]

    if script_code:
        lines.extend([
            "",
            "```python",
            script_code,
            "```",
        ])
    else:
        lines.append("- Source: Not available")

    return "\n".join(lines)


def generate_markdown(normalized: dict) -> str:

    md = []
    flow = normalized.get("flow", {})

    diagram = generate_mermaid(flow)

    md.append("## Flow Diagram\n")
    md.append(diagram)
    md.append("\n")


    name = normalized.get("name", "Unnamed Dataflow")
    description = normalized.get("description", "")
    status = normalized.get("status", "")
    updated_by = normalized.get("lastUpdatedBy", "")
    updated_on = normalized.get("lastUpdatedOn", "")

    scripts = normalized.get("dependencies", {}).get("scripts", [])
    cps = normalized.get("dependencies", {}).get("connection_points", [])
    steps = normalized.get("steps", [])
    artifacts = normalized.get("artifacts", {})
    script_artifacts = artifacts.get("scripts", {})

    parts = [
        f"# {name}",
        "",
        "## Overview",
        f"**Description:** {description}",
        f"**Status:** {status}",
        f"**Last Updated By:** {updated_by}",
        f"**Last Updated On:** {updated_on}",
        "",
        "## Dependencies",
        "### Scripts",
    ]

    if scripts:
        parts.extend([f"- `{s}`" for s in scripts])
    else:
        parts.append("- None")

    parts.extend([
        "",
        "### Connection Points",
    ])

    if cps:
        parts.extend([f"- `{cp}`" for cp in cps])
    else:
        parts.append("- None")

    parts.extend([
        "",
        "## Flow Steps",
        "",
    ])

    for i, step in enumerate(steps, start=1):
        parts.append(_fmt_step(step, i))
        parts.append("")

    parts.extend([
        "",
        "## Script Details",
        "",
    ])

    if scripts:
        for script_name in scripts:
            parts.append(_fmt_script_section(script_name, script_artifacts.get(script_name, {})))
            parts.append("")
    else:
        parts.append("No scripts referenced.")

    return "\n".join(parts)


def save_markdown(normalized: dict, output_dir="output"):
    flow_name = normalized.get("name", "UnnamedDataflow").replace(" ", "_")
    out_dir = Path(output_dir) / flow_name
    out_dir.mkdir(parents=True, exist_ok=True)

    md = generate_markdown(normalized)
    out_file = out_dir / f"{flow_name}.md"
    out_file.write_text(md, encoding="utf-8")

    return out_file


def save_script_files(normalized: dict, output_dir="output"):
    flow_name = normalized.get("name", "UnnamedDataflow").replace(" ", "_")
    out_dir = Path(output_dir) / flow_name / "scripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = normalized.get("artifacts", {})
    script_artifacts = artifacts.get("scripts", {})

    saved = []

    for script_name, script_obj in script_artifacts.items():
        script_code = _extract_script_code(script_obj)
        if script_code:
            file_name = script_name.replace(" ", "_") + ".py"
            out_file = out_dir / file_name
            out_file.write_text(script_code, encoding="utf-8")
            saved.append(out_file)

    return saved

def save_script_files(normalized: dict, output_dir="output"):
    flow_name = normalized.get("name", "UnnamedDataflow").replace(" ", "_")
    out_dir = Path(output_dir) / flow_name / "scripts"
    out_dir.mkdir(parents=True, exist_ok=True)

    artifacts = normalized.get("artifacts", {})
    script_artifacts = artifacts.get("scripts", {})

    saved = []

    for script_name, script_obj in script_artifacts.items():
        script_code = _extract_script_code(script_obj)
        if script_code:
            file_name = script_name.replace(" ", "_") + ".py"
            out_file = out_dir / file_name
            out_file.write_text(script_code, encoding="utf-8")
            saved.append(out_file)

    return saved


def save_json_artifacts(normalized: dict, output_dir="output"):
    flow_name = normalized.get("name", "UnnamedDataflow").replace(" ", "_")
    base_dir = Path(output_dir) / flow_name

    folders = {
        "connection_points": base_dir / "connection_points",
        "mappings": base_dir / "mappings",
        "workflows": base_dir / "workflows",
        "metadata": base_dir / "metadata",
    }

    for folder in folders.values():
        folder.mkdir(parents=True, exist_ok=True)

    artifacts = normalized.get("artifacts", {})
    saved = []

    for name, obj in artifacts.get("connection_points", {}).items():
        out_file = folders["connection_points"] / f"{name.replace(' ', '_')}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    for name, obj in artifacts.get("mappings", {}).items():
        out_file = folders["mappings"] / f"{name.replace(' ', '_')}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    for name, obj in artifacts.get("workflows", {}).items():
        out_file = folders["workflows"] / f"{name.replace(' ', '_')}.json"
        out_file.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        saved.append(out_file)

    dependencies_file = folders["metadata"] / "dependencies.json"
    dependencies_file.write_text(
        json.dumps(normalized.get("dependencies", {}), indent=2),
        encoding="utf-8"
    )
    saved.append(dependencies_file)

    return saved
