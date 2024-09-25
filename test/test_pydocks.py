import pytest
from pydocks.conftest import postgresql_container


@pytest.mark.asyncio
async def test_docker(postgresql_container):
    print("ok")