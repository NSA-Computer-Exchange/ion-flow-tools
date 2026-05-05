## Quick Start (TUG Attendees)

1. Click "Code"
2. Download ZIP (no Git required)

OR

git clone https://github.com/NSA-Computer-Exchange/ion-flow-tools

---

# ION Flow Tools

**ION Flow Tools** is a Python-based toolkit for working with **Infor ION Dataflows** outside the ION UI.

It enables you to export, analyze, document, validate, reconstruct, secure, and enhance ION dataflows using Python tooling and a structured workspace model.

---

# Overview

ION Flow Tools allows you to:

* Export ION dataflows
* Parse and normalize XML into structured JSON
* Generate Markdown documentation
* Generate Mermaid diagrams
* Validate dependencies (scripts, workflows, connection points)
* Reconstruct deployable XML
* Manage flow workspaces
* Sync artifacts to Git
* Secure API access using `.env`
* Enhance documentation using AI

---

# Installation

## 1. Clone the repository

```bash
git clone <your-repo-url>
cd ion_flow_tools
```

---

## 2. Create virtual environment

```bash
python -m venv env
source env/bin/activate      # macOS/Linux
env\Scripts\activate         # Windows
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

Optional (for CLI usage):

```bash
pip install -e .
```

---

# Setup (IMPORTANT)

After installation, run:

```bash
ionflow menu
```

---

## Setup API Credentials (Required)

From the menu, select:

```
Setup API Credentials
```

### Requirements

* A valid `.ionapi` file from:

  * Infor OS → Authorized Apps → Ion API

### What this does

* Reads `.ionapi`
* Extracts credentials
* Automatically creates `.env`

No manual editing required

---

## Setup AI Credentials (Optional)

AI features enhance documentation and analysis.

From the menu:

```
Setup AI Credentials
```

This will add default values to your `.env`.

---

### Manual AI Configuration (Optional)

```env
OPENAI_API_KEY=

INFOR_GENAI_BASE_URL=https://mingle-ionapi.inforcloudsuite.com/NSACOM_DEM
INFOR_GENAI_LOGICAL_ID=infor.genai.genai
INFOR_GENAI_MODEL=CLAUDE
INFOR_GENAI_VERSION=claude-sonnet-4-6
INFOR_GENAI_MAX_TOKENS=1500
```

---

### Notes

* AI features are optional
* If not configured:

  * Core functionality works normally
  * AI features are skipped

---

# Usage

## Launch CLI

```bash
ionflow
```

---

## Common Commands

```bash
ionflow stage <dataflow.xml>
ionflow open
ionflow document
ionflow diagram
ionflow validate
ionflow reconstruct
ionflow pdf
ionflow sync
ionflow ai-doc
```

---

# Workspace Model

Each flow is isolated into its own workspace:

```text
workspace/<flow_name>/

├── exports/
├── artifacts/
└── manifest.json
```

---

## Full Structure

```text
exports/
  dataflows/
  workflows/
  scripts/
  connection_points/
  mappings/

artifacts/
  normalized/
  docs/
  diagrams/
  bundles/
```

---

## Why Workspaces?

* Keeps flows isolated
* Stores generated outputs cleanly
* Enables Git versioning per flow
* Prevents pollution of main repo

---

# Project Structure

```text
ion_flow_tools/

├── ionflow_cli/
├── tools/
├── security/
├── workspace/        (ignored in main repo)
├── .env
├── .gitignore
└── README.md
```

---

# Core Modules

## CLI

**ionflow_cli/**
Handles command routing and user interaction.

---

## Core Processing (`tools/`)

### parse_dataflow_xml.py

Parses raw XML into structured data.

### normalize.py

Creates standardized JSON representation.

### reconstruct_xml.py

Rebuilds deployable ION XML.

### docgen.py

Generates Markdown documentation.

### diagram.py

Generates Mermaid diagrams.

### validate_bundle.py

Validates dependencies.

### workspace.py

Manages workspace structure.

### workspace_context.py

Tracks active workspace.

### extract_embedded.py

Extracts embedded components.

### git_sync.py

Handles workspace Git operations.

### pdf_export.py

Exports docs to PDF.

### ai_docgen.py

AI-enhanced documentation generation.

---

## Security (`security/`)

### auth.py

Handles authentication.

### iontoken.py

Handles token caching and reuse.

---

# Security

* `.env` is required for credentials
* Never commit `.env`
* Token handling is centralized in `security/`
* Supports secure API access and token reuse

---

# AI Features

AI enhances:

* Documentation readability
* Flow summaries
* Natural language explanations

Future enhancements:

* Flow analysis
* Dependency explanations
* Migration insights

---

# Git Strategy

## Main Repo

Tracks:

* Source code
* CLI
* Tools
* Security modules

## Workspace Repo (Optional)

Tracks:

* Exports
* Docs
* Diagrams
* Artifacts

---

## Recommended `.gitignore`

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

---

# Typical Workflow

1. Run `ionflow menu`
2. Setup API credentials
3. Stage a dataflow
4. Generate docs & diagrams
5. Validate dependencies
6. Reconstruct XML (optional)
7. Sync workspace
8. Use AI enhancements

---

# Use Cases

* Reverse engineer flows
* Document integrations
* Prepare deployment bundles
* Visualize architecture
* Generate client-ready documentation

---

# Limitations

* Some activity types may require additional support
* PDF formatting may vary
* AI output should be reviewed

---

# Roadmap

* Expand reconstruction support
* Improve PDF rendering
* Add VS Code integration
* Add CI/CD support
* Expand AI capabilities

---

# Author

**Rob Thayer**
Senior Technical Consultant
NSA / Python / Integration Development
