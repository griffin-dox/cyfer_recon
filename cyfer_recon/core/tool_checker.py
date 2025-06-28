import shutil
import subprocess
from typing import Dict, List, Any, Optional

def check_tools(selected_tasks: List[str], tasks_config: Dict[str, Any], tools_config: Dict[str, Any]) -> Dict[str, str]:
    """
    Check for missing tools required by the selected tasks.
    Returns a dict of missing tool names to their install commands.
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
        if shutil.which(tools_config[tool]['check']) is None:
            missing[tool] = tools_config[tool]['install']
    return missing

def install_tools(missing_tools: Dict[str, str], console: Optional[Any] = None) -> None:
    """
    Attempt to install missing tools globally using their install commands.
    Logs output to the provided console if available.
    """
    for tool, install_cmd in missing_tools.items():
        if console:
            console.print(f"[cyan]Installing [bold]{tool}[/bold] with: {install_cmd}")
        try:
            subprocess.run(install_cmd, shell=True, check=True)
            if console:
                console.print(f"[green]Successfully installed {tool}")
        except subprocess.CalledProcessError as e:
            if console:
                console.print(f"[red]Failed to install {tool}: {e}")
            else:
                print(f"Failed to install {tool}: {e}")
