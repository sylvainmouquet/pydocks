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
    file_exists,
    wait_and_run_container,
)

logger = logging.getLogger(__name__)


TEST_OPENTOFU_DOCKER_IMAGE: str = "ghcr.io/opentofu/opentofu:1.9"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def opentofu_clean_all_containers(docker):
    container_name: str = "test-opentofu"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def opentofu_container(docker: libdocker):  # type: ignore
    container_name = f"test-opentofu-{uuid.uuid4()}"

    async for container in setup_opentofu_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def opentofu_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-opentofu-session")

    container_name = f"test-opentofu-session-{uuid.uuid4()}"

    async for container in setup_opentofu_container(docker, container_name):
        yield container


async def setup_opentofu_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting OpenTofu container setup",
        extra={"container_name": container_name},
    )
    try:
        opentofu_image = (
            TEST_OPENTOFU_DOCKER_IMAGE
            if "TEST_OPENTOFU_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_OPENTOFU_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": opentofu_image},
        )

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
                            "resources",
                        ),
                        "/terraform",
                    ),
                ],
                workdir="/terraform",
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

        await opentofu_test_connection(container)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "OpenTofu container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "OpenTofu container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def opentofu_test_connection(container):
    version = container.execute(["tofu", "version"])
    if not version or "OpenTofu" not in version:
        logger.error(
            "OpenTofu is not available in the container",
            extra={"operation": "tofu_version_check"},
        )
        raise Exception("OpenTofu is not available in the container")

    container.execute(["touch", "/terraform/ready"])
    await file_exists(container, "/terraform/ready")
