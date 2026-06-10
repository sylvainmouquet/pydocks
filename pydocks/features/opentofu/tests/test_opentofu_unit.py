from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydocks.features.opentofu.opentofu import (
    opentofu_clean_all_containers,
    opentofu_container,
    opentofu_container_session,
    opentofu_test_connection,
    setup_opentofu_container,
)


class FakeContainer:
    Status = "running"
    Id = "abc123"


async def _fake_wait_and_run(_docker, container, _name):
    yield container


@pytest.mark.asyncio
async def test_setup_opentofu_container_reuses_existing_container():
    docker = MagicMock()
    existing = FakeContainer()
    docker.ps.return_value = [existing]

    with (
        patch(
            "pydocks.features.opentofu.opentofu.opentofu_test_connection",
            new=AsyncMock(),
        ),
        patch(
            "pydocks.features.opentofu.opentofu.wait_and_run_container",
            side_effect=_fake_wait_and_run,
        ),
    ):
        async for container in setup_opentofu_container(docker, "test-opentofu-123"):
            assert container is existing

    docker.run.assert_not_called()


@pytest.mark.asyncio
async def test_setup_opentofu_container_raises_on_failure():
    docker = MagicMock()
    docker.ps.return_value = []
    docker.run.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        async for _ in setup_opentofu_container(docker, "test-opentofu-123"):
            pass


@pytest.mark.asyncio
async def test_opentofu_container_session_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.opentofu.opentofu.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        with patch(
            "pydocks.features.opentofu.opentofu.setup_opentofu_container",
            side_effect=fake_setup,
        ):
            async for container in opentofu_container_session.__wrapped__(docker):
                assert container is existing

    clean_mock.assert_awaited_once_with(docker, "test-opentofu-session")


@pytest.mark.asyncio
async def test_opentofu_clean_all_containers_fixture():
    docker = MagicMock()

    with patch(
        "pydocks.features.opentofu.opentofu.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        fixture_gen = opentofu_clean_all_containers.__wrapped__(docker)
        await anext(fixture_gen)
        with pytest.raises(StopAsyncIteration):
            await anext(fixture_gen)

    assert clean_mock.await_count == 2
    clean_mock.assert_awaited_with(docker, "test-opentofu")


@pytest.mark.asyncio
async def test_opentofu_container_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.opentofu.opentofu.setup_opentofu_container",
        side_effect=fake_setup,
    ):
        async for container in opentofu_container.__wrapped__(docker):
            assert container is existing


@pytest.mark.asyncio
async def test_opentofu_test_connection_succeeds():
    container = MagicMock()
    container.execute.return_value = "OpenTofu v1.9.0"

    with patch(
        "pydocks.features.opentofu.opentofu.file_exists",
        new=AsyncMock(),
    ) as file_exists_mock:
        await opentofu_test_connection(container)

    file_exists_mock.assert_awaited_once_with(container, "/terraform/ready")


@pytest.mark.asyncio
async def test_opentofu_test_connection_raises_when_unavailable():
    container = MagicMock()
    container.execute.return_value = "not opentofu"

    with pytest.raises(Exception, match="OpenTofu is not available in the container"):
        await opentofu_test_connection(container)
