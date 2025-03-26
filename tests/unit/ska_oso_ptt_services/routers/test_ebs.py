import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import OSOEBStatusHistory, OSOExecutionBlock

from ska_oso_ptt_services.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

TEST_FILES_PATH = "routers/test_data_files"


class TestExecutionBlockAPI:
    """This class contains unit tests for the ExecutionBlockAPI resource,
    which is responsible for handling requests related to
    Execution Block.
    """

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, mock_oda, client):
        """Verifying that get_ebs_with_status API returns All EBs with status"""
        valid_ebs = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_multiple_ebs_with_status.json"
        )

        execution_block = [OSOExecutionBlock(**x) for x in json.loads(valid_ebs)]

        ebs_mock = mock.MagicMock()
        ebs_mock.query.return_value = execution_block
        uow_mock = mock.MagicMock()
        uow_mock.ebs = ebs_mock
        mock_get_eb_status().current_status = "Fully Observed"
        mock_oda.uow().__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/ebs",
            params=query_params,
            headers={"accept": "application/json"},
        )

        resultDict = result.json()

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), json.dumps(json.loads(valid_ebs)))

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    def test_get_eb_with_status(self, mock_get_eb_status, mock_oda, client):
        """Verifying that get_eb_with_status API returns requested EB with status"""
        valid_eb_with_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_eb_with_status.json"
        )

        eb_mock = mock.MagicMock()
        eb_mock.model_dump.return_value = json.loads(valid_eb_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = eb_mock

        mock_get_eb_status().current_status = "Fully Observed"
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004",
            headers={"accept": "application/json"},
        )
        result_json = json.dumps(result.json())

        assert_json_is_equal(
            result_json,
            valid_eb_with_status,
            exclude_paths=["root['metadata']['pdm_version']"],
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_eb_with_invalid_status(self, mock_oda, client):
        """Verifying that get_eb_with_status throws error if invalid data passed"""
        invalid_eb_id = "invalid-eb-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )
        mock_oda.uow().__enter__.return_value = uow_mock

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

        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert result.json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_eb_status_history(self, mock_oda, client):
        """Verifying that get_eb_status_history API returns requested
        EB status history
        """
        valid_eb_status_history = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_eb_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = json.loads(
            valid_eb_status_history
        )

        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004/status",
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(json.dumps(result.json()), valid_eb_status_history)

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_invalid_get_eb_status_history(self, mock_oda, client):
        """Verifying that test_invalid_get_eb_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/ebs/status/history",
            params={"entity_id": "eb-t0001-00100", "eb_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-00100 could not be found."
            )
        }

        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_eb_status(self, mock_oda, mock_get_eb_status, client):
        """Verifying that test_eb_sbd_status API returns requested EB status"""

        valid_eb_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_eb_status.json"
        )

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_eb_status.return_value = json.loads(valid_eb_status)

        result = client.get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004/status",
            params={"eb_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.json(), valid_eb_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_invalid_get_eb_status(self, mock_oda, mock_get_eb_status, client):
        """Verifying that get_eb_status throws error if invalid data passed"""
        invalid_eb_id = "eb-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_eb_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_eb_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/ebs/{invalid_eb_id}/status",
            params={"eb_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier eb-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_put_eb_history(self, mock_oda, client):
        """Verifying that put_eb_history updates the eb status correctly"""
        valid_put_eb_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_eb_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ["eb-mvp01-20240426-5004"]

        ebs_status_history_mock = mock.MagicMock()
        ebs_status_history_mock.add.return_value = (
            OSOEBStatusHistory.model_validate_json(valid_put_eb_history_response)
        )

        uow_mock.ebs_status_history = ebs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        url = f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004/status"
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
        )
        assert_json_is_equal(
            result.json(), valid_put_eb_history_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK
