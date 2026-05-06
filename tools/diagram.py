from __future__ import annotations

from pathlib import Path
import json
import re
from html import escape


CLASS_MAP = {
    "APPLICATION": "app",
    "WORKFLOW": "workflow",
    "CBR_FILTER": "filter",
    "ION_API": "api",
    "SCRIPTING": "script",
}

def _safe_mermaid_id(value: str) -> str:
    """
    Mermaid node IDs should be simple alphanumeric-ish tokens.
    """
    value = re.sub(r"[^A-Za-z0-9_]", "_", value)
    if not value:
        value = "node"
    if value[0].isdigit():
        value = f"N_{value}"
    return value


def _clean_text(value: object) -> str:
    if value is None:
        return ""
    return escape(str(value).strip())


def _activity_label(act: dict) -> str:
    activity_type = act.get("activity_type", "")
    name = _clean_text(act.get("name", "")) or activity_type or "Activity"

    if activity_type == "APPLICATION":
        cp = _clean_text(act.get("connection_points", ""))
        return f"{name}<br/>App<br/>{cp}" if cp else f"{name}<br/>App"

    if activity_type == "ION_API":
        cp = _clean_text(act.get("ion_api_connection_point", ""))
        return f"{name}<br/>API<br/>{cp}" if cp else f"{name}<br/>API"

    if activity_type == "WORKFLOW":
        wf = _clean_text(act.get("workflow_name", ""))
        return f"{name}<br/>Workflow<br/>{wf}" if wf and wf != name else f"{name}<br/>Workflow"

    if activity_type == "SCRIPTING":
        script = _clean_text(act.get("script_name", ""))
        return f"{name}<br/>Script<br/>{script}" if script and script != name else f"{name}<br/>Script"

    if activity_type == "CBR_FILTER":
        filter_name = _clean_text(act.get("filter_name", ""))
        return f"{name}<br/>Filter<br/>{filter_name}" if filter_name and filter_name != name else f"{name}<br/>Filter"

    return f"{name}<br/>{_clean_text(activity_type)}"


def _node_line(node_id: str, label: str, activity_type: str) -> str:
    """
    Mermaid shapes:
    [text]   rectangle
    (text)   rounded
    ([text]) stadium/capsule
    [[text]] subroutine/double border
    {text}   diamond
    [/text/] parallelogram-ish
    """

    if activity_type == "APPLICATION":
        return f'        {node_id}(["{label}"])'

    if activity_type == "WORKFLOW":
        return f'        {node_id}[["{label}"]]'

    if activity_type == "CBR_FILTER":
        return f'        {node_id}{{"{label}"}}'

    if activity_type == "ION_API":
        return f'        {node_id}[("{label}")]'

    if activity_type == "SCRIPTING":
        return f'        {node_id}[/"{label}"/]'

    return f'        {node_id}["{label}"]'


def _node_class(activity_type: str) -> str:
    return CLASS_MAP.get(activity_type, "default")


def _edge_label(act: dict) -> str:
    """
    Optional short edge labels for filters.
    Keep this light; docs should hold the detail.
    """
    if act.get("activity_type") != "CBR_FILTER":
        return ""

    
    return "next"


def _render_classdefs() -> list[str]:
    return [
        "    classDef app fill:#E3F2FD,stroke:#1565C0,stroke-width:1.5px;",
        "    classDef workflow fill:#FFF3E0,stroke:#EF6C00,stroke-width:1.5px;",
        "    classDef filter fill:#FCE4EC,stroke:#AD1457,stroke-width:1.5px;",
        "    classDef api fill:#E8F5E9,stroke:#2E7D32,stroke-width:1.5px;",
        "    classDef script fill:#F3E5F5,stroke:#6A1B9A,stroke-width:1.5px;",
        "    classDef default fill:#F5F5F5,stroke:#616161,stroke-width:1px;",
    ]


def _normalize_activities(data: dict) -> list[dict]:
    activities = sorted(
        data.get("activities", []),
        key=lambda x: int(x.get("sequence_number", 0))
    )

    normalized = []
    for act in activities:
        seq = str(act.get("sequence_number", "0"))
        node_id = _safe_mermaid_id(f"A{seq}")
        label = _activity_label(act)
        activity_type = act.get("activity_type", "")
        normalized.append(
            {
                "raw": act,
                "sequence_number": seq,
                "node_id": node_id,
                "label": label,
                "activity_type": activity_type,
                "class_name": _node_class(activity_type),
            }
        )
    return normalized


def generate_flow_diagram(json_path: str | Path, output_dir: str | Path = "diagrams") -> dict:
    json_path = Path(json_path)

    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    flow_name = data.get("name", json_path.stem)
    safe_flow_name = _clean_text(flow_name)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{flow_name}.mmd"
    activities = _normalize_activities(data)

    lines: list[str] = []
    lines.append("flowchart LR")
    lines.append(f'    subgraph {_safe_mermaid_id(flow_name)}["{safe_flow_name}"]')

    for act in activities:
        lines.append(_node_line(act["node_id"], act["label"], act["activity_type"]))

    lines.append("")

    for i in range(len(activities) - 1):
        current = activities[i]
        nxt = activities[i + 1]
        edge_label = _edge_label(current["raw"])

        if edge_label:
            lines.append(f'        {current["node_id"]} -->|"{edge_label}"| {nxt["node_id"]}')
        else:
            lines.append(f'        {current["node_id"]} --> {nxt["node_id"]}')

    lines.append("    end")
    lines.append("")

    lines.extend(_render_classdefs())
    lines.append("")

    for act in activities:
        lines.append(f'    class {act["node_id"]} {act["class_name"]};')

    with output_file.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {
        "flow_name": flow_name,
        "diagram_path": str(output_file),
        "activity_count": len(activities),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m tools.diagram <normalized-json>")
        raise SystemExit(1)

    result = generate_flow_diagram(sys.argv[1])
    print(result)
