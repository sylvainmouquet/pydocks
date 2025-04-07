import pytest
import os
from loguru import logger
import pytest_asyncio
import logging

# For console output
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# Add this handler to your logger
logger = logging.getLogger("pydocks")
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(alpine_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_alpine_default_version(alpine_container):
    version_output = alpine_container.execute(["cat", "/etc/alpine-release"])
    assert (
        "3.19" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.fixture
def custom_alpine_version():
    os.environ["TEST_ALPINE_DOCKER_IMAGE"] = "docker.io/alpine:3.18"
    yield
    del os.environ["TEST_ALPINE_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_alpine_custom_version(custom_alpine_version, alpine_container):
    version_output = alpine_container.execute(["cat", "/etc/alpine-release"])
    assert (
        "3.18" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_alpine_execute_command(alpine_container):
    # Execute a basic command
    result = alpine_container.execute(["echo", "Hello World"])
    assert result.strip() == "Hello World"

@pytest.fixture
def custom_alpine_sleep_time():
    os.environ["ALPINE_SLEEP_TIME_IN_SECONDS"] = "10"
    yield
    del os.environ["ALPINE_SLEEP_TIME_IN_SECONDS"]

@pytest.mark.asyncio
async def test_alpine_execute_command_with_sleep_10(custom_alpine_sleep_time, alpine_container):
    # Execute a basic command with custom sleep time
    result = alpine_container.execute(["echo", "Hello World"])
    assert result.strip() == "Hello World"