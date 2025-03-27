import pytest
import os


import pytest_asyncio
from python_on_whales import docker as libdocker
from reattempt import reattempt
import logging
import uuid

from pydocks.plugin import (
    clean_containers,
    wait_and_run_container,
    file_exists,
)


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/r/scalr/opentofu/tags
TEST_OPENTOFU_DOCKER_IMAGE: str = "docker.io/scalr/opentofu:1.9.0"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def opentofu_clean_all_containers(docker):
    container_name: str = "test-opentofu"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def opentofu_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-opentofu-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_opentofu_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def opentofu_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-opentofu-session")

    container_name = f"test-opentofu-session-{uuid.uuid4()}"

    async for container in setup_opentofu_container(docker, container_name):
        yield container


async def setup_opentofu_container(docker: libdocker, container_name):  # type: ignore
    opentofu_image = (
        TEST_OPENTOFU_DOCKER_IMAGE
        if "TEST_OPENTOFU_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_OPENTOFU_DOCKER_IMAGE"]
    )
    logger.debug(f"pull docker image : {opentofu_image}")

    def run_container(container_name: str):
        return docker.run(
            image=opentofu_image,
            name=container_name,
            detach=True,
            command=["-c", "sleep 2m"],
            entrypoint="/bin/sh",
            volumes=[
                (
                    os.path.join(
                        os.path.dirname(__file__),
                        "opentofu_resources",
                    ),
                    "/terraform",
                ),
            ],
            workdir="/terraform",
        )

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"found existing container: {container_name}")
    else:
        logger.debug(f"no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    await opentofu_test_connection(container)

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def opentofu_test_connection(container):
    # Check if OpenTofu is available
    version = container.execute(["tofu", "version"])
    if not version or "OpenTofu" not in version:
        raise Exception("OpenTofu is not available in the container")

    # Create a ready file to indicate the container is ready
    container.execute(["touch", "/terraform/ready"])
    await file_exists(container, "/terraform/ready")