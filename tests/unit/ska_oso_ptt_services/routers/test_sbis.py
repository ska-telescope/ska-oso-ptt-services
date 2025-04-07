# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import SBInstance
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.common.constant import (
    MULTIPLE_SBIS,
    MULTIPLE_SBIS_STATUS,
)
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


class TestSBInstanceAPI:
    """This class contains unit tests for the SBInstanceAPI resource,
    which is responsible for handling requests related to
    Scheduling Block Instances.
    """

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    def test_get_multiple_sbi_with_status(
        self, mock_get_sbi_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_multiple_sbi_with_status API returns
        All SBIs with status"""

        valid_sbis = create_entity_object(MULTIPLE_SBIS)

        sbi_instance = [SBInstance(**x) for x in valid_sbis]

        sbis_mock = mock.MagicMock()
        sbis_mock.query.return_value = sbi_instance

        uow_mock = mock.MagicMock()
        uow_mock.sbis = sbis_mock
        mock_get_sbi_status().current_status = "Created"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "query_type": "created_between",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client_get(f"{API_PREFIX}/sbis", params=query_params).json()

        for res in result["result_data"]:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(result["result_data"], valid_sbis)
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    def test_get_single_sbi_with_status(
        self, mock_get_sbi_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_sbi_with_status API returns requested
        SBI with status"""

        valid_sbi = create_entity_object(MULTIPLE_SBIS)[0]

        sbi_mock = mock.MagicMock()
        sbi_mock.model_dump.return_value = valid_sbi

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.return_value = sbi_mock
        mock_get_sbi_status().current_status = "Created"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5016").json()

        exclude_paths = ["root['metadata']['pdm_version']"]

        assert_json_is_equal(
            result["result_data"][0],
            valid_sbi,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_invalid_sbi_with_status(
        self, mock_oda, client_get
    ):
        """Verifying that get_single_sbi_with_status API returns
        requested sbi with status"""

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.side_effect = ODANotFound(identifier="sbi-mvp01-20240426-5007")
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5007").json()

        assert "sbi-mvp01-20240426-5007" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_sbi_with_invalid_status(self, mock_oda, client_get):
        """Verifying that get_single_sbi_with_invalid_status throws error
        if invalid data passed"""

        invalid_sbi_id = "invalid-sbi-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.sbis.get.side_effect = ODANotFound(identifier=invalid_sbi_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/sbis/{invalid_sbi_id}").json()

        assert invalid_sbi_id in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_sbi_status_history(
        self, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_sbi_status_history API returns requested
        SBI status history"""

        valid_sbi_status_history = create_entity_object(MULTIPLE_SBIS_STATUS)

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = valid_sbi_status_history
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/sbis/status/history",
            params={"entity_id": "sbi-mvp01-20220923-00002", "sbi_version": "1"},
        ).json()

        assert_json_is_equal(
            result["result_data"],
            valid_sbi_status_history,
            exclude_regex_paths={
                r"root\[\d+\]\['metadata'\]\['(pdm_version|version)'\]"
            },
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_invalid_sbi_status_history(self, mock_oda, client_get):
        """Verifying that get_single_invalid_sbi_status_history throws error
        if invalid data passed
        """

        uow_mock = mock.MagicMock()
        uow_mock.sbis_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/sbis/status/history",
            params={"entity_id": "sbi-t000-00100", "sbi_version": "1"},
        ).json()

        assert "sbi-t000-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_sbi_status(
        self, mock_oda, mock_get_sbi_status, client_get, create_entity_object
    ):
        """Verifying that get_single_sbi_status API returns requested SBI status"""

        valid_sbi_status = create_entity_object(MULTIPLE_SBIS_STATUS)[0]

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_sbi_status.return_value = valid_sbi_status

        result = client_get(
            f"{API_PREFIX}/sbis/sbi-mvp01-20240426-5016/status",
            params={"sbi_version": "1"},
        ).json()

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result["result_data"][0],
            valid_sbi_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.sbis.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_get_single_invalid_sbi_status(
        self, mock_oda, mock_get_sbi_status, client_get
    ):
        """Verifying that get_single_invalid_sbi_status throws error
        if invalid data passed"""

        invalid_sbi_id = "sbi-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_sbi_status.side_effect = ODANotFound(identifier=invalid_sbi_id)

        result = client_get(
            f"{API_PREFIX}/sbis/{invalid_sbi_id}/status", params={"sbi_version": "1"}
        ).json()

        assert "sbi-t0001-20240702-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.sbis.oda")
    def test_put_sbi_history(self, mock_oda, client_put, create_entity_object):
        """Verifying that put_sbi_history updates the sbi status correctly"""

        valid_sbi_status = create_entity_object(MULTIPLE_SBIS_STATUS)[0]

        uow_mock = mock.MagicMock()
        uow_mock.sbis = ["sbi-mvp01-20220923-00002"]

        sbis_status_history_mock = mock.MagicMock()
        sbis_status_history_mock.add.return_value = (
            SBIStatusHistory.model_validate_json(
                json.dumps(valid_sbi_status)
            )
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

        result = client_put(
            f"{API_PREFIX}/sbis/sbi-mvp01-20220923-00002/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"][0],
            valid_sbi_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK
