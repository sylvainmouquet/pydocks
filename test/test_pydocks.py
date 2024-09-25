import pytest
import asyncpg


@pytest.mark.asyncio
async def test_postgresql(postgresql_container):
    
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