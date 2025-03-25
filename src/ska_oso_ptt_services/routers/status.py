import logging
from enum import EnumMeta
from typing import Dict

from fastapi import APIRouter
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    ProjectStatus,
    SBDStatus,
    SBIStatus,
)

from ska_oso_ptt_services.common.constant import GET_ALL_ENTITY_MODEL
from ska_oso_ptt_services.models.models import EntityStatusResponse

LOGGER = logging.getLogger(__name__)

status_router = APIRouter(prefix="/status")


@status_router.get(
    "/get_entity",
    tags=["Status"],
    summary="Get status dictionary by the entity parameter",
    response_model=EntityStatusResponse,
    responses=GET_ALL_ENTITY_MODEL,
)
def get_entity_status(entity_name: str) -> EntityStatusResponse:
    """
    Function that returns the status dictionary for a given entity type.

    Args:
        entity_name: The name of the entity type (sbi, eb, prj, or sbd)

    Returns:
        Tuple containing dictionary of status names and values, and HTTP status code

    Raises:
        ValueError: If an invalid entity name is provided
    """
    entity_map: Dict[str, EnumMeta] = {
        "sbi": SBIStatus,
        "eb": OSOEBStatus,
        "prj": ProjectStatus,
        "sbd": SBDStatus,
    }

    entity_class = entity_map.get(entity_name.lower())
    if not entity_class:
        raise ValueError(f"Invalid entity name: {entity_name}")

    return EntityStatusResponse(
        entity_type=entity_name.lower(),
        statuses={status.name: status.value for status in entity_class},
    )
