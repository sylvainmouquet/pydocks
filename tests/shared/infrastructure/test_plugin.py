from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import json

from pydocks.shared.infrastructure.plugin import (
    clean_containers,
    create_docker_client,
    file_exists,
    get_container_host_port,
    socket_test_connection,
    wait_and_run_container,
    wait_port_available,
)


class FakeContainer:
    def __init__(
        self, state="running", names="test-container", status="running", id="abc123"
    ):
        self.State = state
        self.Names = names
        self.Status = status
        self.Id = id

    def execute(self, _command):
        return "ok"


@pytest.mark.asyncio
async def test_clean_containers_removes_running_and_stopped():
    docker = MagicMock()
    running = FakeContainer(state="running", names="running-container")
    stopped = FakeContainer(state="exited", names="stopped-container")
    docker.ps.return_value = [running, stopped]

    await clean_containers(docker, "test")

    docker.kill.assert_called_once_with(running)
    assert docker.rm.call_count == 2


@pytest.mark.asyncio
async def test_clean_containers_logs_and_reraises_on_failure():
    docker = MagicMock()
    docker.ps.side_effect = RuntimeError("docker unavailable")

    with pytest.raises(RuntimeError, match="docker unavailable"):
        await clean_containers(docker, "test")


@pytest.mark.asyncio
async def test_file_exists_raises_when_missing():
    container = MagicMock()
    container.execute.return_value = "ko"

    with pytest.raises(FileNotFoundError):
        await file_exists(container, "/missing")


@pytest.mark.asyncio
async def test_file_exists_raises_when_missing_with_trailing_newline():
    container = MagicMock()
    container.execute.return_value = "ko\n"

    with pytest.raises(FileNotFoundError):
        await file_exists(container, "/missing")


@pytest.mark.asyncio
async def test_file_exists_succeeds_when_present():
    container = FakeContainer()

    await file_exists(container, "/ready")


@pytest.mark.asyncio
async def test_wait_and_run_container_kills_running_container():
    docker = MagicMock()
    container = FakeContainer(status="running")

    async for yielded in wait_and_run_container(docker, container, "test-container"):
        assert yielded is container

    docker.kill.assert_called_once_with("abc123")


@pytest.mark.asyncio
async def test_wait_and_run_container_skips_kill_when_not_running():
    docker = MagicMock()
    container = FakeContainer(status="exited")

    async for _ in wait_and_run_container(docker, container, "test-container"):
        pass

    docker.kill.assert_not_called()


@pytest.mark.asyncio
async def test_wait_port_available_completes_when_connect_fails():
    with patch("pydocks.shared.infrastructure.plugin.socket.socket") as socket_mock:
        socket_instance = MagicMock()
        socket_instance.connect.side_effect = OSError("connection refused")
        socket_mock.return_value = socket_instance

        await wait_port_available("localhost", 5433)


@pytest.mark.asyncio
async def test_wait_port_available_waits_until_port_is_free():
    connect_results: list[object] = [None, OSError("connection refused")]

    def connect_side_effect(*_args, **_kwargs):
        result = connect_results.pop(0)
        if isinstance(result, Exception):
            raise result

    with patch("pydocks.shared.infrastructure.plugin.socket.socket") as socket_mock:
        socket_instance = MagicMock()
        socket_instance.connect.side_effect = connect_side_effect
        socket_mock.return_value = socket_instance
        with patch(
            "pydocks.shared.infrastructure.plugin.anyio.wait_writable",
            new=AsyncMock(),
        ):
            with patch(
                "pydocks.shared.infrastructure.plugin.anyio.sleep",
                new=AsyncMock(),
            ) as sleep_mock:
                await wait_port_available("localhost", 5433)

    sleep_mock.assert_awaited_once()


def test_create_docker_client_with_docker_sock(monkeypatch):
    monkeypatch.setenv("DOCKER_SOCK", "/var/run/docker.sock")
    monkeypatch.delenv("CI", raising=False)

    with patch("pydocks.shared.infrastructure.plugin.PyContainers") as pycontainers_mock:
        create_docker_client()

    pycontainers_mock.assert_called_once()


def test_create_docker_client_with_ci(monkeypatch):
    monkeypatch.delenv("DOCKER_SOCK", raising=False)
    monkeypatch.setenv("CI", "true")

    with patch("pydocks.shared.infrastructure.plugin.PyContainers") as pycontainers_mock:
        create_docker_client()

    pycontainers_mock.assert_called_once()


def test_create_docker_client_local(monkeypatch):
    monkeypatch.delenv("DOCKER_SOCK", raising=False)
    monkeypatch.delenv("CI", raising=False)

    with patch("pydocks.shared.infrastructure.plugin.PyContainers") as pycontainers_mock:
        create_docker_client()

    pycontainers_mock.assert_called_once()


@pytest.mark.asyncio
async def test_socket_test_connection_connects():
    with patch("pydocks.shared.infrastructure.plugin.socket.socket") as socket_mock:
        socket_instance = MagicMock()
        socket_instance.__enter__.return_value = socket_instance
        socket_mock.return_value = socket_instance

        with patch(
            "pydocks.shared.infrastructure.plugin.anyio.wait_writable",
            new=AsyncMock(),
        ):
            await socket_test_connection("127.0.0.1", 6379)

    socket_instance.connect.assert_called_once_with(("127.0.0.1", 6379))


def test_get_container_host_port_returns_published_port():
    docker = MagicMock()
    container = MagicMock()
    container.ID = "container-id"
    docker.inspect.return_value = json.dumps(
        [
            {
                "NetworkSettings": {
                    "Ports": {"5432/tcp": [{"HostPort": "15432"}]},
                },
            }
        ]
    )

    assert get_container_host_port(docker, container, 5432) == 15432


def test_get_container_host_port_raises_when_unpublished():
    docker = MagicMock()
    container = MagicMock()
    container.ID = "container-id"
    docker.inspect.return_value = json.dumps(
        [
            {
                "NetworkSettings": {
                    "Ports": {"5432/tcp": None},
                },
            }
        ]
    )

    with pytest.raises(RuntimeError, match="Container port 5432 is not published"):
        get_container_host_port(docker, container, 5432)
