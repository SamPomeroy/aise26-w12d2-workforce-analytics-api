from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Skill(Base):
    """
    skill model for tracking in-demand workforce skills
    includes market demand metrics and category classification
    """
    __tablename__ = "skills"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    category = Column(String, index=True)  # technical, soft, domain-specific
    
    # market metrics
    demand_score = Column(Float, default=0.0)  # 0-100 scale
    growth_rate = Column(Float)  # percentage year-over-year
    
    # metadata
    description = Column(Text)
    related_skills = Column(String)  # comma-separated skill names
    
    # timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
