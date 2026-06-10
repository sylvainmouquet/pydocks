import logging
import json
import os
import socket
import time

import anyio
import pytest
from pycontainers import PyContainers
from reattempt import reattempt

logger = logging.getLogger(__name__)


def create_docker_client() -> PyContainers:
    if "DOCKER_SOCK" in os.environ or "CI" in os.environ:
        return PyContainers()
    return PyContainers()


@pytest.fixture(scope="session", autouse=True)
def docker():
    yield create_docker_client()


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def socket_test_connection(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    await anyio.wait_writable(s)


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def file_exists(container, filepath):
    result = container.execute(
        ["sh", "-c", f'test -e {filepath} && echo "ok" || echo "ko"']
    )
    if result == "ko":
        logger.debug(
            "File not found in container",
            extra={"filepath": filepath},
        )
        raise FileNotFoundError(
            f"[WARNING] File {filepath} does not exist in the container"
        )


def get_container_host_port(docker: PyContainers, container, container_port: int) -> int:
    inspect_output = docker.inspect(container.ID)
    inspect_data = json.loads(inspect_output)[0]
    ports = inspect_data["NetworkSettings"]["Ports"]
    port_bindings = ports[f"{container_port}/tcp"]

    if not port_bindings:
        raise RuntimeError(f"Container port {container_port} is not published")

    return int(port_bindings[0]["HostPort"])


async def clean_containers(docker: PyContainers, name: str):
    start = time.perf_counter()
    logger.info(
        "Starting container cleanup",
        extra={"container_name_prefix": name},
    )
    try:
        containers = docker.ps(all=True, filter={"name": f"^{name}"})

        for container in containers:
            if container.State == "running":
                docker.kill(container)
            logger.info(
                "Removing container",
                extra={"container_name": container.Names},
            )
            docker.rm(container)

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "Container cleanup completed",
            extra={
                "container_name_prefix": name,
                "containers_removed": len(containers),
                "duration_ms": duration_ms,
            },
        )
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "Container cleanup failed",
            extra={
                "container_name_prefix": name,
                "duration_ms": duration_ms,
            },
        )
        raise


async def wait_and_run_container(docker, container, name: str):
    logger.debug(
        "Starting container session",
        extra={"container_name": name},
    )
    try:
        yield container
    finally:
        logger.debug(
            "Stopping container session",
            extra={"container_name": name},
        )
        if container.Status == "running":
            logger.debug(
                "Killing running container",
                extra={"container_name": name},
            )
            docker.kill(container.Id)
        else:
            logger.debug(
                "Container is not running",
                extra={"container_name": name},
            )


async def wait_port_available(host: str, port: int):
    async def _socket_test_connection() -> bool:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            await anyio.wait_writable(s)
            return True
        except OSError:
            logger.debug(
                "Port connection failed during availability check",
                extra={"host": host, "port": port},
            )
            return False

    while await _socket_test_connection():
        logger.info(
            "Waiting for port to become available",
            extra={"host": host, "port": port},
        )
        await anyio.sleep(1)
