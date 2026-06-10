import logging

import pytest

from pydocks.shared.infrastructure.logging import configure_package_logging

logger = logging.getLogger(__name__)


class RetryException(Exception): ...


MAX_ATTEMPTS = 5
MIN_TIME = 0.1
MAX_TIME = 0.2

SHOW_EXCEPTIONS = False

pytest_plugins = ["pytester"]


@pytest.fixture(scope="session", autouse=True)
def configure_test_logging():
    configure_package_logging()


@pytest.fixture
def disable_logging_exception(mocker):
    if not SHOW_EXCEPTIONS:
        mocker.patch("logging.exception", lambda *args, **kwargs: None)
