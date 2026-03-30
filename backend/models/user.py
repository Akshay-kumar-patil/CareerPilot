"""User model for authentication and profile storage."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_username = Column(String(100), nullable=True)
    portfolio_url = Column(String(500), nullable=True)

    # FIX: JSON columns — SQLAlchemy handles serialization automatically.
    # No more manual json.dumps/loads; setting user.skills = ["python"] just works.
    skills = Column(JSON, default=list)
    experience_years = Column(Integer, default=0)
    current_role = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=True)
    education = Column(JSON, default=list)
    work_experience = Column(JSON, default=list)
    projects = Column(JSON, default=list)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_skills_list(self):
        return self.skills or []

    def set_skills_list(self, skills_list):
        self.skills = skills_list

    def get_profile_dict(self):
        return {
            "full_name": self.full_name,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "github_username": self.github_username,
            "portfolio_url": self.portfolio_url,
            "skills": self.skills or [],
            "experience_years": self.experience_years,
            "current_role": self.current_role,
            "target_role": self.target_role,
            "education": self.education or [],
            "work_experience": self.work_experience or [],
            "projects": self.projects or [],
            "summary": self.summary,
        }
