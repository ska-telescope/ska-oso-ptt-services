from http import HTTPStatus

import pytest

from ska_oso_ptt_services.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


@pytest.mark.parametrize(
    "entity_name, expected_response",
    [
        (
            "eb",
            {
                "entity_type": "eb",
                "statuses": {
                    "CREATED": "Created",
                    "FULLY_OBSERVED": "Fully Observed",
                    "FAILED": "Failed",
                },
            },
        ),
        (
            "sbi",
            {
                "entity_type": "sbi",
                "statuses": {
                    "CREATED": "Created",
                    "EXECUTING": "Executing",
                    "FAILED": "Failed",
                    "OBSERVED": "Observed",
                },
            },
        ),
        (
            "sbd",
            {
                "entity_type": "sbd",
                "statuses": {
                    "DRAFT": "Draft",
                    "SUBMITTED": "Submitted",
                    "READY": "Ready",
                    "IN_PROGRESS": "In Progress",
                    "OBSERVED": "Observed",
                    "SUSPENDED": "Suspended",
                    "FAILED_PROCESSING": "Failed Processing",
                    "COMPLETE": "Complete",
                },
            },
        ),
        (
            "prj",
            {
                "entity_type": "prj",
                "statuses": {
                    "DRAFT": "Draft",
                    "SUBMITTED": "Submitted",
                    "READY": "Ready",
                    "IN_PROGRESS": "In Progress",
                    "OBSERVED": "Observed",
                    "COMPLETE": "Complete",
                    "CANCELLED": "Cancelled",
                    "OUT_OF_TIME": "Out of Time",
                },
            },
        ),
    ],
)
def test_entity_status_api(entity_name: str, expected_response, client_get):
    """Parametrized Test cases for status/get_entity API.

    Args:
        entity_name (str): entity name in string format
        expected_response (dict): dictionary of entity and its statutes
        client_get (TestClient): TestClient for FastAPI
    """

    result_response = client_get(
        f"{API_PREFIX}/status/get_entity?entity_name={entity_name}"
    ).json()

    assert_json_is_equal(result_response["result_data"][0], expected_response)
    assert result_response["result_code"] == HTTPStatus.OK


def test_get_invalid_entity_status(client_get):
    """Verifying that get_entity_status API returns error for invalid entity"""

    result_invalid_entity = client_get(
        f"{API_PREFIX}/status/get_entity?entity_name=ebi"
    ).json()

    assert "requested entity" in result_invalid_entity["result_data"]
    assert result_invalid_entity["result_code"] == HTTPStatus.NOT_FOUND
