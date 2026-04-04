from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json

from tools.parse_dataflow_xml import parse_dataflow_xml



def write_normalized_dataflow(
    xml_path: str | Path,
    output_dir: str | Path = "normalized"
) -> Dict[str, Any]:
    """
    Parse an exported dataflow XML and write a normalized JSON version.
    """
    xml_path = Path(xml_path)

    parsed = parse_dataflow_xml(xml_path)

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    flow_name = parsed.get("name", "unnamed_dataflow")
    output_path = output_dir / f"{flow_name}.json"

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2, ensure_ascii=False, sort_keys=False)

    return {
        "flow_name": flow_name,
        "source_xml": str(xml_path),
        "output_json": str(output_path),
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) not in {2, 3}:
        print("Usage: python -m tools.normalize <dataflow-xml> [output-dir]")
        raise SystemExit(1)

    xml_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) == 3 else "normalized/dataflows"

    result = write_normalized_dataflow(xml_path, output_dir)
    print(json.dumps(result, indent=2))