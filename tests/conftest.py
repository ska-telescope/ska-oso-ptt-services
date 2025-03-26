import pytest
from fastapi.testclient import TestClient

from ska_oso_ptt_services.app import create_app


@pytest.fixture
def client():

    app = create_app()

    return TestClient(app)
