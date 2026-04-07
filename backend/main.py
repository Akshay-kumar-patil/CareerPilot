"""
Career Automation & Job Intelligence Platform — FastAPI Backend
Main application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.ai.model_router import model_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


# FIX: lifespan replaces deprecated @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    init_db()
    logger.info("Database initialized")
    status = model_router.get_status()
    logger.info(
        f"AI Status: Internet={status['internet_available']}, "
        f"Gemini={'✓' if status.get('gemini_configured') else '✗'}, "
        f"Groq={'✓' if status.get('groq_configured') else '✗'} ({status.get('groq_model', 'llama-3.3-70b-versatile')}), "
        f"OpenAI={'✓' if status['openai_configured'] else '✗'}"
    )
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered career automation platform.",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# FIX: allow_origins=["*"] with allow_credentials=True is rejected by browsers.
# Use explicit origins from settings instead.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "auth": "/api/auth", "resume": "/api/resume",
            "analyzer": "/api/analyzer", "cover_letter": "/api/cover-letter",
            "applications": "/api/applications", "referrals": "/api/referrals",
            "interview": "/api/interview", "skills": "/api/skills",
            "analytics": "/api/analytics", "email": "/api/email",
            "github": "/api/github", "extract": "/api/extract",
            "auto_apply": "/api/auto-apply",
            "ai_status": "/api/ai/status",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/api/ai/status")
def ai_status():
    return model_router.get_status()


from backend.routers import (
    auth, resume, analyzer, cover_letter, applications,
    referrals, interview, skills, analytics, email_gen,
    github_analyzer, extraction, auto_apply,
)

app.include_router(auth.router)
app.include_router(resume.router)
app.include_router(analyzer.router)
app.include_router(cover_letter.router)
app.include_router(applications.router)
app.include_router(referrals.router)
app.include_router(interview.router)
app.include_router(skills.router)
app.include_router(analytics.router)
app.include_router(email_gen.router)
app.include_router(github_analyzer.router)
app.include_router(extraction.router)
app.include_router(auto_apply.router)

logger.info(f"Registered {len(app.routes)} routes")
