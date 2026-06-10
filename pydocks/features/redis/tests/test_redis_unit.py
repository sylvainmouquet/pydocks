from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydocks.features.redis.redis import (
    redis_clean_all_containers,
    redis_container,
    redis_container_session,
    redis_test_connection,
    setup_redis_container,
)


class FakeContainer:
    Status = "running"
    Id = "abc123"


async def _fake_wait_and_run(_docker, container, _name):
    yield container


@pytest.mark.asyncio
async def test_setup_redis_container_reuses_existing_container():
    docker = MagicMock()
    existing = FakeContainer()
    docker.ps.return_value = [existing]

    with (
        patch(
            "pydocks.features.redis.redis.get_container_host_port",
            return_value=6379,
        ),
        patch(
            "pydocks.features.redis.redis.redis_test_connection",
            new=AsyncMock(),
        ),
        patch(
            "pydocks.features.redis.redis.wait_and_run_container",
            side_effect=_fake_wait_and_run,
        ),
    ):
        async for container in setup_redis_container(docker, "test-redis-123"):
            assert container is existing

    docker.run.assert_not_called()


@pytest.mark.asyncio
async def test_setup_redis_container_raises_on_failure():
    docker = MagicMock()
    docker.ps.return_value = []
    docker.run.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        async for _ in setup_redis_container(docker, "test-redis-123"):
            pass


@pytest.mark.asyncio
async def test_redis_container_session_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.redis.redis.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        with patch(
            "pydocks.features.redis.redis.setup_redis_container",
            side_effect=fake_setup,
        ):
            async for container in redis_container_session.__wrapped__(docker):
                assert container is existing

    clean_mock.assert_awaited_once_with(docker, "test-redis-session")


@pytest.mark.asyncio
async def test_redis_clean_all_containers_fixture():
    docker = MagicMock()

    with patch(
        "pydocks.features.redis.redis.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        fixture_gen = redis_clean_all_containers.__wrapped__(docker)
        await anext(fixture_gen)
        with pytest.raises(StopAsyncIteration):
            await anext(fixture_gen)

    assert clean_mock.await_count == 2
    clean_mock.assert_awaited_with(docker, "test-redis")


@pytest.mark.asyncio
async def test_redis_container_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.redis.redis.setup_redis_container",
        side_effect=fake_setup,
    ):
        async for container in redis_container.__wrapped__(docker):
            assert container is existing


@pytest.mark.asyncio
async def test_redis_test_connection():
    with patch(
        "pydocks.features.redis.redis.socket_test_connection",
        new=AsyncMock(),
    ) as socket_mock:
        await redis_test_connection("127.0.0.1", 6379)

    socket_mock.assert_awaited_once_with("127.0.0.1", 6379)
