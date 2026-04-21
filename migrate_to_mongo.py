import os
import json
import logging
from sqlalchemy import create_engine, Column, Integer, String, Text, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy SQLite Config
from backend.config import settings
SQLITE_URL = settings.DATABASE_URL
engine = create_engine(SQLITE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Legacy Models
class LegacyUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    skills = Column(Text, nullable=True)  # Stored as JSON
    experience_years = Column(Integer, default=0)
    current_role = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=True)
    education = Column(Text, nullable=True)  # Stored as JSON
    work_experience = Column(Text, nullable=True)  # Stored as JSON
    projects = Column(Text, nullable=True)  # Stored as JSON
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class LegacyResume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)  # Stored as JSON
    raw_text = Column(Text, nullable=True)
    template_id = Column(Integer, nullable=True)
    ats_score = Column(Float, nullable=True)
    target_jd = Column(Text, nullable=True)
    keywords_matched = Column(Text, nullable=True)
    keywords_missing = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

def json_loads_safe(data):
    if not data:
        return []
    try:
        return json.loads(data)
    except Exception:
        return []

def migrate():
    from backend.config import settings
    logger.info("Connecting to MongoDB...")
    import certifi
    mongo_client = MongoClient(settings.MONGODB_URL, tlsCAFile=certifi.where())
    mongo_db = mongo_client[settings.MONGODB_DB_NAME]
    
    users_col = mongo_db["authentication"]
    resumes_col = mongo_db["resumes"]

    db = SessionLocal()
    
    try:
        legacy_users = db.query(LegacyUser).all()
        logger.info(f"Found {len(legacy_users)} users in SQLite.")
        
        user_id_map = {} # map old numeric id to new ObjectId string
        
        for u in legacy_users:
            if users_col.find_one({"email": u.email}):
                logger.info(f"User {u.email} already in MongoDB, skipping or getting their _id...")
                existing = users_col.find_one({"email": u.email})
                user_id_map[u.id] = str(existing["_id"])
                continue
                
            doc = {
                "email": u.email,
                "hashed_password": u.hashed_password,
                "full_name": u.full_name,
                "auth_provider": "local",
                "phone": u.phone,
                "linkedin_url": u.linkedin_url,
                "github_username": u.github_username,
                "portfolio_url": u.portfolio_url,
                "skills": json_loads_safe(u.skills) if u.skills else [],
                "experience_years": u.experience_years or 0,
                "current_role": u.current_role,
                "target_role": u.target_role,
                "education": json_loads_safe(u.education) if u.education else [],
                "work_experience": json_loads_safe(u.work_experience) if u.work_experience else [],
                "projects": json_loads_safe(u.projects) if u.projects else [],
                "summary": u.summary,
                "is_active": True,
                "created_at": u.created_at,
                "updated_at": u.updated_at,
            }
            res = users_col.insert_one(doc)
            user_id_map[u.id] = str(res.inserted_id)
            logger.info(f"Migrated user: {u.email}")
            
        legacy_resumes = db.query(LegacyResume).all()
        logger.info(f"Found {len(legacy_resumes)} resumes in SQLite.")
        
        for r in legacy_resumes:
            new_user_id = user_id_map.get(r.user_id)
            if not new_user_id:
                logger.warning(f"Resume {r.id} belongs to unknown user_id {r.user_id}, skipping.")
                continue
                
            if resumes_col.find_one({"user_id": new_user_id, "title": r.title, "created_at": r.created_at}):
                logger.info(f"Resume {r.title} already migrated, skipping.")
                continue
                
            # Content should be dict in Mongo
            try:
                content_dict = json.loads(r.content) if r.content else {}
            except Exception:
                content_dict = {"raw": r.content}
                
            doc = {
                "user_id": new_user_id,
                "title": r.title,
                "content": content_dict,
                "raw_text": r.raw_text,
                "template_id": str(r.template_id) if r.template_id else None,
                "ats_score": r.ats_score,
                "target_jd": r.target_jd,
                "keywords_matched": json_loads_safe(r.keywords_matched) if r.keywords_matched else [],
                "keywords_missing": json_loads_safe(r.keywords_missing) if r.keywords_missing else [],
                "version": r.version or 1,
                "is_active": bool(r.is_active),
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            resumes_col.insert_one(doc)
            logger.info(f"Migrated resume: {r.title} for user {new_user_id}")
            
        logger.info("Migration strictly for users and resumes complete!")
        
        # Now we need to update application / referral records to use the new string user_ids if they exist.
        from sqlalchemy import text
        with engine.begin() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            for old_id, new_id in user_id_map.items():
                conn.execute(text("UPDATE applications SET user_id = :new_id WHERE user_id = :old_id"), {"new_id": new_id, "old_id": old_id})
                conn.execute(text("UPDATE referrals SET user_id = :new_id WHERE user_id = :old_id"), {"new_id": new_id, "old_id": old_id})
                conn.execute(text("UPDATE interview_sessions SET user_id = :new_id WHERE user_id = :old_id"), {"new_id": new_id, "old_id": old_id})
        
        logger.info("Updated SQLite FK references to point to MongoDB string IDs.")

    except Exception as e:
        logger.error(f"Migration error: {e}", exc_info=True)
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
