import logging
import os
import time
import uuid

import pytest
import pytest_asyncio
from pycontainers import docker as libdocker

from pydocks.shared.infrastructure.plugin import (
    clean_containers,
    wait_and_run_container,
)

logger = logging.getLogger(__name__)


# https://hub.docker.com/_/ubuntu/tags
TEST_UBUNTU_DOCKER_IMAGE: str = "docker.io/ubuntu:24.04"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ubuntu_clean_all_containers(docker):
    container_name: str = "test-ubuntu"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def ubuntu_container(docker: libdocker):  # type: ignore
    container_name = f"test-ubuntu-{uuid.uuid4()}"

    async for container in setup_ubuntu_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def ubuntu_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-ubuntu-session")

    container_name = f"test-ubuntu-session-{uuid.uuid4()}"

    async for container in setup_ubuntu_container(docker, container_name):
        yield container


async def setup_ubuntu_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting Ubuntu container setup",
        extra={"container_name": container_name},
    )
    try:
        ubuntu_image = (
            TEST_UBUNTU_DOCKER_IMAGE
            if "TEST_UBUNTU_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_UBUNTU_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": ubuntu_image},
        )

        def run_container(container_name: str):
            ubuntu_sleep_time_in_seconds = int(
                os.getenv("UBUNTU_SLEEP_TIME_IN_SECONDS", 60)
            )
            command = f"sleep {ubuntu_sleep_time_in_seconds}"
            logger.debug(
                "Running container command",
                extra={"container_name": container_name, "command": command},
            )
            return docker.run(
                image=ubuntu_image,
                name=container_name,
                detach=True,
                entrypoint="/bin/sh",
                command=["-c", command],
            )

        containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
        if containers and len(containers) > 0:
            container = containers[0]  # type: ignore
            logger.debug(
                "Found existing container",
                extra={"container_name": container_name},
            )
        else:
            logger.debug(
                "Creating new container",
                extra={"container_name": container_name},
            )
            container = run_container(container_name)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "Ubuntu container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "Ubuntu container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise
