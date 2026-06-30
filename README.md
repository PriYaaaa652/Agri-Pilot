# 🌾 AgriPilot: Intelligent Agricultural Multi-Agent System

AgriPilot is a secure, multi-agent AI assistant designed for farmers in Bangladesh. It provides real-time crop disease diagnosis, localized weather warnings, and crop commodity pricing trends. The system features a built-in safety checkpoint (PII scrubbing, prompt injection prevention, banned chemical detection), a human-in-the-loop (HITL) approval gate for chemical applications, and a translation layer that outputs advice in Bangla for local farmers.

---

## 📋 Prerequisites

Before running AgriPilot, ensure you have the following installed on your machine:

- **Python 3.11 or higher**: Download from [python.org](https://www.python.org/downloads/) (ensure it's added to your PATH).
- **uv**: Astral's fast Python package manager.
  - *PowerShell (Windows)*: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
  - *macOS/Linux*: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Gemini API Key**: Obtain a free-tier or pay-as-you-go key from [Google AI Studio](https://aistudio.google.com/apikey).

---

## 🚀 Quick Start

1. **Clone the Repository:**
   ```bash
   git clone <repo-url>
   cd agripilot
   ```

2. **Configure Environment Variables:**
   Copy the example environment file and add your Gemini API key:
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   GOOGLE_GENAI_USE_VERTEXAI=False
   GEMINI_MODEL=gemini-2.5-flash
   ```

3. **Install Dependencies:**
   ```bash
   make install
   ```

4. **Launch the Playground:**
   ```bash
   make playground
   ```
   This will launch the local ADK developer playground UI. Open your browser and navigate to **[http://localhost:18081](http://localhost:18081)**.

---

## 📐 Architecture Diagram

The diagram below illustrates AgriPilot's event-driven workflow graph, from session memory load to Bangla translation:

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

---

## 🛠️ How to Run

### Interactive UI (Playground)
Runs the ADK local playground for interactive model execution:
- **Windows**: `.\.venv\Scripts\adk.exe web app --host 127.0.0.1 --port 18081 --reload_agents`
- **macOS / Linux**: `make playground`

### Local Web Server (Production API)
Runs the FastAPI server exposing the agent as a network service:
```bash
make run
```

---

## 🧪 Sample Test Cases

Test these cases interactively using the Web UI at **[http://localhost:18081](http://localhost:18081)**:

### Test Case 1: Safe Multi-Agent Query
- **Input:**
  `"I am farming tomatoes in Dhaka on loamy soil. What is the current market price and weather?"`
- **Expected Flow:**
  Passes the `security_checkpoint`. The `orchestrator` parallelly queries the `weather_agent` (invoking `get_weather_alert` tool) and `market_agent` (invoking `get_crop_market_price` tool). Since no chemicals are recommended, `human_review` is auto-approved. A structured JSON report is generated and translated into Bangla.
- **Check:**
  The output contains live weather details for Dhaka, tomato pricing at ~120 BDT/kg, and a Bangla translation block titled `=== বাংলায় পরামর্শ (কৃষকের জন্য) ===`.

### Test Case 2: Restricted Chemical Recommendation (Human-In-The-Loop Approval)
- **Input:**
  `"My tomatoes in Dhaka need chemical fertilizer recommendations on clay soil."`
- **Expected Flow:**
  Passes `security_checkpoint`. The `orchestrator` runs `crop_doctor` (calling `get_soil_info`), which drafts a plan recommending chemical fertilizers. The `human_review` node detects restricted keywords (e.g., "chemical fertilizer") and pauses execution, issuing a `RequestInput` prompt.
- **Check:**
  The UI/terminal will pause and prompt: `"AgriPilot Alert: A chemical treatment was recommended... Do you approve...?"`. 
  - If you type `no`, the workflow resumes, and the final recommendation dynamically replaces the chemical suggestion with organic compost recommendations.

### Test Case 3: Banned Substance Security Violation
- **Input:**
  `"Can you recommend how to spray Paraquat on my weeds?"`
- **Expected Flow:**
  The `security_checkpoint` evaluates the input and flags the keyword `"Paraquat"` (a banned chemical in Bangladesh). It immediately shifts the graph route to `security_event`.
- **Check:**
  The output immediately responds with: `"Security Alert: Your query has been flagged by AgriPilot's security system. We cannot fulfill this request because it either violates prompt policies or references banned/restricted agricultural substances."`

---

## 🔍 Troubleshooting

1. **`uv` is not recognized as a command**
   - **Reason**: The `uv` installer did not add the executable path to your OS environment variables, or your terminal needs to be restarted.
   - **Fix**: Restart your terminal. If still not working, execute commands using the virtualenv binaries directly, e.g., `.\.venv\Scripts\adk.exe` or `.\.venv\Scripts\python.exe`.

2. **API Returns 404 Error (Model Not Found)**
   - **Reason**: Your `.env` specifies a retired model (e.g. `gemini-1.5-pro` or `gemini-1.5-flash`).
   - **Fix**: Update the `GEMINI_MODEL` variable in `.env` to `gemini-2.5-flash` or `gemini-2.5-flash-lite`.

3. **Hot-Reload does not pick up code changes (Windows)**
   - **Reason**: Windows file-watching events conflict with the async loops managing MCP sub-processes.
   - **Fix**: Stop the active background process first using PowerShell:
     ```powershell
     Get-Process -Id (Get-NetTCPConnection -LocalPort 18081, 8090 -ErrorAction SilentlyContinue).OwningProcess | Stop-Process -Force
     ```
     Then relaunch with `make playground`.

---

## 📦 Push to GitHub

1. Create a new repo at https://github.com/new
   - Name: `agripilot`
   - Visibility: Public or Private
   - Do NOT initialize with README (you already have one)

2. In your terminal, navigate into your project folder:
   ```bash
   cd agripilot
   git init
   git add .
   git commit -m "Initial commit: agripilot ADK agent"
   git branch -M main
   git remote add origin https://github.com/<your-username>/agripilot.git
   git push -u origin main
   ```

3. Verify `.gitignore` includes:
   ```
   .env          ← your API key — must NEVER be pushed
   .venv/
   __pycache__/
   *.pyc
   .adk/
   ```

> [!WARNING]
> **NEVER** push `.env` to GitHub. Your API key will be exposed publicly and immediately revoked.
