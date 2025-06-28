import os
import tempfile
import shutil
from core import utils

def test_save_and_load_targets():
    targets = ['example.com', 'test.com']
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, 'targets.txt')
        utils.save_targets(targets, path)
        loaded = utils.load_targets(path)
        assert loaded == targets

def test_prepare_output_dirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        target = 'example.com'
        selected_tasks = ['Automated Subdomain Enumeration', 'Automated Port Scanning']
        target_dir = utils.prepare_output_dirs(tmpdir, target, selected_tasks)
        assert os.path.isdir(target_dir)
        for sub in ['subdomains', 'ports', 'screenshots', 'logs']:
            assert os.path.isdir(os.path.join(target_dir, sub))
