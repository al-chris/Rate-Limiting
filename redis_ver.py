import hashlib
import time
from functools import wraps
from typing import Callable, Awaitable, TypeVar, ParamSpec
from fastapi import Request, HTTPException, status
from redis.asyncio import Redis

P = ParamSpec("P")
R = TypeVar("R")

r = Redis(
    host="REDIS_HOST", # replace with your redis host
    port=6379, # replace with your redis port
    decode_responses=True,
    username="REDIS_USERNAME", # replace with your redis username
    password="REDIS_PASSWORD", # replace with your redis password
)

def rate_limit(max_calls: int, period: int) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Decorator to rate limit FastAPI endpoints using Redis sorted sets.

    Args:
        max_calls (int): Maximum number of allowed calls within the period.
        period (int): Time window in seconds for rate limiting.

    Returns:
        Callable: Decorated async function with rate limiting applied.
    """
    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        """
        Inner decorator function that wraps the endpoint.

        Args:
            func (Callable): The endpoint function to wrap.

        Returns:
            Callable: The wrapped function with rate limiting.
        """
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            """
            Wrapper function that enforces rate limiting.

            Raises:
                ValueError: If the Request object is not found or has no client info.
                HTTPException: If the rate limit is exceeded.

            Returns:
                R: The result of the wrapped endpoint function.
            """
            # Try to find the Request object in args or kwargs
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if request is None:
                request = kwargs.get("request")
            if request is None or not isinstance(request, Request):
                raise ValueError("Request object not found in arguments.")
            
            # get the client's IP address
            if not request.client:
                raise ValueError("Request has no client information.")
            ip_address: str = request.client.host

            # create a unique identifier for the client
            unique_id: str = hashlib.sha256((ip_address).encode()).hexdigest()
            redis_key = f"rate_limit:{unique_id}"

            now = int(time.time() * 1000)  # current time in ms

            # Remove old timestamps
            min_time = now - period * 1000
            await r.zremrangebyscore(redis_key, 0, min_time)

            # Count requests in the current window
            req_count = await r.zcard(redis_key)
            if req_count < max_calls:
                # Add current request timestamp
                await r.zadd(redis_key, {str(now): now})
                # Set expiration for cleanup
                await r.expire(redis_key, period)
                return await func(*args, **kwargs)
            
            # Get oldest timestamp to calculate wait time
            oldest = await r.zrange(redis_key, 0, 0, withscores=True) # type: ignore
            if oldest:
                wait = period - ((now - int(oldest[0][1])) // 1000)
            else:
                wait = period

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {wait:.2f} seconds"
            )
        
        return wrapper
    
    return decorator