import os
import tempfile
from core import task_runner
from rich.console import Console

def test_run_task_for_target(tmp_path):
    # Simulate a harmless echo command
    target = 'example.com'
    task = 'Test Task'
    commands = ["echo Hello {target} > {output}/logs/echo.txt"]
    output_dir = tmp_path
    console = Console()
    task_runner.run_task_for_target(target, task, commands, str(output_dir), console)
    log_file = os.path.join(output_dir, target, 'logs', 'test_task.log')
    assert os.path.isfile(log_file)

# Note: Full run_tasks concurrency/sequential tests would require more advanced mocking of subprocess and threading.
