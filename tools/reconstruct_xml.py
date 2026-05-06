import base64
import json
import xml.etree.ElementTree as ET


_UNKNOWN_ACTIVITY_TYPES = set()
_ACTIVITY_BUILDERS = {}


def register_activity_builder(node_type):
    def decorator(func):
        _ACTIVITY_BUILDERS[node_type] = func
        return func
    return decorator


def _add_text(parent, tag, value):
    elem = ET.SubElement(parent, tag)
    if value is not None:
        elem.text = str(value)
    return elem


def _bool_text(value):
    return "true" if bool(value) else "false"


def _workflow_data_type_code(value):
    mapping = {
        "STRING": "1",
        "INTEGER": "2",
        "INT": "2",
        "DECIMAL": "3",
        "DOUBLE": "3",
        "NUMBER": "3",
        "BOOLEAN": "4",
        "BOOL": "4",
        "DATE": "5",
        "DATETIME": "6",
    }
    return mapping.get(str(value).upper(), "1")


def _workflow_parameter_type_code(value):
    mapping = {
        "IN": "1",
        "OUT": "2",
    }
    return mapping.get(str(value).upper(), str(value))


def _build_activity_documents(parent, docs):
    docs_elem = ET.SubElement(parent, "ActivityDocuments")
    for doc in docs or []:
        d = ET.SubElement(docs_elem, "ActivityDocument")
        _add_text(d, "Noun", doc.get("noun", ""))
        _add_text(d, "Verb", doc.get("verb", ""))
        _add_text(d, "DocumentType", doc.get("documentType", ""))
    return docs_elem


def _build_document_mappings(parent, mappings):
    dm_elem = ET.SubElement(parent, "DocumentMappings")
    for m in mappings or []:
        dm = ET.SubElement(dm_elem, "DocumentMapping")
        _add_text(dm, "InputDocument", m.get("inputDocument", ""))
        _add_text(dm, "InputDocumentType", m.get("inputDocumentType", ""))
        _add_text(dm, "OutputDocument", m.get("outputDocument", ""))
        _add_text(dm, "OutputDocumentType", m.get("outputDocumentType", ""))
    return dm_elem


def _build_scripting_input_parameters(parent, params):
    root = ET.SubElement(parent, "ScriptingActivityInputParameters")
    for p in params or []:
        item = ET.SubElement(root, "ScriptingActivityInputParameter")
        _add_text(item, "FromType", p.get("fromType", ""))
        _add_text(item, "FromValue", p.get("fromValue", ""))
        _add_text(item, "ToType", p.get("toType", ""))
        _add_text(item, "ToName", p.get("toName", ""))
        _add_text(item, "ToDescription", p.get("toDescription", ""))
        _add_text(item, "ToDataType", p.get("toDataType", ""))
    return root


def _build_scripting_output_parameters(parent, params):
    root = ET.SubElement(parent, "ScriptingActivityOutputParameters")
    for p in params or []:
        item = ET.SubElement(root, "ScriptingActivityOutputParameter")
        _add_text(item, "ContentName", p.get("contentName", ""))
        _add_text(item, "ContentType", p.get("contentType", ""))
        _add_text(item, "ContentDataType", p.get("contentDataType", ""))
        _add_text(item, "HeadersName", p.get("headersName", ""))
        _add_text(item, "HeadersType", p.get("headersType", ""))
    return root


def _build_merge_component_mappings(parent, mappings):
    root = ET.SubElement(parent, "MergeComponentMappings")
    for mapping in mappings or []:
        mcm = ET.SubElement(root, "MergeComponentMapping")
        attrs_elem = ET.SubElement(mcm, "MergeAttributes")
        for attr in mapping.get("mergeComponentAttributes", []):
            ma = ET.SubElement(attrs_elem, "MergeAttribute")
            _add_text(ma, "Name", attr.get("name", ""))
            _add_text(ma, "Path", attr.get("path", ""))
            _add_text(ma, "DataType", attr.get("dataType", ""))
            _add_text(ma, "IsFromAttribute", "True" if attr.get("isFromAttribute") else "False")
            _add_text(ma, "DocumentName", attr.get("documentName", ""))
            _add_text(ma, "DocumentType", attr.get("documentType", ""))
            ET.SubElement(ma, "MergeFilterAttributes")
    return root


def _build_generic_activity(flow_part_elem, node):
    activity = ET.SubElement(flow_part_elem, "Activity")

    _add_text(activity, "SequenceNumber", node.get("sequenceNumber"))
    _add_text(activity, "Name", node.get("name", ""))
    _add_text(activity, "Description", node.get("description", ""))
    _add_text(activity, "ActivityType", node.get("activityType", ""))

    activity_type = node.get("activityType")

    if activity_type == "APPLICATION":
        cp = node.get("applicationConnectionPoints")
        if cp:
            if isinstance(cp, list):
                _add_text(activity, "ConnectionPoints", ",".join(cp))
            else:
                _add_text(activity, "ConnectionPoints", cp)

    elif activity_type == "ION_API":
        cp = node.get("ionApiConnectionPoint")
        if cp:
            _add_text(activity, "IonApiConnectionPoint", cp)
            _add_text(activity, "ProcedureName", cp)
        if "intermediate" in node:
            _add_text(activity, "Intermediate", _bool_text(node.get("intermediate")))

    elif activity_type == "SCRIPTING":
        sa = ET.SubElement(activity, "ScriptingActivity")
        _add_text(sa, "ScriptName", node.get("scriptName", ""))
        _build_document_mappings(sa, node.get("documentMappings", []))
        _build_scripting_input_parameters(sa, node.get("inputParameters", []))
        _build_scripting_output_parameters(sa, node.get("outputParameters", []))

    elif activity_type == "WORKFLOW":
        _add_text(activity, "WorkflowName", node.get("workflowName") or node.get("name", ""))

    _build_activity_documents(activity, node.get("activityDocuments", []))
    return activity


@register_activity_builder("workflowActivity")
def _build_workflow_activity(flow_part_elem, node):
    activity = ET.SubElement(flow_part_elem, "Activity")

    _add_text(activity, "SequenceNumber", node.get("sequenceNumber"))
    _add_text(activity, "Name", node.get("name", ""))
    _add_text(activity, "Description", node.get("description", ""))
    _add_text(activity, "ActivityType", node.get("activityType", ""))

    wa = ET.SubElement(activity, "WorkflowActivity")
    _add_text(wa, "WorkflowName", node.get("workflowName") or node.get("name", ""))

    noun_attrs_elem = ET.SubElement(wa, "WorkflowNounAttributes")
    for attr in node.get("workflowNounAttributes", []):
        attr_elem = ET.SubElement(noun_attrs_elem, "WorkflowNounAttribute")

        _add_text(attr_elem, "Name", attr.get("name", ""))
        _add_text(attr_elem, "Xpath", attr.get("xpath", ""))
        _add_text(attr_elem, "ParentPathForFiltering", attr.get("parentPathForFiltering", ""))
        _add_text(attr_elem, "DataType", _workflow_data_type_code(attr.get("dataType", "STRING")))

        input_elem = ET.SubElement(attr_elem, "WorkflowAttributeInputMappings")
        for mapping in attr.get("workflowAttributeOutputMappings", []):
            m = ET.SubElement(input_elem, "WorkflowAttributeMapping")
            _add_text(m, "ParameterName", mapping.get("parameterName", ""))
            _add_text(m, "WorkflowParameterType", _workflow_parameter_type_code(mapping.get("workflowParameterType", "")))
            _add_text(m, "WorkflowParameterDataType", _workflow_data_type_code(mapping.get("workflowDataType", "STRING")))

        output_elem = ET.SubElement(attr_elem, "WorkflowAttributeOutputMappings")
        for mapping in attr.get("workflowAttributeInputMappings", []):
            m = ET.SubElement(output_elem, "WorkflowAttributeMapping")
            _add_text(m, "ParameterName", mapping.get("parameterName", ""))
            _add_text(m, "WorkflowParameterType", _workflow_parameter_type_code(mapping.get("workflowParameterType", "")))
            _add_text(m, "WorkflowParameterDataType", _workflow_data_type_code(mapping.get("workflowDataType", "STRING")))

        ET.SubElement(attr_elem, "WorkflowFilterAttributes")

    ET.SubElement(wa, "WorkflowTrees")

    _build_activity_documents(activity, node.get("activityDocuments", []))
    return activity


@register_activity_builder("cbrFilterActivity")
def _build_cbr_filter_activity(flow_part_elem, node):
    activity = ET.SubElement(flow_part_elem, "Activity")

    _add_text(activity, "SequenceNumber", node.get("sequenceNumber"))
    _add_text(activity, "Name", node.get("name", ""))
    _add_text(activity, "Description", node.get("description", ""))
    _add_text(activity, "ActivityType", node.get("activityType", ""))

    dfnouns = ET.SubElement(activity, "DFNouns")

    for noun in node.get("nouns", []):
        dfnoun = ET.SubElement(dfnouns, "DFNoun")

        _add_text(dfnoun, "Name", noun.get("nounName", ""))
        _add_text(dfnoun, "Filter", "True" if noun.get("filter") else "False")
        _add_text(dfnoun, "DocumentType", noun.get("documentType", ""))

        condition_text = ""
        condition_data = noun.get("conditionData")
        if condition_data:
            try:
                condition_text = base64.b64decode(condition_data).decode("utf-8")
            except Exception:
                condition_text = condition_data
        _add_text(dfnoun, "ConditionData", condition_text)

        attrs_elem = ET.SubElement(dfnoun, "Attributes")
        for attr in noun.get("nounAttributes", []):
            dfattr = ET.SubElement(attrs_elem, "DFAttribute")
            _add_text(dfattr, "Name", attr.get("name", ""))
            _add_text(dfattr, "Path", attr.get("path", ""))
            if attr.get("parentPathForFiltering"):
                _add_text(dfattr, "ParentPathForFiltering", attr.get("parentPathForFiltering"))
            _add_text(dfattr, "DataType", attr.get("dataType", ""))
            ET.SubElement(dfattr, "FilterAttributes")

        verbs_elem = ET.SubElement(dfnoun, "Verbs")
        for verb in noun.get("verbs", []):
            dfverb = ET.SubElement(verbs_elem, "DFVerb")
            _add_text(dfverb, "VerbName", verb.get("verbName", ""))

    _build_activity_documents(activity, node.get("activityDocuments", []))
    return activity


def _build_flow_part_container(parent, node):
    container = ET.SubElement(parent, "FlowPartContainer")
    _add_text(container, "SequenceNumber", node.get("sequenceNumber", 0))
    _add_text(container, "FlowPartContainerType", node.get("flowPartContainerType", "SEQUENTIAL_FLOW"))

    flow_parts_elem = ET.SubElement(container, "FlowParts")
    for child in node.get("flowParts", []):
        fp = ET.SubElement(flow_parts_elem, "FlowPart")
        _build_flow_node(fp, child)

    return container


def _build_merge_component(parent, node):
    merge = ET.SubElement(parent, "MergeComponent")
    _add_text(merge, "Name", node.get("name", ""))
    _add_text(merge, "SequenceNumber", node.get("sequenceNumber"))
    _add_text(merge, "FlowPartContainerType", node.get("flowPartContainerType", "MERGE_COMPONENT"))

    flow_parts_elem = ET.SubElement(merge, "FlowParts")
    for child in node.get("flowParts", []):
        fp = ET.SubElement(flow_parts_elem, "FlowPart")
        _build_flow_node(fp, child)

    _build_merge_component_mappings(merge, node.get("mergeComponentMappings", []))
    return merge


def _build_flow_node(parent, node):
    node_type = node.get("_type")

    if node_type == "flowPartContainer":
        return _build_flow_part_container(parent, node)

    if node_type == "mergeComponent":
        return _build_merge_component(parent, node)

    builder = _ACTIVITY_BUILDERS.get(node_type)
    if builder:
        return builder(parent, node)

    if node_type and node_type.endswith("Activity"):
        _UNKNOWN_ACTIVITY_TYPES.add(node_type)
        return _build_generic_activity(parent, node)

    if "flowParts" in node and "flowPartContainerType" in node:
        return _build_flow_part_container(parent, node)

    raise ValueError(
        f"Unsupported flow node type: {node_type}\n"
        f"Node payload: {json.dumps(node, indent=2, default=str)}"
    )


def _build_connection_points(root, enriched):
    cps = enriched.get("artifacts", {}).get("connection_points", {})
    if not cps:
        return

    cps_root = ET.SubElement(root, "ConnectionPoints")

    for name, value in cps.items():
        if isinstance(value, str) and value.strip().startswith("<"):
            try:
                parsed = ET.fromstring(value)
                if parsed.tag == "ConnectionPoint":
                    cps_root.append(parsed)
                else:
                    found = parsed.find(".//ConnectionPoint")
                    if found is not None:
                        cps_root.append(found)
                    else:
                        cp = ET.SubElement(cps_root, "ConnectionPoint")
                        _add_text(cp, "Name", name)
            except Exception:
                cp = ET.SubElement(cps_root, "ConnectionPoint")
                _add_text(cp, "Name", name)
        elif isinstance(value, dict):
            cp = ET.SubElement(cps_root, "ConnectionPoint")
            _add_text(cp, "Name", value.get("name", name))
            _add_text(cp, "Description", value.get("description", ""))
            _add_text(cp, "Type", value.get("type", ""))
        else:
            cp = ET.SubElement(cps_root, "ConnectionPoint")
            _add_text(cp, "Name", name)


def _build_scripts(root, enriched):
    scripts = enriched.get("artifacts", {}).get("scripts", {})
    if not scripts:
        return

    scripts_root = ET.SubElement(root, "Scripts")

    for name, obj in scripts.items():
        script_elem = ET.SubElement(scripts_root, "Script", {"Name": name})
        payload = json.dumps(obj, ensure_ascii=False)
        script_elem.text = base64.b64encode(payload.encode("utf-8")).decode("utf-8")


def reconstruct_dataflow_xml(enriched):
    dataflow = enriched.get("dataflow", {})
    flow_root = dataflow.get("flowPart", {})

    _UNKNOWN_ACTIVITY_TYPES.clear()

    root = ET.Element("DocumentFlows")
    docflow = ET.SubElement(root, "DocumentFlow")

    _add_text(docflow, "Name", dataflow.get("name", ""))
    _add_text(docflow, "Description", dataflow.get("description", ""))
    _add_text(docflow, "Type", dataflow.get("type", "DATA_FLOW"))
    _add_text(docflow, "LastUpdatedBy", dataflow.get("lastUpdatedBy", ""))

    last_updated = dataflow.get("lastUpdatedOn", "")
    if last_updated:
        last_updated = str(last_updated).replace("T", " ").replace("Z", "")
    _add_text(docflow, "LastUpdatedOn", last_updated)
    _add_text(docflow, "ProtectOnExport", _bool_text(dataflow.get("protectOnExport", False)))

    flow_part = ET.SubElement(docflow, "FlowPart")
    _build_flow_node(flow_part, flow_root)

    if _UNKNOWN_ACTIVITY_TYPES:
        print("Unknown activity types handled generically:", sorted(_UNKNOWN_ACTIVITY_TYPES))

    xml_bytes = ET.tostring(root, encoding="utf-8")
    return b'<?xml version="1.0" encoding="UTF-8"?>\n' + xml_bytes
