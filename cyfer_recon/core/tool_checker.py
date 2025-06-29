import shutil
from typing import Dict, List, Any

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
