import pytest
import os
import redis.asyncio as redis
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(valkey_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_valkey_default_version(valkey_container):
    container_env_dict = dict(env.split("=") for env in valkey_container.config.env)

    assert "VALKEY_VERSION" in container_env_dict, "VALKEY_VERSION environment variable not found"
    assert container_env_dict["VALKEY_VERSION"] == "8.1.1"


@pytest.fixture
def custom_valkey_version():
    os.environ["TEST_VALKEY_DOCKER_IMAGE"] = "docker.io/valkey/valkey:7.2.9"
    yield
    del os.environ["TEST_VALKEY_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_valkey_custom_version(custom_valkey_version, valkey_container):
    container_env_dict = dict(env.split("=") for env in valkey_container.config.env)

    assert "VALKEY_VERSION" in container_env_dict, "VALKEY_VERSION environment variable not found"
    assert container_env_dict["VALKEY_VERSION"] == "7.2.9"


@pytest.mark.asyncio
async def test_valkey_execute_command(valkey_container):
    # Execute Valkey CLI command
    result = valkey_container.execute(["valkey-cli", "PING"])
    assert result.strip() == "PONG"

    # Set a key-value pair
    set_result = valkey_container.execute(["valkey-cli", "SET", "test_key", "test_value"])
    assert set_result.strip() == "OK"

    # Get the value
    get_result = valkey_container.execute(["valkey-cli", "GET", "test_key"])
    assert get_result.strip() == "test_value"

    # Delete the key
    del_result = valkey_container.execute(["valkey-cli", "DEL", "test_key"])
    assert del_result.strip() == "1"

    # Verify key is deleted
    get_deleted = valkey_container.execute(["valkey-cli", "GET", "test_key"])
    assert get_deleted.strip() == ""

    async with await redis.from_url(
        "redis://localhost:6380", encoding="utf8"
    ) as vkey:
        # Flush all existing data
        await vkey.flushall()

        # Set a key-value pair
        await vkey.set("test_key", "test_value")

        # Get the value
        value = await vkey.get("test_key")
        assert value == b"test_value"

        # Delete the key
        deleted = await vkey.delete("test_key")
        assert deleted == 1

        # Verify key is deleted
        deleted_value = await vkey.get("test_key")
        assert deleted_value is None