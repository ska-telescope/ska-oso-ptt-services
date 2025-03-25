import json
import logging
from enum import EnumMeta
from pathlib import Path
from typing import Dict

from fastapi import APIRouter
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    ProjectStatus,
    SBDStatus,
    SBIStatus,
)

# Get the directory of the current script
current_dir = Path(__file__).parent

LOGGER = logging.getLogger(__name__)

status_router = APIRouter(prefix="/status")


@status_router.get(
    "/get_entity",
    tags=["Status"],
    summary="Get status dictionary by the entity parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/status_entity_response.json"
                            ).read_text()
                        )
                    ]
                }
            },
        },
        400: {
            "description": "Bad Request",
            "content": {
                "application/json": {
                    "example": {"message": "Invalid request parameters"}
                }
            },
        },
        404: {
            "description": "Not Found",
            "content": {
                "application/json": {"example": {"message": "Entity Not Found"}}
            },
        },
        422: {
            "description": "Unprocessable Content",
            "content": {
                "application/json": {"example": {"message": "Invalid Entity Id"}}
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {"message": "Internal server error occurred"}
                }
            },
        },
    },
)
def get_entity_status(entity_name: str):
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

    return {status.name: status.value for status in entity_class}
