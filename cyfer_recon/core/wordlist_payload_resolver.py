import os
from .config_utils import load_config, DEFAULT_WORDLISTS, USER_WORDLISTS, DEFAULT_PAYLOADS, USER_PAYLOADS

def get_wordlist_for_tool(tool):
    wordlists = load_config(DEFAULT_WORDLISTS, USER_WORDLISTS)
    return wordlists.get(tool)

def get_payload_for_tool(tool):
    payloads = load_config(DEFAULT_PAYLOADS, USER_PAYLOADS)
    return payloads.get(tool)
