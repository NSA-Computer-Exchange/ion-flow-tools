from zzWorkspace.enrich import enrich_dataflow
from tools.normalize import normalize_dataflow
from zzWorkspace.docgen import generate_markdown
from zzWorkspace.exporters import save_readable_artifacts, save_deployable_artifacts
from zzWorkspace.reconstruct_xml import reconstruct_dataflow_xml


def main():

    flow_name = "Decode_AM_AuditEvent_Keys"

    enriched = enrich_dataflow(flow_name)

    normalized = normalize_dataflow(enriched)

    markdown_text = generate_markdown(normalized)

    readable_saved = save_readable_artifacts(normalized, enriched, markdown_text)

    reconstructed_xml = reconstruct_dataflow_xml(enriched).decode("utf-8")

    deploy_bundle = {
        "dataflow_xml": reconstructed_xml,
        "scripts": {},
        "connection_points": {},
        "mappings": {},
        "workflows": {},
        "activation_policies": {},
    }

    deploy_saved = save_deployable_artifacts(flow_name, deploy_bundle)

    print("\nReadable artifacts:")
    for path in readable_saved:
        print(path)

    print("\nDeployable artifacts:")
    for path in deploy_saved:
        print(path)


if __name__ == "__main__":
    main()
