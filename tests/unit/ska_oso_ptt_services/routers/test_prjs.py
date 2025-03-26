# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

import pytest
from ska_oso_pdm import Project
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

TEST_FILES_PATH = "routers/test_data_files"


class TestProjectAPI:
    """This class contains unit tests for the ProjectAPI resource,
    which is responsible for handling requests related to
    Project.
    """

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs._get_prj_status")
    def test_get_prjs_with_status(self, mock_get_prj_status, mock_oda, client):
        """Verifying that get_prjs_with_status API returns All prjs with status"""
        valid_prjs = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_multiple_prjs_with_status.json"
        )

        project = [Project(**x) for x in json.loads(valid_prjs)]

        prjs_mock = mock.MagicMock()
        prjs_mock.query.return_value = project
        uow_mock = mock.MagicMock()
        uow_mock.prjs = prjs_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/prjs",
            params=query_params,
            headers={"accept": "application/json"},
        )
        resultDict = result.json()

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), json.dumps(json.loads(valid_prjs)))
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    def test_invalid_get_prjs_with_status(self, client):
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
            params=query_params,
            headers={"accept": "application/json"},
        )

        error = {
            "detail": "Different query types are not currently supported"
            " - for example, "
            "cannot combine date created query or entity query with a user query"
        }

        assert json.loads(result.json()) == error

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs._get_prj_status")
    def test_get_prj_with_status(self, mock_get_prj_status, mock_oda, client):
        """Verifying that get_prj_with_status API returns requested prj with status"""
        valid_prj_with_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_with_status.json"
        )

        prj_mock = mock.MagicMock()
        prj_mock.model_dump.return_value = json.loads(valid_prj_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.return_value = prj_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.json(), valid_prj_with_status)
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_prj_with_invalid_status(self, mock_oda, client):
        """Verifying that get_prj_with_status throws error if invalid data passed"""
        invalid_prj_id = "invalid-prj-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_prj_id} could not be found."
        )
        mock_oda.uow().__enter__.return_value = uow_mock

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

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_prj_status_history(self, mock_oda, client):
        """Verifying that get_prj_status_history API returns requested
        prj status history
        """
        valid_prj_status_history = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = json.loads(
            valid_prj_status_history
        )
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/prjs/status/history",
            params={"entity_id": "prj-mvp01-20220923-00001", "prj_version": "1"},
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.json(), valid_prj_status_history)

        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_invalid_get_prj_status_history(self, mock_oda, client):
        """Verifying that test_invalid_get_prj_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/prjs/status/history",
            params={"entity_id": "prj-t0001-00100", "prj_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier prj-t0001-00100 could not be"
                " found."
            )
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs._get_prj_status")
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_prj_status(self, mock_oda, mock_get_prj_status, client):
        """Verifying that test_prj_sbd_status API returns requested prj status"""

        valid_prj_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_prj_status.return_value = json.loads(valid_prj_status)

        result = client.get(
            f"{API_PREFIX}/prjs/prj-mvp01-20240426-5004/status",
            params={"prj_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.json(), valid_prj_status)
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs._get_prj_status")
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_invalid_get_prj_status(self, mock_oda, mock_get_prj_status, client):
        """Verifying that get_prj_status throws error if invalid data passed"""
        invalid_prj_id = "prj-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_prj_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_prj_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/prjs/{invalid_prj_id}/status",
            params={"prj_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier prj-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history(self, mock_oda, client):
        """Verifying that put_prj_history updates the prj status correctly"""
        valid_put_prj_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(valid_put_prj_history_response)
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status"
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
        )
        assert_json_is_equal(
            result.json(), valid_put_prj_history_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history_with_two_version(self, mock_oda, client):
        """Verifying that put_prj_history updates the prj status correctly"""
        valid_put_prj_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(valid_put_prj_history_response)
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status"
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
        )
        assert_json_is_equal(
            result.json(), valid_put_prj_history_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

        valid_put_prj_history_version_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_prj_status_version.json"
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
        mock_oda.uow().__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status"
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
        )
        assert_json_is_equal(
            result.json(), valid_put_prj_history_version_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

    @pytest.mark.skip()
    def test_invalid_put_prj_history(self, client):
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
            f"{API_PREFIX}/prjs/prj-t0001-20240702-00002/status",
            params=query_params,
            json=data,
        )

        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.json(), json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
