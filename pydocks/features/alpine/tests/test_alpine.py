import logging

import pytest
import pytest_asyncio

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(alpine_clean_all_containers):
    logger.info(
        "Beginning container cleanup session",
        extra={"feature": "alpine"},
    )


@pytest.mark.asyncio
async def test_alpine_default_version(alpine_container):
    version_output = alpine_container.execute(["cat", "/etc/alpine-release"])
    assert "3.19" in version_output, f"Unexpected version output: {version_output}"


@pytest.fixture
def custom_alpine_version():
    import os

    os.environ["TEST_ALPINE_DOCKER_IMAGE"] = "docker.io/alpine:3.18"
    yield
    del os.environ["TEST_ALPINE_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_alpine_custom_version(custom_alpine_version, alpine_container):
    version_output = alpine_container.execute(["cat", "/etc/alpine-release"])
    assert "3.18" in version_output, f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_alpine_execute_command(alpine_container):
    result = alpine_container.execute(["echo", "Hello World"])
    assert result.strip() == "Hello World"


@pytest.fixture
def custom_alpine_sleep_time():
    import os

    os.environ["ALPINE_SLEEP_TIME_IN_SECONDS"] = "10"
    yield
    del os.environ["ALPINE_SLEEP_TIME_IN_SECONDS"]


@pytest.mark.asyncio
async def test_alpine_execute_command_with_sleep_10(
    custom_alpine_sleep_time, alpine_container
):
    result = alpine_container.execute(["echo", "Hello World"])
    assert result.strip() == "Hello World"
