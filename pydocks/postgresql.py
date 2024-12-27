import pytest
import os


import pytest_asyncio
import asyncpg
import anyio
from python_on_whales import docker as libdocker
from reattempt import reattempt
import logging
import struct
from anyio.abc import SocketStream
import uuid

from pydocks.plugin import (
    clean_containers,
    socket_test_connection,
    wait_and_run_container,
    wait_port_available,
)


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/_/postgres/tags
# TEST_POSTGRES_DOCKER_IMAGE: str = "docker.io/postgres:16.3"
TEST_POSTGRESQL_DOCKER_IMAGE: str = "docker.io/postgres:17rc1-alpine3.20"


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def postgresql_clean_all_containers(docker):
    container_name: str = "test-postgresql"
    # clean before

    await clean_containers(docker, container_name)
    yield
    # clean after
    await clean_containers(docker, container_name)


@pytest.fixture(scope="function")
async def postgresql_container(docker: libdocker, mocker):  # type: ignore
    mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    container_name = f"test-postgresql-{uuid.uuid4()}"
    # optional : await clean_containers(docker, container_name)

    async for container in setup_postgresql_container(docker, container_name):
        yield container


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def postgresql_container_session(docker: libdocker, session_mocker):  # type: ignore
    session_mocker.patch(
        "logging.exception",
        lambda *args, **kwargs: logger.warning(f"Exception raised {args}"),
    )

    await clean_containers(docker, "test-postgresql-session")

    container_name = f"test-postgresql-session-{uuid.uuid4()}"

    async for container in setup_postgresql_container(docker, container_name):
        yield container


async def setup_postgresql_container(docker: libdocker, container_name):  # type: ignore
    postgresql_image = (
        TEST_POSTGRESQL_DOCKER_IMAGE
        if "TEST_POSTGRESQL_DOCKER_IMAGE" not in os.environ
        else os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"]
    )
    logger.debug(f"pull docker image : {postgresql_image}")

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

    # Select the container with the given name if exists, else create a new one
    containers = docker.ps(all=True, filters={"name": f"^{container_name}$"})
    if containers and len(containers) > 0:
        container = containers[0]  # type: ignore
        logger.debug(f"found existing container: {container_name}")
    else:
        logger.debug(f"no existing container found, creating new one: {container_name}")
        container = run_container(container_name)

    await postgresql_test_connection(
        host="127.0.0.1",
        port=5433,
        username="postgres",
        password="postgres",
        db_name="postgres",
    )

    async for instance in wait_and_run_container(docker, container, container_name):
        yield instance


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def postgresql_test_connection(
    host: str, port: int, username: str, password: str, db_name: str
):
    await socket_test_connection(host, port)

    stream: SocketStream = await anyio.connect_tcp(host, port)

    # Send a startup packet
    startup_packet = f"user=fake-user password=fake-password dbname=fake-db host={host} port={port}\x00".encode()
    await stream.send(struct.pack(">I", len(startup_packet)))
    await stream.send(b"\x00\x03\x00\x00")  # frontend protocol version 3.0
    await stream.send(startup_packet)
    await stream.send(b"\x00")  # terminator byte

    await stream.receive()
    logger.info("connection successful.")
    await stream.aclose()

    conn = await asyncpg.connect(
        user=username, password=password, database=db_name, host=host, port=port
    )
    try:
        # Execute the SELECT 1 query
        result = await conn.fetchval("SELECT 1")
        logger.info(f"query result: {result}")
    finally:
        await conn.close()
