from enum import EnumMeta
from typing import Dict

from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    ProjectStatus,
    SBDStatus,
    SBIStatus,
)

entity_map: Dict[str, EnumMeta] = {
    "sbi": SBIStatus,
    "eb": OSOEBStatus,
    "prj": ProjectStatus,
    "sbd": SBDStatus,
}

API_RESPONSE_RESULT_STATUS_SUCCESS = "success"
API_RESPONSE_RESULT_STATUS_FAILED = "failed"
