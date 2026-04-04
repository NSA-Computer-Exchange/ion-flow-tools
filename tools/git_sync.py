from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tools.document_flow import document_flow
from tools.validate_bundle import validate_bundle
from tools.workspace import workspace_path


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=True,
    )
    return (result.stdout or result.stderr).strip()


def ensure_git_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)

    if not (root / ".git").exists():
        subprocess.run(
            ["git", "init"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )


def ensure_repo_files(root: Path) -> None:
    gitignore_path = root / ".gitignore"
    readme_path = root / "README.md"

    desired_gitignore = (
        "__pycache__/\n"
        "*.pyc\n"
        ".DS_Store\n"
        ".env\n"
        ".ion_token_cache.json\n"
        "ion_flow_tools.egg-info/\n"
        "workspace/.current_workspace.json\n"
    )

    if gitignore_path.exists():
        existing = gitignore_path.read_text(encoding="utf-8")
        missing_lines = [line for line in desired_gitignore.splitlines() if line and line not in existing]
        if missing_lines:
            with gitignore_path.open("a", encoding="utf-8") as f:
                if not existing.endswith("\n"):
                    f.write("\n")
                for line in missing_lines:
                    f.write(line + "\n")
    else:
        gitignore_path.write_text(desired_gitignore, encoding="utf-8")

    if not readme_path.exists():
        readme_path.write_text(
            "# ion_flow_tools\n\n"
            "Git-tracked ION workspace exports and generated artifacts.\n",
            encoding="utf-8",
        )


def has_git_remote(root: Path) -> bool:
    result = subprocess.run(
        ["git", "remote"],
        cwd=str(root),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return False

    remotes = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    return len(remotes) > 0


def get_git_remotes() -> str:
    repo_root = get_project_root() / "workspace"
    try:
        return _run_git(["remote", "-v"], repo_root)
    except subprocess.CalledProcessError as exc:
        text = (exc.stderr or exc.stdout or "").strip()
        if "not a git repository" in text.lower():
            return ""
        raise RuntimeError(text or "Unable to read git remotes.")


def add_or_update_git_remote(
    remote_url: str,
    remote_name: str = "origin",
) -> dict:
    repo_root = get_project_root() / "workspace"
    ensure_git_repo(repo_root)
    ensure_repo_files(repo_root)

    existing = get_git_remotes()

    if f"{remote_name}\t" in existing or existing.startswith(remote_name):
        output = _run_git(["remote", "set-url", remote_name, remote_url], repo_root)
        action = "updated"
    else:
        output = _run_git(["remote", "add", remote_name, remote_url], repo_root)
        action = "added"

    return {
        "remote_name": remote_name,
        "remote_url": remote_url,
        "action": action,
        "message": output or f"Remote {remote_name} {action}.",
    }


def get_current_branch(root: Path) -> str:
    return _run_git(["rev-parse", "--abbrev-ref", "HEAD"], root).strip()


def has_upstream(root: Path) -> bool:
    try:
        _run_git(["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], root)
        return True
    except Exception:
        return False


def sync_workspace_to_git(workspace_name: str, push: bool = False) -> dict:
    repo_root = get_project_root() / "workspace"
    workspace_root = workspace_path(workspace_name).resolve()

    if not workspace_root.exists():
        raise RuntimeError(f"Workspace does not exist: {workspace_root}")

    ensure_git_repo(repo_root)
    ensure_repo_files(repo_root)

    rel_workspace = Path(workspace_name)

    print(f"DEBUG repo_root={repo_root}")
    print(f"DEBUG workspace_root={workspace_root}")
    print(f"DEBUG rel_workspace={rel_workspace}")

    _run_git(
        [
            "add",
            "-A",
            "--",
            ".gitignore",
            "README.md",
            str(rel_workspace),
        ],
        repo_root,
    )

    commit_output = ""
    try:
        commit_output = _run_git(
            ["commit", "-m", f"Update workspace {workspace_name}"],
            repo_root,
        )
    except subprocess.CalledProcessError as exc:
        text = f"{exc.stdout or ''}\n{exc.stderr or ''}".lower()
        if "nothing to commit" in text or "no changes added to commit" in text:
            commit_output = "Nothing to commit."
        else:
            raise RuntimeError((exc.stderr or exc.stdout or "").strip())

    push_output = ""
    if push:
        if not has_git_remote(repo_root):
            raise RuntimeError("No Git remote configured. Add or update a remote first.")

        try:
            if not has_upstream(repo_root):
                branch = get_current_branch(repo_root)
                push_output = _run_git(["push", "-u", "origin", branch], repo_root)
            else:
                _run_git(["pull", "--no-rebase", "origin", "main"], repo_root)
                push_output = _run_git(["push"], repo_root)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or exc.stdout or "").strip())

    message = commit_output
    if push_output:
        message = f"{message}\n{push_output}".strip()

    return {
        "message": message or "Git sync completed.",
        "repo_root": str(repo_root),
        "workspace_path": str(rel_workspace),
    }


def git_sync(
    xml_path: str | Path,
    push: bool = False,
    workspace_dir: str | Path | None = None,
) -> dict:
    xml_path = Path(xml_path).resolve()
    if workspace_dir:
        repo_root = Path(workspace_dir)
    else:
        repo_root = get_project_root() / "workspace"

    ensure_git_repo(repo_root)
    ensure_repo_files(repo_root)

    result = document_flow(xml_path)

    validation = validate_bundle(xml_path, "exports")
    result["bundle_validation"] = validation

    bundle_complete = not any(validation["missing"].values())
    result["bundle_complete"] = bundle_complete

    files = [
    str(xml_path),
    result.get("normalized_path") or result.get("normalized"),
    result.get("doc_path") or result.get("docs"),
    result.get("readme_path"),
    result.get("diagram_path") or result.get("diagram"),
    result.get("pdf_path"),
]

    for f in files:
        if not f:
            continue

        p = Path(f).resolve()
        if not p.exists():
            continue

        try:
            rel_path = p.relative_to(repo_root.resolve())
        except ValueError:
            # Skip anything outside this workspace repo
            continue

        _run_git(["add", str(rel_path)], repo_root)

    diff_result = subprocess.run(
        ["git", "diff", "--cached", "--quiet"],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
    )

    if diff_result.returncode == 0:
        result["commit_message"] = ""
        result["git_status"] = "no_changes"
        result["git_pushed"] = False
        return result

    commit_msg = f"Update ION dataflow: {result.get('flow_name') or result.get('flow', xml_path.stem)}"

    try:
        _run_git(["commit", "-m", commit_msg], repo_root)
    except subprocess.CalledProcessError as exc:
        text = f"{exc.stdout or ''}\n{exc.stderr or ''}".lower()
        if "nothing to commit" not in text and "no changes added to commit" not in text:
            raise RuntimeError((exc.stderr or exc.stdout or "").strip())

    result["commit_message"] = commit_msg
    result["git_status"] = "committed"
    result["git_pushed"] = False

    if push:
        if not has_git_remote(repo_root):
            result["git_pushed"] = False
            return result

        try:
            if not has_upstream(repo_root):
                branch = get_current_branch(repo_root)
                _run_git(["push", "-u", "origin", branch], repo_root)
            else:
                _run_git(["push"], repo_root)
            result["git_pushed"] = True
        except subprocess.CalledProcessError as exc:
            raise RuntimeError((exc.stderr or exc.stdout or "").strip())

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m tools.git_sync <dataflow-xml> [--push] [--workspace-dir <path>]")
        raise SystemExit(1)

    xml_path = sys.argv[1]

    workspace_dir = None
    if "--workspace-dir" in sys.argv:
        idx = sys.argv.index("--workspace-dir")
        if idx + 1 >= len(sys.argv) or sys.argv[idx + 1].startswith("--"):
            print("Error: --workspace-dir requires a value")
            raise SystemExit(1)

        workspace_dir = sys.argv[idx + 1]

    # push flag
    push = "--push" in sys.argv

    output = git_sync(
        xml_path,
        push=push,
        workspace_dir=workspace_dir,
    )

    print(json.dumps(output, indent=2))