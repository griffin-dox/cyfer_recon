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
import logging
from typing import List, Optional
from rich.table import Table
from cyfer_recon import __version__

# Setup logging
logger = logging.getLogger("cyfer_recon")

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


# Utility: Validate config file existence and structure
def validate_json_config(path: str, required_keys: Optional[List[str]] = None) -> dict:
    if not os.path.isfile(path):
        console.print(f"[red]Missing required config file: {path}")
        raise typer.Exit(1)
    try:
        data = load_json(path)
    except Exception as e:
        console.print(f"[red]Failed to load config file {path}: {e}")
        raise typer.Exit(1)
    if required_keys:
        for key in required_keys:
            if key not in data:
                console.print(f"[red]Malformed config: missing key '{key}' in {path}")
                raise typer.Exit(1)
    return data

# Utility: Sanitize shell input (very basic)
def sanitize_shell_arg(arg: str) -> str:
    # Remove dangerous characters (rudimentary)
    return arg.replace(';', '').replace('&', '').replace('|', '').replace('`', '').replace('$(', '').replace(')', '')


@app.command()
def version():
    """Show version information."""
    console.print(f"[bold cyan]Cyfer Recon version:[/bold cyan] {__version__}")

@app.command()
def list_tasks():
    """List all available recon tasks."""
    tasks_config = validate_json_config(TASKS_FILE)
    console.print("[bold cyan]Available Tasks:[/bold cyan]")
    for t in tasks_config:
        console.print(f"- {t}")

@app.command()
def list_tools():
    """List all available tools."""
    tools_config = validate_json_config(TOOLS_FILE)
    console.print("[bold cyan]Available Tools:[/bold cyan]")
    for t in tools_config:
        console.print(f"- {t}")


def cli(
    targets: str = typer.Option(None, help="Comma-separated targets or path to file."),
    setup_tools: bool = typer.Option(False, help="Automatically download and setup missing tools globally."),
    skip_live_check: bool = typer.Option(False, help="Skip live subdomain check after deduplication."),
    live_check_tool: str = typer.Option('httpx', help="Tool to use for live subdomain check: httpx or dnsx."),
    debug: bool = typer.Option(False, help="Enable debug logging."),
    dry_run: bool = typer.Option(False, help="Show what would be run, but do not execute commands."),
):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logger.debug("Debug logging enabled.")
    else:
        logging.basicConfig(level=logging.INFO)
    console.print(Panel(f"[bold cyan]Cybersecurity Recon Automation CLI Tool v{__version__}[/bold cyan]", expand=False))

    # Platform check
    if sys.platform.startswith("win"):
        console.print("[yellow]Windows detected. Some tools may not work natively. For best results, use WSL or ensure all dependencies are available for Windows.")
    elif not (sys.platform.startswith("linux") or sys.platform.startswith("darwin")):
        console.print("[red]Unsupported platform. This tool is designed for Linux, macOS, or Windows (with WSL recommended). Exiting.")
        raise typer.Exit(1)

    # 1. Collect targets
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
    if not targets_list:
        console.print("[red]No targets provided. Exiting.")
        raise typer.Exit(1)

    # 2. Load tasks and tools
    tasks_config = validate_json_config(TASKS_FILE)
    tools_config = validate_json_config(TOOLS_FILE)
    task_names = list(tasks_config.keys())

    # 3. Task selection
    selected_tasks = questionary.checkbox(
        "Select recon tasks to run:", choices=task_names
    ).ask()
    if not selected_tasks:
        console.print("[red]No tasks selected. Exiting.")
        raise typer.Exit(1)

    # 3.5. Wordlist selection (for tasks that use {wordlist})
    wordlist_tasks = [task for task in selected_tasks if any("{wordlist}" in cmd for cmd in tasks_config[task])]
    wordlists_config = load_json(os.path.join(CONFIG_DIR, 'wordlists.json'))
    tool_wordlists = {}
    if wordlist_tasks:
        for task in wordlist_tasks:
            for cmd in tasks_config[task]:
                if "{wordlist}" in cmd:
                    tool = cmd.split()[0]
                    # Use default from wordlists.json
                    tool_wordlists[tool] = wordlists_config.get(tool, None)
    # Remove all payload logic

    # 4. Tool check
    missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
    if missing_tools:
        console.print("[red]The following required tool(s) are missing. Please install them manually before proceeding.\n")
        for tool, install_cmd in missing_tools.items():
            console.print(f"[bold]{tool}[/bold]")
            tool_info = tools_config.get(tool, {})
            install_info = tool_info.get("install", install_cmd)
            # Try to split install_info for Linux/Windows if possible
            linux_cmd = None
            windows_cmd = None
            note = tool_info.get("note", None)
            if "Kali:" in install_info and "Windows:" in install_info:
                parts = install_info.split(";")
                for part in parts:
                    if part.strip().startswith("Kali:"):
                        linux_cmd = part.replace("Kali:", "").strip()
                    elif part.strip().startswith("Windows:"):
                        windows_cmd = part.replace("Windows:", "").strip()
            if linux_cmd:
                console.print(f"  [yellow]Linux install:[/yellow] {linux_cmd}")
            else:
                console.print(f"  [yellow]Linux install:[/yellow] {install_info}")
            if windows_cmd:
                console.print(f"  [yellow]Windows install:[/yellow] {windows_cmd}")
            if note:
                console.print(f"  [blue]Note:[/blue] {note}")
        console.print("\n[red]Exiting. All required tools must be installed manually and available in your PATH.")
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

    # 6. Prepare output dirs and run tasks per target
    summary = []
    for target in targets_list:
        output_dir = os.path.join(os.getcwd(), target)
        prepare_output_dirs(output_dir, target, selected_tasks, extra_folders=list(output_folders))
        try:
            run_tasks(
                targets=[target],
                selected_tasks=selected_tasks,
                tasks_config=tasks_config,
                output_dir=output_dir,
                concurrent=concurrent,
                console=console,
                wordlists=tool_wordlists,
                dry_run=dry_run
            )
            summary.append((target, "[green]Success[/green]"))
        except Exception as e:
            logger.error(f"Error running tasks for {target}: {e}")
            summary.append((target, f"[red]Failed: {e}[/red]"))
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

    # Show summary table
    table = Table(title="Recon Run Summary")
    table.add_column("Target", style="cyan")
    table.add_column("Status", style="magenta")
    for row in summary:
        table.add_row(*row)
    console.print(table)

@app.command()
def wordlist_edit():
    """Interactively edit tool-to-wordlist mapping."""
    wordlists_path = os.path.join(CONFIG_DIR, 'wordlists.json')
    wordlists = load_json(wordlists_path)
    console.print("[bold cyan]Edit tool-to-wordlist mapping[/bold cyan]")
    for tool, current in wordlists.items():
        new = questionary.text(
            f"Wordlist for {tool} [{current}] (leave blank to keep):",
            default=current
        ).ask()
        if new and new != current:
            wordlists[tool] = new
    with open(wordlists_path, 'w', encoding='utf-8') as f:
        json.dump(wordlists, f, indent=2)
    console.print("[green]Wordlist mapping updated!")

@app.command()
def command_edit():
    """Interactively edit commands for a task/tool."""
    tasks_path = os.path.join(CONFIG_DIR, 'tasks.json')
    tasks = load_json(tasks_path)
    task_names = list(tasks.keys())
    task = questionary.select("Select a task to edit:", choices=task_names).ask()
    if not task:
        console.print("[red]No task selected. Exiting.")
        return
    commands = tasks[task]
    console.print(f"[bold cyan]Editing commands for {task}[/bold cyan]")
    new_commands = []
    for i, cmd in enumerate(commands, 1):
        new_cmd = questionary.text(f"Command {i}:", default=cmd).ask()
        if new_cmd:
            new_commands.append(new_cmd)
    # Option to add more commands
    while True:
        add_more = questionary.confirm("Add another command?", default=False).ask()
        if not add_more:
            break
        extra_cmd = questionary.text("Enter new command:").ask()
        if extra_cmd:
            new_commands.append(extra_cmd)
    tasks[task] = new_commands
    with open(tasks_path, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, indent=2)
    console.print(f"[green]Commands for {task} updated!")

@app.command("help")
def help_menu():
    """Show help and usage instructions."""
    console.print(Panel("""
[bold cyan]Cyfer Recon Automation Tool - Help[/bold cyan]

Usage:
  cyfer-recon [OPTIONS]

Main Features:
- Automated recon tasks with selectable profiles
- Tool and wordlist management
- Robust error handling and clear output

Commands:
  cyfer-recon                 # Start the interactive recon workflow
  cyfer-recon wordlist-edit   # Edit tool-to-wordlist mapping interactively
  cyfer-recon command-edit    # Edit task commands interactively
  cyfer-recon help            # Show this help menu

Wordlist Editing:
- Use [bold]cyfer-recon wordlist-edit[/bold] to change which wordlist is used for each tool.
- The mapping is stored in [italic]config/wordlists.json[/italic].

Command Editing:
- Use [bold]cyfer-recon command-edit[/bold] to change the commands for any task/tool.
- The commands are stored in [italic]config/tasks.json[/italic].

For more details, see the README or use the interactive prompts.
""", expand=False))

def main():
    app.command()(cli)
    app()