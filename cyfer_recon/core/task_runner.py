import subprocess
import os
import re
from typing import List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn, SpinnerColumn, TaskID
from rich.console import Console
from rich.style import Style

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
            bar_task_id = progress.add_task(f"{tool}", status="Running")
        try:
            with open(log_file, 'a', encoding='utf-8') as lf:
                if progress is not None and bar_task_id is not None:
                    progress.update(bar_task_id, status="Running")
                process = subprocess.run(cmd_fmt, shell=True, capture_output=True, text=True)
                if process.returncode == 0:
                    if progress is not None and bar_task_id is not None:
                        progress.update(bar_task_id, status="Finished")
                else:
                    if progress is not None and bar_task_id is not None:
                        progress.update(bar_task_id, status="[red]Error")
                lf.write(f"$ {cmd_fmt}\n{process.stdout}\n{process.stderr}\n")
        except Exception as e:
            if progress is not None and bar_task_id is not None:
                progress.update(bar_task_id, status="[red]Error")
            console.print(f"[red]Error running {cmd_fmt}: {e}")
        finally:
            if progress is not None and bar_task_id is not None:
                progress.remove_task(bar_task_id)
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
    progress_columns = [
        SpinnerColumn(),
        TextColumn("{task.description}", justify="right"),
        BarColumn(),
        TextColumn("[bold]{task.fields[status]}", justify="left"),
        TimeElapsedColumn(),
    ]
    with Progress(*progress_columns) as progress:
        parent_task_id = progress.add_task("All Tasks", total=len(jobs), status="Running")
        def run_job(t, task, cmds):
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
                except Exception as e:
                    progress.update(bar_task_id, status="[red]Error")
                    console.print(f"[red]Error running {cmd}: {e}")
                finally:
                    progress.remove_task(bar_task_id)
            progress.advance(parent_task_id, 1)
            console.print(f"[green]Finished {task} for {t}")
        if concurrent:
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(run_job, t, task, cmds) for t, task, cmds in jobs]
                for _ in as_completed(futures):
                    pass
        else:
            for t, task, cmds in jobs:
                run_job(t, task, cmds)
