"""
Shared utilities for all agents - Windows Compatible
"""
import logging
import time
import os
from functools import wraps
from typing import Callable, Any
import json
from datetime import datetime
import tempfile


# Logging configuration
def setup_logging(service_name: str, log_level: str = "INFO"):
    """Setup logging for a service"""
    # Windows-compatible: use current directory
    log_file = f'{service_name}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=f'%(asctime)s - {service_name} - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file)
        ]
    )
    return logging.getLogger(service_name)


# Timing decorator
def timing_decorator(func: Callable) -> Callable:
    """Measure function execution time"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logging.info(f"{func.__name__} took {duration:.2f}ms")
        return result
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logging.info(f"{func.__name__} took {duration:.2f}ms")
        return result
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


# Configuration management
class Config:
    """Configuration management from environment variables"""
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/personalization")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Vector DB
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    
    # Message Queue
    RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
    
    # Services
    SEGMENTATION_URL = os.getenv("SEGMENTATION_URL", "http://localhost:5001")
    CONTENT_RETRIEVAL_URL = os.getenv("CONTENT_RETRIEVAL_URL", "http://localhost:5002")
    MESSAGE_GENERATION_URL = os.getenv("MESSAGE_GENERATION_URL", "http://localhost:5003")
    COMPLIANCE_URL = os.getenv("COMPLIANCE_URL", "http://localhost:5004")
    EXPERIMENT_URL = os.getenv("EXPERIMENT_URL", "http://localhost:5005")
    
    # LLM Configuration
    OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
    
    # Embedding Model
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    
    # Application
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    WORKERS = int(os.getenv("WORKERS", "4"))


# Data generation utilities
def generate_customer_id():
    """Generate a unique customer ID"""
    import uuid
    return f"C{uuid.uuid4().hex[:8].upper()}"


def generate_content_id():
    """Generate a unique content ID"""
    import uuid
    return f"CNT{uuid.uuid4().hex[:8].upper()}"


def generate_experiment_id():
    """Generate a unique experiment ID"""
    import uuid
    return f"EXP{uuid.uuid4().hex[:8].upper()}"


# JSON serialization utilities
class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def json_dumps(obj: Any) -> str:
    """Serialize object to JSON string"""
    return json.dumps(obj, cls=DateTimeEncoder)


# Retry decorator
def retry(max_attempts: int = 3, delay: float = 1.0):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            import asyncio
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (2 ** attempt)
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
                    wait_time = delay * (2 ** attempt)
                    logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator


# Validation utilities
def validate_customer_id(customer_id: str) -> bool:
    """Validate customer ID format"""
    return customer_id.startswith('C') and len(customer_id) == 9


def validate_segment_id(segment_id: str) -> bool:
    """Validate segment ID format"""
    return len(segment_id) > 0


# Cache key generators
def generate_cache_key(prefix: str, *args) -> str:
    """Generate a cache key"""
    parts = [prefix] + [str(arg) for arg in args]
    return ":".join(parts)
