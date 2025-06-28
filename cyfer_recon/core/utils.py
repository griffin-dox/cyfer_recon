import os
import json
import tempfile
import urllib.request
from typing import List, Optional

def load_targets(path: str) -> List[str]:
    """Load targets from a file, one per line."""
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def save_targets(targets: List[str], path: str = 'targets.txt') -> None:
    """Save a list of targets to a file, one per line."""
    with open(path, 'w', encoding='utf-8') as f:
        for t in targets:
            f.write(f"{t}\n")

def prepare_output_dirs(base_dir: str, target: str, selected_tasks: List[str], extra_folders: Optional[List[str]] = None) -> str:
    """
    Create the main output directory and subfolders for each task.
    Returns the path to the output directory.
    """
    os.makedirs(base_dir, exist_ok=True)
    subfolders = ['subdomains', 'ports', 'screenshots', 'logs']
    # Add extra folders for output (e.g., js, gitdump, etc.)
    if extra_folders:
        for folder in extra_folders:
            if folder not in subfolders:
                subfolders.append(folder)
    for sub in subfolders:
        os.makedirs(os.path.join(base_dir, sub), exist_ok=True)
    return base_dir

def list_files_in_folder(folder: str, extensions: Optional[List[str]] = None) -> List[str]:
    """List files in a folder, optionally filtering by extension(s)."""
    if not os.path.isdir(folder):
        return []
    files = [os.path.join(folder, f) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
    if extensions:
        files = [f for f in files if any(f.lower().endswith(ext) for ext in extensions)]
    return files

def download_file(url: str) -> str:
    """Download a file from a URL to a temporary file. Returns the local path."""
    tmp_fd, tmp_path = tempfile.mkstemp()
    os.close(tmp_fd)
    try:
        urllib.request.urlretrieve(url, tmp_path)
        return tmp_path
    except Exception as e:
        os.remove(tmp_path)
        raise RuntimeError(f"Failed to download {url}: {e}")

def validate_local_file(path: str) -> bool:
    """Check if a local file exists and is readable."""
    return os.path.isfile(path) and os.access(path, os.R_OK)
