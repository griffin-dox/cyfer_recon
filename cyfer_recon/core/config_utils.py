import os
import json

CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cyfer_recon")
USER_WORDLISTS = os.path.join(CONFIG_DIR, "wordlists.json")
USER_PAYLOADS = os.path.join(CONFIG_DIR, "payloads.json")
DEFAULT_WORDLISTS = os.path.join(os.path.dirname(__file__), "..", "config", "wordlists.json")
DEFAULT_PAYLOADS = os.path.join(os.path.dirname(__file__), "..", "config", "payloads.json")

def ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)

def load_config(default_path, user_path):
    with open(default_path) as f:
        default = json.load(f)
    if os.path.exists(user_path):
        with open(user_path) as f:
            user = json.load(f)
        default.update(user)
    return default

def save_user_config(user_path, data):
    ensure_config_dir()
    with open(user_path, "w") as f:
        json.dump(data, f, indent=2)
