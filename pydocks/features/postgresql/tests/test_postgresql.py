import logging
import os

import asyncpg
import pytest
import pytest_asyncio

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(postgresql_clean_all_containers):
    logger.info(
        "Beginning container cleanup session",
        extra={"feature": "postgresql"},
    )


@pytest.mark.asyncio
async def test_postgresql_default_version(postgresql_container):
    container_env_dict = dict(env.split("=") for env in postgresql_container.config.env)

    assert container_env_dict["PG_MAJOR"] == "18"


@pytest.fixture
def custom_postgresql_version():
    os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"] = "docker.io/postgres:17-alpine"
    yield
    del os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_postgresql_custom_version(
    custom_postgresql_version, postgresql_container
):
    container_env_dict = dict(env.split("=") for env in postgresql_container.config.env)

    assert container_env_dict["PG_MAJOR"] == "17"


@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "Failed to execute command on PostgreSQL"
    finally:
        await conn.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_1_2(postgresql_container_session):
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)

        await conn.execute("INSERT INTO test_table (value) VALUES ($1)", 42)

        result = await conn.fetchval("SELECT value FROM test_table WHERE id = 1")
        assert result == 42, "Failed to execute command on PostgreSQL"
    finally:
        await conn.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_2_2(postgresql_container_session):
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        result = await conn.fetchval("SELECT value FROM test_table WHERE id = 1")
        assert result == 42, "Failed to retrieve the correct value from test_table"
    finally:
        await conn.close()
