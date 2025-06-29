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

Below are install commands for all tools used in the default and suggested tasks. Run the Linux command in your terminal, or see the Windows/WSL notes. For Go tools, ensure `$GOPATH/bin` or `$HOME/go/bin` (Linux) or `%USERPROFILE%\go\bin` (Windows) is in your PATH. For Python tools, consider using `pipx` for global installs, or ensure your Python Scripts directory is in your PATH. For tools installed via `git clone`, follow the tool's README for setup, and move scripts/binaries to a directory in your PATH if needed.

| Tool                | Linux Install Command                                                                 | Windows/WSL Notes                                                                 |
|---------------------|-------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|
| subfinder           | go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest          | Install Go, run command, add Go bin to PATH                                       |
| amass               | go install -v github.com/owasp-amass/amass/v3/...@latest                             | Install Go, run command, add Go bin to PATH                                       |
| assetfinder         | go install github.com/tomnomnom/assetfinder@latest                                   | Install Go, run command, add Go bin to PATH                                       |
| findomain           | wget https://github.com/Edu4rdSHL/findomain/releases/latest/download/findomain-linux.zip && unzip findomain-linux.zip && sudo mv findomain /usr/local/bin/ | Download Windows binary from GitHub releases, add to PATH                         |
| dnsx                | go install github.com/projectdiscovery/dnsx/cmd/dnsx@latest                          | Install Go, run command, add Go bin to PATH                                       |
| masscan             | sudo apt install masscan                                                             | Use WSL or download from https://github.com/robertdavidgraham/masscan/releases    |
| nmap                | sudo apt install nmap                                                                | Use WSL or download from https://nmap.org/download.html                           |
| eyewitness          | git clone https://github.com/FortyNorthSecurity/EyeWitness.git && cd EyeWitness && sudo ./setup.sh | Use WSL or follow README for Windows setup                                        |
| aquatone            | go install github.com/michenriksen/aquatone@latest                                   | Install Go, run command, add Go bin to PATH                                       |
| gowitness           | go install github.com/sensepost/gowitness@latest                                     | Install Go, run command, add Go bin to PATH                                       |
| ffuf                | go install github.com/ffuf/ffuf@latest                                               | Install Go, run command, add Go bin to PATH                                       |
| gobuster            | go install github.com/OJ/gobuster/v3@latest                                          | Install Go, run command, add Go bin to PATH                                       |
| linkfinder          | pip install linkfinder                                                               | pipx install linkfinder or ensure Scripts dir in PATH                             |
| gf                  | go install github.com/tomnomnom/gf@latest                                            | Install Go, run command, add Go bin to PATH                                       |
| jsfinder            | git clone https://github.com/Threezh1/JSFinder.git                                   | Use WSL or follow README for Windows setup                                        |
| SecretFinder        | git clone https://github.com/m4ll0k/SecretFinder.git                                 | Use WSL or follow README for Windows setup                                        |
| pamspider           | git clone https://github.com/Bo0oM/PamSpider.git                                     | Use WSL or follow README for Windows setup                                        |
| arjun               | pip install arjun                                                                    | pipx install arjun or ensure Scripts dir in PATH                                  |
| paramspider         | git clone https://github.com/devanshbatham/paramspider.git                           | Use WSL or follow README for Windows setup                                        |
| dlox                | pip install dlox                                                                     | pipx install dlox or ensure Scripts dir in PATH                                   |
| xsstrike            | pip install xsstrike                                                                 | pipx install xsstrike or ensure Scripts dir in PATH                               |
| dalfox              | go install github.com/hahwul/dalfox@latest                                           | Install Go, run command, add Go bin to PATH                                       |
| kxss                | go install github.com/tomnomnom/kxss@latest                                          | Install Go, run command, add Go bin to PATH                                       |
| sqlmap              | pip install sqlmap                                                                   | pipx install sqlmap or ensure Scripts dir in PATH                                 |
| gopherus            | git clone https://github.com/tarunkant/Gopherus.git                                  | Use WSL or follow README for Windows setup                                        |
| interactsh-client   | go install github.com/projectdiscovery/interactsh/cmd/interactsh-client@latest       | Install Go, run command, add Go bin to PATH                                       |
| ssrfmap             | git clone https://github.com/swisskyrepo/SSRFmap.git                                 | Use WSL or follow README for Windows setup                                        |
| lfi-suite           | git clone https://github.com/D35m0nd142/LFISuite.git                                 | Use WSL or follow README for Windows setup                                        |
| fimap               | git clone https://github.com/kurobeats/fimap.git                                     | Use WSL or follow README for Windows setup                                        |
| liffy               | git clone https://github.com/D35m0nd142/Liffy.git                                    | Use WSL or follow README for Windows setup                                        |
| oralizer            | pip install oralizer                                                                 | pipx install oralizer or ensure Scripts dir in PATH                               |
| nikto               | sudo apt install nikto                                                               | Use WSL or download from https://cirt.net/Nikto2                                  |
| httpx               | go install github.com/projectdiscovery/httpx/cmd/httpx@latest                        | Install Go, run command, add Go bin to PATH                                       |
| testssl.sh          | git clone https://github.com/drwetter/testssl.sh.git                                 | Use WSL or follow README for Windows setup                                        |
| kiterunner          | go install github.com/assetnote/kiterunner@latest                                    | Install Go, run command, add Go bin to PATH                                       |
| apkleaks            | pip install apkleaks                                                                 | pipx install apkleaks or ensure Scripts dir in PATH                               |
| jhaddix             | go install github.com/jhaddix/domain@latest                                          | Install Go, run command, add Go bin to PATH                                       |
| waybackurls         | go install github.com/tomnomnom/waybackurls@latest                                   | Install Go, run command, add Go bin to PATH                                       |
| gau                 | go install github.com/lc/gau/v2/cmd/gau@latest                                       | Install Go, run command, add Go bin to PATH                                       |
| awsbucketdump       | git clone https://github.com/jordanpotti/AWSBucketDump.git                           | Use WSL or follow README for Windows setup                                        |
| s3scanner           | go install github.com/sa7mon/S3Scanner@latest                                        | Install Go, run command, add Go bin to PATH                                       |
| cmseek              | git clone https://github.com/Tuhinshubhra/CMSeeK.git                                 | Use WSL or follow README for Windows setup                                        |
| wpscan              | sudo gem install wpscan                                                              | Download Windows binary or use WSL                                                |
| wafw00f             | pip install wafw00f                                                                  | pipx install wafw00f or ensure Scripts dir in PATH                                |
| gitdumper           | git clone https://github.com/arthaud/git-dumper.git                                  | Use WSL or follow README for Windows setup                                        |
| gittools            | git clone https://github.com/internetwache/GitTools.git                              | Use WSL or follow README for Windows setup                                        |
| msfvenom/metasploit | sudo apt install metasploit-framework                                                | Use WSL or download from https://metasploit.com                                   |

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
