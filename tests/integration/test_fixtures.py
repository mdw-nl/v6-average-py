import pytest
import docker

@pytest.mark.integration
def test_docker_client(docker_client):
    """
    Test to ensure that the Docker client is working properly.
    """
    try:
        # version
        version = docker_client.version()
        assert version, "Docker client version should not be None."
        print(f"Docker client version: {version['Version']}")
    except Exception as e:
        pytest.fail(f"Unexpected error while checking Docker client: {e}")

@pytest.mark.integration
def test_build_test_image(docker_client, build_test_image):
    """
    Test to ensure that the Docker image created by the build_test_image
    fixture exists.
    """
    # Use docker_client to inspect the image
    try:
        image = docker_client.images.get(build_test_image)
        assert image, f"Docker image '{build_test_image}' should exist but was not found."
        print(f"Image '{build_test_image}' exists with ID: {image.id}")
    except docker.errors.ImageNotFound:
        pytest.fail(f"Docker image '{build_test_image}' was not found.")
    except Exception as e:
        pytest.fail(f"Unexpected error while checking Docker image: {e}")

@pytest.mark.integration
def test_run_all_profile(run_all_profile):
    """
    Test to ensure that the 'run-all' profile is running.
    """
    assert run_all_profile, "The 'run-all' profile should be running."
    print("The 'run-all' profile is running.")

@pytest.mark.integration
def test_client_count_orgs(client):
    """
    Test to ensure that the client is working properly.
    """
    organizations = client.organization.list()['data']
    # There are 3 organizations defined in tests/v6-average-py/server/entities.yaml
    # plus the Root organization.
    assert len(organizations) == 4, "The client should be able to list 3 organizations."

@pytest.mark.integration
def test_ensure_node_mars_online(ensure_node_mars_online):
    """
    Test to ensure that the 'Mars' node is online.
    """
    assert ensure_node_mars_online, "The 'Mars' node should be online."
    print("The 'Mars' node is online.")

@pytest.mark.integration
def test_ensure_all_planetary_nodes_online(ensure_all_planetary_nodes_online):
    """
    Test to ensure that all planetary nodes are online.
    """
    assert ensure_all_planetary_nodes_online, "All planetary nodes should be online."
    print("All planetary nodes are online.")
