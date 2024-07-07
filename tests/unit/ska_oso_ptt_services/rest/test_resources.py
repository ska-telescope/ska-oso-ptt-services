import datetime
import json
import os
import zoneinfo
from http import HTTPStatus
from importlib.metadata import version
from unittest import mock

import pytest
from deepdiff import DeepDiff
from ska_oso_pdm import Metadata
from ska_oso_pdm.entity_status_history import OSOEBStatus, OSOEBStatusHistory

from ska_oso_ptt_services.rest import create_app

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-ptt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"
ebs_API_URL = f"{BASE_API_URL}/ebs"


def normalize_json(json_str):
    """Normalize JSON string by loading and dumping back to string."""
    return json.dumps(json.loads(json_str), sort_keys=True)


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json_file.read()
        return json_data


def assert_json_is_equal(json_a, json_b, exclude_paths=None):
    """
    Utility function to compare two JSON objects
    """
    # Load the JSON strings into Python dictionaries
    obj_a = json.loads(json_a)  # remains string #result.text
    obj_b = json.loads(json_b)  # converts to list

    # Compare the objects using DeepDiff
    diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)

    # Raise an assertion error if there are differences
    assert {} == diff, f"JSON not equal: {diff}"


@pytest.fixture
def client():
    # os.chdir("/home/manish/skao/ska-oso-osd")
    app = create_app()
    with app.app.test_client() as client:
        yield client


class TestebefinitionAPI:
    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_eb_with_status(self, mock_get_eb_status, mock_oda, client):
        valid_eb_with_status = load_string_from_file(
            "../files/testfile_sample_eb_with_status.json"
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
    def test_get_eb_status_history(self, mock_oda, client):
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.return_value = TestDataFactory.ebefinition() #uow.ebs.get
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(f"{ebS_API_URL}/eb-1234")
        """
        valid_eb_status_history = load_string_from_file(
            "../files/testfile_sample_eb_status_history.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs_status_history.query.return_value = json.loads(
            valid_eb_status_history
        )
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/status/history/ebs",
            query_string={"entity_id": "eb-mvp01-20240426-5004", "version": "1"},
        )
        assert_json_is_equal(result.text, valid_eb_status_history)

        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_eb_status")
    def test_get_ebs_with_status(self, mock_get_eb_status, client):
        valid_eb_status = load_string_from_file(
            "../files/testfile_sample_eb_status.json"
        )
        # mock_get_sbd_status = mock.MagicMock()
        mock_get_eb_status.return_value = json.loads(valid_eb_status)

        result = client.get(
            f"{BASE_API_URL}/status/ebs/eb-mvp01-20240426-5004",
            query_string={"version": "1"},
        )

        assert_json_is_equal(result.text, valid_eb_status)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_sbd_history(self, mock_oda, client):
        valid_put_eb_history_response = load_string_from_file(
            "../files/testfile_sample_eb_status.json"
        )

        uow_mock = mock.MagicMock()
        uow_mock.ebs = ["eb-mvp01-20240426-5004"]

        # Create consistent datetime objects
        created_on = datetime.datetime(
            2024, 7, 2, 18, 1, 47, 873431, tzinfo=zoneinfo.ZoneInfo(key="GMT")
        )
        last_modified_on = datetime.datetime(
            2024, 7, 3, 12, 23, 38, 785233, tzinfo=datetime.timezone.utc
        )

        # Setting up nested mocks
        ebs_status_history_mock = mock.MagicMock()
        ebs_status_history_mock.add.return_value = OSOEBStatusHistory(
            metadata=Metadata(
                version=1,
                created_by="DefaultUser",
                created_on=created_on,
                last_modified_by="DefaultUser",
                last_modified_on=last_modified_on,
            ),
            eb_ref="eb-mvp01-20240426-5004",
            current_status=OSOEBStatus.FULLY_OBSERVED,
            previous_status=OSOEBStatus.CREATED,
        )

        uow_mock.ebs_status_history = ebs_status_history_mock
        uow_mock.commit.return_value = "200"
        mock_oda.uow.__enter__.return_value = uow_mock

        url = "/ska-oso-ptt-services/ptt/api/v1/status/ebs/eb-mvp01-20240426-5004"
        params = {"version": "1"}
        data = {"current_status": "fully_observed", "previous_status": "created"}
        exclude_paths = [
            "root['metadata']['created_on']",
            "root['metadata']['last_modified_on']",
        ]

        result = client.put(url, query_string=params, json=data)
        assert_json_is_equal(result.text, valid_put_eb_history_response, exclude_paths)
        assert result.status_code == HTTPStatus.OK

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_eb_id_not_found(self, mock_oda, client):
        """
        Check the sbds_get method returns the Not Found error when identifier not in ODA
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = KeyError("not found")
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(
            f"{BASE_API_URL}/ebs/eb-1234", headers={"accept": "application/json"}
        )
        response = json.loads(result.text)

        assert (
            response["detail"]
            == "Not Found. The requested identifier eb-1234 could not be found."
        )
        assert result.status_code == 404

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_put_eb_id_not_found(self, mock_oda, client):
        """
        Check the sbds_get method returns the Not Found error when identifier not in ODA
        """
        uow_mock = mock.MagicMock()
        uow_mock.ebs.get.side_effect = KeyError("not found")
        mock_oda.uow.__enter__.return_value = uow_mock

        url = "/ska-oso-ptt-services/ptt/api/v1/status/ebs/eb-1234"
        params = {"version": "1"}
        data = {"current_status": "fully_observed", "previous_status": "created"}

        result = client.put(url, query_string=params, json=data)
        response = json.loads(result.text)

        assert (
            response["detail"]
            == "Not Found. The requested identifier eb-1234 could not be found."
        )
        assert result.status_code == 404
