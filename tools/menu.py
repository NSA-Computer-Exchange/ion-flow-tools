from __future__ import annotations

from pathlib import Path
import json

import questionary
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from tools.document_flow import document_flow
from tools.git_sync import (
    sync_workspace_to_git,
    add_or_update_git_remote,
    get_git_remotes,
)
from tools.import_artifacts import import_artifact_file
from tools.validate_bundle import validate_current_workspace_bundle
from tools.workspace import (
    stage_dataflow,
    list_workspaces,
    set_current_workspace,
    get_current_workspace,
    get_current_manifest,
    current_flow_xml_path,
    workspace_path,
)
from tools.locator import find_artifact_candidates
from security.setauth import main as set_authentication

console = Console()

DEFAULT_IMPORT_DIR = Path("exports/dataflows")


def print_header() -> None:
    current = get_current_workspace()
    subtitle = f"[bold green]Current workspace:[/bold green] {current}" if current else "[dim]No workspace selected[/dim]"

    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]ionflow[/bold cyan]\n"
            "[dim]ION flow documentation, validation, bundling, and Git tooling[/dim]\n\n"
            f"{subtitle}",
            border_style="cyan",
        )
    )
    console.print()


def pause() -> None:
    print()
    input("Press Enter to continue...")


def show_message(title: str, body: str, style: str = "cyan") -> None:
    console.print()
    console.print(Panel(body, title=title, border_style=style))
    console.print()


def prompt_main_menu() -> str:
    return questionary.select(
        "Choose an action:",
        choices=[
            questionary.Choice("", ""),
            questionary.Choice("======   ION ACTIONS  ======", ""),
            questionary.Choice("Stage new dataflow set", value="stage"),
            questionary.Choice("Resolve missing artifacts", value="resolve_missing"),
            questionary.Choice("Open existing workspace", value="open"),
            questionary.Choice("Workspace dashboard", value="dashboard"),
            questionary.Choice("Document current workspace", value="document"),
            questionary.Choice("Validate current workspace", value="validate"),
            questionary.Choice("Bundle current workspace", value="bundle"),
            questionary.Choice("", ""),
            questionary.Choice("======   GIT ACTIONS  ======", ""),
            questionary.Choice("Add / update Git remote", value="remote"),
            questionary.Choice("Git sync current workspace", value="sync"),
            questionary.Choice("", ""),
            questionary.Choice("====== AUTHENTICATION ======", ""),
            questionary.Choice("Set API credentials", value="credentials"),
            questionary.Choice("", ""),
            questionary.Choice("Help", value="help"),
            questionary.Choice("Exit", value="exit"),
        ],
        qmark="🚀",
    ).ask()


def choose_candidate_or_browse(artifact_type: str, artifact_name: str) -> Path | None | str:
    candidates = find_artifact_candidates(artifact_type, artifact_name)

    choices = []
    for path in candidates:
        choices.append(questionary.Choice(str(path), value=path))

    if choices:
        choices.append(questionary.Separator())

    choices.extend([
        questionary.Choice("Browse manually", value="browse"),
        questionary.Choice("Skip", value="skip"),
        questionary.Choice("Cancel remaining prompts", value="cancel"),
    ])

    return questionary.select(
        f"Missing {artifact_type[:-1]}: {artifact_name}",
        choices=choices,
        qmark="🔎",
    ).ask()


def prompt_for_xml_file() -> Path | None:
    xml_files = []
    if DEFAULT_IMPORT_DIR.exists():
        xml_files = sorted(DEFAULT_IMPORT_DIR.glob("*.xml"))

    if xml_files:
        choices = [questionary.Choice(p.name, value=p) for p in xml_files]
        choices.append(questionary.Separator())
        choices.append(questionary.Choice("Browse for another file...", value="browse"))
        choices.append(questionary.Choice("Cancel", value=None))

        result = questionary.select(
            "Select exported dataflow XML:",
            choices=choices,
            qmark="📄",
        ).ask()

        if result == "browse":
            return prompt_for_path(
                prompt_text="Enter path to exported dataflow XML:",
                allowed_suffixes=(".xml",),
            )

        return result

    return prompt_for_path(
        prompt_text="Enter path to exported dataflow XML:",
        allowed_suffixes=(".xml",),
    )


def prompt_for_path(
    prompt_text: str = "Enter path:",
    allowed_suffixes: tuple[str, ...] | None = None,
) -> Path | None:
    while True:
        raw = questionary.path(
            prompt_text,
            qmark="📂",
        ).ask()

        if not raw:
            return None

        path = Path(raw).expanduser()

        if not path.exists():
            show_message("File not found", f"[red]{path}[/red] does not exist.", style="red")
            continue

        if not path.is_file():
            show_message("Invalid selection", f"[red]{path}[/red] is not a file.", style="red")
            continue

        if allowed_suffixes:
            suffix = path.suffix.lower()
            allowed = tuple(s.lower() for s in allowed_suffixes)
            if suffix not in allowed:
                show_message(
                    "Invalid file type",
                    f"[red]{path.name}[/red] must be one of: {', '.join(allowed)}",
                    style="red",
                )
                continue

        return path


ARTIFACT_SUFFIXES = {
    "workflows": (".xml",),
    "connection_points": (".xml",),
    "scripts": (".json",),
    "mappings": (".xml",),
}


def prompt_for_artifact_file(artifact_type: str, artifact_name: str) -> Path | None:
    allowed = ARTIFACT_SUFFIXES.get(artifact_type, (".xml", ".json"))
    return prompt_for_path(
        prompt_text=f"Enter path for missing {artifact_type[:-1]} '{artifact_name}':",
        allowed_suffixes=allowed,
    )


def prompt_for_missing_artifacts(validation_result: dict) -> None:
    current = get_current_workspace()
    if not current:
        show_message("No workspace selected", "Stage or open a workspace first.", style="yellow")
        return

    root = workspace_path(current)
    missing = validation_result.get("missing", {})

    artifact_order = [
        ("workflows", "Workflow"),
    ]

    for artifact_type, label in artifact_order:
        names = missing.get(artifact_type, [])
        for name in names:
            selection = choose_candidate_or_browse(artifact_type, name)

            if selection == "cancel":
                return
            if selection == "skip":
                continue
            if selection == "browse":
                source_file = prompt_for_artifact_file(artifact_type, name)
            else:
                source_file = selection

            if not source_file:
                continue

            try:
                dest = import_artifact_file(
                    workspace_root=root,
                    artifact_type=artifact_type,
                    source_file=source_file,
                )
                show_message(
                    "Artifact imported",
                    f"[bold]{name}[/bold] copied to:\n{dest}",
                    style="green",
                )
            except Exception as exc:
                show_message("Import failed", f"[red]{exc}[/red]", style="red")


def handle_resolve_missing_artifacts() -> None:
    console.print(Rule("[bold cyan]Resolve Missing Artifacts[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx

    try:
        validation_result = validate_current_workspace_bundle()
    except Exception as exc:
        show_message("Validation failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    missing = validation_result.get("missing", {})
    referenced = validation_result.get("referenced", {})

    missing_workflows = missing.get("workflows", [])

    if not missing_workflows:
        show_message(
            "No missing external artifacts",
            f"[bold]Workspace:[/bold] {current}\n\n"
            f"[bold]Missing workflows:[/bold] 0\n"
            f"[bold]Referenced embedded connection points:[/bold] {len(referenced.get('connection_points', []))}\n"
            f"[bold]Referenced embedded scripts:[/bold] {len(referenced.get('scripts', []))}\n"
            f"[bold]Referenced embedded mappings:[/bold] {len(referenced.get('mappings', []))}",
            style="green",
        )
        pause()
        return

    summary = (
        f"[bold]Missing workflows:[/bold] {len(missing_workflows)}\n"
        f"[bold]Referenced embedded connection points:[/bold] {len(referenced.get('connection_points', []))}\n"
        f"[bold]Referenced embedded scripts:[/bold] {len(referenced.get('scripts', []))}\n"
        f"[bold]Referenced embedded mappings:[/bold] {len(referenced.get('mappings', []))}"
    )
    show_message("Missing external artifacts detected", summary, style="yellow")

    proceed = questionary.confirm(
        "Prompt for each missing workflow now?",
        default=True,
        qmark="❓",
    ).ask()

    if not proceed:
        return

    prompt_for_missing_artifacts(validation_result)

    try:
        updated = validate_current_workspace_bundle()
    except Exception as exc:
        show_message("Post-import validation failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    remaining = updated.get("missing", {}).get("workflows", [])
    if not remaining:
        show_message(
            "Workflow resolution complete",
            "All missing workflows have now been resolved.",
            style="green",
        )
    else:
        show_message(
            "Workflows still missing",
            "[bold]Remaining missing workflows:[/bold]\n- " + "\n- ".join(remaining),
            style="yellow",
        )

    pause()


def handle_stage_workspace() -> None:
    console.print(Rule("[bold cyan]Stage New Dataflow Set[/bold cyan]"))

    xml_path = prompt_for_xml_file()
    if not xml_path:
        return

    default_name = xml_path.stem

    workspace_name = questionary.text(
        "Workspace name:",
        default=default_name,
        qmark="📦",
    ).ask()

    if not workspace_name:
        return

    try:
        result = stage_dataflow(xml_path, workspace_name)
    except Exception as exc:
        show_message("Stage failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    show_message(
        "Workspace staged",
        f"[bold]Workspace:[/bold] {result['workspace_name']}\n"
        f"[bold]Flow:[/bold] {result['flow_name']}\n"
        f"[bold]Staged XML:[/bold] {result['staged_flow_path']}\n"
        f"[bold]Manifest:[/bold] {result['manifest_path']}",
        style="green",
    )

    resolve_now = questionary.confirm(
        "Scan this workspace for missing artifacts now?",
        default=True,
        qmark="❓",
    ).ask()

    if resolve_now:
        handle_resolve_missing_artifacts()
    else:
        pause()


def handle_open_workspace() -> None:
    console.print(Rule("[bold cyan]Open Existing Workspace[/bold cyan]"))

    workspaces = list_workspaces()
    if not workspaces:
        show_message("No workspaces", "No existing workspaces were found.", style="yellow")
        pause()
        return

    choice = questionary.select(
        "Select a workspace:",
        choices=[questionary.Choice(name, value=name) for name in workspaces] + [questionary.Choice("Cancel", value=None)],
        qmark="📁",
    ).ask()

    if not choice:
        return

    set_current_workspace(choice)

    show_message(
        "Workspace selected",
        f"Current workspace set to [bold]{choice}[/bold].",
        style="green",
    )
    pause()


def handle_workspace_dashboard() -> None:
    console.print(Rule("[bold cyan]Workspace Dashboard[/bold cyan]"))

    manifest = get_current_manifest()
    current = get_current_workspace()

    if not current or not manifest:
        show_message("No workspace selected", "Stage or open a workspace first.", style="yellow")
        pause()
        return

    table = Table(show_header=False, box=None, pad_edge=False)
    table.add_column("Field", style="bold cyan")
    table.add_column("Value", style="white")

    table.add_row("Workspace", manifest.get("workspace_name", ""))
    table.add_row("Flow Name", manifest.get("flow_name", ""))
    table.add_row("Source File", manifest.get("source_file", ""))
    table.add_row("Current Flow", manifest.get("current_flow", ""))
    table.add_row("Created", manifest.get("created_at", ""))
    table.add_row("Updated", manifest.get("updated_at", ""))

    console.print(table)
    console.print()

    flow_path = current_flow_xml_path()
    if flow_path:
        console.print(f"[bold green]Resolved flow XML:[/bold green] {flow_path}")

        root = workspace_path(current)
        console.print(f"[bold green]Artifacts root:[/bold green] {root / 'artifacts'}")
        console.print(f"[bold green]Exports root:[/bold green] {root / 'exports'}")

    pause()


def _require_current_workspace() -> tuple[str, dict, Path] | None:
    current = get_current_workspace()
    manifest = get_current_manifest()
    flow_path = current_flow_xml_path()

    if not current or not manifest or not flow_path:
        show_message("No workspace selected", "Stage or open a workspace first.", style="yellow")
        pause()
        return None

    return current, manifest, flow_path


def handle_document_workspace() -> None:
    console.print(Rule("[bold cyan]Document Current Workspace[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx
    root = workspace_path(current)

    generate_pdf = questionary.confirm(
        "Also generate PDF documentation?",
        default=True,
        qmark="📄",
    ).ask()

    upload_idm = False
    if generate_pdf:
        upload_idm = questionary.confirm(
            "Upload PDF to IDM?",
            default=False,
            qmark="☁️",
        ).ask()

    use_ai = questionary.confirm(
        "Use AI-generated documentation?",
        default=False,
        qmark="🤖",
    ).ask()

    ai_provider = "openai"
    if use_ai:
        ai_provider = questionary.select(
            "Choose AI provider:",
            choices=[
                questionary.Choice("OpenAI", value="openai"),
                questionary.Choice("Infor GenAI", value="infor"),
            ],
            default="infor",
            qmark="🧠",
        ).ask() or "openai"

    try:
        result = document_flow(
            xml_path=flow_path,
            workspace_dir=root,
            normalized_dir=root / "artifacts" / "normalized",
            docs_dir=root / "artifacts" / "docs",
            diagrams_dir=root / "artifacts" / "diagrams",
            generate_pdf=bool(generate_pdf),
            upload_idm=bool(upload_idm),
            use_ai=bool(use_ai),
            ai_provider=ai_provider,
        )
    except Exception as exc:
        show_message("Document generation failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    body = (
        f"[bold]Workspace:[/bold] {current}\n"
        f"[bold]Flow:[/bold] {result.get('flow_name', manifest.get('flow_name', ''))}\n"
        f"[bold]Normalized:[/bold] {result.get('normalized_path', '')}\n"
        f"[bold]Docs:[/bold] {result.get('doc_path', '')}\n"
        f"[bold]Diagram:[/bold] {result.get('diagram_path', '')}"
    )

    if result.get("pdf_path"):
        body += f"\n[bold]PDF:[/bold] {result.get('pdf_path')}"

    if result.get("idm_upload"):
        idm_result = result["idm_upload"]
        if idm_result.get("success"):
            body += "\n[bold]IDM Upload:[/bold] Success"
            if idm_result.get("status_code"):
                body += f"\n[bold]IDM Status:[/bold] {idm_result.get('status_code')}"
        else:
            body += f"\n[bold]IDM Upload:[/bold] Failed - {idm_result.get('error', 'Unknown error')}"

    if result.get("ai_generated"):
        body += "\n[bold]AI:[/bold] Generated"
    elif use_ai:
        body += "\n[bold]AI:[/bold] Requested but not generated"     

    show_message("Documentation complete", body, style="green")
    pause()


def handle_validate_workspace() -> None:
    console.print(Rule("[bold cyan]Validate Current Workspace[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx

    try:
        result = validate_current_workspace_bundle()
    except Exception as exc:
        show_message("Validation failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    available = result.get("available", {})
    resolved = result.get("resolved", {})
    missing = result.get("missing", {})
    referenced = result.get("referenced", {})

    missing_workflows = missing.get("workflows", [])

    body = (
        f"[bold]Workspace:[/bold] {current}\n"
        f"[bold]Flow:[/bold] {result.get('flow', manifest.get('flow_name', ''))}\n\n"
        f"[bold]External dependencies[/bold]\n"
        f"  Workflows available: {len(available.get('workflows', []))}\n"
        f"  Workflows resolved: {len(resolved.get('workflows', []))}\n"
        f"  Workflows missing: {len(missing_workflows)}\n\n"
        f"[bold]Referenced embedded artifacts in dataflow[/bold]\n"
        f"  Connection Points: {len(referenced.get('connection_points', []))}\n"
        f"  Scripts: {len(referenced.get('scripts', []))}\n"
        f"  Mappings: {len(referenced.get('mappings', []))}"
    )

    if missing_workflows:
        body += "\n\n[bold]Missing workflows:[/bold]\n- " + "\n- ".join(missing_workflows)

    style = "green" if not missing_workflows else "yellow"
    show_message("Validation result", body, style=style)
    pause()


def handle_bundle_workspace() -> None:
    console.print(Rule("[bold cyan]Bundle Current Workspace[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx
    root = workspace_path(current)

    try:
        validation_result = validate_current_workspace_bundle()
    except Exception as exc:
        show_message("Bundle failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    bundle_manifest_path = root / "artifacts" / "bundles" / "bundle_manifest.json"
    bundle_manifest_path.parent.mkdir(parents=True, exist_ok=True)

    with bundle_manifest_path.open("w", encoding="utf-8") as f:
        json.dump(validation_result, f, indent=2)

    show_message(
        "Bundle prepared",
        f"[bold]Workspace:[/bold] {current}\n"
        f"[bold]Bundle manifest:[/bold] {bundle_manifest_path}\n\n"
        f"This currently captures dependency state from the staged exports.",
        style="green",
    )
    pause()


def handle_add_remote() -> None:
    console.print(Rule("[bold cyan]Add / Update Git Remote[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx

    remote_url = questionary.text(
        "Enter remote URL:",
        qmark="🔗",
    ).ask()

    if not remote_url:
        return

    try:
        result = add_or_update_git_remote(
            remote_url=remote_url,
            remote_name="origin",
        )
        remotes = get_git_remotes()

    except Exception as exc:
        show_message("Remote update failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    show_message(
        "Git remote updated",
        f"[bold]Workspace:[/bold] {current}\n"
        f"[bold]Action:[/bold] {result.get('action', '')}\n"
        f"[bold]Remote:[/bold] origin\n"
        f"[bold]URL:[/bold] {result.get('remote_url', '')}\n\n"
        f"[bold]Current remotes:[/bold]\n{remotes or '(none)'}",
        style="green",
    )
    pause()


def handle_sync_workspace() -> None:
    console.print(Rule("[bold cyan]Git Sync Current Workspace[/bold cyan]"))

    ctx = _require_current_workspace()
    if not ctx:
        return

    current, manifest, flow_path = ctx

    choice = questionary.select(
        "Choose sync action:",
        choices=[
            questionary.Choice("Sync to Git", value="sync"),
            questionary.Choice("Sync and push", value="sync_push"),
            questionary.Choice("Cancel", value=None),
        ],
        qmark="🧩",
    ).ask()

    if not choice:
        return

    try:
        result = sync_workspace_to_git(
            workspace_name=current,
            push=(choice == "sync_push"),
        )
    except Exception as exc:
        show_message("Git sync failed", f"[red]{exc}[/red]", style="red")
        pause()
        return

    show_message(
        "Git sync complete",
        f"[bold]Workspace:[/bold] {current}\n"
        f"[bold]Message:[/bold] {result.get('message', '')}",
        style="green",
    )
    pause()


def show_help() -> None:
    console.print(Rule("[bold cyan]Help[/bold cyan]"))

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Action")
    table.add_column("Description")

    centered_ion = Align.center("======   ION ACTIONS   ======", vertical="middle")
    table.add_row(centered_ion, centered_ion)
    table.add_row("Stage new dataflow set", "Create a workspace and copy selected XML into exports/dataflows.")
    table.add_row("Resolve missing artifacts", "Prompt for missing workflow, connection point, and script export files.")
    table.add_row("Open existing workspace", "Switch current context to an existing workspace.")
    table.add_row("Workspace dashboard", "Show current workspace manifest and resolved flow.")
    table.add_row("Document current workspace", "Generate normalized JSON, docs, Mermaid, optional PDF, optional IDM upload, and optional AI.")
    table.add_row("Validate current workspace", "Validate referenced vs available artifacts inside the workspace.")
    table.add_row("Bundle current workspace", "Collect dependencies into workspace exports folders.")
    centered_git = Align.center("======   GIT ACTIONS   ======", vertical="middle")
    table.add_row("", "")
    table.add_row(centered_git, centered_git)
    table.add_row("Add / update Git remote", "Add origin if missing, or update origin URL if it already exists.")
    table.add_row("Git sync current workspace", "Commit workspace artifacts to Git, optionally push.")
    table.add_row("", "")
    centered_auth = Align.center("====== AUTHENTICATION  ======", vertical="middle")
    table.add_row(centered_auth, centered_auth)
    table.add_row("Set API credentials", "Configure API credentials for current workspace.")
    table.add_row("", "")
    table.add_row("Help", "Show this help message.")

    console.print(table)
    console.print()
    pause()


def run_menu() -> None:
    while True:
        print_header()

        choice = prompt_main_menu()

        if choice == "stage":
            handle_stage_workspace()
        elif choice == "resolve_missing":
            handle_resolve_missing_artifacts()
        elif choice == "open":
            handle_open_workspace()
        elif choice == "dashboard":
            handle_workspace_dashboard()
        elif choice == "document":
            handle_document_workspace()
        elif choice == "validate":
            handle_validate_workspace()
        elif choice == "bundle":
            handle_bundle_workspace()
        elif choice == "remote":
            handle_add_remote()
        elif choice == "sync":
            handle_sync_workspace()
        elif choice == "credentials":
            set_authentication()
        elif choice == "help":
            show_help()
        elif choice == "exit" or choice is None:
            console.print("\n[bold green]Bye.[/bold green]\n")
            return


if __name__ == "__main__":
    run_menu()