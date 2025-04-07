import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.rest.api import get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import OSOEBStatusHistory

from ska_oso_ptt_services.common.error_handling import ODANotFound
from ska_oso_ptt_services.common.utils import (
    check_entity_id_mismatch,
    common_get_entity_status,
    convert_to_response_object,
    get_responses,
)
from ska_oso_ptt_services.models.models import ApiResponse, EBStatusModel

LOGGER = logging.getLogger(__name__)

eb_router = APIRouter(prefix="/ebs")


@eb_router.get(
    "",
    tags=["EB"],
    summary="Get All Execution Block with status appended, filter by the query "
    "parameter like created_before, created_after and user name",
    response_model=ApiResponse[EBStatusModel],
    responses=get_responses(ApiResponse[EBStatusModel]),
)
def get_ebs_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> ApiResponse[EBStatusModel]:
    """
    Function that a GET /ebs request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
         or appropriate error Response
    """
    query_params = get_qry_params(query_params)

    with oda.uow() as uow:
        ebs = uow.ebs.query(query_params)
        eb_with_status = [
            {
                **eb.model_dump(mode="json"),
                "status": common_get_entity_status(
                    entity_object=uow.ebs_status_history,
                    entity_id=eb.eb_id,
                    entity_version=eb.metadata.version,
                ).current_status,
            }
            for eb in ebs
        ]
    return convert_to_response_object(eb_with_status, result_code=HTTPStatus.OK)


@eb_router.get(
    "/{eb_id}",
    tags=["EB"],
    summary="Get specific Execution Block by identifier with status appended",
    response_model=ApiResponse[EBStatusModel],
    responses=get_responses(ApiResponse[EBStatusModel]),
)
def get_eb_with_status(eb_id: str) -> ApiResponse[EBStatusModel]:
    """
    Function that a GET /ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :return: The ExecutionBlock with status wrapped in a Response,
        or appropriate error Response
    """
    with oda.uow() as uow:

        try:

            eb = uow.ebs.get(eb_id)
            eb_json = eb.model_dump(mode="json")
            eb_json["status"] = common_get_entity_status(
                entity_object=uow.ebs_status_history,
                entity_id=eb.eb_id,
                entity_version=eb_json["metadata"]["version"],
            ).current_status

            return convert_to_response_object(eb_json, result_code=HTTPStatus.OK)

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )

        except ODANotFound as error_msg:

            return convert_to_response_object(
                error_msg.message, result_code=HTTPStatus.NOT_FOUND
            )

        except Exception as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@eb_router.get(
    "/{eb_id}/status",
    tags=["EB"],
    summary="Get specific Execution Block status by the identifier",
    response_model=ApiResponse[OSOEBStatusHistory],
    responses=get_responses(ApiResponse[OSOEBStatusHistory]),
)
def get_eb_status(eb_id: str, version: int = None) -> ApiResponse[OSOEBStatusHistory]:
    """
    Function that a GET /ebs/<eb_id>/status request is routed to.
    This method is used to GET the current status for the given eb_id

    :param eb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,OSOEBStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:

        try:

            eb_status = common_get_entity_status(
                entity_object=uow.ebs_status_history,
                entity_id=eb_id,
                entity_version=version,
            )
            return convert_to_response_object(
                eb_status, result_code=HTTPStatus.OK
            )

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )

        except ODANotFound as error_msg:

            return convert_to_response_object(
                error_msg.message, result_code=HTTPStatus.NOT_FOUND
            )

        except Exception as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@eb_router.put(
    "/{eb_id}/status",
    tags=["EB"],
    summary="Update specific Execution Block status by identifier",
    response_model=ApiResponse[OSOEBStatusHistory],
    responses=get_responses(ApiResponse[OSOEBStatusHistory]),
)
def put_eb_history(
    eb_id: str, eb_status_history: OSOEBStatusHistory
) -> ApiResponse[OSOEBStatusHistory]:
    """
    Function that a PUT /ebs/<eb_id>/status request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :param eb_status_history: Object of OSOEBStatusHistory
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """

    response = check_entity_id_mismatch(eb_id, eb_status_history.eb_ref)

    if response:

        return response

    with oda.uow() as uow:

        try:

            persisted_eb = uow.ebs_status_history.add(eb_status_history)
            uow.commit()
            return convert_to_response_object(
                persisted_eb.model_dump(mode="json"), result_code=HTTPStatus.OK
            )

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )

        except ODANotFound as error_msg:

            return convert_to_response_object(
                error_msg.message, result_code=HTTPStatus.NOT_FOUND
            )

        except Exception as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@eb_router.get(
    "/status/history",
    tags=["EB"],
    summary="Get specific Execution Block status history by identifier and version",
    response_model=ApiResponse[OSOEBStatusHistory],
    responses=get_responses(ApiResponse[OSOEBStatusHistory]),
)
def get_eb_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> ApiResponse[OSOEBStatusHistory]:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, OSOEBStatusHistory wrapped in a Response,
        or appropriate error Response
    """

    query_params = get_qry_params(query_params)

    with oda.uow() as uow:

        ebs_status_history = uow.ebs_status_history.query(
            query_params, is_status_history=True
        )
        if not ebs_status_history:

            return convert_to_response_object(
                ODANotFound(identifier=query_params.entity_id).message,
                result_code=HTTPStatus.NOT_FOUND,
            )

    return convert_to_response_object(ebs_status_history, result_code=HTTPStatus.OK)
