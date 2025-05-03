import hashlib
import time
from functools import wraps
from typing import Callable, Awaitable, TypeVar, ParamSpec

from fastapi import Request, HTTPException, status

P = ParamSpec("P")
R = TypeVar("R")

def rate_limit(max_calls: int, period: int) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """
    Decorator to rate limit FastAPI endpoints in-memory per process.

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
        usage: dict[str, list[float]] = {}

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

            # update the timestamps
            now = time.time()
            if unique_id not in usage:
                usage[unique_id] = []
            timestamps = usage[unique_id]
            timestamps[:] = [t for t in timestamps if now - t < period]

            if len(timestamps) < max_calls:
                timestamps.append(now)
                return await func(*args, **kwargs)
            
            # calculate the time to wait before the next request
            wait = period - (now - timestamps[0])
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {wait:.2f} seconds"
            )
        
        return wrapper
    
    return decorator