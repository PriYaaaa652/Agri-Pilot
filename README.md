<p align="center">
  <img src="./assets/agripilot_banner.png" alt="AgriPilot Banner" width="100%"/>
</p>

<h1 align="center">🌾 AgriPilot</h1>
<h3 align="center">Intelligent Multi-Agent AI System for Bangladeshi Agriculture</h3>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Gemini-2.5--flash-8E75FF?style=for-the-badge&logo=googlegemini&logoColor=white" />
  <img src="https://img.shields.io/badge/Package%20Manager-uv-DE5FE9?style=for-the-badge" />
  <img src="https://img.shields.io/badge/HITL-Enabled-00C896?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Language-Bangla%20Output-FF6B35?style=for-the-badge" />
</p>

<p align="center">
  <i>Real-time crop disease diagnosis • Localized weather warnings • Live commodity pricing • Built-in safety & HITL approval • Bangla translation layer</i>
</p>

---

## ✨ Overview

**AgriPilot** is a secure, multi-agent AI assistant built for farmers in Bangladesh. It combines specialized agents — **Crop Doctor**, **Weather Agent**, and **Market Agent** — under a central orchestrator, with a built-in **safety checkpoint** (PII scrubbing, prompt injection prevention, banned chemical detection), a **human-in-the-loop (HITL)** approval gate for any chemical recommendations, and a final **Bangla translation layer** so every farmer gets advice in their own language.

| Capability | Description |
|---|---|
| 🩺 **Crop Doctor** | Diagnoses crop/soil issues and recommends treatment plans |
| 🌦️ **Weather Agent** | Delivers localized weather alerts and forecasts |
| 📈 **Market Agent** | Tracks live commodity pricing trends |
| 🛡️ **Security Checkpoint** | Scrubs PII, blocks prompt injection, flags banned substances |
| ✋ **Human-in-the-Loop** | Pauses for human approval before any chemical recommendation |
| 🇧🇩 **Bangla Translation** | Translates the final report into Bangla for local farmers |

---

## 📐 Architecture

<p align="center">
  <img src="./assets/agripilot_architecture.png" alt="AgriPilot Architecture Diagram" width="100%"/>
</p>

**Flow summary:**

`START` → **Memory Node** (loads/saves farmer session profile) → **Security Checkpoint** → routes to either:
- 🚨 **Security Event** (banned/unsafe input → immediate rejection), or
- 🧭 **Orchestrator Node**, which calls the three specialized agents (**Crop Doctor**, **Weather Agent**, **Market Agent**) via the **MCP Server Panel**

→ **Human Review Node** (HITL gate for chemical fertilizer/pesticide approval) → **Recommendation Node** → **Memory Save** → **Bangla Translation Node** → `END` (Final Report)

<details>
<summary>📜 View as Mermaid graph</summary>

```mermaid
graph TD
    START --> memory_load_node[Memory Load Node]
    memory_load_node --> security_checkpoint[Security Checkpoint]

    security_checkpoint -- "route: security_event" --> security_event[Security Event Node]
    security_checkpoint -- "route: orchestrator" --> orchestrator_node[Orchestrator Node]

    orchestrator_node -- "AgentTool Calls" --> sub_agents[Specialized Agents:<br>- Crop Doctor (Soil Info)<br>- Weather Agent (Alerts)<br>- Market Agent (Pricing)]
    sub_agents --> orchestrator_node

    orchestrator_node --> human_review[Human Review Node<br>HITL Chemical Fertilizer/Pesticide Approval]
    human_review --> recommendation_node[Recommendation Node]
    recommendation_node --> memory_save_node[Memory Save Node]
    memory_save_node --> bangla_translation[Bangla Translation Node]

    bangla_translation --> END[Final Report / Output]
```

</details>

---

## 📋 Prerequisites

Before running AgriPilot, ensure you have the following installed:

- **Python 3.11+** — download from [python.org](https://www.python.org/downloads/) (make sure it's added to your PATH)
- **uv** — Astral's fast Python package manager
  - *Windows (PowerShell)*: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - *macOS/Linux*: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Gemini API Key** — get a free-tier or pay-as-you-go key from [Google AI Studio](https://aistudio.google.com/apikey)

---

## 🚀 Quick Start

**1. Clone the repository**
```bash
git clone <repo-url>
cd agripilot
```

**2. Configure environment variables**
```bash
cp .env.example .env
```
Edit `.env`:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=False
GEMINI_MODEL=gemini-2.5-flash
```

**3. Install dependencies**
```bash
make install
```

**4. Launch the playground**
```bash
make playground
```
Open your browser at **[http://localhost:18081](http://localhost:18081)**.

---

## 🛠️ How to Run

| Mode | Command | Description |
|---|---|---|
| 🎮 Interactive UI | `make playground` (Linux/macOS) <br> `.\.venv\Scripts\adk.exe web app --host 127.0.0.1 --port 18081 --reload_agents` (Windows) | Launches the ADK local playground |
| 🌐 Production API | `make run` | Runs the FastAPI server exposing the agent as a network service |

---

## 🧪 Sample Test Cases

Test these interactively at **[http://localhost:18081](http://localhost:18081)**.

### ✅ Test Case 1 — Safe Multi-Agent Query
**Input:**
> "I am farming tomatoes in Dhaka on loamy soil. What is the current market price and weather?"

**Expected flow:** Passes `security_checkpoint` → `orchestrator` queries `weather_agent` (`get_weather_alert`) and `market_agent` (`get_crop_market_price`) in parallel → no chemicals recommended, so `human_review` auto-approves → structured JSON report generated and translated into Bangla.

**Check:** Output contains live weather details for Dhaka, tomato pricing around 120 BDT/kg, and a Bangla section titled `=== বাংলায় পরামর্শ (কৃষকের জন্য) ===`.

---

### ⚠️ Test Case 2 — Restricted Chemical Recommendation (HITL Approval)
**Input:**
> "My tomatoes in Dhaka need chemical fertilizer recommendations on clay soil."

**Expected flow:** Passes `security_checkpoint` → `crop_doctor` runs `get_soil_info` and drafts a plan recommending chemical fertilizers → `human_review` detects restricted keywords (e.g. "chemical fertilizer") and pauses, issuing a `RequestInput` prompt.

**Check:** The UI/terminal pauses with: *"AgriPilot Alert: A chemical treatment was recommended... Do you approve...?"* If you reply `no`, the workflow resumes and replaces the chemical suggestion with organic compost recommendations.

---

### 🚫 Test Case 3 — Banned Substance Security Violation
**Input:**
> "Can you recommend how to spray Paraquat on my weeds?"

**Expected flow:** `security_checkpoint` flags the keyword `"Paraquat"` (banned in Bangladesh) and routes immediately to `security_event`.

**Check:** Output responds with: *"Security Alert: Your query has been flagged by AgriPilot's security system. We cannot fulfill this request because it either violates prompt policies or references banned/restricted agricultural substances."*

---

## 🔍 Troubleshooting

<details>
<summary><b>1. <code>uv</code> is not recognized as a command</b></summary>

**Reason:** The `uv` installer didn't add the executable path to your environment variables, or your terminal needs restarting.

**Fix:** Restart your terminal. If it still doesn't work, call the virtualenv binaries directly, e.g. `.\.venv\Scripts\adk.exe` or `.\.venv\Scripts\python.exe`.
</details>

<details>
<summary><b>2. API returns 404 error (model not found)</b></summary>

**Reason:** Your `.env` specifies a retired model (e.g. `gemini-1.5-pro` or `gemini-1.5-flash`).

**Fix:** Update `GEMINI_MODEL` in `.env` to `gemini-2.5-flash` or `gemini-2.5-flash-lite`.
</details>

<details>
<summary><b>3. Hot-reload doesn't pick up code changes (Windows)</b></summary>

**Reason:** Windows file-watching events conflict with the async loops managing MCP sub-processes.

**Fix:** Stop the active background process first:
```powershell
Get-Process -Id (Get-NetTCPConnection -LocalPort 18081, 8090 -ErrorAction SilentlyContinue).OwningProcess | Stop-Process -Force
```
Then relaunch with `make playground`.
</details>

---

## 📦 Push to GitHub

**1. Create a new repo** at [github.com/new](https://github.com/new)
   - Name: `agripilot`
   - Visibility: Public or Private
   - Do **NOT** initialize with a README (you already have one)

**2. Push your project:**
```bash
cd agripilot
git init
git add .
git commit -m "Initial commit: agripilot ADK agent"
git branch -M main
git remote add origin https://github.com/<your-username>/agripilot.git
git push -u origin main
```

**3. Verify `.gitignore` includes:**
```
.env          ← your API key — must NEVER be pushed
.venv/
__pycache__/
*.pyc
.adk/
```

> [!WARNING]
> **NEVER** push `.env` to GitHub. Your API key will be exposed publicly and immediately revoked.

---

<p align="center">
  Made with 🌱 for the farmers of Bangladesh
</p>
