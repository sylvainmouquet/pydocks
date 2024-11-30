import pytest
import os
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(ubuntu_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_ubuntu_default_version(ubuntu_container):
    version_output = ubuntu_container.execute(["cat", "/etc/lsb-release"])
    assert (
        "DISTRIB_RELEASE=24.04" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.fixture
def custom_ubuntu_version():
    os.environ["TEST_UBUNTU_DOCKER_IMAGE"] = "docker.io/ubuntu:22.04"
    yield
    del os.environ["TEST_UBUNTU_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_ubuntu_custom_version(custom_ubuntu_version, ubuntu_container):
    version_output = ubuntu_container.execute(["cat", "/etc/lsb-release"])
    assert (
        "DISTRIB_RELEASE=22.04" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_ubuntu_execute_command(ubuntu_container):
    # Execute Redis CLI command
    result = ubuntu_container.execute(["echo", "Hello World"])
    assert result.strip() == "Hello World"
