# 🛡️ Cyfer Recon Automation CLI Tool

A modular, extensible Python CLI tool for cybersecurity and bug bounty automation. Run 20+ recon tasks (subdomain enumeration, port scanning, screenshots, JS analysis, etc.) on multiple targets with a beautiful TUI/CLI interface.

---

## 🚀 Features
- **Multi-Target Input:** Enter targets manually or load from file
- **Task Selection:** Choose from 20+ recon tasks via interactive menu
- **Tool Availability Check:** Verifies required tools, suggests install commands
- **Concurrent/Sequential Execution:** Choose your preferred mode
- **Organized Output:** Results saved per target in structured folders
- **Modern UI:** Uses `rich`, `questionary`, and `typer` for a great UX

---

## 📦 Installation

1. **Clone the repo:**
   ```bash
   git clone https://github.com/griffin-dox/Cyfer_Recon_Script
   cd cyfer-recon-script
   ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or manually:
   pip install typer rich questionary
   ```
3. **Install external tools:**
   - The tool will check for required binaries and suggest install commands for missing ones.
   - See `config/tools.json` for all supported tools and install instructions.

---

## 🏃 Usage

```bash
python main.py
```

- **Targets:** Enter manually or load from a file
- **Tasks:** Select from a list of 20+ recon automations
- **Execution:** Choose concurrent or sequential
- **Results:** Outputs saved under `output/{target}/`

### Example CLI Options

```bash
python main.py --targets targets.txt
python main.py --profile quick --headless
```

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
  - **A:** The tool will suggest install commands for your OS.
- **Q:** Can I run this on Windows?
  - **A:** Yes, but some tools may require WSL or adaptation.

---

## ✨ Credits
Built with [Typer](https://typer.tiangolo.com/), [Rich](https://rich.readthedocs.io/), [Questionary](https://github.com/tmbo/questionary), and lots of open-source recon tools.
