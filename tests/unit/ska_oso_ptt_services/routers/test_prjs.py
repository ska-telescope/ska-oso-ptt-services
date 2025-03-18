# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient
from ska_oso_pdm import Project
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

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


class TestProjectAPI:
    """This class contains unit tests for the ProjectAPI resource,
    which is responsible for handling requests related to
    Project.
    """

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.api.prjs._get_prj_status")
    def test_get_prjs_with_status(self, mock_get_prj_status, mock_oda):
        """Verifying that get_prjs_with_status API returns All prjs with status"""
        valid_prjs = load_string_from_file(
            "files/testfile_sample_multiple_prjs_with_status.json"
        )

        project = [Project(**x) for x in json.loads(valid_prjs)]

        prjs_mock = mock.MagicMock()
        prjs_mock.query.return_value = project
        uow_mock = mock.MagicMock()
        uow_mock.prjs = prjs_mock
        mock_get_prj_status.return_value = {"current_status": "Draft"}
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/prjs",
            query_string=query_params,
            headers={"accept": "application/json"},
        )
        resultDict = json.loads(result.text)

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), valid_prjs)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_prjs_with_status(self):
        """Verifying that get_prjs_with_status throws error if invalid data passed"""

        query_params = {
            "match_type": "equals",
            "created_before": "2022-03-28T15:43:53.971548+00:00",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
        }

        # Perform the GET request with query parameters using the query_string parameter
        result = client.get(
            f"{API_PREFIX}/prjs",
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

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.api.prjs._get_prj_status")
    def test_get_prj_with_status(self, mock_get_prj_status, mock_oda):
        """Verifying that get_prj_with_status API returns requested prj with status"""
        valid_prj_with_status = load_string_from_file(
            "files/testfile_sample_prj_with_status.json"
        )

        prj_mock = mock.MagicMock()
        prj_mock.model_dump.return_value = json.loads(valid_prj_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.return_value = prj_mock
        mock_get_prj_status.return_value = {"current_status": "Draft"}
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_prj_with_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_get_prj_with_invalid_status(self, mock_oda):
        """Verifying that get_prj_with_status throws error if invalid data passed"""
        invalid_prj_id = "invalid-prj-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_prj_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        # Perform the GET request with the invalid eb ID
        result = client.get(
            f"{API_PREFIX}/prjs/{invalid_prj_id}",
            headers={"accept": "application/json"},
        )

        # Check if the response contains the expected error message
        expected_error_message = {
            "detail": (
                f"Not Found. The requested identifier {invalid_prj_id} could not be"
                " found."
            )
        }

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.get_json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_get_prj_status_history(self, mock_oda):
        """Verifying that get_prj_status_history API returns requested
        prj status history
        """
        valid_prj_status_history = load_string_from_file(
            "files/testfile_sample_prj_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = json.loads(
            valid_prj_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/status/history/prjs",
            query_string={"entity_id": "prj-mvp01-20220923-00001", "prj_version": "1"},
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_prj_status_history)

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_invalid_get_prj_status_history(self, mock_oda):
        """Verifying that test_invalid_get_prj_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/status/history/prjs",
            query_string={"entity_id": "prj-t0001-00100", "prj_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier prj-t0001-00100 could not be"
                " found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.api.prjs._get_prj_status")
    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_get_prj_status(self, mock_oda, mock_get_prj_status):
        """Verifying that test_prj_sbd_status API returns requested prj status"""

        valid_prj_status = load_string_from_file(
            "files/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_prj_status.return_value = json.loads(valid_prj_status)

        result = client.get(
            f"{API_PREFIX}/status/prjs/prj-mvp01-20240426-5004",
            query_string={"prj_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_prj_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.prjs._get_prj_status")
    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_invalid_get_prj_status(self, mock_oda, mock_get_prj_status):
        """Verifying that get_prj_status throws error if invalid data passed"""
        invalid_prj_id = "prj-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow.__enter__.return_value = uow_mock

        mock_get_prj_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_prj_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/status/prjs/{invalid_prj_id}",
            query_string={"prj_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier prj-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_put_prj_history(self, mock_oda):
        """Verifying that put_prj_history updates the prj status correctly"""
        valid_put_prj_history_response = load_string_from_file(
            "files/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(valid_put_prj_history_response)
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/status/prjs/prj-mvp01-20220923-00001"
        data = {
            "current_status": "Draft",
            "previous_status": "Draft",
            "prj_version": "1",
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
        print("qqqqqqqqqqqqqqqqqqqqqqqq", result.text)
        assert_json_is_equal(result.text, valid_put_prj_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.api.prjs.oda")
    def test_put_prj_history_with_two_version(self, mock_oda):
        """Verifying that put_prj_history updates the prj status correctly"""
        valid_put_prj_history_response = load_string_from_file(
            "files/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(valid_put_prj_history_response)
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/status/prjs/prj-mvp01-20220923-00001"
        data = {
            "current_status": "Draft",
            "previous_status": "Draft",
            "prj_version": "1",
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
        assert_json_is_equal(result.text, valid_put_prj_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

        valid_put_prj_history_version_response = load_string_from_file(
            "files/testfile_sample_prj_status_version.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(
                valid_put_prj_history_version_response
            )
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/status/prjs/prj-mvp01-20220923-00001"
        data = {
            "current_status": "Submitted",
            "previous_status": "Draft",
            "prj_version": "2",
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
        assert_json_is_equal(
            result.text, valid_put_prj_history_version_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_prj_history(self):
        """Verifying that put_prj_history error if invalid data passed"""
        query_params = {"prj_version": "1"}
        data = {
            "current1_status": "Submitted",
            "previous_status": "Draft",
            "prj_version": "1",
        }

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{API_PREFIX}/status/prjs/prj-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )

        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR

    def test_get_sbi_entity_status(self):
        """Verifying that get_entity_status API returns correct status
        values for SBI entity
        """

        result_sbi = client.get(
            f"{API_PREFIX}/get_entity?entity_name=sbi",
        )

        expected_sbi_response = {
            "CREATED": "Created",
            "EXECUTING": "Executing",
            "FAILED": "Failed",
            "OBSERVED": "Observed",
        }

        assert_json_is_equal(result_sbi.text, json.dumps(expected_sbi_response))

    def test_get_eb_entity_status(self):
        """Verifying that get_entity_status API returns correct status
        values for EB entity
        """

        result_eb = client.get(
            f"{API_PREFIX}/get_entity?entity_name=eb",
        )

        expected_eb_response = {
            "CREATED": "Created",
            "FULLY_OBSERVED": "Fully Observed",
            "FAILED": "Failed",
        }

        assert_json_is_equal(result_eb.text, json.dumps(expected_eb_response))

    def test_get_sbd_entity_status(self):
        """Verifying that get_entity_status API returns correct status values
        for SBD entity
        """

        result_sbd = client.get(
            f"{API_PREFIX}/get_entity?entity_name=sbd",
        )

        expected_sbd_response = {
            "DRAFT": "Draft",
            "SUBMITTED": "Submitted",
            "READY": "Ready",
            "IN_PROGRESS": "In Progress",
            "OBSERVED": "Observed",
            "SUSPENDED": "Suspended",
            "FAILED_PROCESSING": "Failed Processing",
            "COMPLETE": "Complete",
        }

        assert_json_is_equal(result_sbd.text, json.dumps(expected_sbd_response))

    def test_get_prj_entity_status(self):
        """Verifying that get_entity_status API returns correct status
        values for Project entity
        """

        result_prj = client.get(
            f"{API_PREFIX}/get_entity?entity_name=prj",
        )

        expected_prj_response = {
            "DRAFT": "Draft",
            "SUBMITTED": "Submitted",
            "READY": "Ready",
            "IN_PROGRESS": "In Progress",
            "OBSERVED": "Observed",
            "COMPLETE": "Complete",
            "CANCELLED": "Cancelled",
            "OUT_OF_TIME": "Out of Time",
        }

        assert_json_is_equal(result_prj.text, json.dumps(expected_prj_response))

    def test_get_invalid_entity_status(self):
        """Verifying that get_entity_status API returns error for invalid entity"""

        # Test SBI status
        result_invalid_entity = client.get(
            f"{API_PREFIX}/get_entity?entity_name=ebi",
        )
        result_json = json.loads(result_invalid_entity.text)["detail"]
        expected_eb_response = (
            "ValueError('Invalid entity name: ebi') with args ('Invalid entity name:"
            " ebi',)"
        )

        assert result_json == expected_eb_response
