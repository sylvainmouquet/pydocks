import logging
import os
import time
import uuid

import pytest
import pytest_asyncio
from pycontainers import docker as libdocker
from reattempt import reattempt

from pydocks.shared.infrastructure.plugin import (
    clean_containers,
    get_container_host_port,
    socket_test_connection,
    wait_and_run_container,
)

logger = logging.getLogger(__name__)


# https://hub.docker.com/_/redis/tags
TEST_REDIS_DOCKER_IMAGE: str = "docker.io/redis:7.4.1"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def redis_clean_all_containers(docker):
    container_name: str = "test-redis"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def redis_container(docker: libdocker):  # type: ignore
    container_name = f"test-redis-{uuid.uuid4()}"

    async for container in setup_redis_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def redis_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-redis-session")

    container_name = f"test-redis-session-{uuid.uuid4()}"

    async for container in setup_redis_container(docker, container_name):
        yield container


async def setup_redis_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting Redis container setup",
        extra={"container_name": container_name},
    )
    try:
        redis_image = (
            TEST_REDIS_DOCKER_IMAGE
            if "TEST_REDIS_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_REDIS_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": redis_image},
        )

        def run_container(container_name: str):
            return docker.run(
                image=redis_image,
                name=container_name,
                detach=True,
                expose=[6379],
                publish_all=True,
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

        container.host = "127.0.0.1"
        container.port = get_container_host_port(docker, container, 6379)

        await redis_test_connection(container.host, container.port)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "Redis container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "Redis container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def redis_test_connection(host: str, port: int):
    await socket_test_connection(host, port)
