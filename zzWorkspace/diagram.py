def generate_mermaid(normalized_flow):

    steps = normalized_flow.get("steps", [])

    lines = []
    lines.append("```mermaid")
    lines.append("flowchart TD")

    previous = None

    #for step in sorted(steps, key=lambda s: s["sequenceNumber"]):
    for i, step in enumerate(sorted(steps, key=lambda s: s["sequenceNumber"])):


        #node_id = f"step{step['sequenceNumber']}"
        node_id = f"step{i}"

        label = step.get("name", "unknown")

        lines.append(f'{node_id}["{label}"]')

        if previous:
            lines.append(f"{previous} --> {node_id}")

        previous = node_id

    lines.append("```")

    return "\n".join(lines)
