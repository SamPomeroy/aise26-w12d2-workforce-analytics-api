from fastapi import Request, Depends
from datetime import datetime
import redis.asyncio as redis
from app.config import settings
from app.utils.exceptions import RateLimitError
from typing import Optional

# redis client for rate limiting
redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """get or create redis connection"""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return redis_client


async def rate_limit(
    request: Request,
    redis_conn: redis.Redis = Depends(get_redis),
    max_requests: int = None,
    window: int = None
):
    """
    sliding window rate limiter using redis
    tracks requests per client ip address
    """
    # use settings defaults if not specified
    max_requests = max_requests or settings.rate_limit_requests
    window = window or settings.rate_limit_window
    
    # get client identifier (ip address or user id)
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"
    
    try:
        # get current request count
        current = await redis_conn.get(key)
        
        if current is None:
            # first request in window
            await redis_conn.setex(key, window, 1)
            remaining = max_requests - 1
        else:
            current = int(current)
            
            if current >= max_requests:
                # rate limit exceeded
                ttl = await redis_conn.ttl(key)
                raise RateLimitError(
                    detail=f"rate limit exceeded. try again in {ttl} seconds",
                    retry_after=ttl
                )
            
            # increment counter
            await redis_conn.incr(key)
            remaining = max_requests - (current + 1)
        
        # add rate limit headers to response
        request.state.rate_limit_limit = max_requests
        request.state.rate_limit_remaining = remaining
        request.state.rate_limit_reset = window
        
    except RateLimitError:
        raise
    except Exception as e:
        # if redis is down, log but don't block requests
        print(f"rate limiting error: {e}")
        pass


class RateLimiter:
    """
    class-based rate limiter for easier customization
    usage: Depends(RateLimiter(max_requests=10, window=60))
    """
    def __init__(self, max_requests: int = None, window: int = None):
        self.max_requests = max_requests or settings.rate_limit_requests
        self.window = window or settings.rate_limit_window
    
    async def __call__(
        self, 
        request: Request,
        redis_conn: redis.Redis = Depends(get_redis)
    ):
        await rate_limit(request, redis_conn, self.max_requests, self.window)
