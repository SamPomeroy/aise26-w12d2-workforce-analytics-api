from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies.rate_limit import get_redis
import redis.asyncio as redis

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/")
async def health_check():
    """
    basic health check for load balancers
    returns 200 ok if service is running
    """
    return {
        "status": "healthy",
        "service": "workforce analytics api",
        "version": "1.0.0"
    }


@router.get("/detailed")
async def detailed_health_check(
    db: Session = Depends(get_db),
    redis_conn: redis.Redis = Depends(get_redis)
):
    """
    detailed health check showing dependency status
    checks database and redis connectivity
    """
    health_status = {
        "status": "healthy",
        "service": "workforce analytics api",
        "version": "1.0.0",
        "dependencies": {}
    }
    
    # check database
    try:
        db.execute("SELECT 1")
        health_status["dependencies"]["database"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # check redis
    try:
        await redis_conn.ping()
        health_status["dependencies"]["redis"] = "healthy"
    except Exception as e:
        health_status["dependencies"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
