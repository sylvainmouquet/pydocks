from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydocks.features.vault.vault import (
    setup_vault_container,
    vault_clean_all_containers,
    vault_container,
    vault_container_session,
    vault_test_connection,
)


class FakeContainer:
    Status = "running"
    Id = "abc123"


async def _fake_wait_and_run(_docker, container, _name):
    yield container


@pytest.mark.asyncio
async def test_setup_vault_container_reuses_existing_container():
    docker = MagicMock()
    existing = FakeContainer()
    docker.ps.return_value = [existing]

    with (
        patch(
            "pydocks.features.vault.vault.get_container_host_port",
            return_value=8200,
        ),
        patch(
            "pydocks.features.vault.vault.vault_test_connection",
            new=AsyncMock(),
        ),
        patch(
            "pydocks.features.vault.vault.wait_and_run_container",
            side_effect=_fake_wait_and_run,
        ),
    ):
        async for container in setup_vault_container(docker, "test-vault-123"):
            assert container is existing

    docker.run.assert_not_called()


@pytest.mark.asyncio
async def test_setup_vault_container_raises_on_failure():
    docker = MagicMock()
    docker.ps.return_value = []
    docker.run.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        async for _ in setup_vault_container(docker, "test-vault-123"):
            pass


@pytest.mark.asyncio
async def test_vault_container_session_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.vault.vault.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        with patch(
            "pydocks.features.vault.vault.setup_vault_container",
            side_effect=fake_setup,
        ):
            async for container in vault_container_session.__wrapped__(docker):
                assert container is existing

    clean_mock.assert_awaited_once_with(docker, "test-vault-session")


@pytest.mark.asyncio
async def test_vault_clean_all_containers_fixture():
    docker = MagicMock()

    with patch(
        "pydocks.features.vault.vault.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        fixture_gen = vault_clean_all_containers.__wrapped__(docker)
        await anext(fixture_gen)
        with pytest.raises(StopAsyncIteration):
            await anext(fixture_gen)

    assert clean_mock.await_count == 2
    clean_mock.assert_awaited_with(docker, "test-vault")


@pytest.mark.asyncio
async def test_vault_container_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.vault.vault.setup_vault_container",
        side_effect=fake_setup,
    ):
        async for container in vault_container.__wrapped__(docker):
            assert container is existing


@pytest.mark.asyncio
async def test_vault_test_connection():
    container = MagicMock()
    container.host = "127.0.0.1"
    container.port = 8200

    with (
        patch(
            "pydocks.features.vault.vault.socket_test_connection",
            new=AsyncMock(),
        ) as socket_mock,
        patch(
            "pydocks.features.vault.vault.file_exists",
            new=AsyncMock(),
        ) as file_exists_mock,
    ):
        await vault_test_connection(container)

    socket_mock.assert_awaited_once_with("127.0.0.1", 8200)
    assert file_exists_mock.await_count == 2
