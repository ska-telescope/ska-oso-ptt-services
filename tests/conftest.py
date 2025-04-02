import json
import os
from functools import partial

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


@pytest.fixture(scope="session")
def client_get():

    app = create_app()
    client = TestClient(app)

    return partial(client.get, headers={"accept": "application/json"})


@pytest.fixture(scope="session")
def client_put():

    app = create_app()
    client = TestClient(app)

    return partial(client.put)


@pytest.fixture
def create_entity_object():
    
    def _create_entity_object(filename: str):
        return load_json_from_file(f"{TEST_FILES_PATH}/{filename}")

    return _create_entity_object
