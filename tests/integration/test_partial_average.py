import json
import pytest

@pytest.mark.integration
def test_partial_average(client, run_all_profile, build_test_image, ensure_node_mars_online):
    """Test the 'partial_average' method using the 'run-all' profile."""
    input_ = {
        'method': 'partial_average',
        'kwargs': {'column_name': 'value'}
    }

    # For node 'Mars' get the org id and collab id
    response = client.node.list(is_online=True)
    nodes = response.get("data", [])
    # FIXME: ignoring pagination here
    node_name = 'Mars - Planets Development Node'
    mars_node = next((node for node in nodes if node.get("name") == node_name), None)

    org_id = mars_node["organization"]["id"]
    collab_id = mars_node["collaboration"]["id"]

    task = client.task.create(
        collaboration=collab_id,
        organizations=[org_id],
        name="letters-partial-average-task",
        image=build_test_image,
        description='Test task, partial average on Mars',
        databases=[{'label': 'letters'}],
        input_=input_
    )

    client.wait_for_results(task['id'])
    results = client.result.from_task(task_id=task['id'])
    output_values = [data['result'] for data in results['data']]

    # result from algorithm is a json string
    result = json.loads(output_values[0])

    # the letters.csv is made up of the decimal representation of the
    # characters in 'mars'
    org_name = 'mars'
    assert result['sum'] == sum(map(lambda x: ord(x), org_name))
    assert result['count'] == len(org_name)
