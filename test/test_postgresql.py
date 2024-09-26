import pytest
import asyncpg
import os
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(postgresql_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_postgresql_default_version(postgresql_container):
    # Get environment variables from the PostgreSQL container
    container_env_dict = dict(env.split("=") for env in postgresql_container.config.env)

    assert container_env_dict["PG_MAJOR"] == "17"
    assert container_env_dict["PG_VERSION"] == "17rc1"


@pytest.fixture
def custom_postgresql_version():
    os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"] = "docker.io/postgres:16.3"
    yield
    del os.environ["TEST_POSTGRESQL_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_postgresql_custom_version(
    custom_postgresql_version, postgresql_container
):
    # Get environment variables from the PostgreSQL container
    container_env_dict = dict(env.split("=") for env in postgresql_container.config.env)

    assert container_env_dict["PG_MAJOR"] == "16"
    assert container_env_dict["PG_VERSION"] == "16.3-1.pgdg120+1"


@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        # Execute a simple command
        result = await conn.fetchval("SELECT 1")
        assert result == 1, "Failed to execute command on PostgreSQL"
    finally:
        # Close the connection
        await conn.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_1_2(postgresql_container_session):
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        # Execute a simple command
        # Create a table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id SERIAL PRIMARY KEY,
                value INTEGER
            )
        """)

        # Insert a value
        await conn.execute("INSERT INTO test_table (value) VALUES ($1)", 42)

        # Fetch the inserted value
        result = await conn.fetchval("SELECT value FROM test_table WHERE id = 1")
        assert result == 42, "Failed to execute command on PostgreSQL"
    finally:
        # Close the connection
        await conn.close()


@pytest.mark.asyncio(loop_scope="session")
async def test_reuse_postgresql_container_2_2(postgresql_container_session):
    # the test test_reuse_postgresql_container_2_2 depends of the test test_reuse_postgresql_container_2_1

    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host="127.0.0.1",
        port=5433,
        user="postgres",
        password="postgres",
        database="postgres",
    )

    try:
        # Execute a simple command
        result = await conn.fetchval("SELECT value FROM test_table WHERE id = 1")
        assert result == 42, "Failed to retrieve the correct value from test_table"
    finally:
        # Close the connection
        await conn.close()
