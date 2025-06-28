#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.panel import Panel
import questionary
from core.utils import load_targets, save_targets, prepare_output_dirs
from core.tool_checker import check_tools, install_tools
from core.task_runner import run_tasks
import json
import os

app = typer.Typer()
console = Console()

CONFIG_DIR = os.path.join(os.path.dirname(__file__), 'config')
TASKS_FILE = os.path.join(CONFIG_DIR, 'tasks.json')
TOOLS_FILE = os.path.join(CONFIG_DIR, 'tools.json')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')


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


def main(
    targets: str = typer.Option(None, help="Comma-separated targets or path to file."),
    profile: str = typer.Option(None, help="Profile name for task selection."),
    headless: bool = typer.Option(False, help="Run in headless mode (no prompts)."),
    setup_tools: bool = typer.Option(False, help="Automatically download and setup missing tools globally.")
):
    console.print(Panel("[bold cyan]Cybersecurity Recon Automation CLI Tool[/bold cyan]", expand=False))

    # 1. Collect targets
    if targets:
        if os.path.isfile(targets):
            targets_list = load_targets(targets)
        else:
            targets_list = [t.strip() for t in targets.replace(',', ' ').split() if t.strip()]
        save_targets(targets_list)
    else:
        targets_list = prompt_targets()
    if not targets_list:
        console.print("[red]No targets provided. Exiting.")
        raise typer.Exit(1)

    # 2. Load tasks and tools
    tasks_config = load_json(TASKS_FILE)
    tools_config = load_json(TOOLS_FILE)
    task_names = list(tasks_config.keys())

    # 3. Task selection
    selected_tasks = questionary.checkbox(
        "Select recon tasks to run:", choices=task_names
    ).ask()
    if not selected_tasks:
        console.print("[red]No tasks selected. Exiting.")
        raise typer.Exit(1)

    # 4. Tool check
    missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
    if missing_tools:
        console.print("[yellow]Some required tools are missing:")
        for tool, install_cmd in missing_tools.items():
            console.print(f"[bold]{tool}[/bold]: {install_cmd}")
        if setup_tools or questionary.confirm("Download and setup missing tools globally now?").ask():
            install_tools(missing_tools, console=console)
            # Re-check after install
            missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
            if missing_tools:
                console.print("[red]Some tools could not be installed. Exiting.")
                raise typer.Exit(1)
        else:
            typer.confirm("Continue anyway?", abort=True)

    # 5. Execution mode
    exec_mode = questionary.select(
        "Run tasks concurrently or sequentially?",
        choices=["Concurrent", "Sequential"]
    ).ask()
    concurrent = exec_mode == "Concurrent"

    # 6. Prepare output dirs
    for target in targets_list:
        prepare_output_dirs(OUTPUT_DIR, target, selected_tasks)

    # 7. Run tasks
    run_tasks(
        targets=targets_list,
        selected_tasks=selected_tasks,
        tasks_config=tasks_config,
        output_dir=OUTPUT_DIR,
        concurrent=concurrent,
        console=console
    )

if __name__ == "__main__":
    app.command()(main)
    app()