# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import Project
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.common.constant import (
    MULTIPLE_PRJS,
    MULTIPLE_PRJS_STATUS,
)
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


class TestProjectAPI:
    """This class contains unit tests for the ProjectAPI resource,
    which is responsible for handling requests related to
    Project.
    """

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    def test_get_multiple_prj_with_status(
        self, mock_get_prj_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_multiple_prj_with_status API returns
        All prjs with status"""

        valid_prjs = create_entity_object(MULTIPLE_PRJS)

        project = [Project(**x) for x in valid_prjs]

        prjs_mock = mock.MagicMock()
        prjs_mock.query.return_value = project

        uow_mock = mock.MagicMock()
        uow_mock.prjs = prjs_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "query_type": "created_between",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client_get(f"{API_PREFIX}/prjs", params=query_params).json()

        for res in result["result_data"]:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(result["result_data"], valid_prjs)
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    def test_get_single_prj_with_status(
        self, mock_get_prj_status, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_prj_with_status API returns requested
        prj with status"""

        valid_prj_with_status = create_entity_object(MULTIPLE_PRJS)[0]

        prj_mock = mock.MagicMock()
        prj_mock.model_dump.return_value = valid_prj_with_status

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.return_value = prj_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001").json()

        exclude_paths = ["root['metadata']", "root['obs_programmes']"]

        assert_json_is_equal(
            result["result_data"][0],
            valid_prj_with_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_invalid_prj_with_status(self, mock_oda, client_get):
        """Verifying that get_single_prj_with_status API returns
        requested prj with status"""

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.side_effect = ODANotFound(
            identifier="prj-mvp01-20240426-5007"
        )
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/prjs/prj-mvp01-20240426-5007").json()

        assert "prj-mvp01-20240426-5007" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_with_invalid_status(self, mock_oda, client_get):
        """Verifying that get_single_prj_with_invalid_status throws error
        if invalid data passed"""

        invalid_prj_id = "invalid-prj-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.side_effect = ODANotFound(identifier=invalid_prj_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/prjs/{invalid_prj_id}").json()

        assert invalid_prj_id in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_status_history(
        self, mock_oda, client_get, create_entity_object
    ):
        """Verifying that get_single_prj_status_history API returns requested
        prj status history
        """

        valid_prj_status_history = create_entity_object(MULTIPLE_PRJS_STATUS)

        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = valid_prj_status_history
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/prjs/status/history",
            params={"entity_id": "prj-mvp01-20220923-00001", "prj_version": "1"},
        ).json()

        exclude_regex_paths = {r"root\[\d+\]\['metadata'\]\['(pdm_version|version)'\]"}

        assert_json_is_equal(
            result["result_data"],
            valid_prj_status_history,
            exclude_regex_paths=exclude_regex_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_invalid_prj_status_history(self, mock_oda, client_get):
        """Verifying that test_get_single_invalid_prj_status_history throws error
        if invalid data passed"""

        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = []
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/prjs/status/history",
            params={"entity_id": "prj-t0001-00100", "prj_version": "1"},
        ).json()

        assert "prj-t0001-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_status(
        self, mock_oda, mock_get_prj_status, client_get, create_entity_object
    ):
        """Verifying that test_get_single_prj_status API returns
        requested prj status"""

        valid_prj_status = create_entity_object(MULTIPLE_PRJS_STATUS)[0]

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_prj_status.return_value = valid_prj_status

        result = client_get(
            f"{API_PREFIX}/prjs/prj-mvp01-20240426-5004/status",
            params={"prj_version": "1"},
        ).json()

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result["result_data"][0],
            valid_prj_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_invalid_prj_status(
        self, mock_oda, mock_get_prj_status, client_get
    ):
        """Verifying that get_single_invalid_prj_status throws error
        if invalid data passed"""

        invalid_prj_id = "prj-t0001-20240702-00100"

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_prj_status.side_effect = ODANotFound(identifier=invalid_prj_id)

        result = client_get(
            f"{API_PREFIX}/prjs/{invalid_prj_id}/status", params={"prj_version": "1"}
        ).json()

        assert "prj-t0001-20240702-00100" in result["result_data"]
        assert result["result_code"] == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history(self, mock_oda, client_put, create_entity_object):
        """Verifying that put_prj_history updates the prj status correctly"""

        valid_prj_status = create_entity_object(MULTIPLE_PRJS_STATUS)[0]

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(json.dumps(valid_prj_status))
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Draft",
            "previous_status": "Draft",
            "prj_ref": "prj-mvp01-20220923-00001",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"][0],
            valid_prj_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history_with_two_version(
        self, mock_oda, client_put, create_entity_object
    ):
        """Verifying that put_prj_history updates the prj status correctly"""

        valid_prj_status = create_entity_object(MULTIPLE_PRJS_STATUS)[0]

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(json.dumps(valid_prj_status))
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Draft",
            "previous_status": "Draft",
            "prj_ref": "prj-mvp01-20220923-00001",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"][0],
            valid_prj_status,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK

        valid_put_prj_history_version_response = create_entity_object(
            MULTIPLE_PRJS_STATUS
        )[0]

        uow_mock = mock.MagicMock()
        uow_mock.prjs = ["prj-mvp01-20220923-00001"]

        prjs_status_history_mock = mock.MagicMock()
        prjs_status_history_mock.add.return_value = (
            ProjectStatusHistory.model_validate_json(
                json.dumps(valid_put_prj_history_version_response)
            )
        )

        uow_mock.prjs_status_history = prjs_status_history_mock
        uow_mock.commit().return_value = "200"
        mock_oda.uow().__enter__.return_value = uow_mock

        data = {
            "current_status": "Submitted",
            "previous_status": "Draft",
            "prj_ref": "prj-mvp01-20220923-00001",
        }

        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
            "root['metadata']['version']",
            "root['metadata']['pdm_version']",
        ]

        result = client_put(
            f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001/status", json=data
        ).json()

        assert_json_is_equal(
            result["result_data"][0],
            valid_put_prj_history_version_response,
            exclude_paths,
        )
        assert result["result_code"] == HTTPStatus.OK
