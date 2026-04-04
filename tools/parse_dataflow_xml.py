from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import xml.etree.ElementTree as ET


def _local_name(tag: str) -> str:
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child(elem: ET.Element, name: str) -> Optional[ET.Element]:
    for child in list(elem):
        if _local_name(child.tag) == name:
            return child
    return None


def _children(elem: ET.Element, name: str) -> List[ET.Element]:
    return [child for child in list(elem) if _local_name(child.tag) == name]


def _text(elem: Optional[ET.Element], name: str, default: str = "") -> str:
    if elem is None:
        return default
    child = _child(elem, name)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _first_text(elem: Optional[ET.Element], names: List[str], default: str = "") -> str:
    if elem is None:
        return default
    for name in names:
        value = _text(elem, name, "")
        if value:
            return value
    return default


def _parse_activity_documents(activity_elem: ET.Element) -> List[Dict[str, str]]:
    docs_root = _child(activity_elem, "ActivityDocuments")
    if docs_root is None:
        return []

    docs: List[Dict[str, str]] = []
    for doc in _children(docs_root, "ActivityDocument"):
        docs.append(
            {
                "noun": _text(doc, "Noun"),
                "verb": _text(doc, "Verb"),
                "document_type": _text(doc, "DocumentType"),
            }
        )
    return docs

def _parse_file_details(activity_elem: ET.Element) -> Dict[str, Any]:
    """
    Defensive parser for file-related activities.
    Different exports may use slightly different element names.
    """
    file_elem = (
        _child(activity_elem, "FileActivity")
        or _child(activity_elem, "FileConnectorActivity")
        or _child(activity_elem, "FileConnectionPointActivity")
    )

    source = file_elem if file_elem is not None else activity_elem

    connection_point = _first_text(
        source,
        [
            "ConnectionPoint",
            "ConnectionPoints",
            "FileConnectionPoint",
            "FileConnectionPoints",
            "FileConnectorPoint",
        ],
        "",
    )

    directory = _first_text(
        source,
        [
            "Directory",
            "Folder",
            "Path",
        ],
        "",
    )

    file_name = _first_text(
        source,
        [
            "FileName",
            "Name",
            "Pattern",
        ],
        "",
    )

    result: Dict[str, Any] = {}
    if connection_point:
        result["file_connection_point"] = connection_point
    if directory:
        result["file_directory"] = directory
    if file_name:
        result["file_name"] = file_name

    return result

def _find_first_descendant(elem: ET.Element, name: str) -> Optional[ET.Element]:
    for child in elem.iter():
        if _local_name(child.tag) == name:
            return child
    return None


def _parse_workflow_details(activity_elem: ET.Element) -> Dict[str, Any]:
    wf = _child(activity_elem, "WorkflowActivity")
    if wf is None:
        wf = _find_first_descendant(activity_elem, "WorkflowActivity")
    if wf is None:
        return {}

    attrs_root = _child(wf, "WorkflowNounAttributes")
    noun_attributes: List[Dict[str, Any]] = []

    if attrs_root is not None:
        for attr in _children(attrs_root, "WorkflowNounAttribute"):
            input_root = _child(attr, "WorkflowAttributeInputMappings")
            output_root = _child(attr, "WorkflowAttributeOutputMappings")

            input_mappings = []
            output_mappings = []

            if input_root is not None:
                for m in _children(input_root, "WorkflowAttributeMapping"):
                    input_mappings.append(
                        {
                            "parameter_name": _text(m, "ParameterName"),
                            "workflow_parameter_type": _text(m, "WorkflowParameterType"),
                            "workflow_parameter_data_type": _text(m, "WorkflowParameterDataType"),
                        }
                    )

            if output_root is not None:
                for m in _children(output_root, "WorkflowAttributeMapping"):
                    output_mappings.append(
                        {
                            "parameter_name": _text(m, "ParameterName"),
                            "workflow_parameter_type": _text(m, "WorkflowParameterType"),
                            "workflow_parameter_data_type": _text(m, "WorkflowParameterDataType"),
                        }
                    )

            noun_attributes.append(
                {
                    "name": _text(attr, "Name"),
                    "xpath": _text(attr, "Xpath"),
                    "parent_path_for_filtering": _text(attr, "ParentPathForFiltering"),
                    "data_type": _text(attr, "DataType"),
                    "input_mappings": input_mappings,
                    "output_mappings": output_mappings,
                }
            )

    workflow_name = _text(wf, "WorkflowName")
    if not workflow_name:
        workflow_name_elem = _find_first_descendant(wf, "WorkflowName")
        if workflow_name_elem is not None and workflow_name_elem.text:
            workflow_name = workflow_name_elem.text.strip()

    return {
        "workflow_name": workflow_name,
        "workflow_noun_attributes": noun_attributes,
    }


def _parse_mapping_details(activity_elem: ET.Element) -> Dict[str, Any]:
    """
    Defensive mapping parser.
    Supports simple <Mapping>...</Mapping> as well as nested mapping activity shapes.
    """
    direct_mapping = _text(activity_elem, "Mapping")
    if direct_mapping:
        return {
            "mapping_name": direct_mapping,
        }

    mapping_elem = (
        _child(activity_elem, "MappingActivity")
        or _child(activity_elem, "MapperActivity")
        or _child(activity_elem, "TransformationActivity")
    )

    if mapping_elem is None:
        return {}

    mapping_name = _first_text(
        mapping_elem,
        [
            "MappingName",
            "MapperName",
            "TransformationName",
            "MapName",
            "Name",
        ],
        "",
    )

    return {
        "mapping_name": mapping_name,
    }


def _parse_filter_details(activity_elem: ET.Element) -> Dict[str, Any]:
    dfnouns = _child(activity_elem, "DFNouns")
    if dfnouns is None:
        return {}

    nouns: List[Dict[str, Any]] = []

    for noun in _children(dfnouns, "DFNoun"):
        attrs_root = _child(noun, "Attributes")
        verbs_root = _child(noun, "Verbs")

        attributes = []
        verbs = []

        if attrs_root is not None:
            for attr in _children(attrs_root, "DFAttribute"):
                attributes.append(
                    {
                        "name": _text(attr, "Name"),
                        "path": _text(attr, "Path"),
                        "parent_path_for_filtering": _text(attr, "ParentPathForFiltering"),
                        "data_type": _text(attr, "DataType"),
                    }
                )

        if verbs_root is not None:
            for verb in _children(verbs_root, "DFVerb"):
                verbs.append(
                    {
                        "verb_name": _text(verb, "VerbName"),
                    }
                )

        nouns.append(
            {
                "name": _text(noun, "Name"),
                "filter": _text(noun, "Filter"),
                "document_type": _text(noun, "DocumentType"),
                "condition_data": _text(noun, "ConditionData"),
                "attributes": attributes,
                "verbs": verbs,
            }
        )

    return {
        "df_nouns": nouns,
    }


def _parse_activity(activity_elem: ET.Element) -> Dict[str, Any]:
    activity_type = _text(activity_elem, "ActivityType")

    activity: Dict[str, Any] = {
        "sequence_number": _text(activity_elem, "SequenceNumber"),
        "name": _text(activity_elem, "Name"),
        "description": _text(activity_elem, "Description"),
        "activity_type": activity_type,
        "documents": _parse_activity_documents(activity_elem),
    }

    if activity_type == "APPLICATION":
        activity["connection_points"] = _text(activity_elem, "ConnectionPoints")

    elif activity_type == "ION_API":
        activity["ion_api_connection_point"] = _text(activity_elem, "IonApiConnectionPoint")
        activity["procedure_name"] = _text(activity_elem, "ProcedureName")
        activity["intermediate"] = _text(activity_elem, "Intermediate")

        if activity["ion_api_connection_point"]:
            activity["connection_points"] = activity["ion_api_connection_point"]

    elif activity_type in {"FILE", "FILE_ACTIVITY", "FILE_CONNECTION", "FILE_CONNECTOR"}:
        file_details = _parse_file_details(activity_elem)
        activity.update(file_details)
        if file_details.get("file_connection_point"):
            activity["connection_points"] = file_details["file_connection_point"]

    elif activity_type == "WORKFLOW":
        activity.update(_parse_workflow_details(activity_elem))

    elif activity_type == "CBR_FILTER":
        activity.update(_parse_filter_details(activity_elem))

    elif activity_type == "SCRIPTING":
        scripting = _child(activity_elem, "ScriptingActivity")
        if scripting is not None:
            activity["script_name"] = _text(scripting, "ScriptName")

    elif activity_type in {"XML_MAPPER", "MAPPING", "MAPPER", "TRANSFORMATION"}:
        activity.update(_parse_mapping_details(activity_elem))

    # elif activity_type in {"FILE", "FILE_ACTIVITY", "FILE_CONNECTION", "FILE_CONNECTOR"}:
    #     activity.update(_parse_file_details(activity_elem))

    else:
        file_details = _parse_file_details(activity_elem)
        if file_details:
            activity.update(file_details)

        mapping_details = _parse_mapping_details(activity_elem)
        if mapping_details:
            activity.update(mapping_details)

    return activity


def _walk_flow_parts(flow_part_elem: ET.Element, results: List[Dict[str, Any]]) -> None:
    """
    Recursively walk a FlowPart and collect all activities, even when nested
    inside wrapper/container nodes such as FlowPartContainer, RoutingContainer,
    MergeComponent, or other intermediate XML shapes.
    """

    def _walk_node(node: ET.Element) -> None:
        node_name = _local_name(node.tag)

        if node_name == "FlowPart":
            for child in list(node):
                _walk_node(child)
            return

        if node_name == "Activity":
            results.append(_parse_activity(node))
            return

        if node_name == "MergeComponent":
            results.append(
                {
                    "node_type": "MERGE_COMPONENT",
                    "sequence_number": _text(node, "SequenceNumber"),
                    "name": _text(node, "Name"),
                }
            )
            for child in list(node):
                _walk_node(child)
            return

        # [DEBUG] Generic recursive descent through any container/wrapper node.
        # This is what allows us to survive RoutingContainer,
        # FlowPartContainer, nested FlowParts, etc.
        for child in list(node):
            _walk_node(child)

    _walk_node(flow_part_elem)


def parse_dataflow_xml(xml_path: str | Path) -> Dict[str, Any]:
    xml_path = Path(xml_path)

    tree = ET.parse(xml_path)
    root = tree.getroot()

    if _local_name(root.tag) != "DocumentFlows":
        raise ValueError(f"Expected DocumentFlows root, got {_local_name(root.tag)}")

    docflow = _child(root, "DocumentFlow")
    if docflow is None:
        raise ValueError("DocumentFlow element not found")

    result: Dict[str, Any] = {
        "file_path": str(xml_path),
        "name": _text(docflow, "Name"),
        "description": _text(docflow, "Description"),
        "type": _text(docflow, "Type"),
        "last_updated_by": _text(docflow, "LastUpdatedBy"),
        "last_updated_on": _text(docflow, "LastUpdatedOn"),
        "protect_on_export": _text(docflow, "ProtectOnExport"),
        "activities": [],
    }

    flow_part = _child(docflow, "FlowPart")
    if flow_part is not None:
        _walk_flow_parts(flow_part, result["activities"])

    workflow_refs = sorted(
        {
            a.get("workflow_name", "")
            for a in result["activities"]
            if a.get("activity_type") == "WORKFLOW" and a.get("workflow_name")
        }
    )

    connection_point_refs = sorted(
    {
        cp.strip()
        for a in result["activities"]
        for cp in (a.get("connection_points", "") or "").split(",")
        if cp.strip()
    }
    )

    script_refs = sorted(
        {
            a.get("script_name", "")
            for a in result["activities"]
            if a.get("activity_type") == "SCRIPTING" and a.get("script_name")
        }
    )

    mapping_refs = sorted(
        {
            a.get("mapping_name", "")
            for a in result["activities"]
            if a.get("mapping_name")
        }
    )

    result["dependencies"] = {
        "workflows": workflow_refs,
        "connection_points": connection_point_refs,
        "scripts": script_refs,
        "mappings": mapping_refs,
    }

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m tools.parse_dataflow_xml <dataflow-xml>")
        raise SystemExit(1)

    parsed = parse_dataflow_xml(sys.argv[1])
    print(json.dumps(parsed, indent=2))