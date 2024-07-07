import datetime
import json
import os
import zoneinfo
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

import pytest
from deepdiff import DeepDiff
from ska_oso_pdm import Metadata, OSOExecutionBlock, SBInstance
from ska_oso_pdm.entity_status_history import OSOEBStatus, OSOEBStatusHistory

from ska_oso_ptt_services.rest import create_app

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-ptt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"


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
    obj_a = json.loads(json_a)  # remains string #result.text
    obj_b = json.loads(json_b)  # converts to list

    diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)

    # Raise an assertion error if there are differences
    assert {} == diff, f"JSON not equal: {diff}"


@pytest.fixture
def client():
    app = create_app()
    with app.app.test_client() as client:
        yield client


class TestExecutionBlockAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, mock_oda, client):
        valid_ebs = load_string_from_file(
            "../files/testfile_sample_multiple_ebs_with_status.json"
        )

        execution_block = [OSOExecutionBlock(**x) for x in json.loads(valid_ebs)]

        ebs_mock = mock.MagicMock()
        ebs_mock.query.return_value = execution_block
        uow_mock = mock.MagicMock()
        uow_mock.ebs = ebs_mock
        mock_get_eb_status.return_value = {"current_status": "fully_observed"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{BASE_API_URL}/ebs",
            query_string=query_params,
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_ebs)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_ebs_with_status(self, client):
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
            f"{BASE_API_URL}/ebs",
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
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_eb_with_status(self, mock_get_eb_status, mock_oda, client):
        valid_eb_with_status = load_string_from_file(
            "../files/testfile_sample_eb_with_status.json"
        )

        eb_mock = mock.MagicMock()
        eb_mock.model_dump.return_value = json.loads(valid_eb_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = eb_mock
        mock_get_eb_status.return_value = {"current_status": "fully_observed"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/ebs/eb-mvp01-20240426-5004",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_eb_with_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_eb_with_invalid_status(self, mock_oda, client):
        invalid_eb_id = "invalid-eb-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid eb ID
        result = client.get(
            f"{BASE_API_URL}/ebs/{invalid_eb_id}",
            headers={"accept": "application/json"},
        )

        # Check if the response contains the expected error message
        expected_error_message = {
            "detail": (
                f"Not Found. The requested identifier {invalid_eb_id} could not be"
                " found."
            )
        }

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.get_json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_eb_status_history(self, mock_oda, client):
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = TestDataFactory.ebefinition() #uow.ebs.get
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(f"{ebS_API_URL}/eb-1234")
        """
        valid_eb_status_history = load_string_from_file(
            "../files/testfile_sample_eb_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = json.loads(
            valid_eb_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/status/history/ebs",
            query_string={"entity_id": "eb-mvp01-20240426-5004", "version": "1"},
        )
        assert_json_is_equal(result.text, valid_eb_status_history)

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_invalid_get_eb_status_history(self, mock_oda, client):
        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/ebs",
            query_string={"entity_id": "eb-t0001-00100", "version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-00100 could not be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_eb_status(self, mock_get_eb_status, client):
        valid_eb_status = load_string_from_file(
            "../files/testfile_sample_eb_status.json"
        )
        mock_get_eb_status.return_value = json.loads(valid_eb_status)

        result = client.get(
            f"{BASE_API_URL}/status/ebs/eb-mvp01-20240426-5004",
            query_string={"version": "1"},
        )

        assert_json_is_equal(result.text, valid_eb_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_invalid_get_eb_status(self, mock_get_eb_status, client):
        invalid_eb_id = "eb-t0001-20240702-00100"
        mock_get_eb_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )

        result = client.get(
            f"{BASE_API_URL}/status/ebs/{invalid_eb_id}",
            query_string={"version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_sbi_history(self, mock_oda, client):
        valid_put_eb_history_response = load_string_from_file(
            "../files/testfile_sample_eb_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ["eb-mvp01-20240426-5004"]

        # Create consistent datetime objects
        created_on = datetime.datetime(
            2024, 7, 2, 18, 1, 47, 873431, tzinfo=zoneinfo.ZoneInfo(key="GMT")
        )
        last_modified_on = datetime.datetime(
            2024, 7, 3, 12, 23, 38, 785233, tzinfo=datetime.timezone.utc
        )

        # Setting up nested mocks
        ebs_status_history_mock = mock.MagicMock()
        ebs_status_history_mock.add.return_value = OSOEBStatusHistory(
            metadata=Metadata(
                version=1,
                created_by="DefaultUser",
                created_on=created_on,
                last_modified_by="DefaultUser",
                last_modified_on=last_modified_on,
            ),
            eb_ref="eb-mvp01-20240426-5004",
            current_status=OSOEBStatus.FULLY_OBSERVED,
            previous_status=OSOEBStatus.CREATED,
        )

        uow_mock.ebs_status_history = ebs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = "/ska-oso-ptt-services/ptt/api/v1/status/ebs/eb-mvp01-20240426-5004"
        params = {"version": "1"}
        data = {"current_status": "fully_observed", "previous_status": "created"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(url, query_string=params, json=data)
        assert_json_is_equal(result.text, valid_put_eb_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_eb_history(self, client):
        query_params = {"version": "1"}
        data = {"current1_status": "fully_observed", "previous_status": "created"}

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
            "traceback": {
                "full_traceback": (
                    "Traceback (most recent call last):\n  File"
                    ' "/home/manish/skao/ska-oso-ptt-services/src/ska_oso_ptt_services/rest/api/resources.py",'
                    " line 67, in wrapper\n    return api_fn(*args, **kwargs)\n  File"
                    ' "/home/manish/skao/ska-oso-ptt-services/src/ska_oso_ptt_services/rest/api/resources.py",'
                    " line 187, in put_eb_history\n   "
                    ' current_status=ebStatus(body["current_status"]),\nKeyError:'
                    " 'current_status'\n"
                ),
                "key": "Internal Server Error",
                "type": "<class 'KeyError'>",
            },
        }

        result = client.put(
            f"{BASE_API_URL}/status/ebs/eb-t0001-20240702-00002",
            query_string=query_params,
            json=data,
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)


class TestSBInstanceAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbi_status")
    def test_get_sbis_with_status(self, mock_get_sbi_status, mock_oda, client):
        valid_sbis = load_string_from_file(
            "../files/testfile_sample_multiple_sbis_with_status.json"
        )

        sbi_instance = [SBInstance(**x) for x in json.loads(valid_sbis)]

        sbis_mock = mock.MagicMock()
        sbis_mock.query.return_value = sbi_instance
        uow_mock = mock.MagicMock()
        uow_mock.sbis = sbis_mock
        mock_get_sbi_status.return_value = {"current_status": "created"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{BASE_API_URL}/sbis",
            query_string=query_params,
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbis)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_sbis_with_status(self, client):
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
            f"{BASE_API_URL}/sbis",
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
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbi_status")
    def test_get_sbi_with_status(self, mock_get_sbi_status, mock_oda, client):
        valid_sbi = load_string_from_file(
            "../files/testfile_sample_sbi_with_status.json"
        )

        sbi_mock = mock.MagicMock()
        sbi_mock.model_dump.return_value = json.loads(valid_sbi)
        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.return_value = sbi_mock
        mock_get_sbi_status.return_value = {"current_status": "created"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/sbis/sbi-mvp01-20240426-5016",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_sbi)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbi_with_invalid_status(self, mock_oda, client):
        invalid_sbi_id = "invalid-sbi-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbi_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid sbi ID
        result = client.get(
            f"{BASE_API_URL}/sbis/{invalid_sbi_id}",
            headers={"accept": "application/json"},
        )

        # Check if the response contains the expected error message
        expected_error_message = {
            "detail": (
                f"Not Found. The requested identifier {invalid_sbi_id} could not be"
                " found."
            )
        }

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.get_json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbi_status_history(self, mock_oda, client):
        valid_sbi_status_history = load_string_from_file(
            "../files/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = json.loads(
            valid_sbi_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/sbis",
            query_string={"entity_id": "sbi-mvp01-20240426-5016", "version": "1"},
        )

        assert_json_is_equal(result.text, valid_sbi_status_history)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_invalid_get_sbi_status_history(self, mock_oda, client):
        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/sbis",
            query_string={"entity_id": "sbi-t000-00100", "version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbi-t000-00100 could not be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbi_status")
    def test_get_sbi_status(self, mock_get_sbi_status, client):
        valid_sbi_status = load_string_from_file(
            "../files/testfile_sample_sbi_status.json"
        )
        mock_get_sbi_status.return_value = json.loads(valid_sbi_status)

        result = client.get(
            f"{BASE_API_URL}/status/sbis/sbi-mvp01-20240426-5016",
            query_string={"version": "1"},
        )

        assert_json_is_equal(result.text, valid_sbi_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbi_status")
    def test_invalid_get_sbi_status(self, mock_get_sbi_status, client):
        invalid_sbi_id = "sbi-t0001-20240702-00100"
        mock_get_sbi_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbi_id} could not be found."
        )

        result = client.get(
            f"{BASE_API_URL}/status/sbis/{invalid_sbi_id}",
            query_string={"version": "1"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbi-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND
