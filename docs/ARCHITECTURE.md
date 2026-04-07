# Architecture Overview

This project is organized around a fairly clear separation between interface, API layer, business logic, persistence, and AI orchestration.

## High-level system view

```text
Streamlit UI
    |
    v
FastAPI routers
    |
    v
Service layer
    |
    +--> SQLite via SQLAlchemy
    |
    +--> ChromaDB for vector storage
    |
    `--> AI model router -> Gemini / Groq / OpenAI
```

## Backend design

### Entry point

`backend/main.py` creates the FastAPI app, configures CORS, initializes the database in the lifespan hook, and mounts all route groups.

### Configuration

`backend/config.py` centralizes runtime settings such as:

- app metadata
- database and storage paths
- AI provider keys and model names
- CORS origins
- upload and generated file directories

The settings are loaded from `.env` through `pydantic-settings`.

### Data layer

`backend/database.py` sets up:

- the SQLAlchemy engine and session factory for SQLite
- the declarative base for ORM models
- a persistent ChromaDB client for vector search

The application stores structured records like users, resumes, applications, referrals, and templates in SQLite. Resume embeddings and similar semantic artifacts are stored in ChromaDB.

### Routing layer

Each route file under `backend/routers/` owns a feature area:

- `auth.py`: registration, login, profile, current user
- `resume.py`: resume generation, retrieval, versions, downloads, delete
- `analyzer.py`: resume analysis, upload scoring, recruiter simulation
- `cover_letter.py`: cover-letter generation and download
- `applications.py`: tracked job applications
- `referrals.py`: referral tracking
- `interview.py`: question generation and answer evaluation
- `skills.py`: skill-gap analysis
- `analytics.py`: summary metrics for the dashboard
- `email_gen.py`: recruiter and follow-up email generation
- `github_analyzer.py`: GitHub-to-resume insight extraction
- `extraction.py`: job description extraction from text, files, and URLs
- `auto_apply.py`: AI-prepared job application workflow

### Service layer

Most business logic lives in `backend/services/`. A few notable responsibilities:

- `resume_service.py`: stores AI-generated resumes, versions, ATS score, keyword analysis, and embeddings
- `analyzer_service.py`: resume scoring and analysis logic
- `cover_letter_service.py`: personalized cover-letter creation
- `interview_service.py`: interview question generation and evaluation
- `skill_service.py`: job-description skill comparison
- `github_service.py`: repo analysis for candidate positioning
- `auto_apply_service.py`: job description parsing, answer generation, and optional Playwright automation
- `memory_service.py`: personalized context handling

## AI architecture

### Model router

`backend/ai/model_router.py` is the central decision point for LLM selection.

It:

- checks provider configuration
- checks whether network access is available
- chooses Gemini, Groq, OpenAI, or an automatic fallback
- tracks token usage and estimated cost
- remembers Gemini quota exhaustion during the current session

### Prompts and chains

`backend/ai/prompts.py` and `backend/ai/chains.py` provide the reusable prompt and orchestration layer used by multiple services.

### Embeddings

`backend/ai/embeddings.py` supports semantic search use cases such as storing resume embeddings for later retrieval or comparison.

## Frontend design

The frontend is a Streamlit application in `frontend/app.py`. It handles:

- authentication screens
- page navigation
- dashboard metrics
- all feature-specific forms and result views
- API calls through `frontend/utils/api_client.py`
- session/auth state through `frontend/utils/session.py`

The UI is intentionally centralized in one file, which makes it easy to trace flows but also means future refactors could split the page logic into feature modules.

## Storage and generated assets

The `data/` directory is used for local runtime state:

- uploaded files
- generated documents
- SQLite database
- ChromaDB persistence

The `templates/` directory contains HTML templates for resume and cover-letter generation.

## Deployment shape

The repository supports several deployment paths:

- direct local development with Python processes
- Docker-based local orchestration
- Render deployment via `render.yaml`

## Practical architectural strengths

- clear route and service separation in the backend
- flexible AI provider strategy
- good alignment between product features and backend modules
- local-first persistence that lowers setup complexity

## Practical architectural trade-offs

- `frontend/app.py` is large and contains many responsibilities
- SQLite is convenient but may limit multi-user or high-concurrency scaling
- some advanced flows depend on external AI credentials and internet availability
- Playwright-driven automation adds environment-specific behavior that may differ across local and hosted runs
