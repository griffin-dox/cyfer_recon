import os
import json
from .config_utils import CONFIG_DIR, USER_WORDLISTS, USER_PAYLOADS, DEFAULT_WORDLISTS, DEFAULT_PAYLOADS, save_user_config

def prompt_personalize(defaults, config_type):
    print(f"\nPersonalize {config_type} for each tool (press Enter to keep default):")
    user_config = {}
    for tool, default in defaults.items():
        val = input(f"{tool} [{default}]: ").strip()
        if val:
            user_config[tool] = val
    return user_config

def first_run_personalization():
    # Only run if user config does not exist
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(USER_WORDLISTS):
        with open(DEFAULT_WORDLISTS) as f:
            defaults = json.load(f)
        print("\n[Optional] Personalize wordlists for each tool:")
        user_wordlists = prompt_personalize(defaults, "wordlists")
        if user_wordlists:
            save_user_config(USER_WORDLISTS, user_wordlists)
    if not os.path.exists(USER_PAYLOADS):
        with open(DEFAULT_PAYLOADS) as f:
            defaults = json.load(f)
        print("\n[Optional] Personalize payloads for each tool:")
        user_payloads = prompt_personalize(defaults, "payloads")
        if user_payloads:
            save_user_config(USER_PAYLOADS, user_payloads)
