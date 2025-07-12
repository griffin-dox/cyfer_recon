import subprocess
import os
import re
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn, TimeRemainingColumn
from cyfer_recon.core.utils import ToolNotFoundError, TaskExecutionError, send_discord_notification

def get_tool_and_ext(cmd: str) -> Tuple[str, str]:
    """Extract tool name and output file extension from a command string."""
    tool = cmd.split()[0]
    # Try to guess extension from command (default to .txt)
    match = re.search(r'-o(?:N|G)?\s+([^\s]+)', cmd)
    if match:
        out_file = match.group(1)
        ext = os.path.splitext(out_file)[1] or '.txt'
    elif '>' in cmd:
        # e.g. tool ... > file.ext
        parts = cmd.split('>')
        if len(parts) > 1:
            ext = os.path.splitext(parts[1].strip())[1] or '.txt'
        else:
            ext = '.txt'
    else:
        ext = '.txt'
    return tool, ext

def run_task_for_target(target: str, task: str, commands: List[str], output_dir: str, console: Any, progress: Progress = None, parent_task_id: int = None, discord_webhook: str = None) -> None:
    """
    Run all commands for a given target and task, saving output and logs.
    Shows a progress bar for each tool.
    Improved error handling: logs tool, command, exit code, stdout, stderr for each failure.
    Now prints concise error info to the console instead of writing log files.
    """
    task_dir = output_dir
    # logs_dir = os.path.join(task_dir, 'logs')
    # os.makedirs(logs_dir, exist_ok=True)
    total_cmds = len(commands)
    failed_cmds = []
    for idx, cmd in enumerate(commands):
        tool, ext = get_tool_and_ext(cmd)
        result_file = os.path.join(task_dir, f"{tool}_{task.replace(' ', '_').lower()}_{idx+1}{ext}")
        # Ensure the output directory exists for redirected files
        os.makedirs(os.path.dirname(result_file), exist_ok=True)
        cmd_fmt = cmd.replace('{target}', target).replace('{output}', task_dir)
        def output_repl(m):
            return m.group(1) + result_file
        cmd_fmt = re.sub(r'(-o(?:N|G)?\s+)[^\s]+', output_repl, cmd_fmt)
        if '>' in cmd_fmt:
            def redir_repl(match):
                return f'> "{result_file}"'
            cmd_fmt = re.sub(r'>\s*[^\s]+', redir_repl, cmd_fmt)

        import shutil
        if shutil.which(tool) is None:
            error_msg = f"Tool '{tool}' not found in PATH."
            console.print(f"[red]{error_msg}")
            if discord_webhook:
                send_discord_notification(discord_webhook, f"[ERROR] {error_msg}")
            raise ToolNotFoundError(error_msg)

        try:
            process = subprocess.run(cmd_fmt, shell=True, capture_output=True, text=True)
            if process.returncode != 0:
                raise TaskExecutionError(tool, cmd_fmt, process.returncode, process.stdout, process.stderr)
        except TaskExecutionError as e:
            console.print(f"[red]{e}")
            if discord_webhook:
                send_discord_notification(discord_webhook, f"[ERROR] {e}")
            failed_cmds.append({
                'tool': e.tool,
                'cmd': e.cmd,
                'exit_code': e.exit_code,
                'stdout': e.stdout,
                'stderr': e.stderr
            })
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}")
            if discord_webhook:
                send_discord_notification(discord_webhook, f"[ERROR] Unexpected error: {e}")
            failed_cmds.append({
                'tool': tool,
                'cmd': cmd_fmt,
                'exit_code': None,
                'stdout': '',
                'stderr': str(e)
            })
        finally:
            # Progress is handled at the parent task level
            pass

    if failed_cmds and discord_webhook:
        send_discord_notification(discord_webhook, f"[ERROR] Failed commands for {target} - {task}: {failed_cmds}")

    if progress is not None and parent_task_id is not None:
        progress.advance(parent_task_id, 1)
    if failed_cmds:
        console.print(f"[red]Failed commands for {target} - {task}:")
        for fc in failed_cmds:
            console.print(f"[red]  Tool: {fc['tool']} | Exit code: {fc['exit_code']} | Error: {fc['stderr'].strip().splitlines()[-1] if fc['stderr'].strip() else 'No stderr output.'}")

def run_tasks(targets: List[str], selected_tasks: List[str], tasks_config: Dict[str, Any], output_dir: str, concurrent: bool, console: Any, wordlists: dict = None, dry_run: bool = False, discord_webhook: str = None) -> None:
    """
    Run all selected tasks for all targets, respecting individual task run_mode settings.
    For commands with {wordlist}, use the tool-specific wordlist from the mapping.
    If dry_run is True, print commands instead of executing them.

    Args:
        targets (List[str]): List of target domains/hosts.
        selected_tasks (List[str]): List of task names to run.
        tasks_config (Dict[str, Any]): Task configuration dictionary.
        output_dir (str): Output directory for results.
        concurrent (bool): Whether to run tasks concurrently (can be overridden by task run_mode).
        console (Any): Rich console for output.
        wordlists (dict, optional): Mapping of tool name to wordlist path. Defaults to None.
        dry_run (bool, optional): If True, print commands instead of running. Defaults to False.
        discord_webhook (str, optional): Discord webhook URL for notifications. Defaults to None.

    Returns:
        None
    """
    if wordlists is None:
        wordlists = {}
    
    jobs = []
    for target in targets:
        for task in selected_tasks:
            task_config = tasks_config.get(task, [])
            
            # Handle both old format (list) and new format (dict with commands and run_mode)
            if isinstance(task_config, list):
                commands = task_config
                run_mode = "both"  # Default for old format
            else:
                commands = task_config.get("commands", [])
                run_mode = task_config.get("run_mode", "both")
            
            # Determine if this task should run concurrently
            task_concurrent = concurrent
            if run_mode == "sequential":
                task_concurrent = False
            elif run_mode == "concurrent":
                task_concurrent = True
            # If run_mode == "both", use the user's choice (task_concurrent = concurrent)
            
            for cmd in commands:
                if "{wordlist}" in cmd:
                    tool = cmd.split()[0]
                    wordlist = wordlists.get(tool)
                    if wordlist:
                        wl_name = os.path.splitext(os.path.basename(wordlist))[0]
                        cmd_wl = cmd.replace("{wordlist}", wordlist)
                        cmd_wl = re.sub(r'(ffuf|gobuster|kiterunner)([^>]*)(-o\s*|>\s*)([^\s]+)',
                                        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{output_dir}/{m.group(1)}_{wl_name}.txt",
                                        cmd_wl)
                        jobs.append((target, task, [cmd_wl], task_concurrent))
                else:
                    jobs.append((target, task, [cmd], task_concurrent))
    
    if dry_run:
        console.print("[yellow]Dry run mode: The following commands would be executed:")
        for t, task, cmds, task_conc in jobs:
            mode = "concurrent" if task_conc else "sequential"
            console.print(f"[yellow]{t} - {task} ({mode}): {cmds}")
        return

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TimeElapsedColumn(), TimeRemainingColumn()) as progress:
        parent_task_id = progress.add_task("Overall Progress", total=len(jobs))
        
        # Group jobs by concurrency mode
        concurrent_jobs = [(t, task, cmds) for t, task, cmds, task_conc in jobs if task_conc]
        sequential_jobs = [(t, task, cmds) for t, task, cmds, task_conc in jobs if not task_conc]
        
        # Run concurrent jobs
        if concurrent_jobs:
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(run_task_for_target, t, task, cmds, output_dir, console, progress, parent_task_id, discord_webhook): (t, task)
                    for t, task, cmds in concurrent_jobs
                }
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        console.print(f"[red]Error in task {futures[future]}: {e}")
        
        # Run sequential jobs
        for t, task, cmds in sequential_jobs:
            run_task_for_target(t, task, cmds, output_dir, console, progress, parent_task_id, discord_webhook)

def deduplicate_subdomains(subdomain_files: list, output_file: str, console=None, sort_result=True):
    """Combine, deduplicate, and clean subdomain results from multiple files."""
    subdomains = set()
    for file in subdomain_files:
        if os.path.isfile(file):
            with open(file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        subdomains.add(line)
    if sort_result:
        subdomains = sorted(subdomains)
    with open(output_file, 'w', encoding='utf-8') as f:
        for sub in subdomains:
            f.write(f"{sub}\n")
    if console:
        console.print(f"[green]Deduplicated subdomains saved to {output_file} ({len(subdomains)} unique)")
    return output_file

def check_live_subdomains(input_file: str, output_file: str, console=None, tool_preference='httpx', status_codes=None):
    """Check which subdomains are alive using httpx (preferred) or dnsx."""
    import shutil
    if not os.path.isfile(input_file):
        if console:
            console.print(f"[yellow]Input file {input_file} not found. Skipping live check.")
        return
    if status_codes is None:
        status_codes = [200, 301, 302, 403, 401]
    # Prefer httpx
    if tool_preference == 'httpx' and shutil.which('httpx'):
        cmd = f"cat {input_file} | httpx -silent -status-code -o {output_file}"
        if status_codes:
            codes = ','.join(str(c) for c in status_codes)
            cmd = f"cat {input_file} | httpx -silent -status-code -o {output_file} -mc {codes}"
        tool_used = 'httpx'
    elif shutil.which('dnsx'):
        cmd = f"cat {input_file} | dnsx -silent -o {output_file}"
        tool_used = 'dnsx'
    else:
        if console:
            console.print("[yellow]Neither httpx nor dnsx found. Skipping live subdomain check.")
        return
    try:
        subprocess.run(cmd, shell=True, check=True)
        if console:
            console.print(f"[green]Live subdomains checked with {tool_used}, results saved to {output_file}")
    except Exception as e:
        if console:
            console.print(f"[red]Error running {tool_used} for live subdomain check: {e}")

def postprocess_subdomains(target_dir: str, console=None, skip_live_check=False, tool_preference='httpx', status_codes=None):
    """Deduplicate and check live subdomains for a target directory."""
    # Find all subdomain output files
    subdomain_files = []
    subdomain_dir = os.path.join(target_dir, 'subdomains')
    if os.path.isdir(subdomain_dir):
        for f in os.listdir(subdomain_dir):
            if f.endswith('.txt'):
                subdomain_files.append(os.path.join(subdomain_dir, f))
    # Add findomain, dnsx, etc. if present in main dir
    for f in ['findomain.txt', 'dnsx.txt']:
        fpath = os.path.join(subdomain_dir, f)
        if os.path.isfile(fpath):
            subdomain_files.append(fpath)
    unique_file = os.path.join(target_dir, 'unique_subdomains.txt')
    deduplicate_subdomains(subdomain_files, unique_file, console=console)
    if not skip_live_check:
        live_file = os.path.join(target_dir, 'live_subdomains.txt')
        check_live_subdomains(unique_file, live_file, console=console, tool_preference=tool_preference, status_codes=status_codes)

def run_custom_commands(target: str, commands: List[str], output_dir: str, concurrent: bool, console: Any, wordlists: dict = None, dry_run: bool = False, discord_webhook: str = None) -> None:
    """
    Run custom commands for a target with progress bars.
    
    Args:
        target (str): Target domain/host.
        commands (List[str]): List of commands to run.
        output_dir (str): Output directory for results.
        concurrent (bool): Whether to run commands concurrently.
        console (Any): Rich console for output.
        wordlists (dict, optional): Mapping of tool name to wordlist path. Defaults to None.
        dry_run (bool, optional): If True, print commands instead of running. Defaults to False.
        discord_webhook (str, optional): Discord webhook URL for notifications. Defaults to None.
    """
    if wordlists is None:
        wordlists = {}
    
    # Process commands and substitute placeholders
    processed_commands = []
    for cmd in commands:
        # Replace target placeholder
        cmd_processed = cmd.replace('{target}', target).replace('{output}', output_dir)
        
        # Handle wordlist placeholder
        if "{wordlist}" in cmd_processed:
            tool = cmd.split()[0]
            wordlist = wordlists.get(tool)
            if wordlist:
                cmd_processed = cmd_processed.replace("{wordlist}", wordlist)
            else:
                console.print(f"[yellow]Warning: No wordlist configured for {tool}, skipping command.")
                continue
        
        processed_commands.append(cmd_processed)
    
    if dry_run:
        console.print(f"[yellow]Dry run mode - commands for {target}:")
        for cmd in processed_commands:
            console.print(f"[yellow]  {cmd}")
        return
    
    # Execute commands
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), TimeElapsedColumn(), TimeRemainingColumn()) as progress:
        parent_task_id = progress.add_task("Overall Progress", total=len(processed_commands))
        
        failed_cmds = []
        
        if concurrent:
            with ThreadPoolExecutor() as executor:
                futures = {
                    executor.submit(execute_single_command, cmd, output_dir, console, discord_webhook): cmd
                    for cmd in processed_commands
                }
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        failed_cmds.append({"cmd": futures[future], "error": str(e)})
                        console.print(f"[red]Error in command {futures[future]}: {e}")
                    finally:
                        progress.advance(parent_task_id, 1)
        else:
            for cmd in processed_commands:
                try:
                    execute_single_command(cmd, output_dir, console, discord_webhook)
                except Exception as e:
                    failed_cmds.append({"cmd": cmd, "error": str(e)})
                    console.print(f"[red]Error in command {cmd}: {e}")
                finally:
                    progress.advance(parent_task_id, 1)
        
        if failed_cmds and discord_webhook:
            send_discord_notification(discord_webhook, f"[ERROR] Failed commands for {target}: {failed_cmds}")

def execute_single_command(cmd: str, output_dir: str, console: Any, discord_webhook: str = None) -> None:
    """Execute a single command with error handling."""
    tool = cmd.split()[0]
    
    # Check if tool exists
    import shutil
    if shutil.which(tool) is None:
        error_msg = f"Tool '{tool}' not found in PATH."
        console.print(f"[red]{error_msg}")
        if discord_webhook:
            send_discord_notification(discord_webhook, f"[ERROR] {error_msg}")
        raise ToolNotFoundError(error_msg)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        process = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=output_dir)
        if process.returncode != 0:
            raise TaskExecutionError(tool, cmd, process.returncode, process.stdout, process.stderr)
    except TaskExecutionError as e:
        console.print(f"[red]{e}")
        if discord_webhook:
            send_discord_notification(discord_webhook, f"[ERROR] {e}")
        raise
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}")
        if discord_webhook:
            send_discord_notification(discord_webhook, f"[ERROR] Unexpected error: {e}")
        raise
