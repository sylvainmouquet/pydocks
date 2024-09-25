from unittest.mock import patch
import pytest
from pathlib import Path
import os

import socket
from asyncpg.pool import Pool
from fastapi import FastAPI
#from asgi_lifespan import LifespanManager
import asyncpg
import anyio
from python_on_whales import DockerClient
from python_on_whales import docker as libdocker
from reattempt import reattempt
import logging
import pytest
import struct
import anyio
from anyio.abc import SocketStream
from reattempt import reattempt
import uuid
from requests import Session
from unittest.mock import patch

from pydocks.plugin import clean_containers, socket_test_connection, wait_and_run_container


logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


# https://hub.docker.com/_/postgres/tags
# TEST_POSTGRES_DOCKER_IMAGE: str = "docker.io/postgres:16.3"
TEST_POSTGRESQL_DOCKER_IMAGE: str = "docker.io/postgres:17rc1-alpine3.20"

@pytest.fixture(scope="function")
async def postgresql_container(docker: libdocker, mocker, request):  # type: ignore
    mocker.patch("logging.exception", lambda *args, **kwargs: logger.warning(f"Exception raised {args}"))
    async for container in setup_postgresql_container(docker, request):
        yield container
    
    
@pytest.fixture(scope="session")
@patch.object(logging, 'exception', lambda *args, **kwargs: logger.warning(f"Exception raised {args}"))
def postgresql_container_session(docker: libdocker,request):  # type: ignore
    import asyncio
    loop = asyncio.get_event_loop()
    container = loop.run_until_complete(setup_postgresql_container(docker, request).__anext__())
    yield container
    loop.run_until_complete(clean_containers(docker, "test-postgresql"))


async def setup_postgresql_container(docker: libdocker, request):  # type: ignore
    postgresql_image = TEST_POSTGRESQL_DOCKER_IMAGE if 'TEST_POSTGRESQL_DOCKER_IMAGE' not in os.environ else os.environ['TEST_POSTGRESQL_DOCKER_IMAGE']
    logger.debug(f"[PYDOCKS] Pull docker image : {postgresql_image}")

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

    await clean_containers(docker, "test-postgresql")

    container = run_container(f"test-postgresql-{uuid.uuid4()}")

    await postgresql_test_connection(
        host="127.0.0.1",
        port=5433,
        username="postgres",
        password="postgres",
        db_name="postgres",
    )

    async for instance in wait_and_run_container(docker, container, "postgresql"):
        yield instance

    if request.scope == "session":
        # Clean up after session
        await clean_containers(docker, "test-postgresql")


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
    logger.info("[PYDOCKS] Connection successful.")
    await stream.aclose()


    conn = await asyncpg.connect(user=username, password=password, database=db_name, host=host, port=port)
    try:
        # Execute the SELECT 1 query
        result = await conn.fetchval("SELECT 1")
        logger.info(f"[PYDOCKS] Query result: {result}")
    finally:
        await conn.close()
