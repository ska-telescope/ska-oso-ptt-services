import json
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

from ska_oso_pdm import SBDefinition
from ska_oso_pdm.entity_status_history import SBDStatusHistory, SBIStatusHistory

from tests.unit.ska_oso_ptt_services.util import (
    assert_json_is_equal,
    load_string_from_file,
)

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-ptt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"


class TestSBDefinitionAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbds_with_status(self, mock_get_sbd_status, mock_oda, client):
        """Verifying that get_sbds_with_status API returns All SBDS with status"""

        valid_sbds = load_string_from_file(
            "files/testfile_sample_multiple_sbds_with_status.json"
        )

        sbd_definitions = [SBDefinition(**sbd) for sbd in json.loads(valid_sbds)]
        sbds_mock = mock.MagicMock()
        sbds_mock.query.return_value = sbd_definitions
        uow_mock = mock.MagicMock()
        uow_mock.sbds = sbds_mock
        mock_get_sbd_status.return_value = {"current_status": "draft"}
        mock_oda.uow.__enter__.return_value = uow_mock

        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client.get(
            f"{BASE_API_URL}/sbds",
            query_string=query_params,
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbds)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_get_sbds_with_status(self, client):
        """Verifying that get_sbds_with_status throws error if invalid data passed"""

        query_params = {
            "match_type": "equals",
            "created_before": "2022-03-28T15:43:53.971548+00:00",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_before": "2022-03-28T15:43:53.971548+00:00",
            "last_modified_after": "2022-03-28T15:43:53.971548+00:00",
        }

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
        assert result.status_code == HTTPStatus.BAD_REQUEST

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbd_with_status(self, mock_get_sbd_status, mock_oda, client):
        """Verifying that get_sbd_with_status API returns requested SBD with status"""
        valid_sbd = load_string_from_file(
            "files/testfile_sample_sbd_json_with_status.json"
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
        """Verifying that get_sbd_with_status throws error if invalid data passed"""

        invalid_sbd_id = "invalid-sbd-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbd_id} could not be found."
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/sbds/{invalid_sbd_id}",
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                f"Not Found. The requested identifier {invalid_sbd_id} could not be"
                " found."
            )
        }

        assert result.get_json() == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbd_status_history(self, mock_oda, client):
        valid_sbd_status_history = load_string_from_file(
            "files/testfile_sample_sbd_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = json.loads(
            valid_sbd_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/status/history/sbds",
            query_string={"entity_id": "sbd-t0001-20240702-00002", "version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbd_status_history)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_invalid_get_sbd_status_history(self, mock_oda, client):
        """Verifying that et_sbd_status_history throws error if invalid data passed"""
        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = []
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/sbds",
            query_string={"entity_id": "sbd-t0001-20240702-00100", "version": "1"},
            headers={"accept": "application/json"},
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
            "files/testfile_sample_sbd_status.json"
        )

        mock_get_sbd_status.return_value = json.loads(valid_sbd_status)

        result = client.get(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string={"version": "1"},
            headers={"accept": "application/json"},
        )

        assert_json_is_equal(result.text, valid_sbd_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_invalid_get_sbd_status(self, mock_get_sbd_status, client):
        """Verifying that get_sbd_status throws error if invalid data passed"""
        invalid_sbd_id = "sbd-t0001-20240702-00100"
        mock_get_sbd_status.side_effect = KeyError(
            f"Not Found. The requested identifier {invalid_sbd_id} could not be found."
        )

        result = client.get(
            f"{BASE_API_URL}/status/sbds/{invalid_sbd_id}",
            query_string={"version": "1"},
            headers={"accept": "application/json"},
        )

        error = {
            "detail": (
                "Not Found. The requested identifier sbd-t0001-20240702-00100 could not"
                " be found."
            )
        }
        assert json.loads(result.text) == error
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_sbd_history(self, mock_oda, client):
        valid_put_sbd_history_response = load_string_from_file(
            "files/testfile_sample_sbd_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(valid_put_sbd_history_response)
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        query_params = {"version": "1"}
        data = {"current_status": "complete", "previous_status": "draft"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_sbd_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_sbd_history(self, client):
        """Verifying that put_sbd_history error if invalid data passed"""
        query_params = {"version": "1"}
        data = {"current1_status": "complete", "previous_status": "draft"}

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR


class TestSBIDefinitionAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_sbi_history(self, mock_oda, client):
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

        query_params = {"version": "1"}
        data = {"current_status": "executing", "previous_status": "created"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(
            f"{BASE_API_URL}/status/sbis/sbi-mvp01-20220923-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_sbi_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_sbi_history(self, client):
        """Verifying that put_sbi_history error if invalid data passed"""
        query_params = {"version": "1"}
        data = {"current1_status": "complete", "previous_status": "draft"}

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{BASE_API_URL}/status/sbds/sbd-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
