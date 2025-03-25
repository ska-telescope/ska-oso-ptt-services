from datetime import datetime
from unittest import mock

import pytest
from dateutil.tz import tzlocal
from ska_db_oda.persistence.domain import CODEC
from ska_oso_pdm._shared import Metadata

from tests.conftest import DEFAULT_API_PATH, TestDataFactory
from tests.unit.ska_oso_ptt_services.utils import assert_json_is_equal


@pytest.mark.parametrize(
    "resource, entity",
    [
        ("sbds", TestDataFactory.sbdefinition(sbd_id="test-id-123")),
        ("sbis", TestDataFactory.sbinstance(sbi_id="test-id-123")),
        ("ebs", TestDataFactory.executionblock(eb_id="test-id-123")),
        ("prjs", TestDataFactory.project(prj_id="test-id-123")),
        ("prsls", TestDataFactory.proposal(prsl_id="test-id-123")),
    ],
)
@mock.patch("ska_db_oda.persistence.domain.metadatamixin.datetime")
@mock.patch("ska_db_oda.persistence.domain.skuid.fetch_skuid")
def test_get(mock_skuid_fetch, mock_datetime, client, resource, entity):
    """
    Test successful retrieval of an entity via the GET endpoint
    """
    now = datetime.now(tz=tzlocal())
    mock_datetime.now.return_value = now
    test_id = "test-id-123"
    mock_skuid_fetch.return_value = test_id

    # the server needs an entity before it can be retrieved
    post_response = client.post(
        f"{DEFAULT_API_PATH}/{resource}", content=CODEC.dumps(entity)
    )

    assert post_response.status_code == 200

    entity.metadata = Metadata(
        version=1,
        created_on=now,
        created_by="DefaultUser",
        last_modified_on=now,
        last_modified_by="DefaultUser",
    )
    response = client.get(f"{DEFAULT_API_PATH}/{resource}/{test_id}")
    assert response.status_code == 200
    assert_json_is_equal(response.text, CODEC.dumps(entity))
