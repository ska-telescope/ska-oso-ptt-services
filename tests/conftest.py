import copy
import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Tuple

import pytest
from ska_db_oda.persistence.domain import set_identifier
from ska_oso_pdm.builders.sb_builder import MidSBDefinitionBuilder
from ska_oso_pdm.entity_status_history import (
    OSOEBStatusHistory,
    ProjectStatusHistory,
    SBDStatusHistory,
    SBIStatusHistory,
)
from ska_oso_pdm.execution_block import OSOExecutionBlock
from ska_oso_pdm.project import Project
from ska_oso_pdm.proposal import Proposal
from ska_oso_pdm.sb_definition import SBDefinition
from ska_oso_pdm.sb_definition.sb_definition import SBDefinitionID
from ska_oso_pdm.sb_instance import SBInstance

PROJECT_ROOT = Path(__file__).parents[1].resolve()


KUBE_HOST = os.getenv("KUBE_HOST")
KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-db-oda")
ODA_MAJOR_VERSION = "7"  # Hardcoded for now. See src/ska_db_oda/rest/__init__.py
# Default as it uses the default namespace. When deployed to a
# different namespace the first part will change to that namespace.
DEFAULT_API_PATH = f"ska-db-oda/oda/api/v{ODA_MAJOR_VERSION}"
ODA_URL = os.getenv(
    "ODA_URL", f"http://{KUBE_HOST}/{KUBE_NAMESPACE}/oda/api/v{ODA_MAJOR_VERSION}"
)
TESTFILES_PATH = "unit/ska_oso_ptt_services/test_data_files"

TEST_ENTITY_DATETIME = datetime.fromisoformat("2022-03-28T15:43:53.971548+00:00")


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    print(f"***********path: {path}")
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data


# json_file_path = "unit/ska_oso_slt_services/routers/test_data_files"
@pytest.fixture
def base_working_dir():  # pylint: disable=redefined-outer-name
    """
    Create a new ODA working directory populated with some example SBDs.

    # - create a temporary working directory
    # - copy the sample low SB into the working directory
    # - returns the working directory path

    :return: Path to the newly-created working directory
    """
    with tempfile.TemporaryDirectory() as tempdir:
        base_working_directory = Path(tempdir)

        yield base_working_directory


@pytest.fixture
def empty_working_dir():  # pylint: disable=redefined-outer-name
    """
    Create a new, empty ODA working directory

    :return: Path to the newly-created working directory
    """
    with tempfile.TemporaryDirectory() as tempdir:
        base_working_directory = Path(tempdir)
        sbd_working_directory = Path(tempdir) / "sbd"
        Path(sbd_working_directory).mkdir(parents=True, exist_ok=True)

        yield base_working_directory


# See https://developer.skao.int/projects/ska-ser-xray/en/latest/guide/pytest.html
@pytest.hookimpl
def pytest_collection_modifyitems(
    session, config, items
):  # pylint: disable=unused-argument
    for item in items:
        for marker in item.iter_markers(name="xray"):
            test_key = marker.args[0]
            item.user_properties.append(("test_key", test_key))


VALID_EB_STATUS_JSON = load_string_from_file(
    f"{TESTFILES_PATH}/testfile_sample_eb_status_history.json"
)
VALID_SBI_STATUS_JSON = load_string_from_file(
    f"{TESTFILES_PATH}/testfile_sample_sbi_status_history.json"
)
VALID_SBD_STATUS_JSON = load_string_from_file(
    f"{TESTFILES_PATH}/testfile_sample_sbd_status_history.json"
)
VALID_PRJ_STATUS_JSON = load_string_from_file(
    f"{TESTFILES_PATH}/testfile_sample_prj_status_history.json"
)


class TestDataFactory:
    @staticmethod
    def sbdefinition(
        sbd_id: SBDefinitionID = "sbd-mvp01-20200325-00001",
        version: int = 1,
        created_on: datetime = TEST_ENTITY_DATETIME,
    ) -> SBDefinition:
        sbd = MidSBDefinitionBuilder()
        set_identifier(sbd, sbd_id)

        sbd.metadata.version = version
        sbd.metadata.created_on = created_on
        sbd.metadata.last_modified_on = created_on

        return sbd

    @staticmethod
    def sbinstance(
        sbi_id: str = "sbi-mvp01-20220923-00001",
        version: int = 1,
    ) -> SBInstance:
        with open(f"{TESTFILES_PATH}/testfile_sample_sbi.json", encoding="utf-8") as fh:
            sbi = SBInstance.model_validate_json(fh.read())

        set_identifier(sbi, sbi_id)
        sbi.metadata.version = version

        return sbi

    @staticmethod
    def executionblock(
        eb_id: str = "eb-mvp01-20220923-00001", version: int = 1
    ) -> OSOExecutionBlock:
        with open(
            f"{TESTFILES_PATH}/testfile_sample_execution_block.json", encoding="utf-8"
        ) as fh:
            eb = OSOExecutionBlock.model_validate_json(fh.read())

        set_identifier(eb, eb_id)
        eb.metadata.version = version

        return eb

    @staticmethod
    def ebassociatedwithsbi(
        eb_id: str = "eb-mvp01-20220923-00001", version: int = 1
    ) -> Tuple[OSOExecutionBlock, SBInstance]:
        with open(
            f"{TESTFILES_PATH}/testfile_sample_execution_block.json", encoding="utf-8"
        ) as fh:
            eb = OSOExecutionBlock.model_validate_json(fh.read())
        with open(f"{TESTFILES_PATH}/testfile_sample_sbi.json", encoding="utf-8") as fh:
            sbi = SBInstance.model_validate_json(fh.read())

        set_identifier(eb, eb_id)
        eb.metadata.version = version
        sbi.metadata.version = version

        return eb, sbi

    @staticmethod
    def project(
        prj_id: str = "prj-mvp01-20220923-00001",
        version: int = 1,
    ) -> Project:
        with open(
            f"{TESTFILES_PATH}/testfile_sample_project.json", encoding="utf-8"
        ) as fh:
            prj = Project.model_validate_json(fh.read())

        set_identifier(prj, prj_id)
        prj.metadata.version = version

        return prj

    @staticmethod
    def proposal(
        prsl_id: str = "prsl-mvp01-20220923-00001",
        version: int = 1,
    ) -> Proposal:
        with open(
            f"{TESTFILES_PATH}/testfile_sample_proposal.json", encoding="utf-8"
        ) as fh:
            prsl = Proposal.model_validate_json(fh.read())
        set_identifier(prsl, prsl_id)

        prsl.metadata.version = version

        return prsl

    @staticmethod
    def eb_status(
        eb_ref: str = "eb-mvp01-20220923-00001",
    ) -> OSOEBStatusHistory:
        eb_status_history = OSOEBStatusHistory.model_validate_json(VALID_EB_STATUS_JSON)
        set_identifier(eb_status_history, eb_ref)
        return eb_status_history

    @staticmethod
    def sbi_status(
        sbi_ref: str = "sbi-mvp01-20220923-00001",
    ) -> SBIStatusHistory:
        sbi_status_history = SBIStatusHistory.model_validate_json(VALID_SBI_STATUS_JSON)
        set_identifier(sbi_status_history, sbi_ref)
        return sbi_status_history

    @staticmethod
    def sbd_status(
        sbd_ref: str = "sbd-mvp01-20220923-00001",
    ) -> SBDStatusHistory:
        sbd_status_history = SBDStatusHistory.model_validate_json(VALID_SBD_STATUS_JSON)
        set_identifier(sbd_status_history, sbd_ref)
        return sbd_status_history

    @staticmethod
    def prj_status(
        prj_ref: str = "prj-mvp01-20220923-00001",
    ) -> ProjectStatusHistory:
        prj_status_history = ProjectStatusHistory.model_validate_json(
            VALID_PRJ_STATUS_JSON
        )
        set_identifier(prj_status_history, prj_ref)
        return prj_status_history


@pytest.fixture(scope="module")
def sb_generator():
    """
    Test fixture to return an infinite stream of unique SBs.

    This fixture returns a generator which, on each call, copies the template SB
    and updates its ID to a unique ID.

    :param low_sbd: template SB
    :return: generator that returns SBs
    """
    # as a module-scope fixture, we can't use the test-scope low_sbd fixture
    sbd = MidSBDefinitionBuilder()

    def sb_stream():
        counter = 0
        while True:
            sb_copy = copy.deepcopy(sbd)
            counter += 1
            today = date.today()
            # format is sbd-mvp01-20200325-00001
            sb_copy.sbd_id = f"sbd-mvp01-{today:%Y%m%d}-{counter:05}"
            yield sb_copy

    yield sb_stream()


@pytest.fixture
def test_sbd_v1():
    return TestDataFactory.sbdefinition(version=1)


@pytest.fixture
def test_sbd_v2():
    return TestDataFactory.sbdefinition(version=2)
