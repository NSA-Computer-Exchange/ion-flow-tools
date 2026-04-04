import json
from pathlib import Path
import questionary
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    console.print(Panel.fit("ION Authentication Setup", style="bold cyan"))

    ionapi_path = questionary.path(
        "Path to your .ionapi file"
    ).ask()

    from pathlib import Path
    ionapi_path = Path(ionapi_path)

    if not ionapi_path.exists() or not ionapi_path.is_file():
        console.print(f"[red]Invalid file:[/red] {ionapi_path}")
        return

    ionapi_path = Path(ionapi_path)

    if not ionapi_path.exists():
        console.print(f"[red]File not found:[/red] {ionapi_path}")
        return

    with open(ionapi_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # username = questionary.text("ION Username").ask()
    # password = questionary.password("ION Password").ask()

    tenant_url = f"{data['iu'].rstrip('/')}/{data['ti']}"

    env_values = {
        "ION_CLIENT_ID": data["ci"],
        "ION_CLIENT_SECRET": data["cs"],
        "ION_AUTH_URL": f"{data['pu']}{data['ot']}",
        "ION_API_URL": data["iu"],
        "ION_TENANT": data["ti"],
        "ION_TENANT_URL": tenant_url,
        "ION_USERNAME": data["saak"],
        "ION_PASSWORD": data["sask"],
        "OPENAI_API_KEY": "ENTER VALID OPENAI API KEY HERE",
        "INFOR_GENAI_BASE_URL": tenant_url,
        "INFOR_GENAI_LOGICAL_ID": "infor.genai.genai",
        "INFOR_GENAI_MODEL": "CLAUDE",
        "INFOR_GENAI_VERSION":"claude-sonnet-4-6",
        "INFOR_GENAI_MAX_TOKENS": 1500
    }    

    env_path = Path(".env")
    with open(env_path, "w", encoding="utf-8") as f:
        for k, v in env_values.items():
            f.write(f'{k}="{v}"\n')

    console.print(f"\n[green]✓ .env created at {env_path.resolve()}[/green]")

if __name__ == "__main__":
    main()