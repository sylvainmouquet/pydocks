import pytest
import os


import pytest_asyncio
from python_on_whales import docker as libdocker
from reattempt import reattempt
import logging
import uuid

from pydocks.plugin import (
    clean_containers,
    socket_test_connection,
    wait_and_run_container,
)


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/r/valkey/valkey/tags
TEST_VALKEY_DOCKER_IMAGE: str = "docker.io/valkey/valkey:8.1.1"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def valkey_clean_all_containers(docker):
    container_name: str = "test-valkey"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def valkey_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-valkey-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_valkey_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def valkey_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-valkey-session")

    container_name = f"test-valkey-session-{uuid.uuid4()}"

    async for container in setup_valkey_container(docker, container_name):
        yield container


async def setup_valkey_container(docker: libdocker, container_name):  # type: ignore
    valkey_image = (
        TEST_VALKEY_DOCKER_IMAGE
        if "TEST_VALKEY_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_VALKEY_DOCKER_IMAGE"]
    )
    logger.debug(f"pull docker image : {valkey_image}")

    def run_container(container_name: str):
        return docker.run(
            image=valkey_image,
            name=container_name,
            detach=True,
            publish=[(6380, 6379)],
            expose=[6380],
        )

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"found existing container: {container_name}")
    else:
        logger.debug(f"no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    await valkey_test_connection()

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def valkey_test_connection():
    await socket_test_connection("127.0.0.1", 6380)