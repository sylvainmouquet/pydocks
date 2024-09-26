__version__ = "1.0.7"
__all__ = (
    "__version__",
    "postgresql_clean_all_containers",
    "postgresql_container",
    "postgresql_container_session",
    "docker",
)

# pytest_plugins = ["pydocks.conftest"]
from pydocks.plugin import docker
from pydocks.postgresql import (
    postgresql_clean_all_containers,
    postgresql_container,
    postgresql_container_session,
)
