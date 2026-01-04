import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from pythonjsonlogger import jsonlogger
from app.config import settings

# configure structured json logging
logger = logging.getLogger("api")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    "%(asctime)s %(levelname)s %(name)s %(message)s"
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(settings.log_level)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    logs all api requests and responses with timing info
    uses structured json logging for easy parsing
    """
    
    async def dispatch(self, request: Request, call_next):
        # start timer
        start_time = time.time()
        
        # get request id if available
        request_id = getattr(request.state, "request_id", None)
        
        # log incoming request
        logger.info(
            "incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )
        
        # process request
        try:
            response = await call_next(request)
            
            # calculate processing time
            process_time = time.time() - start_time
            
            # add rate limit headers if available
            if hasattr(request.state, "rate_limit_limit"):
                response.headers["X-RateLimit-Limit"] = str(request.state.rate_limit_limit)
                response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
                response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
            
            # log response
            logger.info(
                "request completed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(process_time * 1000, 2),
                }
            )
            
            return response
            
        except Exception as e:
            # log errors
            process_time = time.time() - start_time
            logger.error(
                "request failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(process_time * 1000, 2),
                    "error": str(e),
                },
                exc_info=True
            )
            raise
