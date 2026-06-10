import logging

import pytest

from pydocks.shared.infrastructure import logging as logging_module
from pydocks.shared.infrastructure.logging import (
    configure_package_logging,
    log_operation,
)


def test_configure_package_logging_is_idempotent():
    logging_module._CONFIGURED = False
    pydocks_logger = logging.getLogger("pydocks")
    initial_handler_count = len(pydocks_logger.handlers)

    configure_package_logging()
    configure_package_logging()

    assert logging_module._CONFIGURED is True
    assert len(pydocks_logger.handlers) == initial_handler_count + 1


def test_log_operation_success(caplog):
    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.logging.success")

    with log_operation(test_logger, "test operation", resource_id="abc"):
        pass

    assert "Starting test operation" in caplog.text
    assert "test operation completed" in caplog.text


def test_log_operation_failure(caplog):
    caplog.set_level(logging.INFO)
    test_logger = logging.getLogger("test.logging.failure")

    with pytest.raises(RuntimeError, match="boom"):
        with log_operation(test_logger, "failing operation", resource_id="xyz"):
            raise RuntimeError("boom")

    assert "Starting failing operation" in caplog.text
    assert "failing operation failed" in caplog.text
