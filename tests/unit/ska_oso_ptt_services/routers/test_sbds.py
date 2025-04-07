# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import SBDefinition
from ska_oso_pdm.entity_status_history import SBDStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.common.constant import (
    MULTIPLE_SBDS,
    MULTIPLE_SBDS_STATUS,
)
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


class TestSBDefinitionAPI:
    """This class contains unit tests for the SBDefinitionAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Definitions.
    """

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbds.common_get_entity_status")
    def test_get_multiple_sbd_with_status(
        self, mock_get_sbd_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_multiple_sbd_with_status API returns
        All SBDS with status"""

        valid_sbds = create_entity_object(MULTIPLE_SBDS)

        sbd_definitions = [SBDefinition(**sbd) for sbd in valid_sbds]

        sbds_mock = mock.MagicMock()
        sbds_mock.query.return_value = sbd_definitions

        uow_mock = mock.MagicMock()
        uow_mock.sbds = sbds_mock
        mock_get_sbd_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "query_type": "created_between",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client_get(f"{API_PREFIX}/sbds", params=query_params).json()

        pdm_version_regex = r"root\[\d+\]\['metadata'\]\['pdm_version'\]"
        epoch_regex = (
            r"root\[\d+\]\['targets'\]\[\d+\]\['reference_coordinate'\]\['epoch'\]"
        )
        exclude_regex_paths = {f"{pdm_version_regex}|{epoch_regex}"}

        assert_json_is_equal(
            result["result_data"], valid_sbds, exclude_regex_paths=exclude_regex_paths
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbds.common_get_entity_status")
    def test_get_single_sbd_with_status(
        self, mock_get_sbd_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_sbd_with_status API returns requested
        SBD with status"""

        valid_sbd = create_entity_object(MULTIPLE_SBDS)[0]

        sbd_mock = mock.MagicMock()
        sbd_mock.model_dump.return_value = valid_sbd

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.return_value = sbd_mock
        mock_get_sbd_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002").json()

        pdm_version_regex = r"root\['metadata'\]\['pdm_version'\]"
        epoch_regex = r"root\['targets'\]\[\d+\]\['reference_coordinate'\]\['epoch'\]"
        exclude_regex_paths = {f"{pdm_version_regex}|{epoch_regex}"}

        assert_json_is_equal(
            result["result_data"][0],
            valid_sbd,
            exclude_regex_paths=exclude_regex_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_invalid_sbd_with_status(
        self, mock_oda, client_get
    ):
        """Verifying that get_single_sbd_with_status API returns
        requested sbd with status"""

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.side_effect = ODANotFound(identifier="sbds-mvp01-20240426-5007")
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbds/sbds-mvp01-20240426-5007").json()

        assert "sbds-mvp01-20240426-5007" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_sbd_with_invalid_status(self, mock_oda, client_get):
        """Verifying that get_single_sbd_with_invalid_status throws error
        if invalid data passed"""

        invalid_sbd_id = "invalid-sbd-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.side_effect = ODANotFound(identifier=invalid_sbd_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbds/{invalid_sbd_id}").json()

        assert "invalid-sbd-id-12345" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_sbd_status_history(
        self, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_sbd_status_history API returns requested
        SBD status history"""

        valid_sbd_status_history = create_entity_object(MULTIPLE_SBDS_STATUS)

        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = valid_sbd_status_history
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/sbds/status/history",
            params={"entity_id": "sbd-t0001-20240702-00002", "sbd_version": "1"},
        ).json()

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result["result_data"],
            valid_sbd_status_history,
            exclude_paths=exclude_paths
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_invalid_sbd_status_history(self, mock_oda, client_get):
        """Verifying that get_single_invalid_sbd_status_history throws error
        if invalid data passed"""

        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/sbds/status/history",
            params={"entity_id": "sbd-t0001-20240702-00100", "sbd_version": "1"},
        )

        assert "sbd-t0001-20240702-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_sbd_status(
        self, mock_oda, mock_get_sbd_status, client_get, create_entity_object
    ):
        """Verifying that get_single_sbd_status API returns requested SBD status"""

        valid_sbd_status = create_entity_object(MULTIPLE_SBDS_STATUS)[0]

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_sbd_status.return_value = valid_sbd_status

        result = client_get(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status",
            params={"sbd_version": "1"},
        ).json()

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result["result_data"][0],
            valid_sbd_status,
            exclude_paths=exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_get_single_invalid_sbd_status(
        self, mock_oda, mock_get_sbd_status, client_get
    ):
        """Verifying that get_single_invalid_sbd_status throws error
        if invalid data passed"""

        invalid_sbd_id = "sbd-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_sbd_status.side_effect = ODANotFound(identifier=invalid_sbd_id)

        result = client_get(
            f"{API_PREFIX}/sbds/{invalid_sbd_id}/status", params={"sbd_version": "1"}
        )

        assert "sbd-t0001-20240702-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_put_sbd_history(self, mock_oda, client_put, create_entity_object):
        """Verifying that put_sbd_history updates the sbd status correctly"""

        valid_sbd_status = create_entity_object(MULTIPLE_SBDS_STATUS)[0]

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(json.dumps(valid_sbd_status))
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Complete",
            "previous_status": "Draft",
            "sbd_ref": "sbd-t0001-20240702-00002",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"],
            valid_sbd_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbds.oda")
    def test_put_sbd_history_version(self, mock_oda, client_put, create_entity_object):
        """Verifying that put_sbd_history updates the sbd status correctly"""

        valid_sbd_status = create_entity_object(MULTIPLE_SBDS_STATUS)[0]

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(json.dumps(valid_sbd_status))
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Complete",
            "previous_status": "Draft",
            "sbd_ref": "sbd-t0001-20240702-00002",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"],
            valid_sbd_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

        valid_put_sbd_history_version_response = create_entity_object(
            MULTIPLE_SBDS_STATUS
        )[0]

        uow_mock = mock.MagicMock()
        uow_mock.sbds = ["sbd-t0001-20240702-00002"]

        sbds_status_history_mock = mock.MagicMock()
        sbds_status_history_mock.add.return_value = (
            SBDStatusHistory.model_validate_json(
                json.dumps(valid_put_sbd_history_version_response)
            )
        )

        uow_mock.sbds_status_history = sbds_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Observed",
            "previous_status": "Draft",
            "sbd_ref": "sbd-t0001-20240702-00002",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/sbds/sbd-t0001-20240702-00002/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"],
            valid_put_sbd_history_version_response,
            exclude_paths=exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK
