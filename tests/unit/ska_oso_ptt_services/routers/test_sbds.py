# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import SBDefinition
from ska_oso_pdm.entity_status_history import SBDStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

TEST_FILES_PATH = "routers/test_data_files"


class TestSBDefinitionAPI:
    """This class contains unit tests for the SBDefinitionAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Definitions.
    """

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbds._get_sbd_status")
    def test_get_sbds_with_status(self, mock_get_sbd_status, mock_oda, client):
        """Verifying that get_sbds_with_status API returns All SBDS with status"""

        valid_sbds = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_multiple_sbds_with_status.json"
        )

        sbd_definitions = [SBDefinition(**sbd) for sbd in json.loads(valid_sbds)]
        sbds_mock = mock.MagicMock()
        sbds_mock.query.return_value = sbd_definitions
        uow_mock = mock.MagicMock()
        uow_mock.sbds = sbds_mock
        mock_get_sbd_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{API_PREFIX}/sbds",
            params=query_params,
            headers={"accept": "application/json"},
        )

        resultDict = result.json()
        for res in resultDict:
            del res["metadata"]["pdm_version"]
            # del res["targets"]["reference_coordinate"]["epoch"]

        assert_json_is_equal(result.text, valid_sbds)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbds._get_sbd_status")
    def test_get_sbd_with_status(self, mock_get_sbd_status, mock_oda, client):
        """Verifying that get_sbd_with_status API returns requested SBD with status"""
        valid_sbd = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_json_with_status.json"
        )

        sbd_mock = mock.MagicMock()
        sbd_mock.model_dump.return_value = json.loads(valid_sbd)
        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.return_value = sbd_mock
        mock_get_sbd_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002",
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(
            result.text,
            valid_sbd,
            exclude_regex_paths={r"root\[\d+\]\['metadata'\]\['(pdm_version)'\]"},
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_sbd_with_invalid_status(self, mock_oda, client):
        """Verifying that get_sbd_with_status throws error if invalid data passed"""

        invalid_sbd_id = "invalid-sbd-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.side_effect = ODANotFound(identifier=invalid_sbd_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbds/{invalid_sbd_id}",
            headers={"accept": "application/json"},
        )

        error = {
            "detail": "The requested identifier invalid-sbd-id-12345 "
            "could not be found."
        }

        assert result.json() == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_sbd_status_history(self, mock_oda, client):
        """Verifying that get_sbd_status_history API returns requested
        SBD status history
        """
        valid_sbd_status_history = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = json.loads(
            valid_sbd_status_history
        )
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbds/status/history",
            params={"entity_id": "sbd-t0001-20240702-00002", "sbd_version": "1"},
            headers={"accept": "application/json"},
        )
        result_dict = result.json()

        assert_json_is_equal(
            json.dumps(result_dict),
            valid_sbd_status_history,
            exclude_regex_paths={
                r"root\[\d+\]\['metadata'\]\['(pdm_version|version)'\]"
            },
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_invalid_get_sbd_status_history(self, mock_oda, client):
        """Verifying that test_invalid_get_sbd_status_history throws error
        if invalid data passed
        """
        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client.get(
            f"{API_PREFIX}/sbds/status/history",
            params={"entity_id": "sbd-t0001-20240702-00100", "sbd_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": "The requested identifier sbd-t0001-20240702-00100 "
            "could not be found."
        }
        assert result.json() == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds._get_sbd_status")
    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_sbd_status(self, mock_oda, mock_get_sbd_status, client):
        """Verifying that test_get_sbd_status API returns requested SBD status"""

        valid_sbd_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_status.json"
        )

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_sbd_status.return_value = json.loads(valid_sbd_status)

        result = client.get(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            params={"sbd_version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.json(), valid_sbd_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds._get_sbd_status")
    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_invalid_get_sbd_status(self, mock_oda, mock_get_sbd_status, client):
        """Verifying that get_sbd_status throws error if invalid data passed"""
        invalid_sbd_id = "sbd-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_sbd_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbd_id} could not be found."
        )

        result = client.get(
            f"{API_PREFIX}/sbds/{invalid_sbd_id}/status",
            params={"sbd_version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbd-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.json()) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_put_sbd_history(self, mock_oda, client):
        """Verifying that put_sbd_history updates the sbd status correctly"""
        valid_put_sbd_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(valid_put_sbd_history_response)
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Complete",
            "previous_status": "Draft",
            "sbd_version": "1",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            json=data,
        )
        assert_json_is_equal(
            result.json(), valid_put_sbd_history_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_put_sbd_history_version(self, mock_oda, client):
        """Verifying that put_sbd_history updates the sbd status correctly"""
        valid_put_sbd_history_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(valid_put_sbd_history_response)
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Complete",
            "previous_status": "Draft",
            "sbd_version": "1",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            json=data,
        )
        assert_json_is_equal(
            result.json(), valid_put_sbd_history_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

        valid_put_sbd_history_version_response = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_sbd_status_version.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(valid_put_sbd_history_version_response)
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Observed",
            "previous_status": "Draft",
            "sbd_version": "2",
        }
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client.put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            json=data,
        )
        assert_json_is_equal(
            result.json(), valid_put_sbd_history_version_response, exclude_paths
        )
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_sbd_history(self, client):
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
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            params=query_params,
            json=data,
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.json(), json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
