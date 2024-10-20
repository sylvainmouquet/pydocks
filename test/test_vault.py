import pytest
import asyncpg
import os
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
    assert version_output.startswith("Vault v1.18"), f"Unexpected version output: {version_output}"

@pytest.fixture
def custom_vault_version():
    os.environ["TEST_VAULT_DOCKER_IMAGE"] = "docker.io/hashicorp/vault:1.17"
    yield
    del os.environ["TEST_VAULT_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_vault_custom_version(
    custom_vault_version, vault_container
):
    # Get environment variables from the Vault container
    container_env_dict = dict(env.split("=") for env in vault_container.config.env)

    assert container_env_dict["NAME"] == "vault"
    assert container_env_dict["VAULT_TOKEN"] == "00000000-0000-0000-0000-000000000000"

    version_output = vault_container.execute(["vault", "version"])
    assert version_output.startswith("Vault v1.17"), f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_vault_execute_command(vault_container):
    # Connect to the Vault
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        # Execute a simple command
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "Failed to execute command on PostgreSQL"
    finally:
        # Close the connection
        await conn.close()

