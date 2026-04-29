"""
Database setup — MongoDB primary for users/resumes, ChromaDB for vectors.
SQLAlchemy/SQLite kept only for legacy models (applications, referrals).
"""
import os
import logging
import certifi
import chromadb
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

logger = logging.getLogger(__name__)

# ─── SQLite / SQLAlchemy (legacy — applications, referrals) ───────────────────
_echo_sql = settings.DEBUG and os.environ.get("SQL_ECHO", "false").lower() == "true"

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=_echo_sql,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── MongoDB (PRIMARY for users & resumes) ─────────────────────────────────────
_mongo_client: MongoClient | None = None
_mongo_db = None


def _init_mongo():
    """Initialise MongoDB client; creates indexes on first run."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db

    try:
        import ssl
        _mongo_client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=10_000,
            connectTimeoutMS=10_000,
            socketTimeoutMS=20_000,
            tls=True,
            tlsAllowInvalidCertificates=True,   # Workaround for OpenSSL 1.1.1 on Windows
        )
        _mongo_client.admin.command("ping")     # Fail fast if unreachable
        _mongo_db = _mongo_client[settings.MONGODB_DB_NAME]

        # ── Indexes ────────────────────────────────────────────────────────────
        _mongo_db["authentication"].create_index(
            [("email", ASCENDING)], unique=True, background=True
        )
        _mongo_db["resumes"].create_index(
            [("user_id", ASCENDING)], background=True
        )
        _mongo_db["resumes"].create_index(
            [("user_id", ASCENDING), ("is_active", ASCENDING)], background=True
        )

        logger.info("✅ MongoDB connected  →  db=%s", settings.MONGODB_DB_NAME)
    except Exception as exc:
        logger.error("❌ MongoDB connection failed: %s", exc)
        _mongo_db = False   # sentinel: don't retry in the same process

    return _mongo_db


def get_mongo_db():
    """FastAPI dependency — returns the MongoDB database object or raises."""
    db = _init_mongo()
    if db is None or db is False:
        raise RuntimeError("MongoDB is unavailable. Check MONGODB_URL in .env")
    return db


def get_users_collection():
    """Return the 'authentication' collection."""
    db = _init_mongo()
    if db is None or db is False:
        return None
    return db["authentication"]


def get_resumes_collection():
    """Return the 'resumes' collection."""
    db = _init_mongo()
    if db is None or db is False:
        return None
    return db["resumes"]


# ─── ChromaDB ─────────────────────────────────────────────────────────────────
chroma_client = None


def _init_chroma_client():
    global chroma_client
    if chroma_client is not None:
        return chroma_client
    try:
        chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    except Exception as e:
        logger.warning("ChromaDB unavailable; semantic search disabled. Error: %s", e)
        chroma_client = False
    return chroma_client


def get_chroma_collection(name: str = "resumes"):
    client = _init_chroma_client()
    if not client:
        raise RuntimeError("ChromaDB is unavailable in this environment")
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


# ─── Startup initialiser ──────────────────────────────────────────────────────
def init_db():
    """Called at app startup. Initialises MongoDB, SQLite legacy tables, ChromaDB."""
    # Legacy SQLite tables (applications, referrals, templates)
    from backend.models import application, referral, template  # noqa: F401
    Base.metadata.create_all(bind=engine)

    _init_chroma_client()
    _init_mongo()
