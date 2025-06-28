import os
import json
from rich.console import Console

def load_targets(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_targets(targets, path='targets.txt'):
    with open(path, 'w', encoding='utf-8') as f:
        for t in targets:
            f.write(f"{t}\n")

def prepare_output_dirs(base_dir, target, selected_tasks):
    # Create per-target directory and subfolders for each task
    target_dir = os.path.join(base_dir, target)
    os.makedirs(target_dir, exist_ok=True)
    # Example subfolders (customize as needed)
    subfolders = ['subdomains', 'ports', 'screenshots', 'logs']
    for sub in subfolders:
        os.makedirs(os.path.join(target_dir, sub), exist_ok=True)
    # Optionally, create subfolders per selected task
    # for task in selected_tasks:
    #     os.makedirs(os.path.join(target_dir, task.replace(' ', '_').lower()), exist_ok=True)
    return target_dir
