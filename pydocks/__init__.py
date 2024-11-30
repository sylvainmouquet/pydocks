__version__ = "1.0.1"
__all__ = (
    "__version__",
    "postgresql_clean_all_containers",
    "postgresql_container",
    "postgresql_container_session",
    "docker",
    "vault_clean_all_containers",
    "vault_container",
    "vault_container_session",
    "redis_clean_all_containers",
    "redis_container",
    "redis_container_session",
    "ubuntu_clean_all_containers",
    "ubuntu_container",
    "ubuntu_container_session",
)

# pytest_plugins = ["pydocks.conftest"]
from pydocks.plugin import docker
from pydocks.postgresql import (
    postgresql_clean_all_containers,
    postgresql_container,
    postgresql_container_session,
)

from pydocks.vault import (
    vault_clean_all_containers,
    vault_container,
    vault_container_session,
)

from pydocks.redis import (
    redis_clean_all_containers,
    redis_container,
    redis_container_session,
)

from pydocks.ubuntu import (
    ubuntu_clean_all_containers,
    ubuntu_container,
    ubuntu_container_session,
)
