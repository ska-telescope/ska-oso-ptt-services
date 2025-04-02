# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

import pytest
from ska_oso_pdm import OSOEBStatusHistory, OSOExecutionBlock

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
# from tests.conftest import json_loader
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


class TestExecutionBlockAPI:
    """This class contains unit tests for the ExecutionBlockAPI resource,
    which is responsible for handling requests related to
    Execution Block.
    """

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs.common_get_entity_status")
    @pytest.mark.parametrize("json_loader", ["testfile_sample_multiple_ebs_with_status.json"], indirect=True)
    def test_get_multiple_eb_with_status(
        self, mock_get_eb_status, mock_oda, client_get, json_loader
    ):
        """Verifying that get_multiple_eb_with_status API returns All EBs with status"""

        execution_block = [OSOExecutionBlock(**x) for x in json_loader.read_json()]

        ebs_mock = mock.MagicMock()
        ebs_mock.query.return_value = execution_block

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ebs_mock
        mock_get_eb_status().current_status = "Fully Observed"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client_get(f"{API_PREFIX}/ebs", params=query_params)

        resultDict = result.json()

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(resultDict, json_loader.read_json())
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    @mock.patch("ska_oso_ptt_services.routers.ebs.common_get_entity_status")
    def test_get_single_eb_with_status(
        self, mock_get_eb_status, mock_oda, client_get, valid_eb_with_status
    ):
        """Verifying that get_single_eb_with_status API returns
        requested EB with status"""

        eb_mock = mock.MagicMock()
        eb_mock.model_dump.return_value = valid_eb_with_status

        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = eb_mock
        mock_get_eb_status().current_status = "Fully Observed"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004")

        exclude_paths = ["root['metadata']['pdm_version']"]

        assert_json_is_equal(result.json(), valid_eb_with_status, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_single_eb_with_invalid_status(self, mock_oda, client_get):
        """Verifying that get_single_eb_with_invalid_status throws error
        if invalid data passed"""

        invalid_eb_id = "invalid-eb-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = ODANotFound(identifier=invalid_eb_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/ebs/{invalid_eb_id}")

        expected_error_message = {
            "detail": (f"The requested identifier {invalid_eb_id} could not be found.")
        }

        assert_json_is_equal(result.json(), expected_error_message)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_single_eb_status_history(
        self, mock_oda, client_get, valid_eb_status_history
    ):
        """Verifying that get_single_eb_status_history API returns requested
        EB status history
        """

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = valid_eb_status_history
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/ebs/status/history",
            params={"entity_id": "eb-mvp01-20240426-5004", "eb_version": "1"},
        )

        assert_json_is_equal(
            result.json(),
            valid_eb_status_history,
            exclude_regex_paths={
                r"root\[\d+\]\['metadata'\]\['(pdm_version|version)'\]"
            },
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_single_invalid_eb_status_history(self, mock_oda, client_get):
        """Verifying that get_single_invalid_eb_status_history throws error
        if invalid data passed
        """

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/ebs/status/history",
            params={"entity_id": "eb-t0001-00100", "eb_version": "1"},
        )

        error = {
            "detail": "The requested identifier eb-t0001-00100 could not be found."
        }

        assert_json_is_equal(result.json(), error)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.ebs.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_single_eb_status(
        self, mock_oda, mock_get_eb_status, client_get, valid_eb_status
    ):
        """Verifying that get_single_eb_status API returns requested EB status"""

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock

        mock_get_eb_status.return_value = valid_eb_status

        result = client_get(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004/status",
            params={"eb_version": "1"},
        )

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result.json(),
            valid_eb_status,
            exclude_paths=exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.ebs.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_get_single_invalid_eb_status(
        self, mock_oda, mock_get_eb_status, client_get
    ):
        """Verifying that get_single_invalid_eb_status throws error
        if invalid data passed"""

        invalid_eb_id = "eb-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_eb_status.side_effect = ODANotFound(identifier=invalid_eb_id)

        result = client_get(
            f"{API_PREFIX}/ebs/{invalid_eb_id}/status", params={"eb_version": "1"}
        )

        error = {
            "detail": (
                "The requested identifier eb-t0001-20240702-00100 could not"
                " be found."
            )
        }

        assert_json_is_equal(result.json(), error)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.ebs.oda")
    def test_put_eb_history(self, mock_oda, client_put, valid_eb_status):
        """Verifying that put_eb_history updates the eb status correctly"""

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ["eb-mvp01-20240426-5004"]

        ebs_status_history_mock = mock.MagicMock()
        ebs_status_history_mock.add.return_value = (
            OSOEBStatusHistory.model_validate_json(json.dumps(valid_eb_status))
        )

        uow_mock.ebs_status_history = ebs_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Fully Observed",
            "previous_status": "Created",
            "eb_ref": "eb-mvp01-20240426-5004",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/ebs/eb-mvp01-20240426-5004/status", json=data
        )

        assert_json_is_equal(
            result.json(),
            valid_eb_status,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK
