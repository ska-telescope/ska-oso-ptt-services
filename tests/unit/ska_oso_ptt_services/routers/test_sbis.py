# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient
from ska_oso_pdm import SBInstance
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.routers.app import (
    create_app,  # Import your create_app function
)
from ska_oso_ptt_services.routers.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)


class TestSBInstanceAPI:
    """This class contains unit tests for the SBInstanceAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Insatnces.
    """

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis._get_sbi_status")
    def test_get_sbis_with_status(self, mock_get_sbi_status, mock_oda):
        """Verifying that get_sbis_with_status API returns All SBIs with status"""
        valid_sbis = load_string_from_file(
            "files/testfile_sample_multiple_sbis_with_status.json"
        )

        sbi_instance = [SBInstance(**x) for x in json.loads(valid_sbis)]

        sbis_mock = mock.MagicMock()
        sbis_mock.query.return_value = sbi_instance
        uow_mock = mock.MagicMock()
        uow_mock.sbis = sbis_mock
        mock_get_sbi_status.return_value = {"current_status": "Created"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/sbis",
            query_string=query_params,
            headers={"accept": "application/json"},
        )
        resultDict = json.loads(result.text)
        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), valid_sbis)

        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_sbis_with_status(self):
        """Verifying that get_sbis_with_status throws error if
        invalid data passed
        """

        query_params = {
            "match_type": "equals",
            "created_before": "2022-03-28T15:43:53.971548+00:00",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
        }

        # Perform the GET request with query parameters using the query_string parameter
        result = client.get(
            f"{API_PREFIX}/sbis",
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

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis._get_sbi_status")
    def test_get_sbi_with_status(self, mock_get_sbi_status, mock_oda):
        """Verifying that get_sbi_with_status API returns requested SBI with status"""

        valid_sbi = load_string_from_file("files/testfile_sample_sbi_with_status.json")

        sbi_mock = mock.MagicMock()
        sbi_mock.model_dump.return_value = json.loads(valid_sbi)
        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.return_value = sbi_mock
        mock_get_sbi_status.return_value = {"current_status": "Created"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5016",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_sbi)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_with_invalid_status(self, mock_oda):
        """Verifying that get_sbi_with_status throws error if invalid data passed"""

        invalid_sbi_id = "invalid-sbi-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbi_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid sbi ID
        result = client.get(
            f"{API_PREFIX}/sbis/{invalid_sbi_id}",
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

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_status_history(self, mock_oda):
        """Verifying that get_sbi_status_history API returns requested
        SBI status history
        """

        valid_sbi_status_history = load_string_from_file(
            "files/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = json.loads(
            valid_sbi_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/status/history/sbis",
            query_string={"entity_id": "sbi-mvp01-20220923-00002", "sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbi_status_history)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_invalid_get_sbi_status_history(self, mock_oda):
        """Verifying that test_invalid_get_sbi_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/status/history/sbis",
            query_string={"entity_id": "sbi-t000-00100", "sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbi-t000-00100 could not be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis._get_sbi_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_status(self, mock_oda, mock_get_sbi_status):
        """Verifying that test_get_sbi_status API returns requested SBI status"""

        valid_sbi_status = load_string_from_file(
            "files/testfile_sample_sbi_status.json"
        )
        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_sbi_status.return_value = json.loads(valid_sbi_status)

        result = client.get(
            f"{API_PREFIX}/status/sbis/sbi-mvp01-20240426-5016",
            query_string={"sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbi_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis._get_sbi_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_invalid_get_sbi_status(self, mock_oda, mock_get_sbi_status):
        """Verifying that get_sbi_status throws error if invalid data passed"""
        invalid_sbi_id = "sbi-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_sbi_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbi_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/status/sbis/{invalid_sbi_id}",
            query_string={"sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbi-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_put_sbi_history(self, mock_oda):
        """Verifying that put_sbi_history updates the sbi status correctly"""
        valid_put_sbi_history_response = load_string_from_file(
            "files/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis = ["sbi-mvp01-20220923-00002"]

        sbis_status_history_mock = mock.MagicMock()

        sbis_status_history_mock.add.return_value = (
            SBIStatusHistory.model_validate_json(valid_put_sbi_history_response)
        )
        uow_mock.sbis_status_history = sbis_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        data = {
            "current_status": "Executing",
            "previous_status": "Created",
            "sbi_version": "1",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            f"{API_PREFIX}/status/sbis/sbi-mvp01-20220923-00002",
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_sbi_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_sbd_history(self):
        """Verifying that put_sbd_history error if invalid data passed"""
        query_params = {"sbd_version": "1"}
        data = {
            "current1_status": "Complete",
            "previous_status": "Draft",
            "sbd_version": "1",
        }

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{API_PREFIX}/status/sbds/sbd-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
