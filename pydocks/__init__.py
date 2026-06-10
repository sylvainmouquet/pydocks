__version__ = "2.0.0"
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
    "opentofu_clean_all_containers",
    "opentofu_container",
    "opentofu_container_session",
    "alpine_clean_all_containers",
    "alpine_container",
    "alpine_container_session",
    "valkey_clean_all_containers",
    "valkey_container",
    "valkey_container_session",
)

from pydocks.shared.infrastructure.plugin import docker
from pydocks.features.postgresql import (
    postgresql_clean_all_containers,
    postgresql_container,
    postgresql_container_session,
)
from pydocks.features.vault import (
    vault_clean_all_containers,
    vault_container,
    vault_container_session,
)
from pydocks.features.redis import (
    redis_clean_all_containers,
    redis_container,
    redis_container_session,
)
from pydocks.features.ubuntu import (
    ubuntu_clean_all_containers,
    ubuntu_container,
    ubuntu_container_session,
)
from pydocks.features.opentofu import (
    opentofu_clean_all_containers,
    opentofu_container,
    opentofu_container_session,
)
from pydocks.features.alpine import (
    alpine_clean_all_containers,
    alpine_container,
    alpine_container_session,
)
from pydocks.features.valkey import (
    valkey_clean_all_containers,
    valkey_container,
    valkey_container_session,
)

from pydocks.shared.infrastructure.logging import configure_package_logging

configure_package_logging()
