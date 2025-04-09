from http import HTTPStatus

import pytest

from ska_oso_ptt_services.app import API_PREFIX

# TODO need to revisit this test file
# for now Query errors are not raised properly
# need to fix this


@pytest.mark.parametrize(
    "entity_name",
    [
        ("ebs"),
        ("sbis"),
        ("sbds"),
        ("prjs"),
    ],
)
def test_get_invalid_all_entity_with_status(entity_name, client_get):
    """Verifying that get_invalid_all_entity_with_status throws error
    if invalid data passed"""

    query_params = {
        "query_type": "created_between",
        "created_before": "2022-03-28T15:43:53.971548+00:00",
        "created_after": "2022-03-28T15:43:53.971548+00:00",
        "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
        "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
    }

    result_response = client_get(
        f"{API_PREFIX}/{entity_name}", params=query_params
    ).json()

    assert "cannot combine date created query" in result_response["result_data"]


@pytest.mark.parametrize(
    "entity_name, entity_id, entity_data",
    [
        (
            "ebs",
            "eb-mvp01-20240426-5003",
            {
                "current_status": "Fully Observed",
                "previous_status": "Created",
                "eb_ref": "eb-mvp01-20240426-5004",
            },
        ),
        (
            "sbis",
            "sbi-mvp01-20240426-5003",
            {
                "current_status": "Executing",
                "previous_status": "Created",
                "sbi_ref": "sbi-mvp01-20240426-5004",
            },
        ),
        (
            "sbds",
            "sbd-mvp01-20240426-5003",
            {
                "current_status": "Submitted",
                "previous_status": "Draft",
                "sbd_ref": "sbd-mvp01-20240426-5004",
            },
        ),
        (
            "prjs",
            "prj-mvp01-20240426-5003",
            {
                "current_status": "Submitted",
                "previous_status": "Draft",
                "prj_ref": "prj-mvp01-20240426-5004",
            },
        ),
    ],
)
def test_put_entity_mismatch_history(entity_name, entity_id, entity_data, client_put):
    """Verifying that put_entity_mismatch_history throws error
    if invalid data passed"""

    result_response = client_put(
        f"{API_PREFIX}/{entity_name}/{entity_id}/status", json=entity_data
    ).json()

    assert "mismatch between" in result_response["result_data"]
    assert result_response["result_code"] == HTTPStatus.UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "entity_name, entity_id, query_params, entity_data",
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
        ),
    ],
)
def test_put_invalid_all_entity_history(
    entity_name, entity_id, query_params, entity_data, client_put
):
    """Verifying that put_invalid_all_entity_history error if invalid data passed"""

    result = client_put(
        f"{API_PREFIX}/{entity_name}/{entity_id}/status",
        params=query_params,
        json=entity_data,
    ).json()

    assert "detail" in result
    # assert result["result_code"] == HTTPStatus.UNPROCESSABLE_ENTITY
