"""
Database setup for SQLite (SQLAlchemy), ChromaDB (vector store),
and MongoDB (pymongo) for the career.users collection.
"""
import os
import logging
import chromadb
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from backend.config import settings

logger = logging.getLogger(__name__)

# ─── SQLite / SQLAlchemy ───────────────────────────────────────────────────
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


# ─── MongoDB (pymongo) ─────────────────────────────────────────────────────
_mongo_client = None
_mongo_db = None


def _init_mongo():
    """Lazily initialise the MongoDB client; degrade gracefully on failure."""
    global _mongo_client, _mongo_db
    if _mongo_db is not None:
        return _mongo_db
    try:
        from pymongo import MongoClient
        from pymongo.errors import ConnectionFailure

        _mongo_client = MongoClient(
            settings.MONGODB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )
        # Force a connection to detect early failures
        _mongo_client.admin.command("ping")
        _mongo_db = _mongo_client[settings.MONGODB_DB_NAME]
        logger.info("MongoDB connected  →  db=%s", settings.MONGODB_DB_NAME)
    except Exception as exc:
        logger.warning("MongoDB unavailable — user sync disabled. Error: %s", exc)
        _mongo_db = False
    return _mongo_db


def get_mongo_db():
    """FastAPI dependency — yields the MongoDB database object (or None)."""
    db = _init_mongo()
    return db if db else None


def get_users_collection():
    """Return the authentication collection, or None if Mongo is unavailable."""
    db = _init_mongo()
    if not db:
        return None
    return db["authentication"]


# ─── ChromaDB ─────────────────────────────────────────────────────────────
chroma_client = None


def _init_chroma_client():
    """Initialize Chroma lazily and degrade gracefully on local disk issues."""
    global chroma_client
    if chroma_client is not None:
        return chroma_client
    try:
        chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
    except Exception as e:
        logger.warning(
            "ChromaDB unavailable; semantic search features will be disabled. Error: %s",
            e,
        )
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


def init_db():
    from backend.models import user, resume, application, referral, template  # noqa
    Base.metadata.create_all(bind=engine)
    _init_chroma_client()
    _init_mongo()

