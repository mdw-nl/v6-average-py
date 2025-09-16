from pathlib import Path
import pytest
import time
import docker
from vantage6.cli.dev.profile import ProfileManager
from vantage6.client import Client
import logging

# TODO:
# - consider moving some of this to vantage6 itself?
# - is a good idea/practice to modify the host (by creating docker images, etc)?

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PROFILE_JSON_PATH = REPO_ROOT / "tests/v6-dev-profile/profiles.json"
DOCKERFILE_PATH = REPO_ROOT
TIMESTAMP = time.strftime("%Y%m%d-%H%M%S")
IMAGE_NAME = f"localhost/ghcr.io/mdw-nl/v6-average-py:test-{TIMESTAMP}"


@pytest.fixture(scope="session")
def docker_client():
    """Fixture to create a Docker client."""
    logger.info("Creating Docker client...")
    return docker.from_env()


@pytest.fixture(scope="session")
def build_test_image(docker_client: docker.DockerClient):
    """Build a Docker image tagged with a unique test-specific tag."""
    print(f"Building Docker image '{IMAGE_NAME}'...")
    logger.info(f"Building Docker image '{IMAGE_NAME}'...")
    try:
        _, logs = docker_client.images.build(path=str(DOCKERFILE_PATH), tag=IMAGE_NAME, rm=True)
        for log in logs:
            if "stream" in log:
                print(log["stream"].strip())
        print(f"Image '{IMAGE_NAME}' built successfully!")
    except docker.errors.BuildError as e:
        pytest.fail(f"Docker build failed: {e}")
    except Exception as e:
        pytest.fail(f"Unexpected error during Docker build: {e}")

    yield IMAGE_NAME

    # Cleanup: Remove the image and ensure only related dangling layers are removed
    print(f"Removing Docker image '{IMAGE_NAME}'...")
    try:
        image = docker_client.images.get(IMAGE_NAME)
        image_id = image.id

        # Remove the image, we don't need it, nor we want to pollute the host
        docker_client.images.remove(image=IMAGE_NAME, force=True)
        print(f"Image '{IMAGE_NAME}' removed successfully.")

        # Remove dangling layers related to this image
        print("Checking for dangling layers related to the removed image...")
        dangling_images = docker_client.images.list(filters={"dangling": True})
        for dangling_image in dangling_images:
            if dangling_image.id == image_id:
                docker_client.images.remove(image=dangling_image.id, force=True)
                print(
                    f"Removed dangling layer '{dangling_image.id}' related to '{IMAGE_NAME}'."
                )

    except docker.errors.ImageNotFound:
        print(f"Image '{IMAGE_NAME}' was already removed.")
    except Exception as e:
        print(f"Failed to remove image '{IMAGE_NAME}': {e}")


@pytest.fixture(scope="session")
def run_all_profile():
    """Start the 'run-all' profile once for all tests in the module."""
    print("Starting 'run-all' profile...")
    logger.info("Starting 'run-all' profile...")
    profile_manager = ProfileManager(str(PROFILE_JSON_PATH))
    profile = profile_manager.get_profile("run-all")
    profile.start()

    yield profile

    print("Stopping 'run-all' profile...")
    profile.stop()


@pytest.fixture
def client():
    """Fixture to set up a Vantage6 client."""
    logger.info("Setting up Vantage6 client...")
    config = {
        "server_url": "http://127.0.6.1",
        "server_port": 80,
        "server_api": "/api",
        "username": "phobos",
        "password": "test-password-two-orbit",
        "organization_key": None,
    }

    client = Client(config["server_url"], config["server_port"], config["server_api"])
    client.authenticate(config["username"], config["password"])
    client.setup_encryption(config["organization_key"])
    return client


@pytest.fixture
def ensure_node_mars_online(client):
    """
    Ensure the 'Mars' node is online, waiting up to 20 seconds.
    """
    try:
        wait_for_nodes_online(client, ["Mars - Planets Development Node"], timeout=20)
    except TimeoutError as e:
        pytest.fail(f"Timeout: {e}")
        return False
    return True


@pytest.fixture
def ensure_all_planetary_nodes_online(client):
    """
    Ensure 'Mars', 'Jupiter', and 'Saturn' nodes are online, waiting up to 20 seconds.
    """
    try:
        wait_for_nodes_online(
            client,
            [
                "Jupiter - Planets Development Node",
                "Saturn - Planets Development Node",
                "Mars - Planets Development Node",
            ],
            timeout=20,
        )
    except TimeoutError as e:
        pytest.fail(f"Timeout: {e}")
        return False
    return True


# TODO: improve & move this somewhere reusable?
def wait_for_nodes_online(client, node_names, timeout=20, poll_interval=1):
    """
    Wait for the specified nodes to come online within a timeout.

    Parameters:
    - client: Vantage6 client instance.
    - node_names: List of node names to wait for (e.g., ["Mars", "Jupiter", "Saturn"]).
    - timeout: Maximum time to wait for nodes to be online, in seconds.
    - poll_interval: Time between checks, in seconds.

    Returns:
    - True if all specified nodes are online within the timeout.

    Raises:
    - TimeoutError if nodes are not online within the timeout.
    """
    target_nodes = set(node_names)
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = client.node.list(is_online=True)
        # FIXME: Ignoring pagination here
        nodes = response.get("data", [])
        online_node_names = {node.get("name") for node in nodes}

        missing_nodes = target_nodes - online_node_names
        if not missing_nodes:
            return True

        # Wait and retry
        time.sleep(poll_interval)

    # Timeout reached
    raise TimeoutError(f"Timeout: Nodes not online: {', '.join(missing_nodes)}")
