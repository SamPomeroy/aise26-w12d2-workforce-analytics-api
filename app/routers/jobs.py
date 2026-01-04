from fastapi import APIRouter, Depends, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import Optional, List
from app.database import get_db
from app.models.user import User
from app.models.job_posting import JobPosting
from app.schemas.job_posting import (
    JobPostingCreate, 
    JobPostingUpdate, 
    JobPostingResponse, 
    JobPostingListResponse
)
from app.dependencies.auth import get_current_user, require_roles, optional_user
from app.dependencies.rate_limit import rate_limit
from app.utils.exceptions import NotFoundError, PermissionDeniedError
from app.services.market_data import analyze_skill_demand

router = APIRouter(prefix="/v1/jobs", tags=["job postings"])


async def log_job_view(job_id: int):
    """background task to log job views for analytics"""
    # in production this might write to analytics db or send to data pipeline
    print(f"job {job_id} viewed")


@router.post("/", response_model=JobPostingResponse, status_code=status.HTTP_201_CREATED)
async def create_job_posting(
    job_data: JobPostingCreate,
    current_user: User = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    create a new job posting
    requires employer or admin role
    """
    new_job = JobPosting(
        **job_data.model_dump(),
        posted_by_user_id=current_user.id
    )
    
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    
    return new_job


@router.get("/", response_model=JobPostingListResponse)
async def list_job_postings(
    skip: int = Query(0, ge=0, description="number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="max records to return"),
    company: Optional[str] = Query(None, description="filter by company name"),
    location: Optional[str] = Query(None, description="filter by location"),
    remote_only: Optional[bool] = Query(None, description="show only remote jobs"),
    experience_level: Optional[str] = Query(None, description="filter by experience level"),
    employment_type: Optional[str] = Query(None, description="filter by employment type"),
    min_salary: Optional[float] = Query(None, ge=0, description="minimum salary"),
    max_salary: Optional[float] = Query(None, ge=0, description="maximum salary"),
    skills: Optional[str] = Query(None, description="comma-separated required skills"),
    sort_by: str = Query("created_at", description="field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="sort order"),
    active_only: bool = Query(True, description="show only active postings"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    list job postings with filtering, sorting, and pagination
    publicly accessible but includes extra data for authenticated users
    """
    # build query
    query = db.query(JobPosting)
    
    # apply filters
    if active_only:
        query = query.filter(JobPosting.is_active == True)
    
    if company:
        query = query.filter(JobPosting.company.ilike(f"%{company}%"))
    
    if location:
        query = query.filter(JobPosting.location.ilike(f"%{location}%"))
    
    if remote_only:
        query = query.filter(JobPosting.remote_allowed == True)
    
    if experience_level:
        query = query.filter(JobPosting.experience_level == experience_level)
    
    if employment_type:
        query = query.filter(JobPosting.employment_type == employment_type)
    
    if min_salary is not None:
        query = query.filter(JobPosting.salary_min >= min_salary)
    
    if max_salary is not None:
        query = query.filter(JobPosting.salary_max <= max_salary)
    
    if skills:
        # filter jobs that have any of the specified skills
        skill_list = [s.strip() for s in skills.split(",")]
        # this is a simple contains check - in production you'd want full-text search
        for skill in skill_list:
            query = query.filter(
                or_(
                    JobPosting.required_skills.contains([skill]),
                    JobPosting.preferred_skills.contains([skill])
                )
            )
    
    # apply sorting
    if sort_order == "desc":
        query = query.order_by(getattr(JobPosting, sort_by).desc())
    else:
        query = query.order_by(getattr(JobPosting, sort_by).asc())
    
    # get total count before pagination
    total = query.count()
    
    # apply pagination
    jobs = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "jobs": jobs,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/{job_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    get a specific job posting by id
    logs view as background task for analytics
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise NotFoundError(f"job posting {job_id} not found")
    
    # log job view in background
    background_tasks.add_task(log_job_view, job_id)
    
    return job


@router.put("/{job_id}", response_model=JobPostingResponse)
async def update_job_posting(
    job_id: int,
    job_data: JobPostingUpdate,
    current_user: User = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    update a job posting
    users can only update their own postings unless they're admin
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise NotFoundError(f"job posting {job_id} not found")
    
    # check ownership unless admin
    if current_user.role != "admin" and job.posted_by_user_id != current_user.id:
        raise PermissionDeniedError("you can only update your own job postings")
    
    # update fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)
    
    db.commit()
    db.refresh(job)
    
    return job


@router.patch("/{job_id}/deactivate", response_model=JobPostingResponse)
async def deactivate_job_posting(
    job_id: int,
    current_user: User = Depends(require_roles("employer", "admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    deactivate a job posting (soft delete)
    users can only deactivate their own postings unless they're admin
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise NotFoundError(f"job posting {job_id} not found")
    
    # check ownership unless admin
    if current_user.role != "admin" and job.posted_by_user_id != current_user.id:
        raise PermissionDeniedError("you can only deactivate your own job postings")
    
    job.is_active = False
    db.commit()
    db.refresh(job)
    
    return job


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_posting(
    job_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    permanently delete a job posting
    admin only - regular users should use deactivate
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise NotFoundError(f"job posting {job_id} not found")
    
    db.delete(job)
    db.commit()
    
    return None


@router.post("/{job_id}/analyze", status_code=status.HTTP_202_ACCEPTED)
async def analyze_job_posting(
    job_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    analyze required skills for a job posting
    demonstrates async processing with background tasks
    """
    job = db.query(JobPosting).filter(JobPosting.id == job_id).first()
    
    if not job:
        raise NotFoundError(f"job posting {job_id} not found")
    
    # schedule async analysis for each required skill
    if job.required_skills:
        for skill in job.required_skills:
            background_tasks.add_task(analyze_skill_demand, skill)
    
    return {
        "status": "accepted",
        "message": "skill analysis started in background",
        "job_id": job_id
    }
