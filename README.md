# JobPulse AI - Multi-Platform Tech Job Discovery & Fit Engine

An intelligent, startup-grade AI platform that searches live job postings across **10 top tech portals**, clusters duplicate company postings using **Cross-Platform Smart Deduplication**, evaluates candidate fit via an **Explainable 5-Factor AI Matcher**, and provides an **Interactive Multi-Filter Control Center** with bidirectional natural language prompt synchronization.

---

## 🌟 Supported 10 Live Portals (100% Authentic Live Data)

JobPulse AI connects directly to real-time public endpoints with **zero mock or hardcoded data**:

1. 🏢 **Company Career Pages (Direct ATS)**: Live Greenhouse, Lever, Ashby, Workday endpoints
2. 💼 **LinkedIn**: Global live guest search with seniority & date posted parameters
3. ⚡ **Instahyre**: Official live Indian & global tech search API
4. 🇮🇳 **Naukri.com**: Real-time keyword & location search engine
5. 🔎 **Indeed**: Live search query feed with direct URLs
6. 🚀 **Wellfound (AngelList)**: Startup tech roles with salary & equity transparency
7. 🎯 **Cutshort / Hirist**: Live premium developer & engineering discovery
8. 🌐 **We Work Remotely**: Multi-category live RSS feeds (Programming, AI, DevOps)
9. 🕒 **FlexJobs**: Verified remote, flexible, & hybrid tech postings
10. 💻 **Remote.co**: Real-time remote developer & IT position categories

---

## ✨ Key Features

- **Cross-Platform Smart Deduplication**: When the same position is posted on multiple portals (e.g. Stripe on LinkedIn and Instahyre), JobPulse AI clusters them into a single card with multi-source redirect badges (`[ 🔗 Available on: LinkedIn | Instahyre ]`).
- **Explainable 5-Factor AI Fit Matcher**:
  - `Skill Match` (40%) + `Title Match` (25%) + `Seniority Fit` (15%) + `Salary Fit` (10%) + `Prompt Match` (10%)
- **Bidirectional Prompt-to-Filter Sync**: Type natural language prompts like *"Remote Senior AI Engineer paying above $130k USD posted this week in London or worldwide"* to instantly populate UI filter controls.
- **Application Status Tracking**: 1-click **"Apply on Portal"** direct employer redirect buttons and status tracking (`PENDING`, `SAVED`, `APPLIED`).
- **FastMCP Server**: Standardized Model Context Protocol integration exposing discovery, fit evaluation, and resume parsing tools.

---

## 📁 Repository Structure

```
Automate_Job_Apply/
├── app.py                    # FastAPI web application backend
├── main.py                   # CLI orchestrator with parallel discovery
├── database.py               # SQLite Database Manager (WAL mode & migrations)
├── mcp_server.py             # FastMCP Standalone Server (stdio / sse)
├── config.yaml               # User preferences & candidate profile configuration
├── requirements.txt          # Python production dependencies
├── .gitignore                # Git ignore rules for venv, db, secrets, uploads
├── .env.example              # Environment variables template
├── templates/
│   └── index.html            # Glassmorphic UI with Multi-Filter Center
├── static/
│   ├── css/styles.css        # Modern design system & responsive layout
│   └── js/app.js             # Frontend reactive controller & SSE stream
├── src/
│   ├── core/
│   │   ├── config.py         # App configuration loader & path sanitizer
│   │   ├── prompt_parser.py  # Natural language search prompt parser
│   │   └── resume_agent.py   # PDF Resume parsing agent
│   ├── matcher.py            # 5-factor explainable fit scoring engine
│   ├── profile_manager.py    # Profile questionnaire & preferences manager
│   ├── models/
│   │   ├── job.py            # JobPosting model & smart deduplication
│   │   └── profile.py        # CandidateProfile & SearchPreferences models
│   └── scrapers/             # 10 Live Scraper Engines
│       ├── __init__.py       # Scraper registry & dynamic factory
│       ├── base.py           # Abstract BaseScraper interface
│       ├── company_careers.py # Direct ATS scraper
│       ├── linkedin.py       # LinkedIn live scraper
│       ├── instahyre.py      # Instahyre live scraper
│       ├── naukri.py         # Naukri.com live scraper
│       ├── indeed.py         # Indeed live scraper
│       ├── wellfound.py      # Wellfound live scraper
│       ├── cutshort_hirist.py # Cutshort / Hirist live scraper
│       ├── weworkremotely.py # WeWorkRemotely live scraper
│       ├── flexjobs.py       # FlexJobs live scraper
│       └── remote_co.py      # Remote.co live scraper
├── tests/                    # Unit and integration test suites
└── uploads/                  # Candidate resume upload directory
```

---

## 🚀 Getting Started

### 1. Create & Activate Virtual Environment

#### Windows (PowerShell):
```powershell
# If script execution is disabled on PowerShell, run this once:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create virtual environment (if not already created)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1
```

#### Windows (Command Prompt `cmd`):
```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

#### macOS / Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Running the Applications

#### Option A: Launch Interactive Web Dashboard (Recommended)
```bash
python app.py
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

#### Option B: Run CLI Discovery Engine
```bash
python main.py --skip-questionnaire
```

#### Option C: Launch FastMCP Server
```bash
python mcp_server.py --transport sse --port 8001
```

---

## 🧪 Running Tests

Execute the comprehensive test suites across all 10 scrapers, deduplication clustering, and API endpoints:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 📄 License
MIT License
