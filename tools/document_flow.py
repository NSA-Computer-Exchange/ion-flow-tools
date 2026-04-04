from __future__ import annotations

from pathlib import Path
import json

from tools.normalize import write_normalized_dataflow
from tools.docgen import generate_dataflow_doc
from tools.diagram import generate_flow_diagram
from tools.pdf_export import export_markdown_to_pdf
from tools.idm_upload import upload_file_to_idm
from tools.ai_docgen import generate_ai_doc_from_json, append_ai_to_markdown_file



def document_flow(
    xml_path: str | Path,
    workspace_dir: str | Path | None = None,
    normalized_dir: str | Path = "normalized",
    docs_dir: str | Path = "docs",
    diagrams_dir: str | Path = "diagrams",
    generate_pdf: bool = False,
    upload_idm: bool = False,
    use_ai: bool = False,
    ai_provider: str = "openai",
) -> dict:
    
    if upload_idm and not generate_pdf:
        raise ValueError("upload_idm=True requires generate_pdf=True")
    
    # if use_ai:
    #     print("AI documentation not implemented yet.")


    xml_path = Path(xml_path)
    normalized_dir = Path(normalized_dir)
    docs_dir = Path(docs_dir)
    diagrams_dir = Path(diagrams_dir)

    normalized_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    diagrams_dir.mkdir(parents=True, exist_ok=True)

    print("Parsing and normalizing dataflow...")
    norm = write_normalized_dataflow(xml_path, output_dir=normalized_dir)

    json_path = Path(norm["output_json"])

    print("Generating documentation...")
    doc = generate_dataflow_doc(json_path, output_dir=docs_dir, workspace_dir=workspace_dir)

    ai_generated = False
    if use_ai:
        print("Generating AI documentation...")
        ai_markdown = generate_ai_doc_from_json(
            json_path,
            provider=ai_provider,
        )

        append_ai_to_markdown_file(doc["doc_path"], ai_markdown)

        if doc.get("readme_path"):
            append_ai_to_markdown_file(doc["readme_path"], ai_markdown)

        ai_generated = True

    print("Generating diagram...")
    diagram = generate_flow_diagram(json_path, output_dir=diagrams_dir)

    result = {
        "flow_name": norm["flow_name"],
        "normalized_path": str(json_path),
        "doc_path": doc["doc_path"],
        "readme_path": doc.get("readme_path"),
        "diagram_path": diagram["diagram_path"],
        "ai_generated": ai_generated,
    }

    if generate_pdf:
        print("Generating PDF...")
        pdf_path = docs_dir / f"{Path(doc['doc_path']).stem}.pdf"
        pdf = export_markdown_to_pdf(doc["doc_path"], pdf_path)
        result["pdf_path"] = str(pdf)

        if upload_idm:
            print("Uploading PDF to IDM...")
            try:
                upload_result = upload_file_to_idm(
                    file_path=pdf,
                    attr_name=norm["flow_name"],
                    attr_type="Dataflow",
                    acl="Public",
                    entity_name="IONFlowDocumentation",
                )
                result["idm_upload"] = upload_result
            except Exception as exc:
                result["idm_upload"] = {
                    "success": False,
                    "error": str(exc),
                }

    return result

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m tools.document_flow <dataflow-xml> "
            "[--normalized-dir <path>] [--docs-dir <path>] [--diagrams-dir <path>] "
            "[--pdf] [--upload-idm] [--ai]"
        )
        raise SystemExit(1)

    xml_path = sys.argv[1]
    if xml_path.startswith("--"):
        print(
            "Usage: python -m tools.document_flow <dataflow-xml> "
            "[--normalized-dir <path>] [--docs-dir <path>] [--diagrams-dir <path>] "
            "[--pdf] [--upload-idm] [--ai]"
        )
        raise SystemExit(1)

    flags = set(arg for arg in sys.argv[2:] if arg.startswith("--"))

    valid_flags = {
    "--pdf",
    "--upload-idm",
    "--ai",
    "--normalized-dir",
    "--docs-dir",
    "--diagrams-dir",
    "--workspace-dir",
    "--ai-provider",
    }

    invalid_flags = [flag for flag in flags if flag not in valid_flags]
    if invalid_flags:
        print(f"Unknown option(s): {', '.join(invalid_flags)}")
        raise SystemExit(1)

    def get_option_value(name: str, default: str):
        if name in sys.argv:
            idx = sys.argv.index(name)
            if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
                print(f"Error: {name} requires a path value")
                raise SystemExit(1)
            return sys.argv[idx + 1]
        return default

    normalized_dir = get_option_value("--normalized-dir", "normalized")
    docs_dir = get_option_value("--docs-dir", "docs")
    diagrams_dir = get_option_value("--diagrams-dir", "diagrams")
    workspace_dir = get_option_value("--workspace-dir", None)
    ai_provider = get_option_value("--ai-provider", "openai")

    generate_pdf = "--pdf" in sys.argv
    upload_idm = "--upload-idm" in sys.argv
    use_ai = "--ai" in sys.argv

    if upload_idm and not generate_pdf:
        print("Error: --upload-idm requires --pdf")
        raise SystemExit(1)

    result = document_flow(
    xml_path,
    workspace_dir=workspace_dir,
    normalized_dir=normalized_dir,
    docs_dir=docs_dir,
    diagrams_dir=diagrams_dir,
    generate_pdf=generate_pdf,
    upload_idm=upload_idm,
    use_ai=use_ai,
    ai_provider=ai_provider,
  )

    print(json.dumps(result, indent=2))