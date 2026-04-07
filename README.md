# Career Automation & Job Intelligence Platform

An AI-assisted career portal that helps users move through the full job search cycle from one workspace. The project combines a FastAPI backend, a Streamlit frontend, local persistence, and multi-provider LLM support to generate resumes, analyze job descriptions, practice interviews, track applications, and prepare application assets.

## Why this project exists

Job searching usually means bouncing between documents, trackers, job boards, and writing tools. This project brings those steps together into a single platform so a user can:

- build or tailor resumes for a role
- measure resume quality with ATS-style analysis
- generate cover letters and recruiter outreach
- track applications and referrals
- prepare for interviews
- compare skills against job descriptions
- use AI assistance without being locked to a single provider

## What the platform includes

### Core user-facing capabilities

- Resume Builder for AI-generated, ATS-oriented resumes
- Resume Analyzer for scoring, keyword matching, and feedback
- Cover Letter Generator with adjustable tone
- Job Tracker for application lifecycle management
- Referral Tracker for networking follow-up
- Mock Interview support with answer evaluation
- Skill Gap analysis against a job description
- Email Generator for follow-ups and outreach
- GitHub Analyzer for turning repository work into resume-ready content
- JD Extraction utilities for text, file, and URL-based parsing
- Auto Apply workflow for AI-prepared application answers and optional Playwright automation
- Analytics dashboard for response and conversion trends
- Resume A/B Testing to compare different resume versions

### AI system design

The backend uses a model router that can work with:

- Google Gemini as the default cloud model
- Groq as a fast fallback option
- OpenAI as an optional alternative provider

The router checks configuration and network availability, then selects the best available provider. It also tracks token usage and estimated cost across requests.

## Tech stack

- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: Streamlit, Plotly, Pandas
- Data: SQLite, ChromaDB
- AI: LangChain, Gemini, Groq, OpenAI
- Embeddings: `sentence-transformers`
- Document generation: Jinja2, WeasyPrint, `python-docx`
- Automation: Playwright

## Repository structure

```text
career-portal/
|-- backend/
|   |-- ai/              # model routing, prompts, chains, embeddings
|   |-- models/          # SQLAlchemy models
|   |-- routers/         # FastAPI route modules
|   |-- schemas/         # request/response models
|   |-- services/        # business logic
|   |-- utils/           # auth, parsing, helpers
|   |-- config.py        # application settings
|   |-- database.py      # database + vector store setup
|   `-- main.py          # FastAPI entrypoint
|-- frontend/
|   |-- utils/           # API client and session helpers
|   `-- app.py           # Streamlit UI
|-- templates/           # resume and cover letter HTML templates
|-- data/                # uploads, generated files, local DB assets
|-- docker-compose.yml
|-- Dockerfile
|-- Dockerfile.frontend
|-- requirements.txt
`-- .env.example
```

## Quick start

### 1. Prerequisites

- Python 3.10+
- `pip`
- Optional: Playwright browsers for automated apply flows
- Optional: Gemini, Groq, or OpenAI API credentials

### 2. Install dependencies

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

For the Streamlit frontend dependencies only:

```bash
pip install -r frontend/requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in the values you plan to use.

Important settings:

- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `OPENAI_API_KEY`
- `DEFAULT_MODEL_PROVIDER`
- `SECRET_KEY`

### 4. Run the application

Backend:

```bash
uvicorn backend.main:app --reload --port 8000
```

Frontend:

```bash
streamlit run frontend/app.py
```

### 5. Open the app

- Frontend: [http://localhost:8501](http://localhost:8501)
- Swagger docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Deployment options

The repository includes:

- `Dockerfile` for the backend
- `Dockerfile.frontend` for the Streamlit UI
- `docker-compose.yml` for local container orchestration
- `render.yaml` for Render deployment

## Key API groups

- `/api/auth` for authentication and profile updates
- `/api/resume` for generation, listing, versions, download, and deletion
- `/api/analyzer` for resume analysis and recruiter simulation
- `/api/cover-letter` for generation and document export
- `/api/applications` for job application CRUD
- `/api/referrals` for referral tracking
- `/api/interview` for interview question generation and answer evaluation
- `/api/skills` for skill-gap analysis
- `/api/email` for recruiter email generation
- `/api/github` for GitHub project analysis
- `/api/extract` for JD extraction from multiple input types
- `/api/analytics` for dashboard metrics
- `/api/auto-apply` for job application preparation and submission support

## Documentation map

- [docs/SETUP.md](docs/SETUP.md) for environment, install, and run instructions
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design and module responsibilities
- [docs/WORKFLOWS.md](docs/WORKFLOWS.md) for the major user journeys supported by the app

## Notes for contributors

- The backend stores relational data in SQLite and semantic data in ChromaDB under `data/`.
- Generated files and uploads also live in `data/`, so local runs can produce stateful artifacts.
- The frontend currently keeps a large amount of UI logic inside `frontend/app.py`, which is useful to know before making interface changes.
- Some AI features depend on external credentials or network availability, so partial functionality is expected if only one provider is configured.

## License

This repository currently does not include a dedicated license file. Add one if you plan to distribute or open the project under a specific license.
