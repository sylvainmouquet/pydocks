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


# https://hub.docker.com/_/ubuntu/tags
TEST_UBUNTU_DOCKER_IMAGE: str = "docker.io/ubuntu:24.04"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ubuntu_clean_all_containers(docker):
    container_name: str = "test-ubuntu"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def ubuntu_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-ubuntu-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_ubuntu_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ubuntu_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-ubuntu-session")

    container_name = f"test-ubuntu-session-{uuid.uuid4()}"

    async for container in setup_ubuntu_container(docker, container_name):
        yield container


async def setup_ubuntu_container(docker: libdocker, container_name):  # type: ignore
    ubuntu_image = (
        TEST_UBUNTU_DOCKER_IMAGE
        if "TEST_UBUNTU_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_UBUNTU_DOCKER_IMAGE"]
    )
    logger.debug(f"pull docker image : {ubuntu_image}")

    def run_container(container_name: str):
        return docker.run(
            image=ubuntu_image,
            name=container_name,
            detach=True,
            entrypoint="/bin/sh",
            command=["-c", "sleep 60"],
        )

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"found existing container: {container_name}")
    else:
        logger.debug(f"no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance
