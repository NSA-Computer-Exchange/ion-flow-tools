def _walk_steps(node, steps, parent_path="root"):
    """
    Recursively flatten the flow into traversal order.
    """
    if isinstance(node, dict):
        node_type = node.get("_type")

        if node_type in {
            "applicationActivity",
            "scriptingActivity",
            "ionApiActivity",
            "mergeComponent",
            "mappingActivity",
            "workflowActivity",
        }:
            steps.append({
                "sequenceNumber": node.get("sequenceNumber"),
                "name": node.get("name"),
                "type": node_type,
                "activityType": node.get("activityType"),
                "scriptName": node.get("scriptName"),
                "mappingName": node.get("mappingName"),
                "workflowName": node.get("workflowName"),
                "ionApiConnectionPoint": node.get("ionApiConnectionPoint"),
                "applicationConnectionPoints": node.get("applicationConnectionPoints"),
                "documentMappings": node.get("documentMappings", []),
                "activityDocuments": node.get("activityDocuments", []),
                "mergeComponentMappings": node.get("mergeComponentMappings", []),
                "path": parent_path,
            })

        for key, value in node.items():
            _walk_steps(value, steps, f"{parent_path}.{key}")

    elif isinstance(node, list):
        for idx, item in enumerate(node):
            _walk_steps(item, steps, f"{parent_path}[{idx}]")


def normalize_dataflow(enriched: dict) -> dict:
    dataflow = enriched.get("dataflow", {})
    flow_part = dataflow.get("flowPart", {})

    steps = []
    _walk_steps(flow_part, steps)

    normalized = {
        "name": dataflow.get("name"),
        "description": dataflow.get("description"),
        "type": dataflow.get("type"),
        "status": dataflow.get("documentFlowStatus"),
        "lastUpdatedBy": dataflow.get("lastUpdatedBy"),
        "lastUpdatedOn": dataflow.get("lastUpdatedOn"),
        "lastActivatedOn": dataflow.get("lastActivatedOn"),
        "protectOnExport": dataflow.get("protectOnExport"),
        "runtimeProcessId": dataflow.get("runtimeProcessId"),
        "dependencies": enriched.get("dependencies", {}),
        "steps": steps,
        "artifacts": enriched.get("artifacts", {}),
    }

    return normalized
