# pylint: disable=no-member
import json
from http import HTTPStatus
from unittest import mock

from ska_oso_pdm import Project
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

from ska_oso_ptt_services.app import API_PREFIX
from ska_oso_ptt_services.common.error_handling import ODANotFound
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


class TestProjectAPI:
    """This class contains unit tests for the ProjectAPI resource,
    which is responsible for handling requests related to
    Project.
    """

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    def test_get_multiple_prj_with_status(
        self, mock_get_prj_status, mock_oda, client_get, valid_prjs
    ):
        """Verifying that get_multiple_prj_with_status API returns
        All prjs with status"""

        project = [Project(**x) for x in valid_prjs]

        prjs_mock = mock.MagicMock()
        prjs_mock.query.return_value = project

        uow_mock = mock.MagicMock()
        uow_mock.prjs = prjs_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        query_params = {
            "match_type": "equals",
            "created_after": "2022-03-28T15:43:53.971548+00:00",
        }

        result = client_get(f"{API_PREFIX}/prjs", params=query_params)

        resultDict = result.json()

        for res in resultDict:
            del res["metadata"]["pdm_version"]

        assert_json_is_equal(resultDict, valid_prjs)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    def test_get_single_prj_with_status(
        self, mock_get_prj_status, mock_oda, client_get, valid_prj_with_status
    ):
        """Verifying that get_single_prj_with_status API returns requested
        prj with status"""

        prj_mock = mock.MagicMock()
        prj_mock.model_dump.return_value = valid_prj_with_status

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.return_value = prj_mock
        mock_get_prj_status().current_status = "Draft"
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/prjs/prj-mvp01-20220923-00001")

        resultDict = result.json()

        exclude_paths = ["root['metadata']", "root['obs_programmes']"]

        assert_json_is_equal(
            resultDict,
            valid_prj_with_status,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_with_invalid_status(self, mock_oda, client_get):
        """Verifying that get_single_prj_with_invalid_status throws error
        if invalid data passed"""

        invalid_prj_id = "invalid-prj-id-12345"

        uow_mock = mock.MagicMock()
        uow_mock.prjs.get.side_effect = ODANotFound(identifier=invalid_prj_id)
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(f"{API_PREFIX}/prjs/{invalid_prj_id}")

        expected_error_message = {
            "detail": (f"The requested identifier {invalid_prj_id} could not be found.")
        }

        assert_json_is_equal(result.json(), expected_error_message)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_status_history(
        self, mock_oda, client_get, valid_prj_status_history
    ):
        """Verifying that get_single_prj_status_history API returns requested
        prj status history
        """

        uow_mock = mock.MagicMock()
        uow_mock.prjs_status_history.query.return_value = valid_prj_status_history
        mock_oda.uow().__enter__.return_value = uow_mock

        result = client_get(
            f"{API_PREFIX}/prjs/status/history",
            params={"entity_id": "prj-mvp01-20220923-00001", "prj_version": "1"},
        )

        exclude_regex_paths = {r"root\[\d+\]\['metadata'\]\['(pdm_version|version)'\]"}

        assert_json_is_equal(
            result.json(),
            valid_prj_status_history,
            exclude_regex_paths=exclude_regex_paths,
        )
        assert result.status_code == HTTPStatus.OK

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
        )

        error = {
            "detail": ("The requested identifier prj-t0001-00100 could not be found.")
        }

        assert_json_is_equal(result.json(), error)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.common_get_entity_status")
    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_get_single_prj_status(
        self, mock_oda, mock_get_prj_status, client_get, valid_prj_status
    ):
        """Verifying that test_get_single_prj_status API returns
        requested prj status"""

        uow_mock = mock.MagicMock()
        mock_oda.uow().__enter__.return_value = uow_mock
        mock_get_prj_status.return_value = valid_prj_status

        result = client_get(
            f"{API_PREFIX}/prjs/prj-mvp01-20240426-5004/status",
            params={"prj_version": "1"},
        )

        exclude_paths = ["root['metadata']"]

        assert_json_is_equal(
            result.json(),
            valid_prj_status,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK

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
        )

        error = {
            "detail": (
                "The requested identifier prj-t0001-20240702-00100 could not"
                " be found."
            )
        }

        assert_json_is_equal(result.json(), error)
        assert result.status_code == HTTPStatus.NOT_FOUND

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history(self, mock_oda, client_put, valid_prj_status):
        """Verifying that put_prj_history updates the prj status correctly"""

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
        )

        assert_json_is_equal(
            result.json(),
            valid_prj_status,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.routers.prjs.oda")
    def test_put_prj_history_with_two_version(
        self,
        mock_oda,
        client_put,
        valid_prj_status,
        valid_put_prj_history_version_response,
    ):
        """Verifying that put_prj_history updates the prj status correctly"""

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
        )

        assert_json_is_equal(
            result.json(),
            valid_prj_status,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK

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
        )

        assert_json_is_equal(
            result.json(),
            valid_put_prj_history_version_response,
            exclude_paths,
        )
        assert result.status_code == HTTPStatus.OK
