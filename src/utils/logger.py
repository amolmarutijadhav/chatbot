"""Logging configuration and setup for the chatbot system."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional
import structlog
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_file_size: str = "10MB",
    backup_count: int = 5,
    console_output: bool = True,
    structured: bool = True,
    include_timestamp: bool = True,
    include_correlation_id: bool = True
) -> None:
    """Setup logging configuration for the chatbot system."""
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert string level to logging level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Clear existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create formatter
    if structured:
        formatter = create_structured_formatter(
            include_timestamp=include_timestamp,
            include_correlation_id=include_correlation_id
        )
    else:
        formatter = create_standard_formatter()
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        if include_correlation_id:
            correlation_filter = CorrelationIdFilter()
            console_handler.addFilter(correlation_filter)
        root_logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Parse max file size
        max_bytes = parse_size_string(max_file_size)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        if include_correlation_id:
            correlation_filter = CorrelationIdFilter()
            file_handler.addFilter(correlation_filter)
        root_logger.addHandler(file_handler)
    
    # Set root logger level
    root_logger.setLevel(log_level)
    
    # Configure structlog if structured logging is enabled
    if structured:
        setup_structlog()
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {level}, File: {log_file}, Structured: {structured}")


def create_standard_formatter() -> logging.Formatter:
    """Create a standard logging formatter."""
    return logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def create_structured_formatter(
    include_timestamp: bool = True,
    include_correlation_id: bool = True
) -> logging.Formatter:
    """Create a structured logging formatter."""
    format_parts = []
    
    if include_timestamp:
        format_parts.append('"timestamp": "%(asctime)s"')
    
    format_parts.extend([
        '"level": "%(levelname)s"',
        '"logger": "%(name)s"',
        '"message": "%(message)s"'
    ])
    
    if include_correlation_id:
        format_parts.append('"correlation_id": "%(correlation_id)s"')
    
    format_string = "{" + ", ".join(format_parts) + "}"
    
    format_string = "{" + ", ".join(format_parts) + "}"
    
    return logging.Formatter(
        fmt=format_string,
        datefmt='%Y-%m-%dT%H:%M:%S'
    )


def setup_structlog() -> None:
    """Setup structlog for structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def parse_size_string(size_str: str) -> int:
    """Parse size string like '10MB' to bytes."""
    size_str = size_str.upper()
    
    if size_str.endswith('KB'):
        return int(size_str[:-2]) * 1024
    elif size_str.endswith('MB'):
        return int(size_str[:-2]) * 1024 * 1024
    elif size_str.endswith('GB'):
        return int(size_str[:-2]) * 1024 * 1024 * 1024
    else:
        return int(size_str)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


def get_structlog_logger(name: str) -> structlog.BoundLogger:
    """Get a structlog logger instance with the given name."""
    return structlog.get_logger(name)


class CorrelationIdFilter(logging.Filter):
    """Logging filter to add correlation ID to log records."""
    
    def __init__(self):
        super().__init__()
        self.correlation_id = None
    
    def filter(self, record):
        record.correlation_id = self.correlation_id or "no-id"
        return True
    
    def set_correlation_id(self, correlation_id: str):
        """Set the correlation ID for this filter."""
        self.correlation_id = correlation_id


# Global correlation ID filter
_correlation_filter = CorrelationIdFilter()


def set_correlation_id(correlation_id: str) -> None:
    """Set the correlation ID for logging."""
    _correlation_filter.set_correlation_id(correlation_id)
    
    # Add filter to root logger if not already added
    root_logger = logging.getLogger()
    if _correlation_filter not in root_logger.filters:
        root_logger.addFilter(_correlation_filter)


def get_correlation_id() -> Optional[str]:
    """Get the current correlation ID."""
    return _correlation_filter.correlation_id


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get a logger instance for this class."""
        return logging.getLogger(self.__class__.__name__)
    
    @property
    def struct_logger(self) -> structlog.BoundLogger:
        """Get a structlog logger instance for this class."""
        return structlog.get_logger(self.__class__.__name__)


def log_function_call(func):
    """Decorator to log function calls."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper


def log_async_function_call(func):
    """Decorator to log async function calls."""
    async def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        logger.debug(f"Calling async {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = await func(*args, **kwargs)
            logger.debug(f"Async {func.__name__} returned {result}")
            return result
        except Exception as e:
            logger.error(f"Async {func.__name__} raised {type(e).__name__}: {e}")
            raise
    return wrapper 