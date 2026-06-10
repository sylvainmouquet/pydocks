"""Shared logging configuration for pydocks."""

import logging
import time
from contextlib import contextmanager
from typing import Any, Iterator

_CONFIGURED = False


def configure_package_logging() -> None:
    """Ensure pydocks loggers do not emit 'No handler found' warnings."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    logging.getLogger("pydocks").addHandler(logging.NullHandler())
    _CONFIGURED = True


@contextmanager
def log_operation(
    logger: logging.Logger,
    operation: str,
    **context: Any,
) -> Iterator[None]:
    start = time.perf_counter()
    logger.info(
        f"Starting {operation}",
        extra={"operation": operation, **context},
    )
    try:
        yield
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            f"{operation} completed",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                **context,
            },
        )
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            f"{operation} failed",
            extra={
                "operation": operation,
                "duration_ms": duration_ms,
                **context,
            },
        )
        raise
