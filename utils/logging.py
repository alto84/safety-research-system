"""
Structured logging configuration for Safety Research System.

This module provides:
- JSON structured logging
- Context-aware logging with correlation IDs
- Performance tracking
- Error tracking with stack traces
- Audit logging for compliance
"""
import logging
import logging.config
import os
import sys
import time
import traceback
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import uuid4

import json

# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs JSON structured logs.
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add context information
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id

        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id

        # Add environment
        log_data["environment"] = os.getenv("APP_ENV", "development")

        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        # Add exception information if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        # Add performance tracking if present
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms

        if hasattr(record, "status_code"):
            log_data["status_code"] = record.status_code

        return json.dumps(log_data)


class PerformanceLogger:
    """Context manager for performance logging."""

    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        """
        Initialize performance logger.

        Args:
            logger: Logger instance
            operation: Operation name being tracked
            **kwargs: Additional context to log
        """
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None

    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        self.logger.info(
            f"Starting {self.operation}",
            extra={"event": "operation_start", "operation": self.operation, **self.context}
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End timing and log results."""
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            self.logger.error(
                f"Failed {self.operation}",
                extra={
                    "event": "operation_failed",
                    "operation": self.operation,
                    "duration_ms": duration_ms,
                    "error": str(exc_val),
                    **self.context
                },
                exc_info=True
            )
        else:
            self.logger.info(
                f"Completed {self.operation}",
                extra={
                    "event": "operation_completed",
                    "operation": self.operation,
                    "duration_ms": duration_ms,
                    **self.context
                }
            )


class AuditLogger:
    """
    Audit logger for compliance and security tracking.

    Logs all critical operations for audit purposes.
    """

    def __init__(self, name: str = "audit"):
        """Initialize audit logger."""
        self.logger = logging.getLogger(name)

    def log_case_created(self, case_id: str, user_id: Optional[str] = None, **kwargs):
        """Log case creation."""
        self.logger.info(
            "Case created",
            extra={
                "event": "case_created",
                "case_id": case_id,
                "user_id": user_id or user_id_var.get(),
                **kwargs
            }
        )

    def log_case_accessed(self, case_id: str, user_id: Optional[str] = None, **kwargs):
        """Log case access."""
        self.logger.info(
            "Case accessed",
            extra={
                "event": "case_accessed",
                "case_id": case_id,
                "user_id": user_id or user_id_var.get(),
                **kwargs
            }
        )

    def log_task_executed(self, task_id: str, task_type: str, **kwargs):
        """Log task execution."""
        self.logger.info(
            "Task executed",
            extra={
                "event": "task_executed",
                "task_id": task_id,
                "task_type": task_type,
                **kwargs
            }
        )

    def log_audit_performed(self, audit_id: str, status: str, **kwargs):
        """Log audit performed."""
        self.logger.info(
            "Audit performed",
            extra={
                "event": "audit_performed",
                "audit_id": audit_id,
                "status": status,
                **kwargs
            }
        )

    def log_security_event(self, event_type: str, severity: str, **kwargs):
        """Log security event."""
        log_level = logging.WARNING if severity.lower() in ["medium", "high"] else logging.ERROR
        self.logger.log(
            log_level,
            f"Security event: {event_type}",
            extra={
                "event": "security_event",
                "event_type": event_type,
                "severity": severity,
                **kwargs
            }
        )


def setup_logging(
    log_level: str = None,
    log_format: str = "json",
    log_file: str = None
):
    """
    Setup structured logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json or text)
        log_file: Path to log file (optional)
    """
    log_level = log_level or os.getenv("LOG_LEVEL", "INFO")
    log_format = log_format or os.getenv("LOG_FORMAT", "json")
    log_file = log_file or os.getenv("LOG_FILE", "logs/safety_research.log")

    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": StructuredFormatter,
            },
            "standard": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": log_format,
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": log_level,
                "formatter": "json",
                "filename": log_file,
                "maxBytes": 104857600,  # 100MB
                "backupCount": 10,
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": "logs/error.log",
                "maxBytes": 104857600,  # 100MB
                "backupCount": 20,
            },
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/audit.log",
                "maxBytes": 104857600,  # 100MB
                "backupCount": 50,  # Keep more audit logs
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file", "error_file"],
                "level": log_level,
            },
            "audit": {  # Audit logger
                "handlers": ["audit_file", "console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_request_context(request_id: str = None, user_id: str = None):
    """
    Set request context for logging.

    Args:
        request_id: Unique request identifier (auto-generated if not provided)
        user_id: User identifier (optional)
    """
    if request_id is None:
        request_id = str(uuid4())
    request_id_var.set(request_id)

    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context."""
    request_id_var.set(None)
    user_id_var.set(None)


def get_request_id() -> Optional[str]:
    """Get current request ID from context."""
    return request_id_var.get()


# Convenience function for performance logging
def track_performance(logger: logging.Logger, operation: str, **kwargs):
    """
    Decorator for tracking function performance.

    Args:
        logger: Logger instance
        operation: Operation name
        **kwargs: Additional context

    Example:
        @track_performance(logger, "database_query", query_type="select")
        def execute_query():
            ...
    """
    def decorator(func):
        def wrapper(*args, **func_kwargs):
            with PerformanceLogger(logger, operation, **kwargs):
                return func(*args, **func_kwargs)
        return wrapper
    return decorator


# Initialize audit logger
audit_logger = AuditLogger()


# Example usage
if __name__ == "__main__":
    # Setup logging
    setup_logging()

    # Get logger
    logger = get_logger(__name__)

    # Set request context
    set_request_context(request_id="req-123", user_id="user-456")

    # Basic logging
    logger.info("Application started")
    logger.warning("Warning message")

    # Performance logging
    with PerformanceLogger(logger, "database_query", query="SELECT * FROM users"):
        time.sleep(0.1)  # Simulate work

    # Audit logging
    audit_logger.log_case_created("CASE-001", user_id="user-456")
    audit_logger.log_security_event("unauthorized_access", "high", ip="192.168.1.1")

    # Error logging
    try:
        1 / 0
    except Exception as e:
        logger.error("Division by zero error", exc_info=True)

    # Clear context
    clear_request_context()
