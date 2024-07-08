import json
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

from ska_oso_pdm import OSOExecutionBlock, SBDefinition, SBInstance
from ska_oso_pdm.entity_status_history import (
    OSOEBStatusHistory,
    SBDStatusHistory,
    SBIStatusHistory,
)

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


class TestSBInstanceAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbi_status")
    def test_get_sbis_with_status(self, mock_get_sbi_status, mock_oda, client):
        valid_sbis = load_string_from_file(
            "files/testfile_sample_multiple_sbis_with_status.json"
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
        valid_sbi = load_string_from_file("files/testfile_sample_sbi_with_status.json")

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
            "files/testfile_sample_sbi_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = json.loads(
            valid_sbi_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock
        result = client.get(
            f"{BASE_API_URL}/status/history/sbis",
            query_string={"entity_id": "sbi-mvp01-20220923-00002", "version": "1"},
            headers={"accept": "application/json"},
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
            headers={"accept": "application/json"},
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
            "files/testfile_sample_sbi_status.json"
        )
        mock_get_sbi_status.return_value = json.loads(valid_sbi_status)

        result = client.get(
            f"{BASE_API_URL}/status/sbis/sbi-mvp01-20240426-5016",
            query_string={"version": "1"},
            headers={"accept": "application/json"},
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


class TestExecutionBlockAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, mock_oda, client):
        valid_ebs = load_string_from_file(
            "files/testfile_sample_multiple_ebs_with_status.json"
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
            "files/testfile_sample_eb_with_status.json"
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
            "files/testfile_sample_eb_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = json.loads(
            valid_eb_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/status/history/ebs",
            query_string={"entity_id": "eb-mvp01-20240426-5004", "version": "1"},
            headers={"accept": "application/json"},
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
            headers={"accept": "application/json"},
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
        valid_eb_status = load_string_from_file("files/testfile_sample_eb_status.json")
        mock_get_eb_status.return_value = json.loads(valid_eb_status)

        result = client.get(
            f"{BASE_API_URL}/status/ebs/eb-mvp01-20240426-5004",
            query_string={"version": "1"},
            headers={"accept": "application/json"},
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

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_eb_history(self, mock_oda, client):
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

        url = "/ska-oso-ptt-services/ptt/api/v1/status/ebs/eb-mvp01-20240426-5004"
        query_params = {"version": "1"}
        data = {"current_status": "fully_observed", "previous_status": "created"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(
            url,
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )
        assert_json_is_equal(result.text, valid_put_eb_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    def test_invalid_put_eb_history(self, client):
        query_params = {"version": "1"}
        data = {"current1_status": "fully_observed", "previous_status": "created"}

        error = {
            "detail": "KeyError('current_status') with args ('current_status',)",
            "title": "Internal Server Error",
        }

        result = client.put(
            f"{BASE_API_URL}/status/ebs/eb-t0001-20240702-00002",
            query_string=query_params,
            json=data,
            headers={"accept": "application/json"},
        )

        exclude_path = ["root['traceback']"]
        assert_json_is_equal(result.text, json.dumps(error), exclude_path)
        assert result.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
