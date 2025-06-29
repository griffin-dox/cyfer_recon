# 🛡️ Cyfer Recon Automation CLI Tool

A modular, extensible Python CLI tool for cybersecurity and bug bounty automation. Run 20+ recon tasks (subdomain enumeration, port scanning, screenshots, JS analysis, etc.) on multiple targets with a beautiful TUI/CLI interface.

---

## ⚡ Quick Start

### Prerequisites
- **Python 3.7+** (Linux/Kali recommended)
- **pipx** (recommended for global CLI install)
- **git**
- **Linux tools**: Many recon tools require `apt`, `go`, or other Linux utilities. See [Supported Recon Tasks](#️-supported-recon-tasks).
- **Recon tools**: You must install all required recon tools manually. The CLI will list missing tools and provide install commands for Linux and Windows, plus extra info for global setup (see below).

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
cyfer-recon --targets targets.txt
```
- `--targets`: Path to a file or comma-separated list of targets

---

## 📦 Payloads and Wordlists

- **Payloads:**
  - Place your custom payload files in the `payloads/` folder in the project root.
  - You can also select a payload by entering a local file path or a URL (the tool will download and use it).
  - There is no system-wide payload directory on Linux/Kali; this folder is project-specific.

- **Wordlists:**
  - On Linux/Kali, the tool will first look in `/usr/share/wordlists/` (the standard system directory).
  - You can also use a local `wordlists/` folder in the project root.
  - Additionally, you can select a wordlist by entering a local file path or a URL.

When running tasks that require payloads or wordlists, the CLI will prompt you to select from these options.

---

## 🛠️ Supported Recon Tasks

- Subdomain Enumeration (subfinder, amass, assetfinder, findomain, dnsx)
- Port Scanning (masscan, nmap)
- Screenshot Capture (eyewitness, aquatone, gowitness)
- Directory Brute Forcing (ffuf, gobuster, HTTPS support)
- JavaScript Analysis (linkfinder, gf, jsfinder, SecretFinder)
- Parameter Discovery (pamspider, arjun, paramspider)
- XSS Detection (dlox, xsstrike, dalfox, kxss)
- SQL Injection Testing (sqlmap)
- SSRF Discovery (gopherus, interactsh-client, ssrfmap)
- LFI/RFI Detection (lfi-suite, fimap, liffy)
- Open Redirect Detection (oralizer, ffuf)
- Security Headers Check (nikto, httpx, testssl.sh)
- API Recon (kiterunner, apkleaks)
- Content Discovery (jhaddix, waybackurls, gau)
- S3 Bucket Enumeration (awsbucketdump, s3scanner)
- CMS Enumeration (cmseek, wpscan)
- WAF Detection (wafw00f)
- Information Disclosure (gitdumper, gittools)
- Reverse Shell Generation (msfvenom)
- Mass Exploitation (metasploit)

See `config/tasks.json` for full command mapping.

---

## 🔧 Tool Installation & Global Setup

- The CLI will check for missing tools before running tasks and display a list of missing tools with install commands for Linux and Windows.
- **You must install all required tools manually.**
- For Go-based tools, ensure `$GOPATH/bin` or `$HOME/go/bin` (Linux) or `%USERPROFILE%\go\bin` (Windows) is in your PATH.
- For Python tools, consider using `pipx` for global installs, or ensure your Python Scripts directory is in your PATH.
- For tools installed via `git clone`, follow the tool's README for setup, and move scripts/binaries to a directory in your PATH if needed.
- For `apt` installs, use WSL on Windows or download from the official website if not available.

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
- **Missing tools:** The CLI will show missing tools and install commands. Install them manually and ensure they are in your PATH.
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
  - **A:** The CLI will show missing tools and install commands. Install them manually and ensure they are in your PATH.
- **Q:** Can I run this on Windows?
  - **A:** The tool is designed for Linux/Kali Linux. For best results on Windows, use WSL (Windows Subsystem for Linux) with a supported Linux distribution. Some tools and commands will not work in native Windows environments.
- **Q:** How do I ignore output and logs in git?
  - **A:** See the included `.gitignore` file for recommended ignores.

---

## ✨ Credits
Built with [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), [Questionary](https://github.com/tmbo/questionary), and lots of open-source recon tools.
