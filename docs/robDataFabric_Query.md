# Dataflow: robDataFabric_Query

## Metadata

| Property | Value |
|---|---|
| Type | DATA_FLOW |
| Last Updated By | Rob Thayer |
| Last Updated On | 2026-04-17 14:25:13.293 |
| Protect On Export | false |

## Summary

| Metric | Count |
|---|---:|
| Activities | 5 |
| External Workflows | 1 |
| Embedded Scripts Referenced | 1 |
| Embedded Mappings Referenced | 0 |
| Referenced Connection Points | 3 |

**Activity Types Present**

- FILE
- ION_API
- SCRIPTING
- WORKFLOW

## Dependencies

### External Dependencies

#### Workflows
- DLWF

### Embedded / Referenced in Export

#### Connection Points
- DL_QEURY_DELIVER
- MCIGB_sFTP
- robDataFabric_Query

#### Scripts
- JSON_XML

#### Mappings
- None

## Activity Table

| Seq | Name | Type | Key Reference |
|---:|---|---|---|
| 0 | Submit Data Fabric Query | ION_API | robDataFabric_Query |
| 1 | Convert JSON to XML | SCRIPTING | JSON_XML |
| 2 | Check Data Fabric Status | WORKFLOW | DLWF |
| 3 | Data Fabric Get Results | ION_API | DL_QEURY_DELIVER |
| 4 | Data Fabric sFTP endpoint | FILE | MCIGB_sFTP |

## Activity Details

### 0. Submit Data Fabric Query

- **Type:** ION_API
- **ION API Connection Point:** robDataFabric_Query
- **Intermediate:** false
- Documents:
  - Noun: DL_QUERY_ID | Type: JSON

### 1. Convert JSON to XML

- **Type:** SCRIPTING
- **Description:** Converts Datafabric JSON response to XML Sync BOD
- **Script Name:** JSON_XML
- Documents:
  - Noun: DataLakeQueryResponse | Verb: Sync | Type: BOD

### 2. Check Data Fabric Status

- **Type:** WORKFLOW
- **Description:** Workflow process loop to check the status of the Data Fabric Query
- **Workflow Name:** DLWF
- Documents:
  - Noun: DataLakeQueryResponse | Verb: Sync | Type: BOD
- **Workflow Noun Attributes:**
  - `queryId` (xpath: `DataLakeQueryResponse/queryId`, type: `1`)
  - `status` (xpath: `DataLakeQueryResponse/status`, type: `1`)
  - `location` (xpath: `DataLakeQueryResponse/location`, type: `1`)

### 3. Data Fabric Get Results

- **Type:** ION_API
- **Description:** Queries Data Fabric to get the results and deliver to an sFTP endpoint
- **ION API Connection Point:** DL_QEURY_DELIVER
- **Procedure Name:** DL_QUERY_DELIVER
- **Intermediate:** true
- Documents:
  - Noun: DL_QUERY_RESPONSE | Type: AnyData

### 4. Data Fabric sFTP endpoint

- **Type:** FILE
- **Description:** sFTP endpoint where Data Fabric Query results are delivered in CSV format
