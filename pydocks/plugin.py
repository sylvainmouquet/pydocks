import pytest
from pathlib import Path
import os

import socket

import anyio
from python_on_whales import DockerClient
from reattempt import reattempt
import logging

logger = logging.getLogger("pydocks")
logger.addHandler(logging.NullHandler())


@pytest.fixture(scope="session", autouse=True)
def docker():
    if "DOCKER_SOCK" in os.environ:
        yield DockerClient(host=os.environ["DOCKER_SOCK"])
    elif "CI" in os.environ:
        # Github Actions, GitLab CI, ...
        yield DockerClient()
    else:
        # local with colima
        home: str = str(Path.home())
        yield DockerClient(host=f"unix://{home}/.colima/default/docker.sock")


@reattempt(max_retries=30, min_time=0.1, max_time=0.5)
async def socket_test_connection(host, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    await anyio.wait_socket_writable(s)


async def clean_containers(docker: DockerClient, name: str):
    containers = docker.ps(all=True, filters={"name": f"^{name}"})

    for container in containers:
        if container.state.running:
            docker.kill(container)
        logger.info(f"remove container {container.name}")
        docker.remove(container)


async def wait_and_run_container(docker, container, name: str):
    logger.debug(f"start {name}")
    try:
        yield container
    finally:
        logger.debug(f"kill container {name} and remove the docker container")
        if container.state.status == "running":
            logger.debug(f"container {name} is running")
            docker.kill(container.id)
            logger.debug(f"killed container {name}")
        else:
            logger.debug(f"container {name} is not running")
