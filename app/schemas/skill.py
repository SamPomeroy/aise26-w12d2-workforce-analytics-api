from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class SkillBase(BaseModel):
    """base skill schema"""
    name: str = Field(..., min_length=2, max_length=100)
    category: str = Field(default="technical", pattern="^(technical|soft|domain-specific)$")
    description: Optional[str] = None


class SkillCreate(SkillBase):
    """schema for creating a skill"""
    demand_score: float = Field(default=0.0, ge=0.0, le=100.0)
    growth_rate: Optional[float] = None
    related_skills: Optional[str] = None


class SkillUpdate(BaseModel):
    """schema for updating a skill (all fields optional)"""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[str] = Field(None, pattern="^(technical|soft|domain-specific)$")
    description: Optional[str] = None
    demand_score: Optional[float] = Field(None, ge=0.0, le=100.0)
    growth_rate: Optional[float] = None
    related_skills: Optional[str] = None


class SkillResponse(SkillBase):
    """schema for skill response"""
    id: int
    demand_score: float
    growth_rate: Optional[float]
    related_skills: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SkillListResponse(BaseModel):
    """paginated response for skill listings"""
    total: int
    skills: List[SkillResponse]
    page: int
    page_size: int
