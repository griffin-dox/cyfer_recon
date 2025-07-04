import subprocess
import os
import re
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn, TimeRemainingColumn

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

def run_task_for_target(target: str, task: str, commands: List[str], output_dir: str, console: Any, progress: Progress = None, parent_task_id: int = None) -> None:
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
        # log_file = os.path.join(logs_dir, f"{task.replace(' ', '_').lower()}.log")
        bar_task_id = None
        if progress is not None:
            bar_task_id = progress.add_task(f"{tool}", status="Running")
        import shutil
        if shutil.which(tool) is None:
            error_msg = f"[ERROR] Tool '{tool}' not found in PATH."
            console.print(f"[red]{error_msg} Please install it before running this task.")
            failed_cmds.append({
                'tool': tool,
                'cmd': cmd_fmt,
                'exit_code': None,
                'stdout': '',
                'stderr': error_msg
            })
            continue
        try:
            if progress is not None and bar_task_id is not None:
                progress.update(bar_task_id, status="Running")
            process = subprocess.run(cmd_fmt, shell=True, capture_output=True, text=True)
            if process.returncode == 0:
                if progress is not None and bar_task_id is not None:
                    progress.update(bar_task_id, status="Finished")
            else:
                if progress is not None and bar_task_id is not None:
                    progress.update(bar_task_id, status="[red]Error")
                failed_cmds.append({
                    'tool': tool,
                    'cmd': cmd_fmt,
                    'exit_code': process.returncode,
                    'stdout': process.stdout,
                    'stderr': process.stderr
                })
                # Print concise error info
                console.print(f"[red][{tool}] [bold]{task}[/bold] for [yellow]{target}[/yellow]: [white]Exit code:[/white] {process.returncode}\n[white]Command:[/white] {cmd_fmt}\n[white]Error:[/white] {process.stderr.strip().splitlines()[-1] if process.stderr.strip() else 'No stderr output.'}")
        except Exception as e:
            if progress is not None and bar_task_id is not None:
                progress.update(bar_task_id, status="[red]Error")
            error_msg = f"Exception running {cmd_fmt}: {e}"
            console.print(f"[red]{error_msg}")
            failed_cmds.append({
                'tool': tool,
                'cmd': cmd_fmt,
                'exit_code': None,
                'stdout': '',
                'stderr': str(e)
            })
        finally:
            if progress is not None and bar_task_id is not None:
                progress.remove_task(bar_task_id)
        if progress is not None and parent_task_id is not None:
            progress.advance(parent_task_id, 1)
    if failed_cmds:
        console.print(f"[red]Failed commands for {target} - {task}:")
        for fc in failed_cmds:
            console.print(f"[red]  Tool: {fc['tool']} | Exit code: {fc['exit_code']} | Error: {fc['stderr'].strip().splitlines()[-1] if fc['stderr'].strip() else 'No stderr output.'}")

def run_tasks(targets: List[str], selected_tasks: List[str], tasks_config: Dict[str, Any], output_dir: str, concurrent: bool, console: Any, wordlists: dict = None, dry_run: bool = False) -> None:
    """
    Run all selected tasks for all targets, concurrently or sequentially, with progress bars.
    For commands with {wordlist}, use the tool-specific wordlist from the mapping.
    If dry_run is True, print commands instead of executing them.
    """
    if wordlists is None:
        wordlists = {}
    jobs = []
    for target in targets:
        for task in selected_tasks:
            commands = tasks_config.get(task, [])
            for cmd in commands:
                if "{wordlist}" in cmd:
                    tool = cmd.split()[0]
                    wordlist = wordlists.get(tool)
                    if wordlist:
                        wl_name = os.path.splitext(os.path.basename(wordlist))[0]
                        cmd_wl = cmd.replace("{wordlist}", wordlist)
                        # Add output file suffix for wordlist
                        cmd_wl = re.sub(r'(ffuf|gobuster|kiterunner)([^>]*)(-o\s*|>\s*)([^\s]+)',
                                        lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}{output_dir}/{m.group(1)}_{wl_name}.txt",
                                        cmd_wl)
                        jobs.append((target, task, [cmd_wl]))
                else:
                    jobs.append((target, task, [cmd]))
    if dry_run:
        console.print("[yellow]Dry run mode: The following commands would be executed:")
        for t, task, cmds in jobs:
            for cmd in cmds:
                console.print(f"[cyan]{task}[/cyan] for [green]{t}[/green]: [white]{cmd}[/white]")
        return
    progress_columns = [
        SpinnerColumn(),
        TextColumn("{task.description}", justify="right"),
        BarColumn(),
        TextColumn("[bold]{task.fields[status]}", justify="left"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),  # ETA column
    ]
    with Progress(*progress_columns) as progress:
        parent_task_id = progress.add_task("All Tasks", total=len(jobs), status="Running")
        failed_jobs = []
        def run_job(t, task, cmds):
            job_failed = False
            for cmd in cmds:
                tool, _ = get_tool_and_ext(cmd)
                bar_task_id = progress.add_task(f"{tool}", status="Running")
                progress.update(bar_task_id, status="Running")
                try:
                    process = subprocess.run(cmd.replace('{target}', t).replace('{output}', output_dir), shell=True, capture_output=True, text=True)
                    if process.returncode == 0:
                        progress.update(bar_task_id, status="Finished")
                    else:
                        progress.update(bar_task_id, status="[red]Error")
                        job_failed = True
                except Exception as e:
                    progress.update(bar_task_id, status="[red]Error")
                    console.print(f"[red]Error running {cmd}: {e}")
                    job_failed = True
                finally:
                    progress.remove_task(bar_task_id)
            progress.advance(parent_task_id, 1)
            if job_failed:
                failed_jobs.append((t, task))
            console.print(f"[green]Finished {task} for {t}")
        if concurrent:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(run_job, t, task, cmds) for t, task, cmds in jobs]
                for _ in as_completed(futures):
                    pass
        else:
            for t, task, cmds in jobs:
                run_job(t, task, cmds)
    if failed_jobs:
        console.print("[red]Summary of failed jobs:")
        for t, task in failed_jobs:
            console.print(f"[red]  {task} for {t}")

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
