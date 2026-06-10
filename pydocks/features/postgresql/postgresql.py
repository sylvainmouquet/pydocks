import logging
import os
import time
import uuid

import anyio
import asyncpg
import pytest
import pytest_asyncio
import struct
from anyio.abc import SocketStream
from pycontainers import docker as libdocker
from reattempt import reattempt

from pydocks.shared.infrastructure.plugin import (
    clean_containers,
    socket_test_connection,
    wait_and_run_container,
    wait_port_available,
)

logger = logging.getLogger(__name__)


# https://hub.docker.com/_/postgres/tags
# TEST_POSTGRES_DOCKER_IMAGE: str = "docker.io/postgres:16.3"
TEST_POSTGRESQL_DOCKER_IMAGE: str = "docker.io/postgres:18-alpine"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def postgresql_clean_all_containers(docker):
    container_name: str = "test-postgresql"

    await clean_containers(docker, container_name)
    yield
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def postgresql_container(docker: libdocker):  # type: ignore
    container_name = f"test-postgresql-{uuid.uuid4()}"

    async for container in setup_postgresql_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def postgresql_container_session(docker: libdocker):  # type: ignore
    await clean_containers(docker, "test-postgresql-session")

    container_name = f"test-postgresql-session-{uuid.uuid4()}"

    async for container in setup_postgresql_container(docker, container_name):
        yield container


async def setup_postgresql_container(docker: libdocker, container_name):  # type: ignore
    start = time.perf_counter()
    logger.info(
        "Starting PostgreSQL container setup",
        extra={"container_name": container_name},
    )
    try:
        postgresql_image = (
            TEST_POSTGRESQL_DOCKER_IMAGE
            if "TEST_POSTGRESQL_DOCKER_IMAGE" not in os.environ
            else os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"]
        )
        logger.debug(
            "Using docker image",
            extra={"container_name": container_name, "image": postgresql_image},
        )

        def run_container(container_name: str):
            return docker.run(
                image=postgresql_image,
                name=container_name,
                detach=True,
                envs={
                    "POSTGRES_PASSWORD": "postgres",
                },
                publish=[(5433, 5432)],
                expose=[5433],
            )

        await wait_port_available(host="localhost", port=5433)

        containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
        if containers and len(containers) > 0:
            container = containers[0]  # type: ignore
            logger.debug(
                "Found existing container",
                extra={"container_name": container_name},
            )
        else:
            logger.debug(
                "Creating new container",
                extra={"container_name": container_name},
            )
            container = run_container(container_name)

        await postgresql_test_connection(
            host="127.0.0.1",
            port=5433,
            username="postgres",
            password="postgres",
            db_name="postgres",
        )

        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.info(
            "PostgreSQL container setup completed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )

        async for instance in wait_and_run_container(docker, container, container_name):
            yield instance
    except Exception:
        duration_ms = round((time.perf_counter() - start) * 1000)
        logger.exception(
            "PostgreSQL container setup failed",
            extra={"container_name": container_name, "duration_ms": duration_ms},
        )
        raise


@reattempt(max_retries=40, min_time=0.1, max_time=0.5)
async def postgresql_test_connection(
    host: str, port: int, username: str, password: str, db_name: str
):
    await socket_test_connection(host, port)

    stream: SocketStream = await anyio.connect_tcp(host, port)

    startup_packet = f"user=fake-user password=fake-password dbname=fake-db host={host} port={port}\x00".encode()
    await stream.send(struct.pack(">I", len(startup_packet)))
    await stream.send(b"\x00\x03\x00\x00")
    await stream.send(startup_packet)
    await stream.send(b"\x00")

    await stream.receive()
    logger.info(
        "PostgreSQL socket connection successful",
        extra={"host": host, "port": port},
    )
    await stream.aclose()

    conn = await asyncpg.connect(
        user=username, password=password, database=db_name, host=host, port=port
    )
    try:
        await conn.fetchval("SELECT 1")
        logger.debug(
            "PostgreSQL health check query completed",
            extra={"host": host, "port": port, "operation": "select_1"},
        )
    finally:
        await conn.close()
