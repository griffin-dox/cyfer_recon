# 🛡️ Cyfer Recon Automation CLI Tool

A modular, extensible Python CLI tool for cybersecurity and bug bounty automation. Run 20+ recon tasks (subdomain enumeration, port scanning, screenshots, JS analysis, etc.) on multiple targets with a beautiful TUI/CLI interface.

---

## 🚀 Features
- **Multi-Target Input:** Enter targets manually or load from file
- **Task Selection:** Choose from 20+ recon tasks via interactive menu
- **Tool Availability Check:** Verifies required tools, suggests install commands, and can auto-install for you
- **Concurrent/Sequential Execution:** Choose your preferred mode
- **Organized Output:** Results saved per target in structured folders
- **Modern UI:** Uses `rich`, `questionary`, and `typer` for a great UX
- **Global CLI:** Usable from anywhere on your system after setup
- **Kali Linux Ready:** Designed and tested for Kali Linux

---

## 📦 Installation & Global Setup (Kali Linux)

1. **Clone the repo:**
   ```bash
   git clone https://github.com/griffin-dox/Cyfer_Recon_Script
   cd cyfer-recon-script
   ```
2. **Run the setup script:**
   ```bash
   chmod +x setup.sh
   sudo ./setup.sh
   ```
   This will:
   - Install Python dependencies
   - Create a global symlink `/usr/local/bin/cyfer-recon` so you can run the tool from anywhere

---

## 🏃 Usage

After setup, run from any directory:
```bash
cyfer-recon
```

- **Targets:** Enter manually or load from a file
- **Tasks:** Select from a list of 20+ recon automations
- **Execution:** Choose concurrent or sequential
- **Results:** Outputs saved under `output/{target}/` as `toolname_result.ext` for each tool (e.g., `subfinder_result.txt`, `nmap_result.txt`)

### Example CLI Options

```bash
cyfer-recon --targets targets.txt --setup-tools
cyfer-recon --profile quick --headless
```

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
- PRs and issues welcome!
- Add new tools/tasks by editing `config/tasks.json` and `config/tools.json`

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
  - **A:** The tool is designed for Linux/Kali Linux. Some tools may require WSL or adaptation on Windows.
- **Q:** How do I ignore output and logs in git?
  - **A:** See the included `.gitignore` file for recommended ignores.

---

## ✨ Credits
Built with [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), [Questionary](https://github.com/tmbo/questionary), and lots of open-source recon tools.
