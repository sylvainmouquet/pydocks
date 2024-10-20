import pytest
import os
import redis.asyncio as redis
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(redis_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_redis_default_version(redis_container):
    container_env_dict = dict(env.split("=") for env in redis_container.config.env)

    assert container_env_dict["REDIS_VERSION"] == "7.4.1"


@pytest.fixture
def custom_redis_version():
    os.environ["TEST_REDIS_DOCKER_IMAGE"] = "docker.io/redis:7.4.0"
    yield
    del os.environ["TEST_REDIS_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_redis_custom_version(custom_redis_version, redis_container):
    container_env_dict = dict(env.split("=") for env in redis_container.config.env)

    assert container_env_dict["REDIS_VERSION"] == "7.4.0"


@pytest.mark.asyncio
async def test_redis_execute_command(redis_container):
    # Execute Redis CLI command
    result = redis_container.execute(["redis-cli", "PING"])
    assert result.strip() == "PONG"

    # Set a key-value pair
    set_result = redis_container.execute(["redis-cli", "SET", "test_key", "test_value"])
    assert set_result.strip() == "OK"

    # Get the value
    get_result = redis_container.execute(["redis-cli", "GET", "test_key"])
    assert get_result.strip() == "test_value"

    # Delete the key
    del_result = redis_container.execute(["redis-cli", "DEL", "test_key"])
    assert del_result.strip() == "1"

    # Verify key is deleted
    get_deleted = redis_container.execute(["redis-cli", "GET", "test_key"])
    assert get_deleted.strip() == ""

    async with await redis.from_url(
        "redis://localhost:6379", encoding="utf8"
    ) as rredis:
        # Flush all existing data
        await rredis.flushall()

        # Set a key-value pair
        await rredis.set("test_key", "test_value")

        # Get the value
        value = await rredis.get("test_key")
        assert value == b"test_value"

        # Delete the key
        deleted = await rredis.delete("test_key")
        assert deleted == 1

        # Verify key is deleted
        deleted_value = await rredis.get("test_key")
        assert deleted_value is None
