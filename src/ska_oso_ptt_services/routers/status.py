import logging
from http import HTTPStatus

from fastapi import APIRouter

from ska_oso_ptt_services.common.constant import entity_map
from ska_oso_ptt_services.common.error_handling import EntityNotFound
from ska_oso_ptt_services.common.utils import convert_to_response_object, get_responses
from ska_oso_ptt_services.models.models import ApiResponse, EntityStatusResponse

LOGGER = logging.getLogger(__name__)

status_router = APIRouter(prefix="/status")


@status_router.get(
    "/get_entity",
    tags=["Status"],
    summary="Get status dictionary by the entity parameter",
    response_model=ApiResponse[EntityStatusResponse],
    responses=get_responses(ApiResponse[EntityStatusResponse]),
)
def get_entity_status(entity_name: str) -> ApiResponse[EntityStatusResponse]:
    """
    Function that returns the status dictionary for a given entity type.

    Args:
        entity_name: The name of the entity type (sbi, eb, prj, or sbd)

    Returns:
        Tuple containing dictionary of status names and values, and HTTP status code

    Raises:
        ValueError: If an invalid entity name is provided
    """

    entity_class = entity_map.get(entity_name.lower())
    if not entity_class:
        return convert_to_response_object(
            EntityNotFound(entity=entity_name).message, result_code=HTTPStatus.NOT_FOUND
        )

    return convert_to_response_object(
        EntityStatusResponse(
            entity_type=entity_name.lower(),
            statuses={status.name: status.value for status in entity_class},
        ).model_dump(mode="json"),
        result_code=HTTPStatus.OK,
    )
