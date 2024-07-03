import json
import os
from http import HTTPStatus
from unittest import mock
from importlib.metadata import version

import pytest
from deepdiff import DeepDiff

from ska_oso_ptt_services.rest import create_app

OSO_SERVICES_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
BASE_API_URL = f"/ska-oso-ptt-services/ptt/api/v{OSO_SERVICES_MAJOR_VERSION}"
SBDS_API_URL = f"{BASE_API_URL}/sbds"

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


# def assert_json_is_equal(json_a, json_b, exclude_paths=None):
#     """
#     Utility function to compare two JSON objects
#     """
#     # key/values in the generated JSON do not necessarily have the same order
#     # as the test string, even though they are equivalent JSON objects, e.g.,
#     # subarray_id could be defined after dish. Ensure a stable test by
#     # comparing the JSON objects themselves.
#     obj_a = json.loads(json_a)
#     obj_b = json.loads(json_b)
#     try:
#         assert obj_a == obj_b
#     except AssertionError:
#         # raise a more useful exception that shows *where* the JSON differs
#         diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)
#         assert {} == diff, f"JSON not equal: {diff}"

def assert_json_is_equal(json_a, json_b, exclude_paths=None):
    """
    Utility function to compare two JSON objects
    """
    # Load the JSON strings into Python dictionaries
    print("%%%%%%%%%%%%%%%%%%%%%%\n\n\n")
    print(f"type of JSON A, {type(json_a)}")
    print(f"type of JSON A, {type(json_b)}")
    #obj_a = json.loads(json.loads(json_a)) #remains string #result.text
    obj_a = json.loads(json_a)  # remains string #result.text
    obj_b = json.loads(json_b) #converts to list
    print(f"type of OBJ A, {type(obj_a)}")
    print(f"type of OBJ B, {type(obj_b)}")

    # obj_a = normalize_json(json_a)
    # obj_b = normalize_json(json_b)
    # Compare the objects using DeepDiff
    diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)

    # Raise an assertion error if there are differences
    assert {} == diff, f"JSON not equal: {diff}"

@pytest.fixture
def client():
    #os.chdir("/home/manish/skao/ska-oso-osd")
    app = create_app()
    with app.app.test_client() as client:
        yield client

class TestSBDefinitionAPI:

    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    @mock.patch("ska_oso_ptt_services.rest.api.resources._get_sbd_status")
    def test_get_sbd_with_status(self, mock_get_sbd_status, mock_oda,client):
        valid_sbd = load_string_from_file("../files/testfile_sample_sbd_json_with_status.json")

        sbd_mock = mock.MagicMock()
        sbd_mock.model_dump.return_value = json.loads(valid_sbd)
        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.return_value = sbd_mock
        mock_get_sbd_status.return_value = {"current_status": "complete"}
        mock_oda.uow.__enter__.return_value = uow_mock
        import pdb
        pdb.set_trace()

        # result = client.get(
        #     f'{BASE_API_URL}/sbds',
        #     query_string={'sbd_id': 'sbd-t0001-20240702-00002'}
        # )

        result = client.get(
            f'{BASE_API_URL}/sbds/sbd-t0001-20240702-00002',
            headers={'accept': 'application/json'}
        )
        assert_json_is_equal(result.text, valid_sbd)
        assert result.status_code == HTTPStatus.OK



    @mock.patch("ska_oso_ptt_services.rest.api.resources.oda")
    def test_get_sbd_status_history(self,mock_oda,client):
        valid_sbd_status_history = load_string_from_file("../files/testfile_sample_sbd_status_history.json")


        """
        uow_mock = mock.MagicMock()
        uow_mock.sbds.get.return_value = TestDataFactory.sbdefinition() #uow.sbds.get
        mock_oda.uow.__enter__.return_value = uow_mock

        result = client.get(f"{SBDS_API_URL}/sbd-1234")
        """
        uow_mock = mock.MagicMock()
        uow_mock.sbds_status_history.query.return_value = json.loads(valid_sbd_status_history)
        mock_oda.uow.__enter__.return_value = uow_mock
        print("&&&&&&&&&&&&&&&&&&&&&& in test case ")
        #result = client.get(f"{SBDS_API_URL}/sbd-t0001-20240702-00002")
        result = client.get(
            f'{BASE_API_URL}/status/history/sbds',
            query_string={'entity_id': 'sbd-t0001-20240702-00002', 'version': '1'}
        )
        import pdb
        pdb.set_trace()
        assert_json_is_equal(result.text, valid_sbd_status_history)
        assert result.status_code == HTTPStatus.OK

