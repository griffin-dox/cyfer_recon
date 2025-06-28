#!/bin/bash
# Cyfer Recon Automation CLI Tool Installer (for Kali Linux)
# This script will install dependencies and set up the CLI tool globally

set -e

# 1. Install Python dependencies
pip3 install --user typer rich questionary

# 2. Install pytest for testing (optional)
pip3 install --user pytest

# 3. Create a global symlink for the CLI tool
INSTALL_PATH="/usr/local/bin/cyfer-recon"
SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)/main.py"

if [ -L "$INSTALL_PATH" ]; then
    sudo rm "$INSTALL_PATH"
fi
sudo ln -s "$SCRIPT_PATH" "$INSTALL_PATH"
sudo chmod +x "$SCRIPT_PATH"

# 4. Print success message
cat <<EOF

[+] Cyfer Recon CLI installed!

You can now run the tool from anywhere with:

    cyfer-recon

EOF
