import logging
from typing import List

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.common.constant import (
    GET_ALL_SBI_MODEL,
    GET_ID_SBI_MODEL,
    GET_ID_SBI_STATUS_MODEL,
    GET_PUT_ID_SBI_STATUS_MODEL,
)
from ska_oso_ptt_services.common.error_handling import ODANotFound
from ska_oso_ptt_services.common.utils import common_get_entity_status
from ska_oso_ptt_services.models.models import SBInstanceStatusModel

LOGGER = logging.getLogger(__name__)

sbi_router = APIRouter(prefix="/sbis")


@sbi_router.get(
    "/",
    tags=["SBI"],
    summary="Get All SB Instance with status appended, filter by the query parameter"
    " like created_before, created_after and user name",
    response_model=List[SBInstanceStatusModel],
    responses=GET_ALL_SBI_MODEL,
)
def get_sbis_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> List[SBInstanceStatusModel]:
    """
    Function that a GET /sbis request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All SBInstance present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(query_params)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        sbis = uow.sbis.query(maybe_qry_params)
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
    return sbi_with_status


@sbi_router.get(
    "/{sbi_id}",
    tags=["SBI"],
    summary="Get specific SB Instance by identifier with status appended",
    response_model=SBInstanceStatusModel,
    responses=GET_ID_SBI_MODEL,
)
def get_sbi_with_status(sbi_id: str) -> SBInstanceStatusModel:
    """
    Function that a GET /sbis/<sbi_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBInstance with status wrapped in a Response,
         or appropriate error Response
    """
    with oda.uow() as uow:
        sbi = uow.sbis.get(sbi_id)
        sbi_json = sbi.model_dump(mode="json")
        sbi_json["status"] = common_get_entity_status(
            entity_object=uow.sbis_status_history,
            entity_id=sbi_id,
            entity_version=sbi_json["metadata"]["version"],
        ).current_status
    return sbi_json


@sbi_router.get(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Get SB Instance status by the identifier",
    response_model=SBIStatusHistory,
    responses=GET_PUT_ID_SBI_STATUS_MODEL,
)
def get_sbi_status(sbi_id: str, version: int = None):
    """
    Function that a GET /sbi/<sbi_id>/status request is routed to.
    This method is used to GET the current status for the given sbi_id

    :param sbi_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,SBIStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:
        sbi_status = common_get_entity_status(
            entity_object=uow.sbis_status_history,
            entity_id=sbi_id,
            entity_version=version,
        )
    return sbi_status


@sbi_router.put(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Update specific SB Instance status by identifier",
    response_model=SBIStatusHistory,
    responses=GET_PUT_ID_SBI_STATUS_MODEL,
)
def put_sbi_history(
    sbi_id: str, sbi_status_history: SBIStatusHistory
) -> SBIStatusHistory:
    """
    Function that a PUT /sbis/<sbi_id>/status request is routed to.

    :param sbi_id: Requested identifier from the path parameter
    :param sbi_status_history: Object of SBIStatusHistory
    :return: The SBInstance wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(sbi_id, sbi_status_history.sbi_ref):
        return response

    with oda.uow() as uow:
        if sbi_id not in uow.sbis:
            raise ODANotFound(identifier=sbi_id)

        persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
        uow.commit()
    return persisted_sbi


@sbi_router.get(
    "/status/history",
    tags=["SBI"],
    summary="Get specific SB Instance status history by identifier and version",
    response_model=List[SBIStatusHistory],
    responses=GET_ID_SBI_STATUS_MODEL,
)
def get_sbi_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> SBIStatusHistory:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, SBIStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(query_params), QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        sbis_status_history = uow.sbis_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not sbis_status_history:
            raise ODANotFound(identifier=query_params.entity_id)

    return sbis_status_history
