import asyncio
import random
import logging
from functools import wraps
from typing import Callable, Type, Tuple
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
    after_log
)

logger = logging.getLogger(__name__)


def retry_with_exponential_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    add_jitter: bool = True
):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time in seconds
        max_wait: Maximum wait time in seconds
        exceptions: Tuple of exception types to retry on
        add_jitter: Whether to add random jitter to prevent thundering herd
    """
    def decorator(func: Callable):
        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exceptions),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            after=after_log(logger, logging.INFO)
        )
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                result = await func(*args, **kwargs)
                
                if add_jitter:
                    jitter = random.uniform(0, 0.1)
                    await asyncio.sleep(jitter)
                
                return result
            except exceptions as e:
                logger.warning(f"Retry attempt failed: {str(e)}")
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            raise ValueError("Only async functions are supported")
    
    return decorator


def retry_on_lms_error(max_attempts: int = 3):
    """Retry decorator for LMS operations"""
    return retry_with_exponential_backoff(
        max_attempts=max_attempts,
        min_wait=2.0,
        max_wait=15.0,
        exceptions=(Exception,),
        add_jitter=True
    )
