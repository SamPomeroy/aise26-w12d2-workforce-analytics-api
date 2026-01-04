import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    adds unique request id to each request
    allows tracking requests through logs and distributed systems
    """
    
    async def dispatch(self, request: Request, call_next):
        # check if request already has an id (from load balancer, etc)
        request_id = request.headers.get("X-Request-ID")
        
        if not request_id:
            # generate new uuid for this request
            request_id = str(uuid.uuid4())
        
        # attach to request state for use in handlers
        request.state.request_id = request_id
        
        # call the actual endpoint
        response = await call_next(request)
        
        # add request id to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
