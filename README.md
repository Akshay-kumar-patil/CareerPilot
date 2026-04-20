# 🚀 Career Automation & Job Intelligence Platform

An AI-powered career operating system that automates the entire job search lifecycle — resume generation, analysis, job tracking, mock interviews, and data-driven insights.

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Resume Builder** | AI-generated, ATS-optimized resumes with keyword alignment |
| 🔍 **Resume Analyzer** | ATS scoring (0-100), section feedback, keyword gap analysis |
| ✉️ **Cover Letter Generator** | Personalized cover letters with tone options (formal/concise/creative) |
| 🤖 **AI Recruiter Simulator** | Predict shortlist/reject decisions with reasoning |
| 🎤 **Mock Interview** | AI-generated HR & technical questions with answer evaluation |
| 📊 **Skill Gap Analyzer** | Compare skills vs JD, get learning roadmap |
| 🎯 **Job Tracker** | Track applications (Saved → Applied → Interview → Offer) |
| 👥 **Referral Manager** | Track referral contacts and status |
| 🧪 **Resume A/B Testing** | Compare resume versions and track performance |
| 📈 **Analytics Dashboard** | Response rates, trends, resume performance metrics |
| 📧 **Email Generator** | Cold emails, referral requests, follow-ups |
| 🐙 **GitHub Analyzer** | Extract resume bullet points from repos |
| 📑 **JD Extraction Engine** | Extract skills/requirements from PDFs, text, URLs |
| 🧠 **Personal Memory** | Context-aware AI using your profile and history |

## 🧠 AI Architecture

**Hybrid Multi-Model System** with automatic fallback:

- ☁️ **Google Gemini** — Primary cloud AI, fast & generous free tier
- ⚡ **Groq (llama-3.3-70b-versatile)** — Ultra-fast fallback, free tier
- ☁️ **OpenAI GPT** — Optional cloud-based alternative
- 🔄 **Auto-routing** — Detects connectivity and routes to best available model
- 💰 **Cost tracking** — Monitor API usage and costs

## 🏗️ Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Frontend:** Streamlit (dark theme, modern UI)
- **AI:** LangChain + Google Gemini + Groq (llama-3.3-70b)
- **Vector DB:** ChromaDB (semantic search)
- **Embeddings:** sentence-transformers (offline)
- **File Gen:** WeasyPrint (PDF), python-docx (DOCX)

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10+
- Gemini API key (free at https://aistudio.google.com)
- (Optional) Groq API key (free at https://console.groq.com) for ultra-fast fallback
- (Optional) OpenAI API key for cloud AI

### 2. Setup

```bash
cd career-platform

# Create virtual environment
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env   # Windows
# cp .env.example .env   # Linux/Mac
# Edit .env with your API keys
```

### 3. Run

```bash
# Terminal 1 — Start Backend
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Start Frontend
streamlit run frontend/app.py
```

### 4. Access

- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **API ReDoc:** http://localhost:8000/redoc

### 5. Docker (optional)

```bash
docker-compose up --build
```

## 📁 Project Structure

```
career-platform/
├── backend/                  # FastAPI backend
│   ├── main.py              # App entry point
│   ├── config.py            # Settings
│   ├── database.py          # SQLite + ChromaDB
│   ├── ai/                  # AI engine
│   │   ├── model_router.py  # Hybrid model routing
│   │   ├── chains.py        # LangChain pipelines
│   │   ├── prompts.py       # Prompt templates
│   │   └── embeddings.py    # Vector embeddings
│   ├── models/              # ORM models
│   ├── schemas/             # Pydantic schemas
│   ├── routers/             # API endpoints
│   ├── services/            # Business logic
│   └── utils/               # Helpers
├── frontend/                 # Streamlit UI
│   ├── app.py               # Main app (all 14 pages)
│   └── utils/               # API client & session
├── templates/                # HTML resume templates
├── data/                     # SQLite DB, uploads, generated files
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login |
| POST | `/api/resume/generate` | Generate AI resume |
| GET | `/api/resume/list` | List user resumes |
| POST | `/api/analyzer/analyze` | Analyze resume |
| POST | `/api/cover-letter/generate` | Generate cover letter |
| POST/GET | `/api/applications/` | CRUD applications |
| POST/GET | `/api/referrals/` | CRUD referrals |
| POST | `/api/interview/generate` | Generate interview Q's |
| POST | `/api/interview/evaluate` | Evaluate answer |
| POST | `/api/skills/analyze-gap` | Skill gap analysis |
| POST | `/api/email/generate` | Generate email |
| POST | `/api/github/analyze` | Analyze GitHub |
| POST | `/api/extract/jd` | Extract JD info |
| GET | `/api/analytics/summary` | Career analytics |
| GET | `/api/ai/status` | AI system status |

## 🔒 Security

- JWT-based authentication
- Bcrypt password hashing
- CORS protection
- All data stored locally (SQLite)

## 📝 License

MIT
