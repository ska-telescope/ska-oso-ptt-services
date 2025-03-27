import json
import os

import pytest
from fastapi.testclient import TestClient

from ska_oso_ptt_services.app import create_app

TEST_FILES_PATH = "unit/ska_oso_ptt_services/routers/test_data_files"


def load_json_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        return json.load(json_file)


@pytest.fixture
def client():

    app = create_app()

    return TestClient(app)


@pytest.fixture
def valid_ebs():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_multiple_ebs_with_status.json"
    )


@pytest.fixture
def valid_eb_with_status():
    return load_json_from_file(f"{TEST_FILES_PATH}/testfile_sample_eb_with_status.json")


@pytest.fixture
def valid_eb_status_history():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_eb_status_history.json"
    )


@pytest.fixture
def valid_eb_status():
    return load_json_from_file(f"{TEST_FILES_PATH}/testfile_sample_eb_status.json")


@pytest.fixture
def valid_sbds():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_multiple_sbds_with_status.json"
    )


@pytest.fixture
def valid_sbd():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_sbd_json_with_status.json"
    )


@pytest.fixture
def valid_sbd_status_history():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_sbd_status_history.json"
    )


@pytest.fixture
def valid_sbd_status():
    return load_json_from_file(f"{TEST_FILES_PATH}/testfile_sample_sbd_status.json")


@pytest.fixture
def valid_put_sbd_history_version_response():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_sbd_status_version.json"
    )


@pytest.fixture
def valid_prjs():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_multiple_prjs_with_status.json"
    )


@pytest.fixture
def valid_prj_with_status():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_prj_with_status.json"
    )


@pytest.fixture
def valid_prj_status_history():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_prj_status_history.json"
    )


@pytest.fixture
def valid_prj_status():
    return load_json_from_file(f"{TEST_FILES_PATH}/testfile_sample_prj_status.json")


@pytest.fixture
def valid_put_prj_history_version_response():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_prj_status_version.json"
    )


@pytest.fixture
def valid_sbis():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_multiple_sbis_with_status.json"
    )


@pytest.fixture
def valid_sbi():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_sbi_with_status.json"
    )


@pytest.fixture
def valid_sbi_status_history():
    return load_json_from_file(
        f"{TEST_FILES_PATH}/testfile_sample_sbi_status_history.json"
    )


@pytest.fixture
def valid_sbi_status():
    return load_json_from_file(f"{TEST_FILES_PATH}/testfile_sample_sbi_status.json")
