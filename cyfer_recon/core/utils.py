import os
import json
from typing import List
from rich.console import Console

def load_targets(path: str) -> List[str]:
    """Load targets from a file, one per line."""
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_targets(targets: List[str], path: str = 'targets.txt') -> None:
    """Save a list of targets to a file, one per line."""
    with open(path, 'w', encoding='utf-8') as f:
        for t in targets:
            f.write(f"{t}\n")

def prepare_output_dirs(base_dir: str, selected_tasks: List[str]) -> str:
    """
    Create the main output directory and subfolders for each task.
    Returns the path to the output directory.
    """
    os.makedirs(base_dir, exist_ok=True)
    subfolders = ['subdomains', 'ports', 'screenshots', 'logs']
    for sub in subfolders:
        os.makedirs(os.path.join(base_dir, sub), exist_ok=True)
    # Optionally, create subfolders per selected task
    # for task in selected_tasks:
    #     os.makedirs(os.path.join(base_dir, task.replace(' ', '_').lower()), exist_ok=True)
    return base_dir
