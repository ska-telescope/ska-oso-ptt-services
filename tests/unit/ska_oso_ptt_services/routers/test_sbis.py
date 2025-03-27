# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import SBInstance
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

TEST_FILES_PATH = "routers/test_data_files"


class TestSBInstanceAPI:
    """This class contains unit tests for the SBInstanceAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Instances.
    """

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    def test_get_sbis_with_status(self, mock_get_sbi_status, mock_oda, client):
        """Verifying that get_sbis_with_status API returns All SBIs with status"""
        valid_sbis = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_multiple_sbis_with_status.json"
        )

        sbi_instance = [SBInstance(**x) for x in json.loads(valid_sbis)]

        sbis_mock = mock.MagicMock()
        sbis_mock.query.return_value = sbi_instance
        uow_mock = mock.MagicMock()
        uow_mock.sbis = sbis_mock
        mock_get_sbi_status().current_status = "Created"
        mock_oda.uow().__enter__.return_value = uow_mock

        # Perform the GET request with query parameters using the query_string parameter
        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/sbis",
            params=query_params,
            headers={"accept": "application/json"},
        )
        resultDict = result.json()

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), json.dumps(json.loads(valid_sbis)))

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    def test_get_sbi_with_status(self, mock_get_sbi_status, mock_oda, client):
        """Verifying that get_sbi_with_status API returns requested SBI with status"""

        valid_sbi = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbi_with_status.json"
        )

        sbi_mock = mock.MagicMock()
        sbi_mock.model_dump.return_value = json.loads(valid_sbi)
        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.return_value = sbi_mock
        mock_get_sbi_status().current_status = "Created"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5016",
            headers={"accept": "application/json"},
        )
        result_json = json.dumps(result.json())

        assert_json_is_equal(
            json.dumps(result_json),
            json.dumps(json.loads(valid_sbi)),
            exclude_paths=["root['metadata']['pdm_version']"],
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_with_invalid_status(self, mock_oda, client):
        """Verifying that get_sbi_with_status throws error if invalid data passed"""

        invalid_sbi_id = "invalid-sbi-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.side_effect = ODANotFound(identifier=invalid_sbi_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        # Perform the GET request with the invalid sbi ID
        result = client.get(
            f"{API_PREFIX}/sbis/{invalid_sbi_id}",
            headers={"accept": "application/json"},
        )

        # Check if the response contains the expected error message
        expected_error_message = {
            "detail": (f"The requested identifier {invalid_sbi_id} could not be found.")
        }

        assert result.status_code == HTTPStatus.NOT_FOUND
        assert result.json() == expected_error_message

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_status_history(self, mock_oda, client):
        """Verifying that get_sbi_status_history API returns requested
        SBI status history
        """

        valid_sbi_status_history = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = json.loads(
            valid_sbi_status_history
        )
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/sbis/status/history",
            params={"entity_id": "sbi-mvp01-20220923-00002", "sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.json(), valid_sbi_status_history)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_invalid_get_sbi_status_history(self, mock_oda, client):
        """Verifying that test_invalid_get_sbi_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/sbis/status/history",
            params={"entity_id": "sbi-t000-00100", "sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": ("The requested identifier sbi-t000-00100 could not be found.")
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_sbi_status(self, mock_oda, mock_get_sbi_status, client):
        """Verifying that test_get_sbi_status API returns requested SBI status"""

        valid_sbi_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbi_status.json"
        )
        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_sbi_status.return_value = json.loads(valid_sbi_status)

        result = client.get(
            f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5016/status",
            params={"sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.json(), valid_sbi_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_invalid_get_sbi_status(self, mock_oda, mock_get_sbi_status, client):
        """Verifying that get_sbi_status throws error if invalid data passed"""
        invalid_sbi_id = "sbi-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_sbi_status.side_effect = ODANotFound(identifier=invalid_sbi_id)

        result = client.get(
            f"{API_PREFIX}/sbis/{invalid_sbi_id}/status",
            params={"sbi_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "The requested identifier sbi-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_put_sbi_history(self, mock_oda, client):
        """Verifying that put_sbi_history updates the sbi status correctly"""
        valid_put_sbi_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis = ["sbi-mvp01-20220923-00002"]

        sbis_status_history_mock = mock.MagicMock()

        sbis_status_history_mock.add.return_value = (
            SBIStatusHistory.model_validate_json(valid_put_sbi_history_response)
        )
        uow_mock.sbis_status_history = sbis_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Executing",
            "previous_status": "Created",
            "sbi_ref": "sbi-mvp01-20220923-00002",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            f"{API_PREFIX}/sbis/sbi-mvp01-20220923-00002/status",
            json=data,
        )

        assert_json_is_equal(
            json.dumps(result.json()),
            json.dumps(json.loads(valid_put_sbi_history_response)),
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK
