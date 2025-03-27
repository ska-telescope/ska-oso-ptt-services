from http import HTTPStatus

import pytest

from ska_oso_ptt_services.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal

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
def test_get_invalid_all_entity_with_status(entity_name, expected_response, client):
    """Verifying that get_invalid_all_entity_with_status throws error
    if invalid data passed"""

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
    ).json()

    assert_json_is_equal(result_response, expected_response)


@pytest.mark.parametrize(
    "entity_name, entity_id, query_params, entity_data, expected_error",
    [
        (
            "prjs",
            "prj-t0001-20240702-00002",
            {"prj_version": "1"},
            {
                "current1_status": "Submitted",
                "previous_status": "Draft",
                "prj_version": "1",
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "prj_ref"],
                        "msg": "Field required",
                        "input": {
                            "current1_status": "Submitted",
                            "previous_status": "Draft",
                            "prj_version": "1",
                        },
                    }
                ]
            },
        ),
        (
            "sbds",
            "sbd-t0001-20240702-00002",
            {"sbd_version": "1"},
            {
                "current1_status": "Complete",
                "previous_status": "Draft",
                "sbd_version": "1",
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "sbd_ref"],
                        "msg": "Field required",
                        "input": {
                            "current1_status": "Complete",
                            "previous_status": "Draft",
                            "sbd_version": "1",
                        },
                    }
                ]
            },
        ),
        (
            "sbis",
            "sbi-t0001-20240702-00002",
            {"sbi_version": "1"},
            {
                "current1_status": "Executing",
                "previous_status": "Created",
                "sbi_version": "1",
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "sbi_ref"],
                        "msg": "Field required",
                        "input": {
                            "current1_status": "Executing",
                            "previous_status": "Created",
                            "sbi_version": "1",
                        },
                    }
                ]
            },
        ),
        (
            "ebs",
            "eb-t0001-20240702-00002",
            {"eb_version": "1"},
            {
                "current1_status": "Fully Observed",
                "previous_status": "Created",
                "eb_version": "1",
            },
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "eb_ref"],
                        "msg": "Field required",
                        "input": {
                            "current1_status": "Fully Observed",
                            "previous_status": "Created",
                            "eb_version": "1",
                        },
                    }
                ]
            },
        ),
    ],
)
def test_put_invalid_all_entity_history(
    entity_name, entity_id, query_params, entity_data, expected_error, client
):
    """Verifying that put_invalid_all_entity_history error if invalid data passed"""

    result = client.put(
        f"{API_PREFIX}/{entity_name}/{entity_id}/status",
        params=query_params,
        json=entity_data,
    )

    assert_json_is_equal(result.json(), expected_error)
    assert result.status_code == HTTPStatus.UNPROCESSABLE_ENTITY
