# CareerPilot

CareerPilot is an AI-powered career operating system for modern job seekers. It goes far beyond resume creation by helping users build stronger application materials, evaluate job fit, track opportunities, prepare for interviews, manage referrals, and improve outcomes with analytics.

If "resume builder" sounds too small for what this project does, that is because the platform already behaves more like a personal CareerPilot center.

## What This Project Is

This project combines a FastAPI backend, a Streamlit frontend, and a multi-provider AI layer to support the full job search workflow in one place.

Core product areas:

- Resume generation with ATS-oriented content and keyword alignment
- Resume analysis with scoring, feedback, and missing keyword detection
- Cover letter generation with different tones
- Job application tracking across the pipeline
- Referral tracking and follow-up support
- Mock interview generation and answer evaluation
- Skill gap analysis with roadmap suggestions
- Outreach email generation for cold emails, referrals, follow-ups, and thank-you notes
- GitHub project analysis for resume-ready bullet points
- Job description extraction from text, files, and supported sources
- Analytics to measure application activity and performance
- AI recruiter simulation to estimate shortlist vs rejection outcomes
- A/B comparison of resume variants

## Why It Matters

Most tools in this space solve one isolated problem:

- build a resume
- write a cover letter
- track applications
- practice interviews

This project brings those steps together into one workflow so a user can move from preparation to application to improvement without switching systems.

That makes the platform more valuable as:

- a portfolio project
- a startup MVP
- a SaaS foundation
- a career-tech product demo
- an internal productivity tool for career coaches or placement teams

## Product Positioning

Best recommended product name:

**CareerPilot**

Why this name fits:

- It sounds larger and more important than "Resume Builder"
- It suggests control, direction, and decision-making
- It fits the platform's broad scope across resumes, interviews, tracking, and analytics
- It is easy to remember and feels like software people can rely on daily

More naming ideas are in [docs/project-positioning.md](/D:/aiml/career-platform/docs/project-positioning.md).

## Feature Overview

| Area | What it does |
| --- | --- |
| Resume Builder | Generates structured resumes tailored to job descriptions |
| Resume Analyzer | Scores resumes and highlights strengths, gaps, and keyword coverage |
| Cover Letter Generator | Produces role-specific and tone-controlled cover letters |
| Job Tracker | Tracks saved, applied, interviewing, offered, and rejected opportunities |
| Referral Manager | Tracks referral contacts, outreach, and status |
| Mock Interview | Generates interview questions and reviews answers |
| Skill Gap Analyzer | Compares current skills against target job requirements |
| Email Generator | Creates career outreach and follow-up emails |
| GitHub Analyzer | Converts repository work into resume-friendly achievements |
| JD Extraction Engine | Pulls useful hiring signals from job descriptions |
| Analytics Dashboard | Measures conversion, response rate, and application momentum |
| AI Recruiter Simulator | Predicts recruiter reaction and explains likely outcomes |
| Resume A/B Testing | Compares multiple resume versions and performance signals |
| Personal Memory Layer | Uses user profile and history for more contextual outputs |

## Architecture

### Frontend

- Streamlit application in [frontend/app.py](/D:/aiml/career-platform/frontend/app.py)
- Multi-page interface with authentication, dashboards, editors, and analysis tools
- API client helpers in [frontend/utils/api_client.py](/D:/aiml/career-platform/frontend/utils/api_client.py)

### Backend

- FastAPI application in [backend/main.py](/D:/aiml/career-platform/backend/main.py)
- Router-based API structure under [backend/routers](/D:/aiml/career-platform/backend/routers)
- Service layer for business logic under [backend/services](/D:/aiml/career-platform/backend/services)
- ORM models under [backend/models](/D:/aiml/career-platform/backend/models)
- Pydantic schemas under [backend/schemas](/D:/aiml/career-platform/backend/schemas)

### AI Layer

- Prompt and chain logic under [backend/ai](/D:/aiml/career-platform/backend/ai)
- Multi-provider routing with Gemini, Groq, and optional OpenAI
- Automatic fallback and provider status reporting
- Embedding-based support through sentence-transformers and ChromaDB

### Data and Storage

- SQLite for relational application data
- MongoDB configuration for user-related storage and connectivity checks
- ChromaDB for semantic retrieval and embeddings
- Local file generation and storage under `data/`

## Technology Stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: Streamlit, Plotly, Pandas
- AI orchestration: LangChain
- AI providers: Google Gemini, Groq, OpenAI
- Vector search: ChromaDB
- Embeddings: sentence-transformers
- Auth and security: JWT, bcrypt, Authlib, session middleware
- File generation: Jinja2, python-docx, WeasyPrint, PyPDF2

## Project Structure

```text
career-platform/
|-- backend/
|   |-- ai/                 # prompts, routing, chains, embeddings
|   |-- models/             # database models
|   |-- routers/            # API route groups
|   |-- schemas/            # request/response schemas
|   |-- services/           # business logic
|   |-- utils/              # auth, parsing, helpers
|   |-- config.py           # environment-based settings
|   |-- database.py         # DB initialization and helpers
|   `-- main.py             # FastAPI entry point
|-- frontend/
|   |-- utils/              # frontend API and session helpers
|   `-- app.py              # Streamlit UI
|-- templates/              # resume templates
|-- data/                   # generated files, uploads, local storage
|-- docs/                   # product and branding notes
|-- requirements.txt
`-- README.md
```

## Local Setup

### Prerequisites

- Python 3.10+
- A virtual environment tool
- At least one AI provider key for full functionality

Recommended provider setup:

- Gemini API key for the default experience
- Groq API key for fast fallback
- OpenAI API key if you want OpenAI-based generation

### Installation

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Then update `.env` with the keys and values you want to use.

### Run Locally

Backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
streamlit run frontend/app.py
```

Default local URLs:

- Frontend: `http://localhost:8501`
- API docs: `http://localhost:8000/docs`
- API redoc: `http://localhost:8000/redoc`

## Environment Notes

Important configuration lives in [backend/config.py](/D:/aiml/career-platform/backend/config.py).

Key settings include:

- app name and version
- JWT secret and token expiry
- SQLite path
- MongoDB URL and database name
- AI provider keys and model names
- upload and generated file directories
- cleanup retention windows
- CORS origins

## API Surface

Primary route groups exposed by the backend:

- `/api/auth`
- `/api/resume`
- `/api/analyzer`
- `/api/cover-letter`
- `/api/applications`
- `/api/referrals`
- `/api/interview`
- `/api/skills`
- `/api/analytics`
- `/api/email`
- `/api/github`
- `/api/extract`
- `/api/ai/status`

Operational endpoints:

- `/`
- `/health`
- `/health/db`
- `/docs`
- `/redoc`

## Deployment Links

Frontend:

- [Streamlit app](https://akshay-kumar-patil-career-portal-frontendapp-gkbra3.streamlit.app/)

Backend:

- [Render API](https://career-portal-cxgd.onrender.com/)

## Who This Is For

This project is well suited for:

- students preparing for internships and placements
- working professionals changing roles
- job seekers managing high-volume applications
- bootcamp graduates building a career-tech portfolio
- recruiters or mentors who want a structured candidate support tool

## Next Documentation Improvements

If you want, the next useful step would be adding:

- a full API reference table by route file
- screenshots for each major frontend module
- a contributor guide for local development and deployment
- a product pitch section for using this in interviews or demos
