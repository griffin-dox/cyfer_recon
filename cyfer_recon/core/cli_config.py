import os
import json
from .config_utils import CONFIG_DIR, USER_WORDLISTS, USER_PAYLOADS, save_user_config

def set_wordlist(tool, path):
    if not os.path.isfile(path):
        print(f"[ERROR] Wordlist file not found: {path}")
        return
    if os.path.exists(USER_WORDLISTS):
        with open(USER_WORDLISTS) as f:
            data = json.load(f)
    else:
        data = {}
    data[tool] = path
    save_user_config(USER_WORDLISTS, data)
    print(f"[OK] Set wordlist for {tool} to {path}")

def set_payload(tool, path):
    if not os.path.isfile(path):
        print(f"[ERROR] Payload file not found: {path}")
        return
    if os.path.exists(USER_PAYLOADS):
        with open(USER_PAYLOADS) as f:
            data = json.load(f)
    else:
        data = {}
    data[tool] = path
    save_user_config(USER_PAYLOADS, data)
    print(f"[OK] Set payload for {tool} to {path}")

def show_config(config_type):
    if config_type == "wordlist":
        path = USER_WORDLISTS
    elif config_type == "payload":
        path = USER_PAYLOADS
    else:
        print("[ERROR] Unknown config type.")
        return
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        print(json.dumps(data, indent=2))
    else:
        print(f"[INFO] No user {config_type} config found.")
