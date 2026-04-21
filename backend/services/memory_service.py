"""Personal memory service — stores and retrieves user context for AI."""
import json
from bson.errors import InvalidId
from backend.database import get_users_collection, get_resumes_collection
from backend.models.user import user_doc_to_response

# Optional: keep for app history if apps are still in sqlite
from sqlalchemy.orm import Session
from backend.models.application import Application

class MemoryService:

    def get_user_context(self, db: Session, user_id: str) -> str:
        """Assemble full user context for AI prompts."""
        # 1. Fetch user from MongoDB
        user_col = get_users_collection()
        try:
            from bson import ObjectId
            user_doc = user_col.find_one({"_id": ObjectId(user_id)})
        except InvalidId:
            return "No user profile found."
            
        if not user_doc:
            return "No user profile found."

        profile = user_doc_to_response(user_doc)

        # 2. Get latest active resume from MongoDB
        resume_col = get_resumes_collection()
        latest_resume = resume_col.find_one(
            {"user_id": user_id, "is_active": True},
            sort=[("created_at", -1)]
        )

        # 3. Get application stats from SQLite (legacy)
        apps = db.query(Application).filter(Application.user_id == user_id).all()
        app_stats = {
            "total": len(apps),
            "by_status": {},
        }
        for app in apps:
            status = app.status
            app_stats["by_status"][status] = app_stats["by_status"].get(status, 0) + 1

        context_parts = [
            f"User Profile: {json.dumps(profile)}",
            f"Application History: {json.dumps(app_stats)}",
        ]

        if latest_resume:
            raw_text = latest_resume.get("raw_text", "")
            version = latest_resume.get("version", 1)
            context_parts.append(f"Latest Resume (v{version}): {raw_text[:1000]}")

        return "\n\n".join(context_parts)

    def update_profile(self, user_id: str, updates: dict) -> dict:
        """Update user profile fields in MongoDB."""
        user_col = get_users_collection()
        try:
            from bson import ObjectId
            user_col.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": updates}
            )
            return user_doc_to_response(user_col.find_one({"_id": ObjectId(user_id)}))
        except InvalidId:
            return None

memory_service = MemoryService()
