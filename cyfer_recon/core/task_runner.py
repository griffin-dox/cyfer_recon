import subprocess
import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress

def get_tool_and_ext(cmd):
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

def run_task_for_target(target, task, commands, output_dir, console):
    task_dir = os.path.join(output_dir, target)
    logs_dir = os.path.join(task_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    for cmd in commands:
        tool, ext = get_tool_and_ext(cmd)
        result_file = os.path.join(task_dir, f"{tool}_result{ext}")
        # Replace {target}, {output}, and output file in command
        cmd_fmt = cmd.replace('{target}', target).replace('{output}', task_dir)
        # Replace any -o/-oN/-oG or > output with our result_file
        cmd_fmt = re.sub(r'(-o(?:N|G)?\s+)[^\s]+', f"\\1{result_file}", cmd_fmt)
        if '>' in cmd_fmt:
            cmd_fmt = re.sub(r'>\s*[^\s]+', f'> {result_file}', cmd_fmt)
        log_file = os.path.join(logs_dir, f"{task.replace(' ', '_').lower()}.log")
        try:
            with open(log_file, 'a', encoding='utf-8') as lf:
                process = subprocess.run(cmd_fmt, shell=True, capture_output=True, text=True)
                lf.write(f"$ {cmd_fmt}\n{process.stdout}\n{process.stderr}\n")
        except Exception as e:
            console.print(f"[red]Error running {cmd_fmt}: {e}")

def run_tasks(targets, selected_tasks, tasks_config, output_dir, concurrent, console):
    jobs = []
    for target in targets:
        for task in selected_tasks:
            commands = tasks_config.get(task, [])
            jobs.append((target, task, commands))
    if concurrent:
        with Progress() as progress:
            task_progress = progress.add_task("Running tasks...", total=len(jobs))
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(run_task_for_target, t, task, cmds, output_dir, console) for t, task, cmds in jobs]
                for _ in as_completed(futures):
                    progress.update(task_progress, advance=1)
    else:
        for t, task, cmds in jobs:
            run_task_for_target(t, task, cmds, output_dir, console)
            console.print(f"[green]Finished {task} for {t}")
