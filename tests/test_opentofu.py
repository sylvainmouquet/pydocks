import pytest
import os
from loguru import logger
import pytest_asyncio


@pytest_asyncio.fixture(scope="session", loop_scope="session", autouse=True)
async def begin_clean_all_containers(opentofu_clean_all_containers):
    logger.info("Begin - clean all containers")


@pytest.mark.asyncio
async def test_opentofu_default_version(opentofu_container):
    version_output = opentofu_container.execute(["tofu", "version"])
    assert (
        "OpenTofu v1.9.0" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.fixture
def custom_opentofu_version():
    os.environ["TEST_OPENTOFU_DOCKER_IMAGE"] = "docker.io/scalr/opentofu:1.6.0"
    yield
    del os.environ["TEST_OPENTOFU_DOCKER_IMAGE"]


@pytest.mark.asyncio
async def test_opentofu_custom_version(custom_opentofu_version, opentofu_container):
    version_output = opentofu_container.execute(["tofu", "version"])
    assert (
        "OpenTofu v1.6.0" in version_output
    ), f"Unexpected version output: {version_output}"


@pytest.mark.asyncio
async def test_opentofu_execute_command(opentofu_container):
    # Create a simple Terraform file
    opentofu_container.execute(
        [
            "sh",
            "-c",
            """
cat > main.tf << 'EOF'
output "hello_world" {
  value = "Hello, World!"
}
EOF
    """
        ]
    )

    # Initialize OpenTofu
    init_result = opentofu_container.execute(["tofu", "init"])
    assert "OpenTofu has been successfully initialized" in init_result

    # Apply the configuration
    apply_result = opentofu_container.execute(["tofu", "apply", "-auto-approve"])
    assert "Apply complete!" in apply_result
    assert "Hello, World!" in apply_result

    # Output the result
    output_result = opentofu_container.execute(["tofu", "output", "hello_world"])
    assert output_result.strip() == '"Hello, World!"'