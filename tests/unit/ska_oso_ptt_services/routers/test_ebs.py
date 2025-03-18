# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient
from ska_oso_pdm import OSOExecutionBlock
from ska_oso_pdm.entity_status_history import OSOEBStatusHistory

from ska_oso_ptt_services.routers.app import (
    create_app,  # Import your create_app function
)
from ska_oso_ptt_services.routers.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.util import (
    assert_json_is_equal,
    load_string_from_file,
)

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


class TestExecutionBlockAPI:
    """This class contains unit tests for the ExecutionBlockAPI resource,
    which is responsible for handling requests related to
    Execution Block.
    """

    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.api.ebs._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, mock_oda):
        """Verifying that get_ebs_with_status API returns All EBs with status"""
        valid_ebs = load_string_from_file(
            "files/testfile_sample_multiple_ebs_with_status.json"
        )

        execution_block = [OSOExecutionBlock(**x) for x in json.loads(valid_ebs)]

        ebs_mock = mock.MagicMock()
        ebs_mock.query.return_value = execution_block
        uow_mock = mock.MagicMock()
        uow_mock.ebs = ebs_mock
        mock_get_eb_status.return_value = {"current_status": "Fully Observed"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/ebs",
            query_string=query_params,
            headers={"accept": "application/json"},
        )
        resultDict = json.loads(result.text)

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), valid_ebs)

        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_ebs_with_status(self):
        """Verifying that get_ebs_with_status throws error if invalid data passed"""

        query_params = {
            "match_type": "equals",
            "created_before": "2022-03-28T15:43:53.971548+00:00",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
        }

        # Perform the GET request with query parameters using the query_string parameter
        result = client.get(
            f"{API_PREFIX}/ebs",
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

    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.api.ebs._get_eb_status")
    def test_get_eb_with_status(self, mock_get_eb_status, mock_oda):
        """Verifying that get_eb_with_status API returns requested EB with status"""
        valid_eb_with_status = load_string_from_file(
            "files/testfile_sample_eb_with_status.json"
        )

        eb_mock = mock.MagicMock()
        eb_mock.model_dump.return_value = json.loads(valid_eb_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = eb_mock
        mock_get_eb_status.return_value = {"current_status": "Fully Observed"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_eb_with_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.ebs")
    def test_get_eb_with_invalid_status(self, mock_oda):
        """Verifying that get_eb_with_status throws error if invalid data passed"""
        invalid_eb_id = "invalid-eb-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid eb ID
        result = client.get(
            f"{API_PREFIX}/ebs/{invalid_eb_id}",
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

    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    def test_get_eb_status_history(self, mock_oda):
        """Verifying that get_eb_status_history API returns requested
        EB status history
        """
        valid_eb_status_history = load_string_from_file(
            "files/testfile_sample_eb_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = json.loads(
            valid_eb_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/status/history/ebs",
            query_string={"entity_id": "eb-mvp01-20240426-5004", "eb_version": "1"},
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_eb_status_history)

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    def test_invalid_get_eb_status_history(self, mock_oda):
        """Verifying that test_invalid_get_eb_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/status/history/ebs",
            query_string={"entity_id": "eb-t0001-00100", "eb_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-00100 could not be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.api.ebs._get_eb_status")
    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    def test_get_eb_status(self, mock_oda, mock_get_eb_status):
        """Verifying that test_eb_sbd_status API returns requested EB status"""

        valid_eb_status = load_string_from_file("files/testfile_sample_eb_status.json")

        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_eb_status.return_value = json.loads(valid_eb_status)

        result = client.get(
            f"{API_PREFIX}/status/ebs/eb-mvp01-20240426-5004",
            query_string={"eb_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_eb_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.ebs._get_eb_status")
    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    def test_invalid_get_eb_status(self, mock_oda, mock_get_eb_status):
        """Verifying that get_eb_status throws error if invalid data passed"""
        invalid_eb_id = "eb-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_eb_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/status/ebs/{invalid_eb_id}",
            query_string={"eb_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.api.ebs.oda")
    def test_put_eb_history(self, mock_oda):
        """Verifying that put_eb_history updates the eb status correctly"""
        valid_put_eb_history_response = load_string_from_file(
            "files/testfile_sample_eb_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ["eb-mvp01-20240426-5004"]

        ebs_status_history_mock = mock.MagicMock()
        ebs_status_history_mock.add.return_value = (
            OSOEBStatusHistory.model_validate_json(valid_put_eb_history_response)
        )

        uow_mock.ebs_status_history = ebs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/status/ebs/eb-mvp01-20240426-5004"
        data = {
            "current_status": "Fully Observed",
            "previous_status": "Created",
            "eb_version": "1",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            url,
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_eb_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_eb_history(self):
        """Verifying that put_eb_history error if invalid data passed"""
        query_params = {"eb_version": "1"}
        data = {
            "current1_status": "Fully Observed",
            "previous_status": "Created",
            "eb_version": "1",
        }

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{API_PREFIX}/status/ebs/eb-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )

        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
