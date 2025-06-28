#!/bin/bash
# Cyfer Recon Automation CLI Tool Installer (for Kali Linux, pipx version)
# This script will install dependencies and set up the CLI tool globally using pipx

set -e

# 1. Ensure pipx is installed
if ! command -v pipx &> /dev/null; then
    echo "[+] Installing pipx..."
    sudo apt update && sudo apt install -y pipx
    pipx ensurepath
fi

# 2. Install Python dependencies in an isolated pipx environment
pipx install --force --python python3 .

# 3. Print success message
cat <<EOF

[+] Cyfer Recon CLI installed with pipx!

You can now run the tool from anywhere with:

    pipx run cyfer-recon-script

Or add an entry point in setup.py for a direct command.

EOF
