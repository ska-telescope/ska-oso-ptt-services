import json
from http import HTTPStatus
from unittest import mock

from fastapi.testclient import TestClient
from ska_oso_pdm import OSOExecutionBlock

from ska_oso_ptt_services.app import create_app  # Import your create_app function
from ska_oso_ptt_services.app import API_PREFIX
from tests.unit.ska_oso_ptt_services.utils import (
    assert_json_is_equal,
    load_string_from_file,
)

# Create the FastAPI app instance
app = create_app()

# Create the TestClient with the app instance
client = TestClient(app)

TEST_FILES_PATH = "routers/test_data_files"


class TestExecutionBlockAPI:
    """This class contains unit tests for the ExecutionBlockAPI resource,
    which is responsible for handling requests related to
    Execution Block.
    """

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, mock_oda):
        """Verifying that get_ebs_with_status API returns All EBs with status"""
        valid_ebs = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_multiple_ebs_with_status.json"
        )

        execution_block = [OSOExecutionBlock(**x) for x in json.loads(valid_ebs)]

        ebs_mock = mock.MagicMock()
        ebs_mock.query.return_value = execution_block
        uow_mock = mock.MagicMock()
        uow_mock.ebs = ebs_mock
        mock_get_eb_status.current_status = "Fully Observed"
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

        resultDict = result.json()[0]

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(json.dumps(resultDict), json.dumps(json.loads(valid_ebs)))

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
            params=query_params,
            headers={"accept": "application/json"},
        )

        error = {
            "detail": "Different query types are not currently supported"
            " - for example, "
            "cannot combine date created query or entity query with a user query"
        }

        assert json.loads(result.text) == error

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs._get_eb_status")
    def test_get_eb_with_status(self, mock_get_eb_status, mock_oda):
        """Verifying that get_eb_with_status API returns requested EB with status"""
        valid_eb_with_status = load_string_from_file(
            f"{TEST_FILES_PATH}/testfile_sample_eb_with_status.json"
        )

        eb_mock = mock.MagicMock()
        eb_mock.model_dump.return_value = json.loads(valid_eb_with_status)
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = eb_mock
        mock_get_eb_status.return_value = {"current_status": "Fully Observed"}
        mock_oda.uow().__enter__.return_value = uow_mock
        result = client.get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004",
            headers={"accept": "application/json"},
        )
        result_json = json.dumps(result.json()[0])

        assert_json_is_equal(result_json, valid_eb_with_status)
        assert result.status_code == HTTPStatus.OK
