from zzWorkspace.ion_client import IONClient


def _walk_node(node, scripts, connection_points, mappings, workflows):
    """
    Recursively walk a dataflow JSON structure and collect dependency names.
    """
    if isinstance(node, dict):
        script_name = node.get("scriptName")
        if script_name:
            scripts.add(script_name)

        ion_cp = node.get("ionApiConnectionPoint")
        if ion_cp:
            connection_points.add(ion_cp)

        app_cp = node.get("applicationConnectionPoints")
        if app_cp:
            if isinstance(app_cp, str):
                connection_points.add(app_cp)
            elif isinstance(app_cp, list):
                for cp in app_cp:
                    if cp:
                        connection_points.add(cp)

        cp_names = node.get("connectionPointNames")
        if isinstance(cp_names, list):
            for cp in cp_names:
                if cp:
                    connection_points.add(cp)

        mapping_name = node.get("mappingName")
        if mapping_name:
            mappings.add(mapping_name)

        workflow_name = node.get("workflowName")
        if workflow_name:
            workflows.add(workflow_name)

        for value in node.values():
            _walk_node(value, scripts, connection_points, mappings, workflows)

    elif isinstance(node, list):
        for item in node:
            _walk_node(item, scripts, connection_points, mappings, workflows)
                   

def fetch_script(client, name):
    return client.get_json(f"/IONSERVICES/connect/model/v1/scripts/{name}")


def fetch_ionapi_cp(client, name):
    return client.get_raw(f"/IONSERVICES/connect/model/v1/connectionpoints/{name}")


def fetch_app_cp(client, name):
    return client.get_raw(f"/IONSERVICES/connect/model/v1/applicationconnectionpoints/{name}")


def _safe_get_json(client, endpoint):
    try:
        return client.get_json(endpoint)
    except Exception as exc:
        return {
            "error": str(exc),
            "endpoint": endpoint
        }


def list_dataflows():
    client = IONClient()
    return client.get_json("/IONSERVICES/connect/model/v1/dataflows")


def get_dataflow(flow_name: str):
    client = IONClient()
    return client.get_json(f"/IONSERVICES/connect/model/v1/dataflows/{flow_name}")


def enrich_dataflow(flow_name: str):

    client = IONClient()

    dataflow = client.get_json(
        f"/IONSERVICES/connect/model/v1/dataflows/{flow_name}"
    )

    script_names = set()
    connection_point_names = set()
    mappings = set()
    workflows = set()

    _walk_node(dataflow, script_names, connection_point_names, mappings, workflows)

    print("\nDiscovered Dependencies:")
    print("Scripts:", script_names)
    print("Connection Points:", connection_point_names)
    print("Mappings:", mappings)
    print("Workflows:", workflows)


    # -----------------------------
    # Fetch Scripts
    # -----------------------------

    script_artifacts = {}

    for script_name in sorted(script_names):
        script_artifacts[script_name] = _safe_get_json(
            client,
            f"/IONSERVICES/scriptingservice/model/v1/scripts/{script_name}"
        )

    # -----------------------------
    # Fetch Connection Points
    # -----------------------------

    connection_point_artifacts = {}

    for cp_name in sorted(connection_point_names):

        try:
            connection_point_artifacts[cp_name] = client.get_raw(
                f"/IONSERVICES/connect/model/v1/connectionpoints/{cp_name}"
            )

        except Exception:

            connection_point_artifacts[cp_name] = client.get_raw(
                f"/IONSERVICES/connect/model/v1/connectionpoints/{cp_name}"
            )

    # -----------------------------
    # Fetch Mappings
    # -----------------------------

    mapping_artifacts = {}

    for mapping_name in sorted(mappings):

        mapping_artifacts[mapping_name] = _safe_get_json(
            client,
            f"/IONSERVICES/connect/model/v1/mappings/{mapping_name}"
        )

    # -----------------------------
    # Fetch Workflows
    # -----------------------------

    workflow_artifacts = {}

    for workflow_name in sorted(workflows):

        workflow_artifacts[workflow_name] = _safe_get_json(
            client,
            f"/IONSERVICES/process/model/v1/workflows/{workflow_name}"
        )

    # -----------------------------
    # Final Object
    # -----------------------------

    enriched = {

        "dataflow": dataflow,

        "dependencies": {
            "scripts": sorted(script_names),
            "connection_points": sorted(connection_point_names),
            "mappings": sorted(mappings),
            "workflows": sorted(workflows),
        },

        "artifacts": {
            "scripts": script_artifacts,
            "connection_points": connection_point_artifacts,
            "mappings": mapping_artifacts,
            "workflows": workflow_artifacts,
        },
    }

    return enriched
