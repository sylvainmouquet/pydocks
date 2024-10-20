from http import HTTPStatus

import aiohttp
import pytest
import os

from aiohttp import ClientTimeout
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(vault_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_vault_default_version(vault_container):
    # Get environment variables from the Vault container
    container_env_dict = dict(env.split("=") for env in vault_container.config.env)

    assert container_env_dict["NAME"] == "vault"
    assert container_env_dict["VAULT_TOKEN"] == "00000000-0000-0000-0000-000000000000"

    version_output = vault_container.execute(["vault", "version"])
    assert version_output.startswith(
        "Vault v1.18"
    ), f"Unexpected version output: {version_output}"


@pytest.fixture
def custom_vault_version():
    os.environ["TEST_VAULT_DOCKER_IMAGE"] = "docker.io/hashicorp/vault:1.17"
    yield
    del os.environ["TEST_VAULT_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_vault_custom_version(custom_vault_version, vault_container):
    # Get environment variables from the Vault container
    container_env_dict = dict(env.split("=") for env in vault_container.config.env)

    assert container_env_dict["NAME"] == "vault"
    assert container_env_dict["VAULT_TOKEN"] == "00000000-0000-0000-0000-000000000000"

    version_output = vault_container.execute(["vault", "version"])
    assert version_output.startswith(
        "Vault v1.17"
    ), f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_vault_execute_command(vault_container):
    # Connect to the Vault

    async with aiohttp.ClientSession(timeout=ClientTimeout(60)) as session:
        data = {
            "role_id": "unknown",
            "secret_id": "unknown",
        }

        async with session.post(
            "http://host.docker.internal:8200/v1/auth/approle/login", json=data
        ) as response:
            assert response.status == HTTPStatus.BAD_REQUEST

        # Read the vault credentials from the file
        credentials = vault_container.execute(["cat", "/vault-credentials.env"])
        credentials_dict = dict(line.split("=") for line in credentials.splitlines())
        role_id = credentials_dict.get("ROLE_ID")
        secret_id = credentials_dict.get("SECRET_ID")

        assert role_id is not None, "ROLE_ID not found in /vault-credentials.env"
        assert secret_id is not None, "SECRET_ID not found in /vault-credentials.env"

        data = {
            "role_id": role_id,
            "secret_id": secret_id,
        }
        async with session.post(
            "http://host.docker.internal:8200/v1/auth/approle/login", json=data
        ) as response:
            assert response.status == HTTPStatus.OK
            response_data = await response.json()
            assert response_data["auth"]["client_token"] is not None
