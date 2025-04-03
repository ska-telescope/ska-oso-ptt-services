from http import HTTPStatus
from typing import Any, Dict, List, TypeVar

from fastapi import status
from ska_db_oda.rest.api import check_for_mismatch
from ska_db_oda.rest.errors import UnprocessableEntityError

from ska_oso_ptt_services.common.constant import (
    API_RESPONSE_RESULT_STATUS_FAILED,
    API_RESPONSE_RESULT_STATUS_SUCCESS,
)
from ska_oso_ptt_services.models.models import ApiResponse

T = TypeVar("T")


def common_get_entity_status(
    entity_object, entity_id: str, entity_version: str = None
) -> Dict[str, Any]:
    """
    Takes an entity ID and version and returns status
    :param: entity_object: entity_object
    :param entity_id: Execution Block ID
    :param entity_version: entity_version

    Returns retrieved entity status in Dictionary format

    """

    retrieved_entity = entity_object.get(
        entity_id=entity_id, version=entity_version, is_status_history=False
    )

    return retrieved_entity


def get_responses(response_model) -> Dict[str, Any]:
    """
    Takes response_model as argument and returns responses dict
    :param: response_model: entity_object

    Returns formatted response dictionary

    """

    responses = {
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": response_model,
        }
    }

    return responses


def check_entity_id_mismatch(entity_id, request_entity_id):

    try:

        check_for_mismatch(entity_id, request_entity_id)

    except UnprocessableEntityError as e:

        return convert_to_response_object(
            e.detail, result_code=HTTPStatus.UNPROCESSABLE_ENTITY
        )


def convert_to_response_object(
    response: List[T] | Dict[str, T] | str, result_code: HTTPStatus
) -> ApiResponse:
    """
    Takes response as argument and returns ApiResponse object
    :param: response: response

    Returns formatted response object

    """

    if isinstance(response, list):

        return ApiResponse(
            result_data=response,
            result_code=result_code,
            result_status=API_RESPONSE_RESULT_STATUS_SUCCESS,
        )

    if isinstance(response, dict):

        return ApiResponse(
            result_data=[response],
            result_code=result_code,
            result_status=API_RESPONSE_RESULT_STATUS_SUCCESS,
        )

    if isinstance(response, str):

        return ApiResponse(
            result_data=response,
            result_code=result_code,
            result_status=API_RESPONSE_RESULT_STATUS_FAILED,
        )
