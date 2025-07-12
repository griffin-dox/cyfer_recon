#!/usr/bin/env python3
import typer
from rich.console import Console
from rich.panel import Panel
import questionary
from cyfer_recon.core.utils import load_targets, save_targets, prepare_output_dirs
from cyfer_recon.core.tool_checker import check_tools
from cyfer_recon.core.task_runner import run_tasks, postprocess_subdomains, run_custom_commands
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
PRESETS_FILE = os.path.join(CONFIG_DIR, 'presets.json')
CUSTOM_PRESETS_FILE = os.path.join(CONFIG_DIR, 'custom_presets.json')


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


# Utility: Preset management
def load_presets():
    if not os.path.isfile(PRESETS_FILE):
        return {}
    with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, indent=2)

def load_custom_presets():
    if not os.path.isfile(CUSTOM_PRESETS_FILE):
        return {}
    with open(CUSTOM_PRESETS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        return data.get("Custom Preset Examples", {}).get("presets", {})

def save_custom_presets(custom_presets):
    data = {
        "Custom Preset Examples": {
            "description": "Custom presets with direct commands - edit or create new ones",
            "presets": custom_presets
        }
    }
    with open(CUSTOM_PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

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

@app.command()
def list_presets():
    """List all available presets (task-based and command-based)."""
    presets = load_presets()
    custom_presets = load_custom_presets()
    
    console.print("[bold cyan]Task-based Presets:[/bold cyan]")
    for name, data in presets.items():
        desc = data.get("description", "No description")
        console.print(f"- [bold]{name}[/bold]: {desc}")
        console.print(f"  Tasks: {', '.join(data['tasks'])}")
    
    console.print("\n[bold cyan]Command-based Presets:[/bold cyan]")
    for name, data in custom_presets.items():
        desc = data.get("description", "No description")
        console.print(f"- [bold]{name}[/bold]: {desc}")
        console.print(f"  Commands: {len(data['commands'])} command(s)")
        for i, cmd in enumerate(data['commands'], 1):
            console.print(f"    {i}. {cmd}")

def cli(
    targets: str = typer.Option(None, help="Comma-separated targets or path to file."),
    setup_tools: bool = typer.Option(False, help="Automatically download and setup missing tools globally."),
    skip_live_check: bool = typer.Option(False, help="Skip live subdomain check after deduplication."),
    live_check_tool: str = typer.Option('httpx', help="Tool to use for live subdomain check: httpx or dnsx."),
    debug: bool = typer.Option(False, help="Enable debug logging."),
    dry_run: bool = typer.Option(False, help="Show what would be run, but do not execute commands."),
    preset: str = typer.Option(None, help="Run a specific preset by name (bypass menu)."),
    discord_webhook: str = typer.Option(None, help="Discord webhook URL for notifications."),
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
    presets = load_presets()
    custom_presets = load_custom_presets()
    
    # Validate and sort presets
    valid_presets = {}
    for name, data in presets.items():
        valid_tasks = [t for t in data["tasks"] if t in task_names]
        if len(valid_tasks) != len(data["tasks"]):
            console.print(f"[yellow]Warning: Some tasks in preset '{name}' do not exist and will be ignored.")
        valid_presets[name] = {"tasks": valid_tasks, "description": data.get("description", "")}
    save_presets(valid_presets)
    presets = valid_presets
    
    # Preset selection logic
    selected_tasks = []
    selected_custom_preset = None
    
    if preset and preset in presets:
        selected_tasks = presets[preset]["tasks"]
        console.print(f"[green]Preset '{preset}' selected via CLI. Tasks: {', '.join(selected_tasks)}")
    elif preset and preset in custom_presets:
        selected_custom_preset = custom_presets[preset]
        console.print(f"[green]Custom preset '{preset}' selected via CLI. Commands: {len(selected_custom_preset['commands'])}")
    else:
        # Group built-in and custom presets
        builtin = [k for k in presets if k in ("Quick Recon", "Full Recon", "API Recon")]
        custom = sorted([k for k in presets if k not in builtin])
        custom_command_presets = list(custom_presets.keys())
        
        # Build preset choices
        preset_names = []
        preset_map = {}
        
        # Add built-in presets
        for k in builtin:
            display_name = f"{k} - {presets[k]['description']}" if presets[k]['description'] else k
            preset_names.append(f"[Task] {display_name}")
            preset_map[f"[Task] {display_name}"] = ("task", k)
        
        # Add custom task presets
        for k in custom:
            display_name = f"{k} - {presets[k]['description']}" if presets[k]['description'] else k
            preset_names.append(f"[Task] {display_name}")
            preset_map[f"[Task] {display_name}"] = ("task", k)
        
        # Add custom command presets
        for k in custom_command_presets:
            display_name = f"{k} - {custom_presets[k]['description']}" if custom_presets[k]['description'] else k
            preset_names.append(f"[Command] {display_name}")
            preset_map[f"[Command] {display_name}"] = ("command", k)
        
        # Add options to create new presets
        preset_names.extend(["Create Task Preset", "Create Command Preset", "Custom (One-off)"])
        
        preset_choice = questionary.select(
            "Choose a recon preset:", choices=preset_names
        ).ask()
        
        if preset_choice in preset_map:
            preset_type, preset_key = preset_map[preset_choice]
            if preset_type == "task":
                selected_tasks = presets[preset_key]["tasks"]
                console.print(f"[green]Task preset '{preset_key}' selected. Tasks: {', '.join(selected_tasks)}")
            else:  # command
                selected_custom_preset = custom_presets[preset_key]
                console.print(f"[green]Command preset '{preset_key}' selected. Commands: {len(selected_custom_preset['commands'])}")
        elif preset_choice == "Create Task Preset":
            # User creates a new task-based preset
            custom_tasks = questionary.checkbox(
                "Select tasks for your custom preset:", choices=task_names
            ).ask()
            if not custom_tasks:
                console.print("[red]No tasks selected. Exiting.")
                raise typer.Exit(1)
            preset_name = questionary.text("Enter a name for this preset:").ask()
            if not preset_name:
                console.print("[red]No preset name provided. Exiting.")
                raise typer.Exit(1)
            desc = questionary.text("Enter a description for this preset (optional):").ask()
            presets[preset_name] = {"tasks": custom_tasks, "description": desc}
            save_presets(presets)
            console.print(f"[green]Task preset '{preset_name}' saved!")
            selected_tasks = custom_tasks
        elif preset_choice == "Create Command Preset":
            # User creates a new command-based preset
            commands = []
            console.print("[cyan]Enter commands for your custom preset (one per line, press Enter with empty line to finish):")
            console.print("[cyan]You can use placeholders: {target}, {output}, {wordlist}")
            console.print("[cyan]Example: nmap -sS -sV {target} -oN {output}/my_nmap_{target}.txt")
            
            while True:
                cmd = questionary.text("Command (or press Enter to finish):").ask()
                if not cmd:
                    break
                commands.append(cmd)
            
            if not commands:
                console.print("[red]No commands provided. Exiting.")
                raise typer.Exit(1)
            
            preset_name = questionary.text("Enter a name for this command preset:").ask()
            if not preset_name:
                console.print("[red]No preset name provided. Exiting.")
                raise typer.Exit(1)
            desc = questionary.text("Enter a description for this preset (optional):").ask()
            
            custom_presets[preset_name] = {"commands": commands, "description": desc}
            save_custom_presets(custom_presets)
            console.print(f"[green]Command preset '{preset_name}' saved!")
            selected_custom_preset = custom_presets[preset_name]
        else:
            # Custom (One-off)
            selected_tasks = questionary.checkbox(
                "Select recon tasks to run:", choices=task_names
            ).ask()
            console.print(f"[yellow]DEBUG: Selected tasks: {selected_tasks}")
            if not selected_tasks or not isinstance(selected_tasks, list) or all(not t for t in selected_tasks):
                console.print("[red]No tasks selected. Exiting.")
                raise typer.Exit(1)

    # 3.5. Wordlist selection (for tasks that use {wordlist})
    wordlist_tasks = []
    tool_wordlists = {}
    wordlists_config = load_json(os.path.join(CONFIG_DIR, 'wordlists.json'))
    
    if selected_tasks:
        # Handle task-based presets
        wordlist_tasks = []
        for task in selected_tasks:
            task_config = tasks_config[task]
            # Handle both old format (list) and new format (dict with commands)
            commands = task_config if isinstance(task_config, list) else task_config.get("commands", [])
            if any("{wordlist}" in cmd for cmd in commands):
                wordlist_tasks.append(task)
        
        if wordlist_tasks:
            for task in wordlist_tasks:
                task_config = tasks_config[task]
                commands = task_config if isinstance(task_config, list) else task_config.get("commands", [])
                for cmd in commands:
                    if "{wordlist}" in cmd:
                        tool = cmd.split()[0]
                        # Use default from wordlists.json
                        tool_wordlists[tool] = wordlists_config.get(tool, None)
    elif selected_custom_preset:
        # Handle command-based presets
        for cmd in selected_custom_preset["commands"]:
            if "{wordlist}" in cmd:
                tool = cmd.split()[0]
                tool_wordlists[tool] = wordlists_config.get(tool, None)
    
    # 4. Tool check
    if selected_tasks:
        missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
    else:
        # For custom presets, check tools from commands
        tools_to_check = []
        for cmd in selected_custom_preset["commands"]:
            tool = cmd.split()[0]
            tools_to_check.append(tool)
        
        missing_tools = {}
        for tool in tools_to_check:
            if tool in tools_config:
                check_val = tools_config[tool]['check']
                if check_val.startswith('file:'):
                    file_path = check_val.split(':', 1)[1]
                    if not os.path.isfile(file_path):
                        # Check in project wordlists/ dir
                        alt_path = os.path.join('wordlists', os.path.basename(file_path))
                        if not os.path.isfile(alt_path):
                            missing_tools[tool] = tools_config[tool]['install']
                else:
                    import shutil
                    if shutil.which(check_val) is None:
                        missing_tools[tool] = tools_config[tool]['install']
    
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

    # 5.5. Collect all output folders from tasks_config for selected_tasks and custom presets
    import re
    output_folders = set()
    if selected_tasks:
        for task in selected_tasks:
            task_config = tasks_config[task]
            commands = task_config if isinstance(task_config, list) else task_config.get("commands", [])
            for cmd in commands:
                matches = re.findall(r'\{output\}/([\w\-]+)/', cmd)
                output_folders.update(matches)
        # Add known folders from commands (e.g., js, gitdump, etc.)
        for task in selected_tasks:
            task_config = tasks_config[task]
            commands = task_config if isinstance(task_config, list) else task_config.get("commands", [])
            for cmd in commands:
                if '{output}/js/' in cmd:
                    output_folders.add('js')
                if '{output}/gitdump/' in cmd:
                    output_folders.add('gitdump')
    elif selected_custom_preset:
        for cmd in selected_custom_preset["commands"]:
            matches = re.findall(r'\{output\}/([\w\-]+)/', cmd)
            output_folders.update(matches)
            if '{output}/js/' in cmd:
                output_folders.add('js')
            if '{output}/gitdump/' in cmd:
                output_folders.add('gitdump')

    # 6. Prepare output dirs and run tasks per target
    summary = []
    for target in targets_list:
        output_dir = os.path.join(os.getcwd(), target)
        if selected_tasks:
            prepare_output_dirs(output_dir, target, selected_tasks, extra_folders=list(output_folders))
        else:
            prepare_output_dirs(output_dir, target, [], extra_folders=list(output_folders))
        
        try:
            if selected_tasks:
                # Run task-based preset
                run_tasks(
                    targets=[target],
                    selected_tasks=selected_tasks,
                    tasks_config=tasks_config,
                    output_dir=output_dir,
                    concurrent=concurrent,
                    console=console,
                    wordlists=tool_wordlists,
                    dry_run=dry_run,
                    discord_webhook=discord_webhook
                )
            else:
                # Run custom command preset
                run_custom_commands(
                    target=target,
                    commands=selected_custom_preset["commands"],
                    output_dir=output_dir,
                    concurrent=concurrent,
                    console=console,
                    wordlists=tool_wordlists,
                    dry_run=dry_run,
                    discord_webhook=discord_webhook
                )
            summary.append((target, "[green]Success[/green]"))
        except Exception as e:
            logger.error(f"Error running tasks for {target}: {e}")
            summary.append((target, f"[red]Failed: {e}[/red]"))
        
        # Post-processing for subdomain enumeration
        if selected_tasks and any(task.lower().startswith('automated subdomain enumeration') for task in selected_tasks):
            from cyfer_recon.core.task_runner import postprocess_subdomains
            postprocess_subdomains(
                output_dir,
                console=console,
                skip_live_check=skip_live_check,
                tool_preference=live_check_tool,
                status_codes=[200, 301, 302, 403, 401]
            )
        elif selected_custom_preset and any('subfinder' in cmd or 'amass' in cmd for cmd in selected_custom_preset["commands"]):
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
def notify_discord(webhook_url: str, message: str):
    """Send a custom notification to a Discord channel."""
    from cyfer_recon.core.utils import send_discord_notification
    try:
        send_discord_notification(webhook_url, message)
        console.print("[green]Notification sent successfully.")
    except Exception as e:
        console.print(f"[red]Failed to send notification: {e}")

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

@app.command()
def preset_edit():
    """Edit or delete custom presets and their descriptions."""
    presets = load_presets()
    if not presets:
        console.print("[red]No presets found.")
        return
    preset_names = list(presets.keys())
    preset = questionary.select("Select a preset to edit/delete:", choices=preset_names).ask()
    if not preset:
        return
    action = questionary.select("Edit or delete this preset?", choices=["Edit", "Delete", "Cancel"]).ask()
    if action == "Edit":
        # Edit tasks
        tasks_config = validate_json_config(TASKS_FILE)
        task_names = list(tasks_config.keys())
        current_tasks = presets[preset]["tasks"]
        new_tasks = questionary.checkbox(
            f"Edit tasks for {preset}:", choices=task_names, default=current_tasks
        ).ask()
        # Edit description
        new_desc = questionary.text(
            f"Edit description for {preset}:", default=presets[preset].get("description", "")
        ).ask()
        presets[preset]["tasks"] = new_tasks
        presets[preset]["description"] = new_desc
        save_presets(presets)
        console.print(f"[green]Preset '{preset}' updated!")
    elif action == "Delete":
        confirm = questionary.confirm(f"Are you sure you want to delete preset '{preset}'?", default=False).ask()
        if confirm:
            presets.pop(preset)
            save_presets(presets)
            console.print(f"[green]Preset '{preset}' deleted!")
    else:
        return

@app.command()
def custom_preset_edit():
    """Edit or delete custom command presets."""
    custom_presets = load_custom_presets()
    if not custom_presets:
        console.print("[red]No custom presets found.")
        return
    
    preset_names = list(custom_presets.keys())
    preset = questionary.select("Select a custom preset to edit/delete:", choices=preset_names).ask()
    if not preset:
        return
    
    action = questionary.select("Edit or delete this custom preset?", choices=["Edit", "Delete", "Cancel"]).ask()
    if action == "Edit":
        # Edit commands
        current_commands = custom_presets[preset]["commands"]
        console.print(f"[bold cyan]Editing commands for custom preset '{preset}'[/bold cyan]")
        new_commands = []
        for i, cmd in enumerate(current_commands, 1):
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
        
        # Edit description
        new_desc = questionary.text(
            f"Edit description for {preset}:", default=custom_presets[preset].get("description", "")
        ).ask()
        
        custom_presets[preset]["commands"] = new_commands
        custom_presets[preset]["description"] = new_desc
        save_custom_presets(custom_presets)
        console.print(f"[green]Custom preset '{preset}' updated!")
    elif action == "Delete":
        confirm = questionary.confirm(f"Are you sure you want to delete custom preset '{preset}'?", default=False).ask()
        if confirm:
            custom_presets.pop(preset)
            save_custom_presets(custom_presets)
            console.print(f"[green]Custom preset '{preset}' deleted!")
    else:
        return

@app.command("help")
def help_menu():
    """Show help and usage instructions."""
    console.print(Panel("""
[bold cyan]Cyfer Recon Automation Tool - Help[/bold cyan]

Usage:
  cyfer-recon [OPTIONS]

Main Features:
- Automated recon tasks with selectable profiles
- Task-based and command-based presets
- Tool and wordlist management
- Robust error handling and clear output

Commands:
  cyfer-recon                      # Start the interactive recon workflow
  cyfer-recon list-presets         # List all available presets
  cyfer-recon preset-edit          # Edit task-based presets
  cyfer-recon custom-preset-edit   # Edit command-based presets
  cyfer-recon wordlist-edit        # Edit tool-to-wordlist mapping
  cyfer-recon command-edit         # Edit task commands
  cyfer-recon help                 # Show this help menu

Preset Types:
- [bold]Task-based presets[/bold]: Collections of predefined tasks (e.g., "Quick Recon", "Full Recon")
- [bold]Command-based presets[/bold]: Custom collections of direct commands with placeholders

Placeholders for Commands:
- {target} - Target domain/host
- {output} - Output directory
- {wordlist} - Wordlist path for the tool

Example Custom Commands:
- nmap -sS -sV {target} -oN {output}/my_nmap_{target}.txt
- httpx -u https://{target} -sc -title -o {output}/my_httpx_{target}.txt

For more details, see the README or use the interactive prompts.
""", expand=False))

def main():
    app.command()(cli)
    app()

if __name__ == "__main__":
    main()