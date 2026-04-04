from __future__ import annotations

from pathlib import Path
from typing import Any
import json


def _safe(value: Any) -> str:
    if value is None:
        return ""
    return str(value).replace("\n", " ").strip()


def _bullet_list(items: list[str]) -> list[str]:
    if not items:
        return ["- None"]
    return [f"- {item}" for item in items]


def _activity_detail_lines(act: dict) -> list[str]:
    lines: list[str] = []

    seq = _safe(act.get("sequence_number", ""))
    name = _safe(act.get("name", ""))
    typ = _safe(act.get("activity_type", ""))
    desc = _safe(act.get("description", ""))

    lines.append(f"### {seq}. {name}")
    lines.append("")
    lines.append(f"- **Type:** {typ}")

    if desc:
        lines.append(f"- **Description:** {desc}")

    if typ == "WORKFLOW" and act.get("workflow_name"):
        lines.append(f"- **Workflow Name:** {_safe(act.get('workflow_name'))}")

    if typ == "SCRIPTING" and act.get("script_name"):
        lines.append(f"- **Script Name:** {_safe(act.get('script_name'))}")

    if act.get("mapping_name"):
        lines.append(f"- **Mapping Name:** {_safe(act.get('mapping_name'))}")

    if typ == "APPLICATION" and act.get("connection_points"):
        lines.append(f"- **Connection Point(s):** {_safe(act.get('connection_points'))}")

    if typ == "ION_API" and act.get("ion_api_connection_point"):
        lines.append(f"- **ION API Connection Point:** {_safe(act.get('ion_api_connection_point'))}")

    if typ == "ION_API" and act.get("procedure_name"):
        lines.append(f"- **Procedure Name:** {_safe(act.get('procedure_name'))}")

    if typ == "ION_API" and act.get("intermediate") != "":
        lines.append(f"- **Intermediate:** {_safe(act.get('intermediate'))}")


    docs = act.get("documents", [])
    if docs:
        lines.append("- Documents:")
        for doc in docs:
            noun = _safe(doc.get("noun", ""))
            verb = _safe(doc.get("verb", ""))
            dtype = _safe(doc.get("document_type", ""))

            parts = []
            if noun:
                parts.append(f"Noun: {noun}")
            if verb:
                parts.append(f"Verb: {verb}")
            if dtype:
                parts.append(f"Type: {dtype}")

            if parts:
                lines.append(f"  - {' | '.join(parts)}")
            else:
                lines.append("  - None")
                

    if typ == "CBR_FILTER":
        df_nouns = act.get("df_nouns", [])
        if df_nouns:
            lines.append("- **Filter Details:**")
            for noun in df_nouns:
                noun_name = _safe(noun.get("name", ""))
                filter_expr = _safe(noun.get("filter", ""))
                doc_type = _safe(noun.get("document_type", ""))
                condition_data = _safe(noun.get("condition_data", ""))

                lines.append(f"  - **DF Noun:** {noun_name or '(unnamed)'}")
                if doc_type:
                    lines.append(f"    - Document Type: `{doc_type}`")
                if filter_expr:
                    lines.append(f"    - Filter: `{filter_expr}`")
                if condition_data:
                    lines.append(f"    - Condition Data: `{condition_data}`")

                attrs = noun.get("attributes", [])
                if attrs:
                    lines.append("    - Attributes:")
                    for attr in attrs:
                        lines.append(
                            f"      - `{_safe(attr.get('name'))}` "
                            f"(path: `{_safe(attr.get('path'))}`, type: `{_safe(attr.get('data_type'))}`)"
                        )

                verbs = noun.get("verbs", [])
                if verbs:
                    lines.append("    - Verbs:")
                    for verb in verbs:
                        lines.append(f"      - `{_safe(verb.get('verb_name'))}`")

    if typ == "WORKFLOW":
        noun_attrs = act.get("workflow_noun_attributes", [])
        if noun_attrs:
            lines.append("- **Workflow Noun Attributes:**")
            for attr in noun_attrs:
                lines.append(
                    f"  - `{_safe(attr.get('name'))}` "
                    f"(xpath: `{_safe(attr.get('xpath'))}`, type: `{_safe(attr.get('data_type'))}`)"
                )

    lines.append("")
    return lines


def generate_dataflow_doc(
    json_path: str | Path,
    output_dir: str | Path = "docs",
    workspace_dir: str | Path | None = None,
) -> dict:
    json_path = Path(json_path)

    with json_path.open(encoding="utf-8") as f:
        data = json.load(f)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    flow_name = _safe(data.get("name", json_path.stem))
    output_file = output_dir / f"{flow_name}.md"

    activities = data.get("activities", [])
    deps = data.get("dependencies", {})

    workflows = deps.get("workflows", [])
    connection_points = deps.get("connection_points", [])
    scripts = deps.get("scripts", [])
    mappings = deps.get("mappings", [])

    activity_types = sorted(
        { _safe(act.get("activity_type", "")) for act in activities if _safe(act.get("activity_type", "")) }
    )

    lines: list[str] = []

    # Title
    lines.append(f"# Dataflow: {flow_name}")
    lines.append("")

    if _safe(data.get("description")):
        lines.append(_safe(data.get("description")))
        lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append("| Property | Value |")
    lines.append("|---|---|")
    lines.append(f"| Type | {_safe(data.get('type'))} |")
    lines.append(f"| Last Updated By | {_safe(data.get('last_updated_by'))} |")
    lines.append(f"| Last Updated On | {_safe(data.get('last_updated_on'))} |")
    lines.append(f"| Protect On Export | {_safe(data.get('protect_on_export'))} |")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Activities | {len(activities)} |")
    lines.append(f"| External Workflows | {len(workflows)} |")
    lines.append(f"| Embedded Scripts Referenced | {len(scripts)} |")
    lines.append(f"| Embedded Mappings Referenced | {len(mappings)} |")
    lines.append(f"| Referenced Connection Points | {len(connection_points)} |")
    lines.append("")

    if activity_types:
        lines.append("**Activity Types Present**")
        lines.append("")
        lines.extend([f"- {t}" for t in activity_types])
        lines.append("")

    # Dependencies
    lines.append("## Dependencies")
    lines.append("")
    lines.append("### External Dependencies")
    lines.append("")
    lines.append("#### Workflows")
    lines.extend(_bullet_list(workflows))
    lines.append("")

    lines.append("### Embedded / Referenced in Export")
    lines.append("")
    lines.append("#### Connection Points")
    lines.extend(_bullet_list(connection_points))
    lines.append("")

    lines.append("#### Scripts")
    lines.extend(_bullet_list(scripts))
    lines.append("")

    lines.append("#### Mappings")
    lines.extend(_bullet_list(mappings))
    lines.append("")

    # Activity Table
    lines.append("## Activity Table")
    lines.append("")
    lines.append("| Seq | Name | Type | Key Reference |")
    lines.append("|---:|---|---|---|")

    for act in activities:
        seq = _safe(act.get("sequence_number", ""))
        name = _safe(act.get("name", ""))
        typ = _safe(act.get("activity_type", ""))

        key_ref = (
            _safe(act.get("workflow_name"))
            or _safe(act.get("script_name"))
            or _safe(act.get("mapping_name"))
            or _safe(act.get("connection_points"))
        )

        lines.append(f"| {seq} | {name} | {typ} | {key_ref} |")

    lines.append("")

    # Detailed Activities
    lines.append("## Activity Details")
    lines.append("")

    for act in activities:
        lines.extend(_activity_detail_lines(act))

    
    markdown_text = "\n".join(lines)
    with output_file.open("w", encoding="utf-8") as f:
        f.write(markdown_text)

    readme_path = None
    if workspace_dir is not None:
        workspace_dir = Path(workspace_dir)
        workspace_dir.mkdir(parents=True, exist_ok=True)

        readme_path = workspace_dir / "README.md"
        with readme_path.open("w", encoding="utf-8") as f:
            f.write(markdown_text)

    return {
        "flow_name": flow_name,
        "doc_path": str(output_file),
        "readme_path": str(readme_path) if readme_path else None,
    }


if __name__ == "__main__":
    import sys
    from pathlib import Path

    if len(sys.argv) not in {2, 3, 4}:
        print("Usage: python -m tools.docgen <normalized-json> [output-dir] [workspace-dir]")
        raise SystemExit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) >= 3 else "docs"
    workspace_dir = sys.argv[3] if len(sys.argv) == 4 else None

    result = generate_dataflow_doc(
        json_path=json_path,
        output_dir=output_dir,
        workspace_dir=workspace_dir,
    )
    print(result)