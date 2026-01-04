from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import init_db
from app.routers import health_router, auth_router, jobs_router, skills_router
from app.middleware import RequestIDMiddleware, LoggingMiddleware
from app.utils.exceptions import (
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ValidationError,
    RateLimitError
)

# configure logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    application startup and shutdown logic
    initializes database tables on startup
    """
    # startup
    logger.info("initializing database...")
    init_db()
    logger.info(f"starting {settings.app_name} v{settings.app_version}")
    
    yield
    
    # shutdown
    logger.info("shutting down application")


# create fastapi app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="production-ready workforce analytics api with jwt auth, rate limiting, and comprehensive crud operations",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)


# add cors middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# add custom middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(LoggingMiddleware)


# global exception handlers
@app.exception_handler(AuthenticationError)
async def authentication_error_handler(request: Request, exc: AuthenticationError):
    """handle authentication errors with standardized response"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "authentication_error",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        },
        headers=exc.headers
    )


@app.exception_handler(PermissionDeniedError)
async def permission_denied_handler(request: Request, exc: PermissionDeniedError):
    """handle permission denied errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "permission_denied",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    """handle resource not found errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "not_found",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(ValidationError)
async def validation_error_handler(request: Request, exc: ValidationError):
    """handle validation errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "validation_error",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    """handle rate limit errors"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "rate_limit_exceeded",
            "message": exc.detail,
            "request_id": getattr(request.state, "request_id", None)
        },
        headers=exc.headers
    )


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    """handle pydantic validation errors"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "request validation failed",
            "details": exc.errors(),
            "request_id": getattr(request.state, "request_id", None)
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """catch-all handler for unexpected errors"""
    logger.error(f"unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "an unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# register routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(skills_router)


# root endpoint
@app.get("/", tags=["root"])
async def root():
    """api root - provides basic info and links"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


# api version info
@app.get("/v1", tags=["versioning"])
async def api_v1_info():
    """v1 api information"""
    return {
        "version": "1.0.0",
        "endpoints": {
            "auth": "/v1/auth",
            "jobs": "/v1/jobs",
            "skills": "/v1/skills"
        }
    }
