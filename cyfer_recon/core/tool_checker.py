import os
import shutil
from typing import Dict, List, Any

def check_tools(selected_tasks: List[str], tasks_config: Dict[str, Any], tools_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Check for missing tools required by the selected tasks.
    Returns a dict of missing tool names to their install commands.
    Supports checking for files in both the project wordlists/ dir and /usr/share/wordlists/ for wordlists.
    """
    required_tools = set()
    for task in selected_tasks:
        commands = tasks_config.get(task, [])
        for cmd in commands:
            tool = cmd.split()[0]
            if tool in tools_config:
                required_tools.add(tool)
    missing = {}
    for tool in required_tools:
        check_val = tools_config[tool]['check']
        if check_val.startswith('file:'):
            # Support multiple locations for wordlists
            file_path = check_val.split(':', 1)[1]
            found = False
            # Check original location
            if os.path.isfile(file_path):
                found = True
            # If not found, check in project wordlists/ dir (basename only)
            elif os.path.basename(file_path) != file_path:
                alt_path = os.path.join('wordlists', os.path.basename(file_path))
                if os.path.isfile(alt_path):
                    found = True
            if not found:
                missing[tool] = tools_config[tool]['install']
        else:
            if shutil.which(check_val) is None:
                missing[tool] = tools_config[tool]['install']
    return missing
