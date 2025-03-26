import json

import pytest

from ska_oso_ptt_services.app import API_PREFIX

common_error = {
    "detail": "Different query types are not currently supported"
    " - for example, "
    "cannot combine date created query or entity query with a user query"
}


@pytest.mark.parametrize(
    "entity_name, expected_response",
    [
        ("ebs", common_error),
        ("sbis", common_error),
        ("sbds", common_error),
        ("prjs", common_error),
    ],
)
def test_invalid_get_prjs_with_status(entity_name, expected_response, client):
    """Verifying that get_prjs_with_status throws error if invalid data passed"""

    query_params = {
        "match_type": "equals",
        "created_before": "2022-03-28T15:43:53.971548+00:00",
        "created_after": "2022-03-28T15:43:53.971548+00:00",
        "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
        "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
    }

    result_response = client.get(
        f"{API_PREFIX}/{entity_name}",
        params=query_params,
        headers={"accept": "application/json"},
    )

    assert json.dumps(result_response.json()), json.dumps(json.loads(expected_response))
