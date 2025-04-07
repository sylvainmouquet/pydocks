import pytest
import os


import pytest_asyncio
from python_on_whales import docker as libdocker
import logging
import uuid

from pydocks.plugin import (
    clean_containers,
    wait_and_run_container,
)


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/_/alpine/tags
TEST_ALPINE_DOCKER_IMAGE: str = "docker.io/alpine:3.19"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def alpine_clean_all_containers(docker):
    container_name: str = "test-alpine"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def alpine_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-alpine-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_alpine_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def alpine_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-alpine-session")

    container_name = f"test-alpine-session-{uuid.uuid4()}"

    async for container in setup_alpine_container(docker, container_name):
        yield container


async def setup_alpine_container(docker: libdocker, container_name):  # type: ignore
    alpine_image = (
        TEST_ALPINE_DOCKER_IMAGE
        if "TEST_ALPINE_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_ALPINE_DOCKER_IMAGE"]
    )
    logger.debug(f"[ALPINE] pull docker image : {alpine_image}")

    def run_container(container_name: str):
        ALPINE_SLEEP_TIME_IN_SECONDS = int(os.getenv("ALPINE_SLEEP_TIME_IN_SECONDS", 60))
        command = f"sleep {ALPINE_SLEEP_TIME_IN_SECONDS}"
        logger.debug(f"[ALPINE] run container with {command}")
        return docker.run(
            image=alpine_image,
            name=container_name,
            detach=True,
            entrypoint="/bin/sh",
            command=["-c", command],
        )

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"[ALPINE] found existing container: {container_name}")
    else:
        logger.debug(f"[ALPINE] no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance