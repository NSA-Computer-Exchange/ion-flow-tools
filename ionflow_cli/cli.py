import sys
import subprocess
from pathlib import Path
from tools.workspace import workspace_path
from tools.workspace_context import get_current_workspace
import json

import questionary


def usage():
    print("""
ION Flow Tools CLI

Usage:
  ionflow menu
      Interactive menu for documentation, validation, and Git sync
          
  ionflow stage <DataflowXml> [workspace-name]
      Stage a new dataflow workspace from an exported dataflow XML          

  ionflow workspace list
      List available workspaces

  ionflow workspace set <name>
      Set the current workspace context

  ionflow workspace current
      Show the current workspace context

  ionflow document <DataflowXml> [--pdf] [--upload-idm] [--ai] [--ai-provider openai|infor]
      Parse a dataflow export and generate normalized JSON, docs, diagram,
      optional PDF, optional IDM upload, and optional AI-generated sections

  ionflow validate <DataflowXml>
      Validate whether referenced artifacts are present in the workspace bundle

  ionflow sync <DataflowXml>
      Document the flow, validate the bundle, and commit it to Git

  ionflow sync <DataflowXml> --push
      Same as sync, then push to the configured Git remote

  ionflow add-remote
      Add a GitHub remote to the current repo

  ionflow git-status
      Show local Git status

  ionflow --help
      Show this help text

Notes:
    If a target is omitted for document, validate, or sync, the CLI will use
    the current workspace if one is set.

    You may also pass a workspace name for document, validate, or sync.

Examples:
    ionflow workspace list
    ionflow workspace set Stitch
    ionflow workspace current
    ionflow document --ai --ai-provider infor
    ionflow sync --push
""")
    sys.exit(1)


def resolve_document_target(arg_index=2):
    if len(sys.argv) <= arg_index or sys.argv[arg_index].startswith("--"):
        current = get_current_workspace()

        if current:
            print(f"[ionflow | workspace: {current}]")
            ws_root = workspace_path(current)
            manifest_path = ws_root / "manifest.json"

            if manifest_path.exists():
                with manifest_path.open("r", encoding="utf-8") as f:
                    manifest = json.load(f)

                current_flow = manifest.get("current_flow")
                if current_flow:
                    flow_path = ws_root / current_flow
                    if flow_path.exists():
                        return {
                            "xml_path": str(flow_path),
                            "workspace_name": current,
                            "workspace_root": ws_root,
                        }

        print("Error: no workspace target provided and no current workspace is set.")
        print("Use: ionflow workspace set <name>")
        print("Or:  ionflow document <workspace-name>")
        print("To stage a new flow: ionflow stage <DataflowXml> [workspace-name]")
        sys.exit(1)

    raw = sys.argv[arg_index]
    candidate = Path(raw)

    # 1. Direct file path
    if candidate.exists() and candidate.is_file():
        return {
            "xml_path": str(candidate),
            "workspace_name": None,
            "workspace_root": None,
        }

    # 2. Workspace name
    from tools.workspace import workspace_path
    import json

    ws_root = workspace_path(raw)
    manifest_path = ws_root / "manifest.json"

    if manifest_path.exists():
        with manifest_path.open("r", encoding="utf-8") as f:
            manifest = json.load(f)

        current_flow = manifest.get("current_flow")
        if not current_flow:
            print(f"Workspace '{raw}' has no current_flow in manifest.json")
            sys.exit(1)

        flow_path = ws_root / current_flow
        if not flow_path.exists():
            print(f"Workspace '{raw}' flow XML not found: {flow_path}")
            sys.exit(1)

        return {
            "xml_path": str(flow_path),
            "workspace_name": raw,
            "workspace_root": ws_root,
        }

    print(f"No such XML file or workspace: {raw}")
    print("Tip: pass a workspace name like 'OEACK' or a path to a dataflow XML file.")
    sys.exit(1)


def pick_dataflow_xml():
    exports_dir = Path("exports/dataflows")
    files = sorted(exports_dir.glob("*.xml"))

    if not files:
        print("No XML files found in exports/dataflows/")
        sys.exit(1)

    choice = questionary.select(
        "Choose a dataflow export:",
        choices=[str(f) for f in files],
    ).ask()

    if not choice:
        sys.exit(1)

    return choice


def resolve_xml_arg(arg_index=2):
    if len(sys.argv) > arg_index and not sys.argv[arg_index].startswith("--"):
        return sys.argv[arg_index]
    return pick_dataflow_xml()


def main():
    if len(sys.argv) < 2 or sys.argv[1] in {"--help", "-h", "help"}:
        usage()

    command = sys.argv[1]

    if command == "menu":
        subprocess.run([sys.executable, "-m", "tools.menu"])


    elif command == "stage":
        if len(sys.argv) < 3 or sys.argv[2].startswith("--"):
            print("Usage: ionflow stage <DataflowXml> [workspace-name]")
            sys.exit(1)

        from tools.workspace import stage_dataflow

        xml_path = sys.argv[2]
        workspace_name = sys.argv[3] if len(sys.argv) >= 4 and not sys.argv[3].startswith("--") else None

        try:
            result = stage_dataflow(xml_path, workspace_name)
        except Exception as exc:
            print(f"Stage failed: {exc}")
            sys.exit(1)

        print("Workspace staged")
        print(f"Workspace: {result['workspace_name']}")
        print(f"Flow: {result['flow_name']}")
        print(f"XML: {result['staged_flow_path']}")
        print(f"Manifest: {result['manifest_path']}")


    elif command == "document":
        target = resolve_document_target(2)

        args = [sys.executable, "-m", "tools.document_flow", target["xml_path"]]

        if target["workspace_root"]:
            workspace_root = Path(target["workspace_root"])
            artifacts_root = workspace_root / "artifacts"
            args.extend([
                "--workspace-dir", str(workspace_root),
                "--normalized-dir", str(artifacts_root / "normalized"),
                "--docs-dir", str(artifacts_root / "docs"),
                "--diagrams-dir", str(artifacts_root / "diagrams"),
            ])
        else:
            print("Error: document must target a workspace to avoid writing docs/normalized/diagrams at project root.")
            print("Use: ionflow stage <DataflowXml> [workspace-name]")
            print("Then: ionflow document <workspace-name>")
            sys.exit(1)

        if "--pdf" in sys.argv:
            args.append("--pdf")

        if "--upload-idm" in sys.argv:
            args.append("--upload-idm")

        if "--ai" in sys.argv:
            args.append("--ai")


        if "--ai-provider" in sys.argv:
            idx = sys.argv.index("--ai-provider")
            if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
                print("Error: --ai-provider requires a value: openai or infor")
                sys.exit(1)

            ai_provider = sys.argv[idx + 1].strip().lower()
            if ai_provider not in {"openai", "infor"}:
                print("Error: --ai-provider must be 'openai' or 'infor'")
                sys.exit(1)

            args.extend(["--ai-provider", ai_provider])
            
        subprocess.run(args)

    elif command == "validate":
        target = resolve_document_target(2)
        subprocess.run([sys.executable, "-m", "tools.validate_bundle", target["xml_path"]])
        

    elif command == "sync":
        target = resolve_document_target(2)

        if not target["workspace_name"]:
            print("Sync requires a workspace name or current workspace.")
            sys.exit(1)

        from tools.git_sync import sync_workspace_to_git

        push = "--push" in sys.argv

        result = sync_workspace_to_git(
            workspace_name=target["workspace_name"],
            push=push,
        )

        print(result.get("message", "Git sync completed."))


    elif command == "add-remote":
        if len(sys.argv) < 3:
            print("Usage: ionflow add-remote <git-url>")
            sys.exit(1)

        from tools.git_sync import add_or_update_git_remote

        remote_url = sys.argv[2]

        try:
            add_or_update_git_remote(remote_url)
            print(f"Git remote configured: {remote_url}")
        except Exception as exc:
            print(f"Failed to configure remote: {exc}")
            sys.exit(1)


    elif command == "git-status":
        from tools.git_sync import get_git_remotes

        try:
            subprocess.run(["git", "status"], check=False)
            print()
            print("Remotes:")
            print(get_git_remotes() or "(none)")
        except Exception as exc:
            print(f"Failed to read Git status: {exc}")
            sys.exit(1)


    elif command == "workspace":
        from tools.workspace_context import (
            list_workspaces,
            set_current_workspace,
            get_current_workspace,
        )

        if len(sys.argv) < 3:
            print("Usage: ionflow workspace [list|set|current]")
            sys.exit(1)

        sub = sys.argv[2]

        if sub == "list":
            for w in list_workspaces():
                print(w)

        elif sub == "set":
            if len(sys.argv) < 4:
                print("Usage: ionflow workspace set <name>")
                sys.exit(1)

            name = sys.argv[3]
            try:
                set_current_workspace(name)
                print(f"Current workspace set to: {name}")
            except Exception as e:
                print(str(e))
                sys.exit(1)

        elif sub == "current":
            ws = get_current_workspace()
            if ws:
                print(ws)
            else:
                print("No workspace set")

        else:
            print("Usage: ionflow workspace [list|set|current]")
            sys.exit(1)        

    else:
        usage()


if __name__ == "__main__":
    main()