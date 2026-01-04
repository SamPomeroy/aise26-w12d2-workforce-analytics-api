from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class JobPosting(Base):
    """
    job posting model for workforce analytics
    tracks job market data, required skills, and salary info
    """
    __tablename__ = "job_postings"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    company = Column(String, index=True, nullable=False)
    location = Column(String, index=True)
    
    # job details
    description = Column(Text)
    employment_type = Column(String)  # full-time, part-time, contract
    experience_level = Column(String)  # entry, mid, senior
    
    # salary data
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String, default="USD")
    
    # skills and requirements (stored as json array)
    required_skills = Column(JSON)
    preferred_skills = Column(JSON)
    
    # metadata
    remote_allowed = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    posted_by_user_id = Column(Integer)  # fk to users table
    
    # timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    expires_at = Column(DateTime(timezone=True))
