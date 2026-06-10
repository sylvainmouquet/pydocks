import logging
import os

import pytest
import pytest_asyncio
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(redis_clean_all_containers):
    logger.info(
        "Beginning container cleanup session",
        extra={"feature": "redis"},
    )


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
    result = redis_container.execute(["redis-cli", "PING"])
    assert result.strip() == "PONG"

    set_result = redis_container.execute(["redis-cli", "SET", "test_key", "test_value"])
    assert set_result.strip() == "OK"

    get_result = redis_container.execute(["redis-cli", "GET", "test_key"])
    assert get_result.strip() == "test_value"

    del_result = redis_container.execute(["redis-cli", "DEL", "test_key"])
    assert del_result.strip() == "1"

    get_deleted = redis_container.execute(["redis-cli", "GET", "test_key"])
    assert get_deleted.strip() == ""

    async with await redis.from_url(
        f"redis://{redis_container.host}:{redis_container.port}", encoding="utf8"
    ) as rredis:
        await rredis.flushall()
        await rredis.set("test_key", "test_value")
        value = await rredis.get("test_key")
        assert value == b"test_value"
        deleted = await rredis.delete("test_key")
        assert deleted == 1
        deleted_value = await rredis.get("test_key")
        assert deleted_value is None
