import pytest
import asyncpg
import os

@pytest.mark.asyncio
async def test_postgresql_default_version(postgresql_container):
    # Get environment variables from the PostgreSQL container
    container_env_dict = dict(env.split('=') for env in postgresql_container.config.env)

    assert container_env_dict['PG_MAJOR'] == '17'
    assert container_env_dict['PG_VERSION'] == '17rc1'


@pytest.fixture
def custom_postgresql_version():
    os.environ['TEST_POSTGRESQL_DOCKER_IMAGE'] = "docker.io/postgres:16.3"
    yield
    del os.environ['TEST_POSTGRESQL_DOCKER_IMAGE']

@pytest.mark.asyncio
async def test_postgresql_custom_version(custom_postgresql_version, postgresql_container):
    # Get environment variables from the PostgreSQL container
    container_env_dict = dict(env.split('=') for env in postgresql_container.config.env)

    assert container_env_dict['PG_MAJOR'] == '16'
    assert container_env_dict['PG_VERSION'] == '16.3-1.pgdg120+1'

@pytest.mark.asyncio
async def test_postgresql_execute_command(postgresql_container):
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host='127.0.0.1',
        port=5433,
        user='postgres',
        password='postgres',
        database='postgres'
    )

    try:
        # Execute a simple command
        result = await conn.fetchval('SELECT 1')
        assert result == 1, "Failed to execute command on PostgreSQL"
    finally:
        # Close the connection
        await conn.close()