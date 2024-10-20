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
    file_exists,
)


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/r/hashicorp/vault/tags
TEST_VAULT_DOCKER_IMAGE: str = "docker.io/hashicorp/vault:1.18"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def vault_clean_all_containers(docker):
    container_name: str = "test-vault"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def vault_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-vault-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_vault_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def vault_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-vault-session")

    container_name = f"test-vault-session-{uuid.uuid4()}"

    async for container in setup_vault_container(docker, container_name):
        yield container


async def setup_vault_container(docker: libdocker, container_name):  # type: ignore
    vault_image = (
        TEST_VAULT_DOCKER_IMAGE
        if "TEST_VAULT_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_VAULT_DOCKER_IMAGE"]
    )
    logger.debug(f"pull docker image : {vault_image}")

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
            publish=[(8200, 8200)],
            expose=[8200],
            volumes=[
                (
                    os.path.join(
                        os.path.dirname(__file__),
                        "vault_resources",
                        "test-vault-init.sh",
                    ),
                    "/test-vault-init.sh",
                ),
                (
                    os.path.join(
                        os.path.dirname(__file__), "vault_resources", "vault-test.json"
                    ),
                    "/vault-test.json",
                ),
            ],
        )

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"found existing container: {container_name}")
    else:
        logger.debug(f"no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    await vault_test_connection(container)

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def vault_test_connection(container):
    await socket_test_connection("host.docker.internal", 8200)
    await file_exists(container, "/started")
