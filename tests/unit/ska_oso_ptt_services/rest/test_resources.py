import datetime
import json
import os
import zoneinfo
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

import pytest
from deepdiff import DeepDiff
from ska_oso_pdm import Metadata, SBDefinition
from ska_oso_pdm.entity_status_history import SBDStatus, SBDStatusHistory

from ska_oso_ptt_services.rest import create_app

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-ptt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"
SBDS_API_URL = f"{BASE_API_URL}/sbds"


# def normalize_json(json_str):
#     """Normalize JSON string by loading and dumping back to string."""
#     return json.dumps(json.loads(json_str), sort_keys=True)


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json_file.read()
        return json_data


def assert_json_is_equal(json_a, json_b, exclude_paths=None):
    """
    Utility function to compare two JSON objects
    """
    # Load the JSON strings into Python dictionaries
    print("%%%%%%%%%%%%%%%%%%%%%%\n\n\n")
    print(f"type of JSON A, {type(json_a)}")
    print(f"type of JSON A, {type(json_b)}")
    # obj_a = json.loads(json.loads(json_a)) #remains string #result.text
    obj_a = json.loads(json_a)  # remains string #result.text
    obj_b = json.loads(json_b)  # converts to list
    print(f"type of OBJ A, {type(obj_a)}")
    print(f"type of OBJ B, {type(obj_b)}")

    # obj_a = normalize_json(json_a)
    # obj_b = normalize_json(json_b)
    # Compare the objects using DeepDiff
    diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)

    # Raise an assertion error if there are differences
    assert {} == diff, f"JSON not equal: {diff}"


@pytest.fixture
def client():
    # os.chdir("/home/manish/skao/ska-oso-osd")
    app = create_app()
    with app.app.test_client() as client:
        yield client


class TestSBDefinitionAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbds_with_status(self, mock_get_sbd_status, mock_oda, client):
        valid_sbds = load_string_from_file(
            "../files/testfile_sample_multiple_sbds_with_status.json"
        )

        sbd_definitions = [SBDefinition(**x) for x in json.loads(valid_sbds)]

        print(f"working\n\n\n {sbd_definitions=}\n\n\n\n")
        sbds_mock = mock.MagicMock()
        sbds_mock.query.return_value = sbd_definitions
        # sbds_mock.model_dump.return_value = json.loads(valid_sbds)
        uow_mock = mock.MagicMock()
        uow_mock.sbds = sbds_mock
        mock_get_sbd_status.return_value = {"current_status": "draft"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{BASE_API_URL}/sbds",
            query_string=query_params,
            headers={"accept": "application/json"},
        )
        # import pdb
        # pdb.set_trace()
        print(f"==========={result.text}")
        assert_json_is_equal(result.text, valid_sbds)
        assert result.status_code == HTTPStatus.OK


    def test_invalid_get_sbds_with_status(self, client):
        # Define the query parameters
        query_params = {
            "match_type": "equals",
            "created_before": "2022-03-28T15:43:53.971548+00:00",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
        }

        # Perform the GET request with query parameters using the query_string parameter
        result = client.get(
            f"{BASE_API_URL}/sbds",
            query_string=query_params,
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Different query types are not currently supported - for example,"
                " cannot combine date created query or entity query with a user query"
            ),
            "title": "Not Supported",
        }

        assert json.loads(result.text) == error

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbd_with_status(self, mock_get_sbd_status, mock_oda, client):
        valid_sbd = load_string_from_file(
            "../files/testfile_sample_sbd_json_with_status.json"
        )

        sbd_mock = mock.MagicMock()
        sbd_mock.model_dump.return_value = json.loads(valid_sbd)
        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.return_value = sbd_mock
        mock_get_sbd_status.return_value = {"current_status": "complete"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/sbds/sbd-t0001-20240702-00002",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_sbd)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbd_with_invalid_status(self, mock_oda, client):
        invalid_sbd_id = "invalid-sbd-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbd_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid SBD ID
        result = client.get(
            f"{BASE_API_URL}/sbds/{invalid_sbd_id}",
            headers={"accept": "application/json"},
        )

        # Check if the response contains the expected error message
        expected_error_message = {
            "detail": (
                f"Not Found. The requested identifier {invalid_sbd_id} could not be"
                " found."
            )
        }

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.get_json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbd_status_history(self, mock_oda, client):
        valid_sbd_status_history = load_string_from_file(
            "../files/testfile_sample_sbd_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = json.loads(
            valid_sbd_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock
        print("&&&&&&&&&&&&&&&&&&&&&& in test case ")
        result = client.get(
            f"{BASE_API_URL}/status/history/sbds",
            query_string={"entity_id": "sbd-t0001-20240702-00002", "version": "1"},
        )

        assert_json_is_equal(result.text, valid_sbd_status_history)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_invalid_get_sbd_status_history(self, mock_oda, client):
        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/sbds",
            query_string={"entity_id": "sbd-t0001-20240702-00100", "version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbd-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbd_status(self, mock_get_sbd_status, client):
        valid_sbd_status = load_string_from_file(
            "../files/testfile_sample_sbd_status.json"
        )
        # mock_get_sbd_status = mock.MagicMock()
        mock_get_sbd_status.return_value = json.loads(valid_sbd_status)

        result = client.get(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string={"version": "1"},
        )

        assert_json_is_equal(result.text, valid_sbd_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_invalid_get_sbd_status(self, mock_get_sbd_status, client):
        invalid_sbd_id = "sbd-t0001-20240702-00100"
        mock_get_sbd_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbd_id} could not be found."
        )
        # uow_mock = mock.MagicMock()
        # uow_mock.sbds_status_history.query.return_value = []
        # mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/sbds/{invalid_sbd_id}",
            query_string={"version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbd-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    # @mock.patch("ska_oso_ptt_services.rest.api.resources.SBDStatusHistory")
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_sbd_history(self, mock_oda, client):
        valid_put_sbd_history_response = load_string_from_file(
            "../files/testfile_sample_sbd_status.json"
        )

        # mock sbd_status_history
        # mock_sbd_status_history = SBDStatusHistory(metadata=Metadata(version=1, created_by=None, created_on=datetime.datetime(2024, 7, 3, 12, 23, 38, 773706, tzinfo=datetime.timezone.utc), last_modified_by=None, last_modified_on=datetime.datetime(2024, 7, 3, 12, 23, 38, 773750, tzinfo=datetime.timezone.utc)), sbd_ref='sbd-t0001-20240702-00002', current_status=SBDStatus.COMPLETE, previous_status=SBDStatus.DRAFT)

        # Mock oda
        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        # Create consistent datetime objects
        created_on = datetime.datetime(
            2024, 7, 2, 18, 1, 47, 873431, tzinfo=zoneinfo.ZoneInfo(key="GMT")
        )
        last_modified_on = datetime.datetime(
            2024, 7, 3, 12, 23, 38, 785233, tzinfo=datetime.timezone.utc
        )

        # Setting up nested mocks
        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = SBDStatusHistory(
            metadata=Metadata(
                version=1,
                created_by="DefaultUser",
                created_on=created_on,
                last_modified_by="DefaultUser",
                last_modified_on=last_modified_on,
            ),
            sbd_ref="sbd-t0001-20240702-00002",
            current_status=SBDStatus.COMPLETE,
            previous_status=SBDStatus.DRAFT,
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = "/ska-oso-ptt-services/ptt/api/v1/status/sbds/sbd-t0001-20240702-00002"
        params = {"version": "1"}
        data = {"current_status": "complete", "previous_status": "draft"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(url, query_string=params, json=data)
        assert_json_is_equal(result.text, valid_put_sbd_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_sbd_history(self, client):
        query_params = {"version": "1"}
        data = {"current1_status": "complete", "previous_status": "draft"}

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
            "traceback": {
                "full_traceback": (
                    "Traceback (most recent call last):\n  File"
                    ' "/home/manish/skao/ska-oso-ptt-services/src/ska_oso_ptt_services/rest/api/resources.py",'
                    " line 67, in wrapper\n    return api_fn(*args, **kwargs)\n  File"
                    ' "/home/manish/skao/ska-oso-ptt-services/src/ska_oso_ptt_services/rest/api/resources.py",'
                    " line 187, in put_sbd_history\n   "
                    ' current_status=SBDStatus(body["current_status"]),\nKeyError:'
                    " 'current_status'\n"
                ),
                "key": "Internal Server Error",
                "type": "<class 'KeyError'>",
            },
        }

        result = client.put(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string=query_params,
            json=data,
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)

    # print(result.text)
