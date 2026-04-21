"""Referral management model."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from backend.database import Base


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), nullable=False)
    contact_name = Column(String(255), nullable=False)
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    relationship = Column(String(100), nullable=True)  # colleague, friend, alumni, etc.
    status = Column(String(50), default="pending")  # pending, contacted, referred, declined
    referral_date = Column(DateTime, nullable=True)
    response_received = Column(Integer, default=0)
    notes = Column(Text, nullable=True)
    follow_up_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
