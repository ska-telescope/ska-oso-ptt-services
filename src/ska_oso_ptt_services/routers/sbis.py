import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.rest.api import get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.common.error_handling import ODANotFound
from ska_oso_ptt_services.common.utils import (
    check_entity_id_mismatch,
    common_get_entity_status,
    convert_to_response_object,
    get_responses,
)
from ska_oso_ptt_services.models.models import ApiResponse, SBInstanceStatusModel

LOGGER = logging.getLogger(__name__)

sbi_router = APIRouter(prefix="/sbis")


@sbi_router.get(
    "",
    tags=["SBI"],
    summary="Get All SB Instance with status appended, filter by the query parameter"
    " like created_before, created_after and user name",
    response_model=ApiResponse[SBInstanceStatusModel],
    responses=get_responses(ApiResponse[SBInstanceStatusModel]),
)
def get_sbis_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> ApiResponse[SBInstanceStatusModel]:
    """
    Function that a GET /sbis request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All SBInstance present with status wrapped in a Response,
         or appropriate error Response
    """

    query_params = get_qry_params(query_params)

    with oda.uow() as uow:
        sbis = uow.sbis.query(query_params)
        sbi_with_status = [
            {
                **sbi.model_dump(mode="json"),
                "status": common_get_entity_status(
                    entity_object=uow.sbis_status_history,
                    entity_id=sbi.sbi_id,
                    entity_version=sbi.metadata.version,
                ).current_status,
            }
            for sbi in sbis
        ]
    return convert_to_response_object(sbi_with_status, result_code=HTTPStatus.OK)


@sbi_router.get(
    "/{sbi_id}",
    tags=["SBI"],
    summary="Get specific SB Instance by identifier with status appended",
    response_model=ApiResponse[SBInstanceStatusModel],
    responses=get_responses(ApiResponse[SBInstanceStatusModel]),
)
def get_sbi_with_status(sbi_id: str) -> ApiResponse[SBInstanceStatusModel]:
    """
    Function that a GET /sbis/<sbi_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBInstance with status wrapped in a Response,
         or appropriate error Response
    """
    with oda.uow() as uow:

        try:

            sbi = uow.sbis.get(sbi_id)
            sbi_json = sbi.model_dump(mode="json")
            sbi_json["status"] = common_get_entity_status(
                entity_object=uow.sbis_status_history,
                entity_id=sbi_id,
                entity_version=sbi_json["metadata"]["version"],
            ).current_status

            return convert_to_response_object(sbi_json, result_code=HTTPStatus.OK)

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@sbi_router.get(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Get SB Instance status by the identifier",
    response_model=ApiResponse[SBIStatusHistory],
    responses=get_responses(ApiResponse[SBIStatusHistory]),
)
def get_sbi_status(sbi_id: str, version: int = None) -> ApiResponse[SBIStatusHistory]:
    """
    Function that a GET /sbi/<sbi_id>/status request is routed to.
    This method is used to GET the current status for the given sbi_id

    :param sbi_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,SBIStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:

        try:

            sbi_status = common_get_entity_status(
                entity_object=uow.sbis_status_history,
                entity_id=sbi_id,
                entity_version=version,
            )

            return convert_to_response_object(sbi_status, result_code=HTTPStatus.OK)

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@sbi_router.put(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Update specific SB Instance status by identifier",
    response_model=ApiResponse[SBIStatusHistory],
    responses=get_responses(ApiResponse[SBIStatusHistory]),
)
def put_sbi_history(
    sbi_id: str, sbi_status_history: SBIStatusHistory
) -> ApiResponse[SBIStatusHistory]:
    """
    Function that a PUT /sbis/<sbi_id>/status request is routed to.

    :param sbi_id: Requested identifier from the path parameter
    :param sbi_status_history: Object of SBIStatusHistory
    :return: The SBInstance wrapped in a Response, or appropriate error Response
    """

    response = check_entity_id_mismatch(sbi_id, sbi_status_history.sbi_ref)

    if response:

        return response

    with oda.uow() as uow:

        try:

            persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
            uow.commit()

            return convert_to_response_object(persisted_sbi, result_code=HTTPStatus.OK)

        except KeyError as error_msg:

            return convert_to_response_object(
                str(error_msg), result_code=HTTPStatus.NOT_FOUND
            )


@sbi_router.get(
    "/status/history",
    tags=["SBI"],
    summary="Get specific SB Instance status history by identifier and version",
    response_model=ApiResponse[SBIStatusHistory],
    responses=get_responses(ApiResponse[SBIStatusHistory]),
)
def get_sbi_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> ApiResponse[SBIStatusHistory]:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, SBIStatusHistory wrapped in a Response,
        or appropriate error Response
    """

    query_params = get_qry_params(query_params)

    with oda.uow() as uow:

        sbis_status_history = uow.sbis_status_history.query(
            query_params, is_status_history=True
        )
        if not sbis_status_history:

            return convert_to_response_object(
                ODANotFound(identifier=query_params.entity_id).message,
                result_code=HTTPStatus.NOT_FOUND,
            )

    return convert_to_response_object(sbis_status_history, result_code=HTTPStatus.OK)
