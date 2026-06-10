import logging
import os

import pytest
import pytest_asyncio
import redis.asyncio as redis

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(valkey_clean_all_containers):
    logger.info(
        "Beginning container cleanup session",
        extra={"feature": "valkey"},
    )


@pytest.mark.asyncio
async def test_valkey_default_version(valkey_container):
    version_output = valkey_container.execute(["valkey-server", "--version"])
    assert "v=8.1.1" in version_output


@pytest.fixture
def custom_valkey_version():
    os.environ["TEST_VALKEY_DOCKER_IMAGE"] = "docker.io/valkey/valkey:7.2.9"
    yield
    del os.environ["TEST_VALKEY_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_valkey_custom_version(custom_valkey_version, valkey_container):
    version_output = valkey_container.execute(["valkey-server", "--version"])
    assert "v=7.2.9" in version_output


@pytest.mark.asyncio
async def test_valkey_execute_command(valkey_container):
    result = valkey_container.execute(["valkey-cli", "PING"])
    assert result.strip() == "PONG"

    set_result = valkey_container.execute(
        ["valkey-cli", "SET", "test_key", "test_value"]
    )
    assert set_result.strip() == "OK"

    get_result = valkey_container.execute(["valkey-cli", "GET", "test_key"])
    assert get_result.strip() == "test_value"

    del_result = valkey_container.execute(["valkey-cli", "DEL", "test_key"])
    assert del_result.strip() == "1"

    get_deleted = valkey_container.execute(["valkey-cli", "GET", "test_key"])
    assert get_deleted.strip() == ""

    async with await redis.from_url(
        f"redis://{valkey_container.host}:{valkey_container.port}", encoding="utf8"
    ) as vkey:
        await vkey.flushall()
        await vkey.set("test_key", "test_value")
        value = await vkey.get("test_key")
        assert value == b"test_value"
        deleted = await vkey.delete("test_key")
        assert deleted == 1
        deleted_value = await vkey.get("test_key")
        assert deleted_value is None
