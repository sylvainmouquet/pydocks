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


# https://hub.docker.com/_/alpine/tags
TEST_ALPINE_DOCKER_IMAGE: str = "docker.io/alpine:3.19"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def alpine_clean_all_containers(docker):
    container_name: str = "test-alpine"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def alpine_container(docker: libdocker):  # type: ignore
    container_name = f"test-alpine-{uuid.uuid4()}"

    async for container in setup_alpine_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def alpine_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-alpine-session")

    container_name = f"test-alpine-session-{uuid.uuid4()}"

    async for container in setup_alpine_container(docker, container_name):
        yield container


async def setup_alpine_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting Alpine container setup",
        extra={"container_name": container_name},
    )
    try:
        alpine_image = (
            TEST_ALPINE_DOCKER_IMAGE
            if "TEST_ALPINE_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_ALPINE_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": alpine_image},
        )

        def run_container(container_name: str):
            alpine_sleep_time_in_seconds = int(
                os.getenv("ALPINE_SLEEP_TIME_IN_SECONDS", 60)
            )
            command = f"sleep {alpine_sleep_time_in_seconds}"
            logger.debug(
                "Running container command",
                extra={"container_name": container_name, "command": command},
            )
            return docker.run(
                image=alpine_image,
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
            "Alpine container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "Alpine container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise
