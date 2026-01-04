from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.skill import Skill
from app.schemas.skill import (
    SkillCreate,
    SkillUpdate,
    SkillResponse,
    SkillListResponse
)
from app.dependencies.auth import get_current_user, require_roles, optional_user
from app.dependencies.rate_limit import rate_limit
from app.utils.exceptions import NotFoundError, ValidationError

router = APIRouter(prefix="/v1/skills", tags=["skills"])


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    create a new skill
    admin only to maintain data quality
    """
    # check if skill name already exists
    existing_skill = db.query(Skill).filter(Skill.name == skill_data.name).first()
    if existing_skill:
        raise ValidationError(f"skill '{skill_data.name}' already exists")
    
    new_skill = Skill(**skill_data.model_dump())
    
    db.add(new_skill)
    db.commit()
    db.refresh(new_skill)
    
    return new_skill


@router.get("/", response_model=SkillListResponse)
async def list_skills(
    skip: int = Query(0, ge=0, description="number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="max records to return"),
    category: Optional[str] = Query(None, description="filter by category"),
    min_demand: Optional[float] = Query(None, ge=0, le=100, description="minimum demand score"),
    search: Optional[str] = Query(None, description="search in skill name or description"),
    sort_by: str = Query("demand_score", description="field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="sort order"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    list skills with filtering, sorting, and pagination
    publicly accessible for job seekers to explore in-demand skills
    """
    # build query
    query = db.query(Skill)
    
    # apply filters
    if category:
        query = query.filter(Skill.category == category)
    
    if min_demand is not None:
        query = query.filter(Skill.demand_score >= min_demand)
    
    if search:
        query = query.filter(
            (Skill.name.ilike(f"%{search}%")) | 
            (Skill.description.ilike(f"%{search}%"))
        )
    
    # apply sorting
    if sort_order == "desc":
        query = query.order_by(getattr(Skill, sort_by).desc())
    else:
        query = query.order_by(getattr(Skill, sort_by).asc())
    
    # get total count before pagination
    total = query.count()
    
    # apply pagination
    skills = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "skills": skills,
        "page": skip // limit + 1,
        "page_size": limit
    }


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    get a specific skill by id
    includes demand metrics and related skills
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise NotFoundError(f"skill {skill_id} not found")
    
    return skill


@router.get("/name/{skill_name}", response_model=SkillResponse)
async def get_skill_by_name(
    skill_name: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    get a skill by name (case-insensitive)
    useful for looking up specific skills
    """
    skill = db.query(Skill).filter(Skill.name.ilike(skill_name)).first()
    
    if not skill:
        raise NotFoundError(f"skill '{skill_name}' not found")
    
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    update a skill's information
    admin only to maintain data quality
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise NotFoundError(f"skill {skill_id} not found")
    
    # check if updating name to one that already exists
    if skill_data.name and skill_data.name != skill.name:
        existing = db.query(Skill).filter(Skill.name == skill_data.name).first()
        if existing:
            raise ValidationError(f"skill '{skill_data.name}' already exists")
    
    # update fields
    update_data = skill_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(skill, field, value)
    
    db.commit()
    db.refresh(skill)
    
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limit)
):
    """
    permanently delete a skill
    admin only - use with caution
    """
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    
    if not skill:
        raise NotFoundError(f"skill {skill_id} not found")
    
    db.delete(skill)
    db.commit()
    
    return None


@router.get("/trending/top", response_model=SkillListResponse)
async def get_trending_skills(
    limit: int = Query(10, ge=1, le=50, description="number of top skills to return"),
    category: Optional[str] = Query(None, description="filter by category"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(optional_user),
    _: None = Depends(rate_limit)
):
    """
    get top trending skills based on demand score and growth rate
    useful for job seekers identifying valuable skills to learn
    """
    query = db.query(Skill)
    
    if category:
        query = query.filter(Skill.category == category)
    
    # sort by demand score and growth rate
    query = query.order_by(Skill.demand_score.desc(), Skill.growth_rate.desc())
    
    skills = query.limit(limit).all()
    total = query.count()
    
    return {
        "total": total,
        "skills": skills,
        "page": 1,
        "page_size": limit
    }
