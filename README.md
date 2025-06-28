# 🛡️ Cyfer Recon Automation CLI Tool

A modular, extensible Python CLI tool for cybersecurity and bug bounty automation. Run 20+ recon tasks (subdomain enumeration, port scanning, screenshots, JS analysis, etc.) on multiple targets with a beautiful TUI/CLI interface.

---

## ⚡ Quick Start

### Prerequisites
- **Python 3.7+** (Linux/Kali recommended)
- **pipx** (recommended for global CLI install)
- **git**
- **Linux tools**: Many recon tools require `apt`, `go`, or other Linux utilities. See [Supported Recon Tasks](#️-supported-recon-tasks).

### For Linux/Kali/WSL Users
1. **Clone the repo:**
   ```bash
   git clone https://github.com/griffin-dox/cyfer_recon.git
   cd cyfer_recon
   ```
2. **Install pipx (if not installed):**
   ```bash
   python3 -m pip install --user pipx
   python3 -m pipx ensurepath
   # Restart your shell if needed
   ```
3. **Install Cyfer Recon globally:**
   ```bash
   pipx install --force --python python3 .
   ```
   This will:
   - Install Python dependencies in an isolated environment
   - Create a global command `cyfer-recon` you can run from anywhere

### For Windows Users
> **Strongly recommended:** Use [Windows Subsystem for Linux (WSL)](https://docs.microsoft.com/en-us/windows/wsl/) and follow the Linux/Kali steps above inside your WSL terminal.
> Some features and tools will not work in native Windows CMD or PowerShell.

---

## 🏃 Usage

After setup, run from any directory:
```bash
cyfer-recon
```

- **Targets:** Enter manually or load from a file
- **Tasks:** Select from a list of 20+ recon automations
- **Execution:** Choose concurrent or sequential
- **Results:** Outputs saved under `{target}/` as `{tool}_result.ext` for each tool (e.g., `subfinder_result.txt`, `nmap_result.txt`)

### Example CLI Options

```bash
cyfer-recon --targets targets.txt --setup-tools
```
- `--targets`: Path to a file or comma-separated list of targets
- `--setup-tools`: Automatically download and set up any missing tools globally

---

## 🛠️ Supported Recon Tasks

- Subdomain Enumeration (subfinder, amass, assetfinder)
- Port Scanning (masscan, nmap)
- Screenshot Capture (eyewitness, aquatone)
- Directory Brute Forcing (ffuf, gobuster)
- JavaScript Analysis (linkfinder, gf)
- Parameter Discovery (pamspider, arjun)
- XSS Detection (dlox, xsstrike)
- SQL Injection Testing (sqlmap)
- SSRF Discovery (gopherus, interactsh)
- LFI/RFI Detection (lfi-suite, fimap)
- Open Redirect Detection (oralizer)
- Security Headers Check (nikto, httpx)
- API Recon (kiterunner)
- Content Discovery (jhaddix, waybackurls)
- S3 Bucket Enumeration (awsbucketdump)
- CMS Enumeration (cmseek)
- WAF Detection (wafw00f)
- Information Disclosure (gitdumper)
- Reverse Shell Generation (msfvenom)
- Mass Exploitation (metasploit)

See `config/tasks.json` for full command mapping.

---

## 🧪 Testing

Run all tests with:
```bash
pytest tests/
```

---

## 🤝 Contributing

We welcome contributions! To get started:

1. **Fork the repo** and create a new branch for your feature or fix.
2. **Add new tools/tasks:**
   - Edit `config/tasks.json` to add new tasks/commands.
   - Edit `config/tools.json` to add tool install/check commands.
3. **Follow code style:**
   - Use clear, descriptive names and docstrings.
   - Keep code modular and testable.
4. **Test your changes:**
   - Add or update tests in `tests/`.
   - Run `pytest tests/` to ensure all tests pass.
5. **Submit a Pull Request:**
   - Describe your changes and reference any related issues.

For questions or suggestions, open an issue or start a discussion!

---

## 🆘 Troubleshooting & Tips
- **Missing tools:** Use `--setup-tools` or follow the install commands shown in the CLI.
- **Permission errors:** Some tools require `sudo` or special permissions. Run the CLI as a user with appropriate rights.
- **Windows issues:** Use WSL for best compatibility. Native Windows is not fully supported.
- **Output not found:** Check the `{target}/` directory for results and logs.
- **Need help?** Open an issue on GitHub or check the FAQ below.

---

## 📄 License
MIT

---

## 🙋 FAQ
- **Q:** How do I add a new recon task?
  - **A:** Add it to `config/tasks.json` and ensure the tool is in `config/tools.json`.
- **Q:** How do I install missing tools?
  - **A:** Use `--setup-tools` or let the tool prompt you to install them.
- **Q:** Can I run this on Windows?
  - **A:** The tool is designed for Linux/Kali Linux. For best results on Windows, use WSL (Windows Subsystem for Linux) with a supported Linux distribution. Some tools and commands will not work in native Windows environments.
- **Q:** How do I ignore output and logs in git?
  - **A:** See the included `.gitignore` file for recommended ignores.

---

## ✨ Credits
Built with [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), [Questionary](https://github.com/tmbo/questionary), and lots of open-source recon tools.
