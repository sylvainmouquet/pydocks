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
    get_container_host_port,
    socket_test_connection,
    wait_and_run_container,
)

logger = logging.getLogger(__name__)


# https://hub.docker.com/r/hashicorp/vault/tags
TEST_VAULT_DOCKER_IMAGE: str = "docker.io/hashicorp/vault:1.18"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def vault_clean_all_containers(docker):
    container_name: str = "test-vault"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def vault_container(docker: libdocker):  # type: ignore
    container_name = f"test-vault-{uuid.uuid4()}"

    async for container in setup_vault_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def vault_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-vault-session")

    container_name = f"test-vault-session-{uuid.uuid4()}"

    async for container in setup_vault_container(docker, container_name):
        yield container


async def setup_vault_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting Vault container setup",
        extra={"container_name": container_name},
    )
    try:
        vault_image = (
            TEST_VAULT_DOCKER_IMAGE
            if "TEST_VAULT_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_VAULT_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": vault_image},
        )

        def run_container(container_name: str):
            return docker.run(
                image=vault_image,
                name=container_name,
                detach=True,
                envs={
                    "VAULT_DEV_ROOT_TOKEN_ID": "00000000-0000-0000-0000-000000000000",
                    "VAULT_TOKEN": "00000000-0000-0000-0000-000000000000",
                    "VAULT_ADDR": "http://127.0.0.1:8200",
                },
                command=["/test-vault-init.sh"],
                expose=[8200],
                publish_all=True,
                volumes=[
                    (
                        os.path.join(
                            os.path.dirname(__file__),
                            "resources",
                            "test-vault-init.sh",
                        ),
                        "/test-vault-init.sh",
                    ),
                    (
                        os.path.join(
                            os.path.dirname(__file__), "resources", "vault-test.json"
                        ),
                        "/vault-test.json",
                    ),
                ],
            )

        containers = docker.ps(all=True, filter={"name": f"^{container_name}$"})
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
        container.port = get_container_host_port(docker, container, 8200)

        await vault_test_connection(container)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "Vault container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "Vault container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def vault_test_connection(container):
    await socket_test_connection(container.host, container.port)
    await file_exists(container, "/started")
