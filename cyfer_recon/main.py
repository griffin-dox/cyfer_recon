#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.panel import Panel
import questionary
from cyfer_recon.core.utils import load_targets, save_targets, prepare_output_dirs
from cyfer_recon.core.tool_checker import check_tools
from cyfer_recon.core.task_runner import run_tasks, postprocess_subdomains
import json
import os
import sys
import glob
from cyfer_recon.core.personalize import first_run_personalization
from cyfer_recon.core import cli_config
from cyfer_recon.core.wordlist_payload_resolver import get_wordlist_for_tool, get_payload_for_tool

app = typer.Typer()
console = Console()

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
TASKS_FILE = os.path.join(CONFIG_DIR, 'tasks.json')
TOOLS_FILE = os.path.join(CONFIG_DIR, 'tools.json')


def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prompt_targets():
    method = questionary.select(
        "How would you like to provide targets?",
        choices=["Enter manually", "Load from file"]
    ).ask()
    if method == "Enter manually":
        targets = questionary.text("Enter targets (comma or space separated):").ask()
        targets = [t.strip() for t in targets.replace(',', ' ').split() if t.strip()]
    else:
        file_path = questionary.path("Path to targets file:").ask()
        with open(file_path, 'r', encoding='utf-8') as f:
            targets = [line.strip() for line in f if line.strip()]
    save_targets(targets)
    return targets


# Add profile support
PROFILES = {
    "Quick Recon": [
        "Automated Subdomain Enumeration",
        "Automated Port Scanning",
        "Automated Content Discovery"
    ],
    "Full Recon": [
        "Automated Subdomain Enumeration",
        "Automated Port Scanning",
        "Automating Screenshot Capture",
        "Automated Directory Brute Forcing",
        "Automated JavaScript Analysis",
        "Automated Parameter Discovery",
        "Automated XSS Detection",
        "Automated SQL Injection Testing",
        "Automated SSRF Discovery",
        "Automated LFI and RFI Detection",
        "Automated Open Redirect Detection",
        "Automated Security Headers Check",
        "Automated API Recon",
        "Automated Content Discovery",
        "Automated S3 Bucket Enumeration"
    ],
    "API Recon": [
        "Automated API Recon",
        "Automated Content Discovery"
    ]
}


# Remove the @app.command() for cli and make it the root command
@app.callback()
def main_callback():
    print_logo()
    first_run_personalization()

@app.command()
def config(
    action: str = typer.Argument(..., help="Action: set/show"),
    config_type: str = typer.Argument(..., help="Config type: wordlist/payload"),
    tool: str = typer.Argument(None, help="Tool name (for set)"),
    path: str = typer.Argument(None, help="File path (for set)")
):
    """Edit or show wordlist/payload config from CLI."""
    if action == "set":
        if not tool or not path:
            console.print("[red]Usage: cyfer-recon config set wordlist ffuf wordlists/custom.txt")
            raise typer.Exit(1)
        if config_type == "wordlist":
            cli_config.set_wordlist(tool, path)
        elif config_type == "payload":
            cli_config.set_payload(tool, path)
        else:
            console.print("[red]Unknown config type.")
    elif action == "show":
        cli_config.show_config(config_type)
    else:
        console.print("[red]Unknown action. Use set/show.")

# Make the recon flow the root command
def main_recon(
    targets: str = typer.Option(None, help="Comma-separated targets or path to file."),
    setup_tools: bool = typer.Option(False, help="Automatically download and setup missing tools globally."),
    skip_live_check: bool = typer.Option(False, help="Skip live subdomain check after deduplication."),
    live_check_tool: str = typer.Option('httpx', help="Tool to use for live subdomain check: httpx or dnsx."),
):
    console.print(Panel("[bold cyan]Cybersecurity Recon Automation CLI Tool[/bold cyan]", expand=False))

    # Platform check
    if sys.platform.startswith("win"):
        console.print("[yellow]Windows detected. Some tools may not work natively. For best results, use WSL or ensure all dependencies are available for Windows.")
    elif not (sys.platform.startswith("linux") or sys.platform.startswith("darwin")):
        console.print("[red]Unsupported platform. This tool is designed for Linux, macOS, or Windows (with WSL recommended). Exiting.")
        raise typer.Exit(1)

    # 1. Collect targets
    # Enhanced target input: validate and show summary
    if targets:
        if os.path.isfile(targets):
            try:
                targets_list = load_targets(targets)
            except Exception as e:
                console.print(f"[red]Failed to load targets from file: {e}")
                raise typer.Exit(1)
        else:
            targets_list = [t.strip() for t in targets.replace(',', ' ').split() if t.strip()]
        save_targets(targets_list)
    else:
        try:
            targets_list = prompt_targets()
        except FileNotFoundError as e:
            console.print(f"[red]File not found: {e}")
            raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error: {e}")
            raise typer.Exit(1)
    # Validate and normalize targets
    valid_targets = []
    for t in targets_list:
        if t and ('.' in t or t.replace('.', '').isdigit()):
            valid_targets.append(t)
        else:
            console.print(f"[yellow]Skipping invalid target: {t}")
    if not valid_targets:
        console.print("[red]No valid targets provided. Exiting.")
        raise typer.Exit(1)
    console.print(Panel(f"[green]Targets to scan:[/green]\n" + "\n".join(valid_targets), expand=False))
    targets_list = valid_targets

    # 2. Load tasks and tools
    tasks_config = load_json(TASKS_FILE)
    tools_config = load_json(TOOLS_FILE)
    task_names = list(tasks_config.keys())

    # 3. Task selection or profile
    profile_or_custom = questionary.select(
        "Select a recon profile or choose custom tasks:",
        choices=[*PROFILES.keys(), "Custom"]
    ).ask()
    if profile_or_custom != "Custom":
        selected_tasks = PROFILES[profile_or_custom]
    else:
        selected_tasks = questionary.checkbox(
            "Select recon tasks to run:", choices=task_names
        ).ask()
    if not selected_tasks:
        console.print("[red]No tasks selected. Exiting.")
        raise typer.Exit(1)

    # 3.5. Wordlist and payload resolution (config-driven, no menu)
    wordlists = {}
    payloads = {}
    for task in selected_tasks:
        for cmd in tasks_config[task]:
            if "{wordlist}" in cmd:
                tool = cmd.split()[0]
                wl = get_wordlist_for_tool(tool)
                if wl:
                    wordlists[tool] = wl
            if "{payload}" in cmd:
                tool = cmd.split()[0]
                pl = get_payload_for_tool(tool)
                if pl:
                    payloads[tool] = pl

    # 4. Tool check (single, clear block)
    # Use install info from tools_config
    missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
    if missing_tools:
        console.print("[red]The following required tool(s) or wordlist(s) are missing. Please install or download them manually before proceeding.\n")
        for tool, install_cmd in missing_tools.items():
            console.print(f"[bold]{tool}[/bold]")
            # Try to get platform-specific install info and notes from tools.json
            tool_info = tools_config.get(tool, {})
            linux_install = tool_info.get("install", "")
            windows_install = tool_info.get("install", "")
            note = tool_info.get("note", "")
            # Try to split install by platform if possible
            if ";" in linux_install:
                parts = linux_install.split(";")
                linux_install = next((p.split(":",1)[1].strip() for p in parts if p.strip().lower().startswith("kali")), linux_install)
                windows_install = next((p.split(":",1)[1].strip() for p in parts if p.strip().lower().startswith("windows")), windows_install)
            console.print(f"  [yellow]Linux install:[/yellow] {linux_install}")
            console.print(f"  [yellow]Windows install:[/yellow] {windows_install}")
            if note:
                console.print(f"  [blue]Note:[/blue] {note}")
        console.print("\n[red]Exiting. All required tools and wordlists must be installed/downloaded and available in your PATH or wordlists folder.")
        raise typer.Exit(1)

    # 5. Execution mode
    exec_mode = questionary.select(
        "Run tasks concurrently or sequentially?",
        choices=["Concurrent", "Sequential"]
    ).ask()
    concurrent = exec_mode == "Concurrent"

    # 5.5. Collect all output folders from tasks_config for selected_tasks
    import re
    output_folders = set()
    for task in selected_tasks:
        for cmd in tasks_config[task]:
            matches = re.findall(r'\{output\}/([\w\-]+)/', cmd)
            output_folders.update(matches)
    # Add known folders from commands (e.g., js, gitdump, etc.)
    for task in selected_tasks:
        for cmd in tasks_config[task]:
            if '{output}/js/' in cmd:
                output_folders.add('js')
            if '{output}/gitdump/' in cmd:
                output_folders.add('gitdump')

    # Add dry-run mode
    dry_run = questionary.confirm("Do you want to do a dry run (preview commands only)?").ask()
    if dry_run:
        console.print("[bold yellow]Dry run mode: displaying commands that would be executed.[/bold yellow]")
        for target in targets_list:
            for task in selected_tasks:
                for cmd in tasks_config[task]:
                    preview_cmd = cmd.replace('{target}', target).replace('{output}', os.path.join(os.getcwd(), target))
                    console.print(f"[cyan]{task}[/cyan] for [green]{target}[/green]: [white]{preview_cmd}[/white]")
        raise typer.Exit(0)

    # 6. Prepare output dirs and run tasks per target
    summary = []
    for target in targets_list:
        output_dir = os.path.join(os.getcwd(), target)
        prepare_output_dirs(output_dir, target, selected_tasks, extra_folders=list(output_folders))
        run_tasks(
            targets=[target],
            selected_tasks=selected_tasks,
            tasks_config=tasks_config,
            output_dir=output_dir,
            concurrent=concurrent,
            console=console,
            wordlists=wordlists,
            payloads=payloads
        )
        # Post-processing for subdomain enumeration
        if any(task.lower().startswith('automated subdomain enumeration') for task in selected_tasks):
            from cyfer_recon.core.task_runner import postprocess_subdomains
            postprocess_subdomains(
                output_dir,
                console=console,
                skip_live_check=skip_live_check,
                tool_preference=live_check_tool,
                status_codes=[200, 301, 302, 403, 401]
            )
        # Collect summary info
        summary.append(f"[green]{target}[/green]: [cyan]{', '.join(selected_tasks)}[/cyan] -> [white]{output_dir}[/white]")
    # Generate summary report
    report_path = os.path.join(os.getcwd(), "cyfer_recon_summary.md")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Cyfer Recon Summary\n\n")
        for line in summary:
            f.write(f"- {line}\n")
    console.print(Panel(f"[bold green]Recon complete! Summary saved to {report_path}[/bold green]", expand=False))

CYFER_TRACE_LOGO = '''
[bold cyan]
   ██████╗██╗   ██╗███████╗███████╗██████╗     ████████╗██████╗  █████╗  ██████╗███████╗
  ██╔════╝╚██╗ ██╔╝██╔════╝██╔════╝██╔══██╗    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██╔════╝
  ██║      ╚████╔╝ █████╗  █████╗  ██████╔╝       ██║   ██████╔╝███████║██║     █████╗  
  ██║       ╚██╔╝  ██╔══╝  ██╔══╝  ██╔══██╗       ██║   ██╔══██╗██╔══██║██║     ██╔══╝  
  ╚██████╗   ██║   ██║     ███████╗██║  ██║       ██║   ██║  ██║██║  ██║╚██████╗███████╗
   ╚═════╝   ╚═╝   ╚═╝     ╚══════╝╚═╝  ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚══════╝
[/bold cyan]
'''

def print_logo():
    console.print(Panel(CYFER_TRACE_LOGO, style="bold cyan", expand=False))

# Register the main recon CLI as the default command
@app.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context):
    print_logo()
    first_run_personalization()
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch main recon CLI
        main_recon()

def main():
    app()