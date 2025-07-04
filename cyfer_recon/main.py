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


def cli(
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

    # 3.5. Wordlist selection (for tasks that use {wordlist})
    wordlist_tasks = [task for task in selected_tasks if any("{wordlist}" in cmd for cmd in tasks_config[task])]
    wordlists = []
    if wordlist_tasks:
        wordlists = []
        wordlist_menu_choices = []
        # 1. List from default dir
        default_wordlist_dir = "/usr/share/wordlists/"
        if os.path.isdir(default_wordlist_dir):
            import glob
            found_wordlists = glob.glob(os.path.join(default_wordlist_dir, "**", "*.txt"), recursive=True)
            wordlist_menu_choices += [f"[Folder] {os.path.relpath(w, default_wordlist_dir)}" for w in found_wordlists]
        # 2. List from local wordlists/ folder
        from cyfer_recon.core.utils import list_files_in_folder, download_file, validate_local_file
        local_wordlist_dir = os.path.join(os.getcwd(), "wordlists")
        local_wordlists = list_files_in_folder(local_wordlist_dir, extensions=[".txt", ".lst", ".wordlist"])
        wordlist_menu_choices += [f"[Local] {os.path.basename(w)}" for w in local_wordlists]
        # 3. Add custom path/URL option
        wordlist_menu_choices += ["[Custom] Enter local file path", "[Custom] Enter URL"]
        selected = questionary.checkbox(
            "Select wordlists to use:",
            choices=wordlist_menu_choices
        ).ask()
        for sel in selected:
            if sel.startswith("[Folder]"):
                wordlists.append(os.path.join(default_wordlist_dir, sel.replace("[Folder] ", "")))
            elif sel.startswith("[Local]"):
                wordlists.append(os.path.join(local_wordlist_dir, sel.replace("[Local] ", "")))
            elif sel == "[Custom] Enter local file path":
                path = questionary.path("Enter path to a wordlist:").ask()
                if validate_local_file(path):
                    wordlists.append(path)
                else:
                    console.print(f"[red]File not found or not readable: {path}")
            elif sel == "[Custom] Enter URL":
                url = questionary.text("Enter URL to a wordlist:").ask()
                try:
                    tmp_path = download_file(url)
                    wordlists.append(tmp_path)
                except Exception as e:
                    console.print(f"[red]Failed to download: {e}")
    else:
        wordlists = []

    # 3.6. Payload selection (for tasks that use {payload})
    payload_tasks = [task for task in selected_tasks if any("{payload}" in cmd for cmd in tasks_config[task])]
    payloads = []
    if payload_tasks:
        payload_menu_choices = []
        payload_folder = os.path.join(os.getcwd(), "payloads")
        payload_files = list_files_in_folder(payload_folder)
        payload_menu_choices += [f"[Payloads] {os.path.basename(p)}" for p in payload_files]
        payload_menu_choices += ["[Custom] Enter local file path", "[Custom] Enter URL"]
        selected = questionary.checkbox(
            "Select payloads to use:",
            choices=payload_menu_choices
        ).ask()
        for sel in selected:
            if sel.startswith("[Payloads]"):
                payloads.append(os.path.join(payload_folder, sel.replace("[Payloads] ", "")))
            elif sel == "[Custom] Enter local file path":
                path = questionary.path("Enter path to a payload:").ask()
                if validate_local_file(path):
                    payloads.append(path)
                else:
                    console.print(f"[red]File not found or not readable: {path}")
            elif sel == "[Custom] Enter URL":
                url = questionary.text("Enter URL to a payload:").ask()
                try:
                    tmp_path = download_file(url)
                    payloads.append(tmp_path)
                except Exception as e:
                    console.print(f"[red]Failed to download: {e}")
    else:
        payloads = []

    # 4. Tool check
    missing_tools = check_tools(selected_tasks, tasks_config, tools_config)
    # Extra install info for new/suggested tools
    extra_tool_info = {
        "findomain": {
            "linux": "wget https://github.com/Edu4rdSHL/findomain/releases/latest/download/findomain-linux.zip && unzip findomain-linux.zip && sudo mv findomain /usr/local/bin/",
            "windows": "Download Windows binary from GitHub releases, add to PATH",
            "note": "Findomain is a fast subdomain enumerator. Download the binary for your OS and add it to your PATH."
        },
        "dnsx": {
            "linux": "go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "dnsx is a fast DNS resolver. Ensure Go bin directory is in your PATH."
        },
        "gowitness": {
            "linux": "go install github.com/sensepost/gowitness@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "gowitness is a screenshot tool. Ensure Go bin directory is in your PATH."
        },
        "jsfinder": {
            "linux": "git clone https://github.com/Threezh1/JSFinder.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "JSFinder is a JS endpoint discovery tool. Run with Python3."
        },
        "SecretFinder": {
            "linux": "git clone https://github.com/m4ll0k/SecretFinder.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "SecretFinder finds secrets in JS files. Run with Python3."
        },
        "paramspider": {
            "linux": "git clone https://github.com/devanshbatham/paramspider.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "ParamSpider discovers parameters. Run with Python3."
        },
        "dalfox": {
            "linux": "go install github.com/hahwul/dalfox@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "Dalfox is a fast XSS scanner. Ensure Go bin directory is in your PATH."
        },
        "kxss": {
            "linux": "go install github.com/tomnomnom/kxss@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "KXSS finds reflected XSS params. Ensure Go bin directory is in your PATH."
        },
        "ssrfmap": {
            "linux": "git clone https://github.com/swisskyrepo/SSRFmap.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "SSRFmap automates SSRF testing. Run with Python3."
        },
        "liffy": {
            "linux": "git clone https://github.com/D35m0nd142/Liffy.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "Liffy is an LFI fuzzing tool. Run with Python3."
        },
        "testssl.sh": {
            "linux": "git clone https://github.com/drwetter/testssl.sh.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "testssl.sh checks SSL/TLS configs. Run the script directly."
        },
        "apkleaks": {
            "linux": "pip install apkleaks",
            "windows": "pipx install apkleaks or ensure Scripts dir in PATH",
            "note": "Apkleaks scans APKs for secrets."
        },
        "gau": {
            "linux": "go install github.com/lc/gau/v2/cmd/gau@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "gau collects URLs from public sources."
        },
        "s3scanner": {
            "linux": "go install github.com/sa7mon/S3Scanner@latest",
            "windows": "Install Go, run command, add Go bin to PATH",
            "note": "S3Scanner checks S3 buckets."
        },
        "wpscan": {
            "linux": "sudo gem install wpscan",
            "windows": "Download Windows binary or use WSL",
            "note": "WPScan scans WordPress sites. Requires Ruby."
        },
        "gittools": {
            "linux": "git clone https://github.com/internetwache/GitTools.git",
            "windows": "Use WSL or follow README for Windows setup",
            "note": "GitTools is a suite for .git repo extraction."
        }
    }
    if missing_tools:
        console.print("[red]The following required tool(s) are missing. Please install them manually before proceeding.\n")
        for tool, install_cmd in missing_tools.items():
            console.print(f"[bold]{tool}[/bold]")
            # Check if tool is in extra_tool_info
            if tool in extra_tool_info:
                info = extra_tool_info[tool]
                console.print(f"  [yellow]Linux install:[/yellow] {info['linux']}")
                console.print(f"  [yellow]Windows install:[/yellow] {info['windows']}")
                console.print(f"  [blue]Note:[/blue] {info['note']}")
            else:
                console.print(f"  [yellow]Linux install:[/yellow] {install_cmd}")
                # Suggest a Windows install if possible, else generic message
                extra_info = None
                if install_cmd.startswith("pip install"):
                    win_cmd = install_cmd.replace("sudo ", "")
                    console.print(f"  [yellow]Windows install:[/yellow] {win_cmd}")
                    extra_info = f"For global use, consider using 'pipx install {tool}' or ensure your Python Scripts directory is in your PATH."
                elif install_cmd.startswith("go install"):
                    console.print(f"  [yellow]Windows install:[/yellow] Install Go, run command, add Go bin to PATH")
                    extra_info = "Go installs binaries to $GOPATH/bin or $HOME/go/bin. Add this directory to your PATH for global use. On Windows, add %USERPROFILE%\\go\\bin to your PATH."
                elif install_cmd.startswith("git clone"):
                    console.print(f"  [yellow]Windows install:[/yellow] Install Git, then run: {install_cmd}")
                    extra_info = "After cloning, follow the tool's README for setup. For global use, you may need to move the script or binary to a directory in your PATH (e.g., /usr/local/bin or C:/Windows/System32)."
                elif install_cmd.startswith("sudo apt install"):
                    console.print(f"  [yellow]Windows install:[/yellow] Use WSL or install the tool manually from its website.")
                    extra_info = "If using WSL, run the Linux command above. Otherwise, download the tool from its official website and add it to your PATH."
                else:
                    console.print(f"  [yellow]Windows install:[/yellow] Please refer to the tool's documentation.")
                if extra_info:
                    console.print(f"  [blue]Note:[/blue] {extra_info}")
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

def main():
    app.command()(cli)
    app()