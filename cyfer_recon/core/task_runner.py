import subprocess
import os
import re
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TaskProgressColumn, TimeElapsedColumn

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
    """
    task_dir = output_dir
    logs_dir = os.path.join(task_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    total_cmds = len(commands)
    for idx, cmd in enumerate(commands):
        tool, ext = get_tool_and_ext(cmd)
        result_file = os.path.join(task_dir, f"{tool}_result{ext}")
        cmd_fmt = cmd.replace('{target}', target).replace('{output}', task_dir)
        cmd_fmt = re.sub(r'(-o(?:N|G)?\s+)[^\s]+', f"\\1{result_file}", cmd_fmt)
        if '>' in cmd_fmt:
            cmd_fmt = re.sub(r'>\s*[^\s]+', f'> {result_file}', cmd_fmt)
        log_file = os.path.join(logs_dir, f"{task.replace(' ', '_').lower()}.log")
        bar_task_id = None
        if progress is not None:
            bar_task_id = progress.add_task(f"{tool}", total=100)
        try:
            with open(log_file, 'a', encoding='utf-8') as lf:
                # Simulate progress bar for the tool (since subprocess.run is blocking)
                if progress is not None and bar_task_id is not None:
                    progress.update(bar_task_id, completed=0)
                process = subprocess.run(cmd_fmt, shell=True, capture_output=True, text=True)
                if progress is not None and bar_task_id is not None:
                    progress.update(bar_task_id, completed=100)
                lf.write(f"$ {cmd_fmt}\n{process.stdout}\n{process.stderr}\n")
        except Exception as e:
            console.print(f"[red]Error running {cmd_fmt}: {e}")
        finally:
            if progress is not None and bar_task_id is not None:
                progress.remove_task(bar_task_id)
        # Optionally update parent progress
        if progress is not None and parent_task_id is not None:
            progress.advance(parent_task_id, 1)

def run_tasks(targets: List[str], selected_tasks: List[str], tasks_config: Dict[str, Any], output_dir: str, concurrent: bool, console: Any) -> None:
    """
    Run all selected tasks for all targets, concurrently or sequentially, with progress bars.
    """
    jobs = []
    for target in targets:
        for task in selected_tasks:
            commands = tasks_config.get(task, [])
            jobs.append((target, task, commands))
    tool_columns = [
        TextColumn("{task.fields[tool_name]}", justify="right"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.percentage:>3.0f}/100")
    ]
    all_tasks_columns = [
        TextColumn("{task.description}", justify="right"),
        BarColumn(),
        TaskProgressColumn(),
        TextColumn("{task.percentage:>3.0f}/100")
    ]
    if concurrent:
        with Progress(*all_tasks_columns, TimeElapsedColumn()) as all_progress:
            parent_task_id = all_progress.add_task("All Tasks", total=len(jobs))
            with Progress(*tool_columns, TimeElapsedColumn()) as tool_progress:
                with ThreadPoolExecutor() as executor:
                    futures = [executor.submit(run_task_for_target, t, task, cmds, output_dir, console, tool_progress, parent_task_id) for t, task, cmds in jobs]
                    for _ in as_completed(futures):
                        all_progress.advance(parent_task_id, 1)
    else:
        with Progress(*all_tasks_columns, TimeElapsedColumn()) as all_progress:
            parent_task_id = all_progress.add_task("All Tasks", total=len(jobs))
            with Progress(*tool_columns, TimeElapsedColumn()) as tool_progress:
                for t, task, cmds in jobs:
                    for cmd in cmds:
                        tool, _ = get_tool_and_ext(cmd)
                        bar_task_id = tool_progress.add_task(f"{tool}", total=100, tool_name=tool)
                        tool_progress.update(bar_task_id, completed=0)
                        try:
                            process = subprocess.run(cmd.replace('{target}', t).replace('{output}', output_dir), shell=True, capture_output=True, text=True)
                            tool_progress.update(bar_task_id, completed=100)
                        except Exception as e:
                            console.print(f"[red]Error running {cmd}: {e}")
                        finally:
                            tool_progress.remove_task(bar_task_id)
                    all_progress.advance(parent_task_id, 1)
                    console.print(f"[green]Finished {task} for {t}")
