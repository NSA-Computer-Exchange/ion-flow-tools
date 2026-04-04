# 🚀 ION Flow Tools

**ION Flow Tools** is a Python-based toolkit designed to export, analyze, document, validate, and reconstruct Infor ION Dataflows into deployable and human-readable formats.

It enables developers, consultants, and architects to:

* Extract ION Dataflows from the API
* Normalize them into structured JSON
* Generate documentation and diagrams
* Validate dependencies (scripts, workflows, connection points)
* Reconstruct deployable XML artifacts

---

# 📦 Features

* 🔄 Export ION Dataflows via API
* 🧠 Normalize XML into structured JSON
* 📄 Generate Markdown documentation
* 📊 Create Mermaid diagrams
* ✅ Validate dependencies and missing components
* 🔧 Reconstruct deployable XML
* 📁 Workspace-based project structure
* 🔁 Git-friendly workflow integration

---

# 🏗️ Project Structure

```
ion_flow_tools/
│
├── ionflow_cli/               # CLI entry point and command handling
├── tools/                    # Core processing modules
│   ├── parse_dataflow_xml.py
│   ├── normalize.py
│   ├── reconstruct_xml.py
│   ├── docgen.py
│   ├── diagram.py
│   ├── validate_bundle.py
│   ├── workspace.py
│   ├── extract_embedded.py
│   ├── git_sync.py
│   └── pdf_export.py
│
├── workspace/                # Working directory (IGNORED by Git)
│   └── <flow_name>/
│       ├── exports/
│       └── artifacts/
│
├── .env                      # Environment variables (IGNORED)
├── .gitignore
├── pyproject.toml / setup.py
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone <your-repo-url>
cd ion_flow_tools
```

---

## 2. Create virtual environment

```bash
python -m venv env
source env/bin/activate   # Mac/Linux
env\Scripts\activate      # Windows
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure environment variables

Create a `.env` file:

```
ION_AUTH_URL=
ION_TENANT_URL=
ION_CLIENT_ID=
ION_CLIENT_SECRET=
ION_USERNAME=
ION_PASSWORD=
```

---

# 🚀 Usage

## Launch CLI

```bash
ionflow
```

---

## Common Commands

### 📂 Stage a dataflow into workspace

```
ionflow stage <dataflow.xml>
```

---

### 📄 Generate documentation

```
ionflow document
```

---

### 📊 Generate diagrams

```
ionflow diagram
```

---

### ✅ Validate dependencies

```
ionflow validate
```

---

### 🔧 Reconstruct XML

```
ionflow reconstruct
```

---

### 🔁 Sync workspace (optional Git integration)

```
ionflow sync
```

---

# 🧠 Workspace Structure

Each dataflow is staged into its own workspace:

```
workspace/<flow_name>/

├── exports/
│   ├── dataflows/
│   ├── workflows/
│   ├── scripts/
│   └── connection_points/
│
├── artifacts/
│   ├── normalized/
│   ├── docs/
│   ├── diagrams/
│   └── bundles/
```

---

# 🧩 Module Breakdown

## 🔹 parse_dataflow_xml.py

Parses raw ION export XML into a structured intermediate format.

---

## 🔹 normalize.py

Transforms parsed XML into normalized JSON used across all tools.

---

## 🔹 reconstruct_xml.py

Rebuilds deployable ION XML from normalized JSON.
Supports various activity types including workflows and filters.

---

## 🔹 docgen.py

Generates Markdown documentation describing the dataflow structure.

---

## 🔹 diagram.py

Creates Mermaid diagrams representing flow logic and relationships.

---

## 🔹 validate_bundle.py

Checks for missing dependencies such as:

* Workflows
* Scripts
* Connection points

---

## 🔹 workspace.py

Handles workspace creation, context management, and manifest tracking.

---

## 🔹 extract_embedded.py

Extracts embedded scripts and connection points from dataflows.

---

## 🔹 git_sync.py

Handles Git integration for syncing workspace artifacts.

---

## 🔹 pdf_export.py

Converts generated documentation into PDF format.

---

# 🔐 Git Strategy

* `workspace/` is intentionally excluded from the main repository
* Prevents large files and generated artifacts from polluting commits
* Optional: workspace can be its own Git repo

---

# 🧪 Development Notes

* Designed for extensibility and modular processing
* Supports multiple output formats (XML, JSON, Markdown, PDF)
* CLI-driven workflow for ease of use
* Intended for use in CI/CD pipelines and developer tooling

---

# 🚧 Known Limitations

* Some activity types may require additional reconstruction support
* PDF rendering may require formatting adjustments
* Large dataflows may impact processing speed

---

# 🛣️ Roadmap

* [ ] Full support for all activity types
* [ ] VS Code extension
* [ ] CI/CD pipeline integration
* [ ] Enhanced diagram styling
* [ ] Automated dependency import

---

# 👤 Author

**Rob Thayer**
Senior Technical Consultant – Infor Ecosystem

---

# 📄 License

MIT License (or your preferred license)

