from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydocks.features.postgresql.postgresql import (
    postgresql_clean_all_containers,
    postgresql_container,
    postgresql_container_session,
    postgresql_test_connection,
    setup_postgresql_container,
)


class FakeContainer:
    Status = "running"
    Id = "abc123"


async def _fake_wait_and_run(_docker, container, _name):
    yield container


@pytest.mark.asyncio
async def test_setup_postgresql_container_creates_new_container():
    docker = MagicMock()
    new_container = FakeContainer()
    docker.ps.return_value = []
    docker.run.return_value = new_container

    with (
        patch(
            "pydocks.features.postgresql.postgresql.get_container_host_port",
            return_value=5432,
        ),
        patch(
            "pydocks.features.postgresql.postgresql.postgresql_test_connection",
            new=AsyncMock(),
        ),
        patch(
            "pydocks.features.postgresql.postgresql.wait_and_run_container",
            side_effect=_fake_wait_and_run,
        ),
    ):
        async for container in setup_postgresql_container(docker, "test-postgresql-123"):
            assert container is new_container

    docker.run.assert_called_once()


@pytest.mark.asyncio
async def test_setup_postgresql_container_raises_on_failure():
    docker = MagicMock()
    docker.ps.return_value = []
    docker.run.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        async for _ in setup_postgresql_container(docker, "test-postgresql-123"):
            pass


@pytest.mark.asyncio
async def test_setup_postgresql_container_reuses_existing_container():
    docker = MagicMock()
    existing = FakeContainer()
    docker.ps.return_value = [existing]

    with (
        patch(
            "pydocks.features.postgresql.postgresql.get_container_host_port",
            return_value=5432,
        ),
        patch(
            "pydocks.features.postgresql.postgresql.postgresql_test_connection",
            new=AsyncMock(),
        ),
        patch(
            "pydocks.features.postgresql.postgresql.wait_and_run_container",
            side_effect=_fake_wait_and_run,
        ),
    ):
        async for container in setup_postgresql_container(docker, "test-postgresql-123"):
            assert container is existing

    docker.run.assert_not_called()


@pytest.mark.asyncio
async def test_postgresql_clean_all_containers_fixture():
    docker = MagicMock()

    with patch(
        "pydocks.features.postgresql.postgresql.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        fixture_gen = postgresql_clean_all_containers.__wrapped__(docker)
        await anext(fixture_gen)
        with pytest.raises(StopAsyncIteration):
            await anext(fixture_gen)

    assert clean_mock.await_count == 2
    clean_mock.assert_awaited_with(docker, "test-postgresql")


@pytest.mark.asyncio
async def test_postgresql_container_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.postgresql.postgresql.setup_postgresql_container",
        side_effect=fake_setup,
    ):
        async for container in postgresql_container.__wrapped__(docker):
            assert container is existing


@pytest.mark.asyncio
async def test_postgresql_container_session_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.postgresql.postgresql.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        with patch(
            "pydocks.features.postgresql.postgresql.setup_postgresql_container",
            side_effect=fake_setup,
        ):
            async for container in postgresql_container_session.__wrapped__(docker):
                assert container is existing

    clean_mock.assert_awaited_once_with(docker, "test-postgresql-session")


@pytest.mark.asyncio
async def test_postgresql_test_connection():
    connection = AsyncMock()

    with (
        patch(
            "pydocks.features.postgresql.postgresql.socket_test_connection",
            new=AsyncMock(),
        ) as socket_mock,
        patch(
            "pydocks.features.postgresql.postgresql.asyncpg.connect",
            new=AsyncMock(return_value=connection),
        ) as connect_mock,
    ):
        await postgresql_test_connection(
            host="127.0.0.1",
            port=5432,
            username="postgres",
            password="postgres",
            db_name="postgres",
        )

    socket_mock.assert_awaited_once_with("127.0.0.1", 5432)
    connect_mock.assert_awaited_once_with(
        user="postgres",
        password="postgres",
        database="postgres",
        host="127.0.0.1",
        port=5432,
    )
    connection.fetchval.assert_awaited_once_with("SELECT 1")
    connection.close.assert_awaited_once()
