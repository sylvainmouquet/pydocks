from typing import AsyncGenerator

import pytest
from reattempt import reattempt
from test.conftest import MAX_ATTEMPTS, MIN_TIME, MAX_TIME, RetryException


@pytest.mark.asyncio
async def test_docker(disable_logging_exception):
    ...