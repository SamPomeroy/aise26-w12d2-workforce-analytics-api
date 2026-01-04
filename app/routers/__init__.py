from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.jobs import router as jobs_router
from app.routers.skills import router as skills_router

__all__ = [
    "health_router",
    "auth_router",
    "jobs_router",
    "skills_router",
]
