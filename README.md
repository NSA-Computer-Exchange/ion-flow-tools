# 🚀 ION Flow Tools

**ION Flow Tools** is a Python-based toolkit for working with **Infor ION Dataflows** outside the ION UI.

It helps you export, analyze, document, validate, reconstruct, secure, and enhance ION dataflows using Python tooling and an organized workspace structure.

The project is designed for consultants, developers, architects, and technical teams who want better visibility and control over ION integrations.

---

# ✨ What This Project Does

ION Flow Tools allows you to:

* Export ION dataflows from source artifacts
* Parse and normalize flow XML into structured JSON
* Generate readable Markdown documentation
* Generate Mermaid diagrams for flow visualization
* Validate dependencies such as workflows, scripts, and connection points
* Reconstruct deployable XML from normalized representations
* Manage workspaces for each flow
* Sync generated workspace artifacts to Git
* Apply security-related checks and protections
* Use AI-assisted documentation and analysis features

---

# 📦 Key Features

* **Dataflow Parsing**
  Convert ION export XML into structured Python data.

* **Normalization**
  Standardize parsed flow content into a reusable JSON format.

* **Documentation Generation**
  Produce Markdown documentation describing activities, dependencies, and structure.

* **Diagram Generation**
  Create Mermaid flow diagrams for architecture and support documentation.

* **Reconstruction**
  Rebuild deployable XML from normalized JSON.

* **Validation**
  Detect missing or unresolved dependencies before deployment.

* **Workspace Management**
  Organize each dataflow and its generated artifacts into a repeatable directory structure.

* **Git Sync**
  Sync workspace content independently from the main tool source code.

* **Security Utilities**
  Support token handling, configuration protection, and secure environment-based authentication.

* **AI-Assisted Tools**
  Use AI-related modules to generate richer docs, insights, and future analysis features.

---

# 🏗️ Project Structure

```text
ion_flow_tools/
│
├── ionflow_cli/                  # CLI entry point and command routing
│
├── tools/                        # Core tool modules
│   ├── parse_dataflow_xml.py
│   ├── normalize.py
│   ├── reconstruct_xml.py
│   ├── docgen.py
│   ├── diagram.py
│   ├── validate_bundle.py
│   ├── workspace.py
│   ├── workspace_context.py
│   ├── extract_embedded.py
│   ├── git_sync.py
│   ├── pdf_export.py
│   ├── ai_docgen.py              # AI-assisted doc generation
│   └── ...                       # Other helpers/utilities
│
├── security/                     # Authentication and token-related helpers
│   ├── auth.py
│   ├── iontoken.py
│   └── ...
│
├── workspace/                    # Flow workspaces (typically gitignored in main repo)
│   └── <flow_name>/
│       ├── exports/
│       ├── artifacts/
│       └── manifest.json
│
├── exports/                      # Optional root export staging
├── docs/                         # Optional generated docs output
├── diagrams/                     # Optional generated diagrams output
├── normalized/                   # Optional normalized JSON output
│
├── .env                          # Local environment config (ignored by Git)
├── .gitignore
├── requirements.txt
├── setup.py / pyproject.toml
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <your-repo-url>
cd ion_flow_tools
```

## 2. Create a virtual environment

### macOS / Linux

```bash
python3 -m venv env
source env/bin/activate
```

### Windows

```bash
python -m venv env
env\Scripts\activate
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

If the project is packaged as an installable CLI:

```bash
pip install -e .
```

---

# 🔐 Environment Configuration

Create a `.env` file in the project root for secure local configuration.

Example:

```env
ION_AUTH_URL=
ION_TENANT_URL=
ION_CLIENT_ID=
ION_CLIENT_SECRET=
ION_USERNAME=
ION_PASSWORD=
```

These values are used for authentication against Infor ION APIs and related tooling.

---

# 🔒 Security Notes

This project uses the `security/` folder to isolate authentication and token management logic from the rest of the application.

The intent is to:

* Keep API authentication logic centralized
* Avoid hardcoding secrets in scripts
* Support local `.env` usage
* Support token reuse and caching
* Make CLI/API tooling safer and easier to maintain

## Security Best Practices

* Never commit `.env` files
* Never commit token cache files unless intentionally required
* Use environment variables for all tenant credentials
* Rotate credentials if they were ever pushed to GitHub
* Keep the `workspace/` repo separate if it may contain customer-specific artifacts

---

# 🚀 Usage

## Start the CLI

```bash
ionflow
```

Depending on your CLI implementation, this may open an interactive menu or accept direct commands.

---

# 🧭 Common Functions

## Stage a dataflow into a workspace

```bash
ionflow stage <path-to-dataflow-xml>
```

Stages a selected dataflow into a structured workspace folder.

## Open current workspace

```bash
ionflow open
```

Loads the current workspace context for later commands.

## Generate documentation

```bash
ionflow document
```

Creates Markdown documentation for the current dataflow.

## Generate diagrams

```bash
ionflow diagram
```

Creates Mermaid diagrams for the current dataflow.

## Validate dependencies

```bash
ionflow validate
```

Checks whether referenced workflows, scripts, and connection points are available.

## Reconstruct deployable XML

```bash
ionflow reconstruct
```

Builds deployable XML from normalized flow data.

## Sync workspace artifacts

```bash
ionflow sync
```

Commits and pushes workspace artifacts if the workspace is configured as a separate Git repository.

## Export PDF documentation

```bash
ionflow pdf
```

Converts generated Markdown documentation into PDF output.

## Run AI-assisted documentation

```bash
ionflow ai-doc
```

Uses AI-related tooling to generate or enhance documentation content.

---

# 🗂️ Workspace Structure

Each flow is staged into its own workspace so that raw exports and generated artifacts remain organized.

Example:

```text
workspace/<flow_name>/
│
├── exports/
│   ├── dataflows/
│   ├── workflows/
│   ├── scripts/
│   ├── connection_points/
│   └── mappings/
│
├── artifacts/
│   ├── normalized/
│   ├── docs/
│   ├── diagrams/
│   └── bundles/
│
└── manifest.json
```

## Purpose of the workspace

The workspace is designed to:

* Keep each flow self-contained
* Preserve exported source artifacts
* Store generated outputs in predictable locations
* Support versioning of workspace content separately from the main codebase

---

# 🧩 Code File Descriptions

## `ionflow_cli/`

Contains the command-line interface entry points and routing logic.

### Typical responsibilities

* Parse command-line arguments
* Present menus or commands
* Dispatch actions to core modules
* Manage current workspace selection

---

## `tools/parse_dataflow_xml.py`

Parses raw ION dataflow export XML into structured Python objects or dictionaries.

### Purpose

* Read original flow XML
* Extract flow nodes, activities, metadata, and relationships
* Feed parsed output into normalization logic

---

## `tools/normalize.py`

Transforms parsed dataflow content into a normalized JSON structure.

### Purpose

* Standardize flow representation
* Simplify downstream processing
* Produce input for docs, diagrams, validation, and reconstruction

---

## `tools/reconstruct_xml.py`

Rebuilds deployable ION XML from normalized JSON data.

### Purpose

* Convert normalized structures back into ION-compatible XML
* Support deployment and re-import workflows
* Handle specific flow node and activity types

---

## `tools/docgen.py`

Generates Markdown documentation from normalized data.

### Purpose

* Describe flow structure in readable form
* Document activities, dependencies, and metadata
* Produce Git-friendly technical documentation

---

## `tools/diagram.py`

Generates Mermaid diagrams from normalized flow structures.

### Purpose

* Create visual representations of the flow
* Help architects and support teams understand integration logic
* Support presentations and design documentation

---

## `tools/validate_bundle.py`

Checks whether referenced dependencies are available.

### Purpose

* Detect unresolved workflows
* Detect missing scripts
* Detect missing connection points
* Help prepare a complete deployment bundle

---

## `tools/workspace.py`

Handles workspace creation, initialization, and management.

### Purpose

* Create standard folder structures
* Store workspace metadata
* Manage output paths for generated artifacts

---

## `tools/workspace_context.py`

Tracks or resolves the active workspace.

### Purpose

* Remember which workspace is currently open
* Help commands operate on the correct flow
* Reduce the need to repeatedly specify paths

---

## `tools/extract_embedded.py`

Extracts embedded content from dataflows.

### Purpose

* Pull out scripts, connection point references, or embedded metadata
* Support dependency tracking and packaging
* Improve visibility into hidden flow components

---

## `tools/git_sync.py`

Handles Git integration for the workspace.

### Purpose

* Commit workspace changes
* Push generated artifacts
* Keep flow documentation and exports versioned separately from source code

### Important note

This is typically intended to run against the **workspace repository**, not the main `ion_flow_tools` source repo.

---

## `tools/pdf_export.py`

Converts generated Markdown documents into PDF files.

### Purpose

* Produce presentation-ready and shareable documentation
* Support client handoff and internal review workflows

---

## `tools/ai_docgen.py`

Provides AI-assisted documentation generation.

### Purpose

* Enrich generated docs with summaries or narrative explanations
* Improve readability beyond raw structural documentation
* Lay groundwork for future AI features such as analysis, remediation suggestions, or migration summaries

---

## `security/auth.py`

Handles authentication to ION or related services.

### Purpose

* Obtain tokens from configured credentials
* Centralize login logic
* Support secure API access from CLI or helper tools

---

## `security/iontoken.py`

Handles token retrieval, caching, and reuse.

### Purpose

* Reduce repeated authentication calls
* Store usable token state locally
* Simplify downstream API requests

---

# 🤖 AI Features

The AI portion of the project is intended to make flow documentation and analysis more intelligent and easier to consume.

Current or planned AI use cases include:

* AI-assisted documentation summaries
* Flow explanation generation
* Dependency explanation
* Natural-language descriptions of dataflows
* Future remediation suggestions
* Future deployment-readiness insights

## Why AI is useful here

Traditional integration exports are difficult to read quickly. AI can help turn raw technical structures into clearer explanations for:

* Consultants
* Developers
* Architects
* Support teams
* Customers and stakeholders

---

# 🔄 Git Strategy

This project works best with a **two-repo model**:

## Main repo

Tracks:

* source code
* CLI
* tools
* security modules
* documentation templates

## Workspace repo

Tracks:

* exported flows
* generated docs
* generated diagrams
* normalized artifacts
* bundle outputs

## Recommended `.gitignore`

The main repo should usually ignore:

```gitignore
.env
*.env
workspace/
__pycache__/
*.pyc
.DS_Store
build/
dist/
*.egg-info/
```

This keeps generated content and secrets out of the main code repository.

---

# 📘 Typical Workflow

1. Export or obtain a dataflow XML file
2. Stage it into a workspace
3. Parse and normalize the flow
4. Generate docs and diagrams
5. Validate dependencies
6. Reconstruct deployable XML if needed
7. Sync workspace outputs to Git
8. Use AI tooling to enrich documentation or analysis

---

# 🧪 Example Use Cases

* Reverse-engineer an existing ION dataflow
* Document customer integrations for handoff
* Build a reusable deployment bundle
* Identify missing dependencies before import
* Visualize a complex flow for presentations
* Use AI to generate better documentation for technical and non-technical audiences

---

# 🚧 Known Limitations

* Reconstruction support may still need expansion for some activity types
* PDF formatting may need tuning depending on document size and structure
* AI-generated descriptions should still be reviewed for technical accuracy
* Some commands may depend on workspace context being initialized correctly

---

# 🛣️ Roadmap

* Expand activity-type support in reconstruction
* Improve PDF layout and formatting
* Add richer dependency reports
* Add more AI-based summarization and analysis
* Add VS Code integration
* Add CI/CD support for documentation and validation
* Add smarter bundle assembly helpers

---

# 👤 Author

**Rob Thayer**
Senior Technical Consultant
Python / Infor ION / Integration Development

