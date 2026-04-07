# Setup Guide

This guide is meant for someone opening the repository for the first time and wanting a dependable local development setup.

## Prerequisites

- Python 3.10 or newer
- `pip`
- A virtual environment tool such as `venv`
- Optional API keys for Gemini, Groq, or OpenAI
- Optional Playwright browser installation if you want browser-assisted auto apply flows

## Recommended local setup

### 1. Clone and enter the project

```bash
git clone <repository-url>
cd career-portal
```

### 2. Create a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

On Unix-like systems:

```bash
source venv/bin/activate
```

### 3. Install dependencies

Full project dependencies:

```bash
pip install -r requirements.txt
```

If you want to install the frontend-specific requirements separately:

```bash
pip install -r frontend/requirements.txt
```

### 4. Configure environment variables

Create a `.env` file from the example:

```bash
copy .env.example .env
```

Update the values based on the features you plan to use.

## Important environment variables

### AI providers

- `GEMINI_API_KEY`: primary AI option in the current configuration
- `GROQ_API_KEY`: useful fallback when Gemini is unavailable or rate-limited
- `OPENAI_API_KEY`: optional alternate provider
- `DEFAULT_MODEL_PROVIDER`: one of `gemini`, `groq`, `openai`, or `auto`

### Security and app behavior

- `SECRET_KEY`: required for JWT signing in non-demo environments
- `ENABLE_COST_TRACKING`: turns token-cost tracking on or off
- `MAX_MONTHLY_COST_USD`: soft cost-control setting

### Optional integrations

- `GITHUB_TOKEN`: enables richer GitHub analysis for repository-driven resume bullets

## Running the application

### Backend

```bash
uvicorn backend.main:app --reload --port 8000
```

What happens on startup:

- SQLite tables are initialized
- ChromaDB persistence directory is prepared
- AI provider status is checked and logged
- FastAPI docs are exposed at `/docs` and `/redoc`

### Frontend

```bash
streamlit run frontend/app.py
```

The frontend expects the FastAPI backend to be available, so start the backend first.

## Optional Docker workflow

For a container-based run:

```bash
docker-compose up --build
```

The repository also includes separate Dockerfiles for backend and frontend deployments.

## Playwright support

The auto-apply workflow can work in two modes:

- AI preparation mode, where the app generates answers for manual submission
- Browser automation mode, where Playwright can fill and submit forms when installed and supported

If you want the second mode, make sure Playwright and its browsers are installed in your environment.

## Common issues

### AI features are unavailable

Check:

- whether at least one provider API key is present in `.env`
- whether the configured provider matches the keys you supplied
- whether the machine can reach the provider endpoints

### Frontend loads but actions fail

Check:

- whether the backend is running on the expected port
- whether CORS origins match your frontend URL
- whether authentication was completed successfully

### Resume generation or semantic features fail

Check:

- whether `data/` is writable
- whether ChromaDB initialized correctly
- whether the embedding and LLM dependencies installed without error
