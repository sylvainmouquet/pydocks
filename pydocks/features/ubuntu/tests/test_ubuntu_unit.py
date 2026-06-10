from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pydocks.features.ubuntu.ubuntu import (
    setup_ubuntu_container,
    ubuntu_clean_all_containers,
    ubuntu_container,
    ubuntu_container_session,
)


class FakeContainer:
    Status = "running"
    Id = "abc123"


async def _fake_wait_and_run(_docker, container, _name):
    yield container


@pytest.mark.asyncio
async def test_setup_ubuntu_container_reuses_existing_container():
    docker = MagicMock()
    existing = FakeContainer()
    docker.ps.return_value = [existing]

    with patch(
        "pydocks.features.ubuntu.ubuntu.wait_and_run_container",
        side_effect=_fake_wait_and_run,
    ):
        async for container in setup_ubuntu_container(docker, "test-ubuntu-123"):
            assert container is existing

    docker.run.assert_not_called()


@pytest.mark.asyncio
async def test_setup_ubuntu_container_raises_on_failure():
    docker = MagicMock()
    docker.ps.return_value = []
    docker.run.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        async for _ in setup_ubuntu_container(docker, "test-ubuntu-123"):
            pass


@pytest.mark.asyncio
async def test_ubuntu_container_session_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.ubuntu.ubuntu.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        with patch(
            "pydocks.features.ubuntu.ubuntu.setup_ubuntu_container",
            side_effect=fake_setup,
        ):
            async for container in ubuntu_container_session.__wrapped__(docker):
                assert container is existing

    clean_mock.assert_awaited_once_with(docker, "test-ubuntu-session")


@pytest.mark.asyncio
async def test_ubuntu_clean_all_containers_fixture():
    docker = MagicMock()

    with patch(
        "pydocks.features.ubuntu.ubuntu.clean_containers",
        new=AsyncMock(),
    ) as clean_mock:
        fixture_gen = ubuntu_clean_all_containers.__wrapped__(docker)
        await anext(fixture_gen)
        with pytest.raises(StopAsyncIteration):
            await anext(fixture_gen)

    assert clean_mock.await_count == 2
    clean_mock.assert_awaited_with(docker, "test-ubuntu")


@pytest.mark.asyncio
async def test_ubuntu_container_fixture():
    docker = MagicMock()
    existing = FakeContainer()

    async def fake_setup(_docker, _name):
        yield existing

    with patch(
        "pydocks.features.ubuntu.ubuntu.setup_ubuntu_container",
        side_effect=fake_setup,
    ):
        async for container in ubuntu_container.__wrapped__(docker):
            assert container is existing
