import pytest
from python_on_whales import docker as libdocker
import socket
import struct
import anyio
#import asyncpg
from anyio.abc import SocketStream
#from app.utils.logger import logger
from python_on_whales import DockerClient
from reattempt import reattempt
from logging import logger
import uuid
from pydocks.docker import clean_containers, socket_test_connection, wait_and_run_container

from logging import logger

TEST_POSTGRES_DOCKER_IMAGE = "docker.io/"


@pytest.fixture(autouse=False)
async def postgres_server(docker: libdocker, mocker):  # type: ignore
    mocker.patch("logging.exception", lambda *args, **kwargs: logger.warning(f"Exception raised {args}"))

    logger.debug(f"[PYTEST] Pull docker image : {TEST_POSTGRES_DOCKER_IMAGE}")

    def run_container(container_name: str):
        return docker.run(
            image=TEST_POSTGRES_DOCKER_IMAGE,
            name=container_name,
            detach=True,
            envs={
                "POSTGRES_PASSWORD": "postgres",
            },
            publish=[(5433, 5432)],
            expose=[5433],
        )

    await clean_containers(docker, "test-postgres")

    container = run_container(f"test-postgres-{uuid.uuid4()}")

    """
    if not os.getenv('reuse', True): 
        # Create container on 5433:5432 port exposition
        # Use default login / password
        await clean_containers(docker, "test-postgres")

        container = run_container("test-postgres")
    else:
            # Check if container exists, if not create it
        container_name = "test-postgres"
        existing_container = docker.ps(all=True, filters={"name": f"^{container_name}"})

        if existing_container:
            container = existing_container[0]
            if container.state.status != "running":
                container.start()
        else:
            container = run_container(container_name)
    """

    await postgresql_test_connection(host="127.0.0.1", port=5433, username="postgres", password="postgres", db_name="postgres")

    async for instance in wait_and_run_container(docker, container, "postgres"):
        yield instance



@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def postgresql_test_connection(host: str, port: int, username: str, password: str, db_name: str):
    await socket_test_connection(host, port)

    stream: SocketStream = await anyio.connect_tcp(host, port)

    # Send a startup packet
    startup_packet = f"user=fake-user password=fake-password dbname=fake-db host={host} port={port}\x00".encode()
    await stream.send(struct.pack(">I", len(startup_packet)))
    await stream.send(b"\x00\x03\x00\x00")  # frontend protocol version 3.0
    await stream.send(startup_packet)
    await stream.send(b"\x00")  # terminator byte

    await stream.receive()
    logger.info("Connection successful.")
    await stream.aclose()

    """
    conn = await asyncpg.connect(user=username, password=password, database=db_name, host=host, port=port)
    try:
        # Execute the SELECT 1 query
        result = await conn.fetchval("SELECT 1")
        logger.info(f"Query result: {result}")
    finally:
        await conn.close()
    """

