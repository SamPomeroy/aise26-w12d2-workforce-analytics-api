from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List


class JobPostingBase(BaseModel):
    """base job posting schema"""
    title: str = Field(..., min_length=5, max_length=200)
    company: str = Field(..., min_length=2, max_length=200)
    location: Optional[str] = None
    description: Optional[str] = None
    employment_type: str = Field(default="full-time", pattern="^(full-time|part-time|contract|temporary)$")
    experience_level: str = Field(default="mid", pattern="^(entry|mid|senior|executive)$")


class JobPostingCreate(JobPostingBase):
    """schema for creating a job posting"""
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    salary_currency: str = Field(default="USD", max_length=3)
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    remote_allowed: bool = False
    expires_at: Optional[datetime] = None
    
    @validator('salary_max')
    def validate_salary_range(cls, v, values):
        """ensure max salary is greater than min"""
        if v is not None and 'salary_min' in values and values['salary_min'] is not None:
            if v < values['salary_min']:
                raise ValueError('salary_max must be greater than or equal to salary_min')
        return v


class JobPostingUpdate(BaseModel):
    """schema for updating a job posting (all fields optional)"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    company: Optional[str] = Field(None, min_length=2, max_length=200)
    location: Optional[str] = None
    description: Optional[str] = None
    employment_type: Optional[str] = Field(None, pattern="^(full-time|part-time|contract|temporary)$")
    experience_level: Optional[str] = Field(None, pattern="^(entry|mid|senior|executive)$")
    salary_min: Optional[float] = Field(None, ge=0)
    salary_max: Optional[float] = Field(None, ge=0)
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    remote_allowed: Optional[bool] = None
    is_active: Optional[bool] = None


class JobPostingResponse(JobPostingBase):
    """schema for job posting response"""
    id: int
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: str
    required_skills: Optional[List[str]]
    preferred_skills: Optional[List[str]]
    remote_allowed: bool
    is_active: bool
    posted_by_user_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    expires_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobPostingListResponse(BaseModel):
    """paginated response for job listings"""
    total: int
    jobs: List[JobPostingResponse]
    page: int
    page_size: int
