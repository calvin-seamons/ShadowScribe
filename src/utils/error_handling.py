"""
Error Handling - Comprehensive error management for ShadowScribe
"""

import asyncio
import logging
from typing import Optional, Callable, Any, TypeVar
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ShadowScribeError(Exception):
    """Base exception for ShadowScribe errors."""
    pass


class DataLoadError(ShadowScribeError):
    """Error loading data from knowledge base."""
    pass


class LLMError(ShadowScribeError):
    """Error communicating with LLM."""
    pass


class ValidationError(ShadowScribeError):
    """Error validating data or responses."""
    pass


class ConfigurationError(ShadowScribeError):
    """Error in system configuration."""
    pass


def with_fallback(fallback_value: Any, log_errors: bool = True):
    """Decorator to provide fallback values on error."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return fallback_value
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"Error in {func.__name__}: {str(e)}")
                return fallback_value
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)):
    """Decorator to retry function calls on failure."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}")
            
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class ErrorHandler:
    """Centralized error handling and logging."""
    
    @staticmethod
    def handle_data_load_error(file_path: str, error: Exception) -> dict:
        """Handle data loading errors gracefully."""
        logger.error(f"Failed to load data from {file_path}: {str(error)}")
        return {
            "error": True,
            "message": f"Could not load {file_path}",
            "details": str(error),
            "data": {}
        }
    
    @staticmethod
    def handle_llm_error(operation: str, error: Exception) -> dict:
        """Handle LLM communication errors."""
        logger.error(f"LLM error during {operation}: {str(error)}")
        return {
            "error": True,
            "operation": operation,
            "message": "LLM communication failed",
            "details": str(error),
            "response": None
        }
    
    @staticmethod
    def handle_validation_error(data_type: str, error: Exception) -> dict:
        """Handle validation errors."""
        logger.error(f"Validation error for {data_type}: {str(error)}")
        return {
            "error": True,
            "data_type": data_type,
            "message": "Data validation failed",
            "details": str(error),
            "valid": False
        }