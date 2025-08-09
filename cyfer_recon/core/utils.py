import os
import json
import tempfile
import urllib.request
import urllib.parse
import urllib.error
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
    subfolders = [
        'subdomains', 'ports', 'screenshots', 'logs',
        'js', 'params', 'xss', 'sqlmap', 'ssrf', 
        'api', 'urls', 's3', 'takeovers', 'cors',
        'cloud', 'dns', 'vhosts', 'tech', 'favicons',
        'github', 'dorking', 'headers', 'redirects',
        'lfi', 'vuln', 'secretfinder_results', 'linkfinder_results',
        'endpoints', 'secrets'
    ]
    # Add extra folders for output (e.g., custom folders, etc.)
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

class ToolNotFoundError(Exception):
    """Exception raised when a required tool is not found."""
    pass

class TaskExecutionError(Exception):
    """Exception raised for errors during task execution."""
    def __init__(self, tool, cmd, exit_code, stdout, stderr):
        self.tool = tool
        self.cmd = cmd
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"Error executing {tool}: {stderr}")

def send_discord_notification(webhook_url: str, message: str) -> None:
    """Send a notification to a Discord channel via webhook."""
    try:
        # Prepare the data
        data = json.dumps({"content": message}).encode('utf-8')
        
        # Create the request
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        
        # Send the request
        with urllib.request.urlopen(req) as response:
            if response.status >= 400:
                raise RuntimeError(f"Discord webhook returned status {response.status}")
                
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        raise RuntimeError(f"Failed to send Discord notification: {e}")
