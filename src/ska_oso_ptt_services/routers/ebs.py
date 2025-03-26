import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import OSOEBStatusHistory

from ska_oso_ptt_services.common.constant import (
    GET_ALL_EB_MODEL,
    GET_ID_EB_MODEL,
    GET_ID_EB_STATUS_MODEL,
    GET_PUT_ID_EB_STATUS_MODEL,
)
from ska_oso_ptt_services.common.error_handling import ODANotFound
from ska_oso_ptt_services.models.models import EBStatusModel

LOGGER = logging.getLogger(__name__)

eb_router = APIRouter(prefix="/ebs")


@eb_router.get(
    "/",
    tags=["EB"],
    summary="Get All Execution Block with status appended, filter by the query "
    "parameter like created_before, created_after and user name",
    response_model=List[EBStatusModel],
    responses=GET_ALL_EB_MODEL,
)
def get_ebs_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> List[EBStatusModel]:
    """
    Function that a GET /ebs request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(query_params)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        ebs = uow.ebs.query(maybe_qry_params)
        eb_with_status = [
            {
                **eb.model_dump(mode="json"),
                "status": _get_eb_status(
                    uow=uow, eb_id=eb.eb_id, version=eb.metadata.version
                ).current_status,
            }
            for eb in ebs
        ]
    return eb_with_status


@eb_router.get(
    "/{eb_id}",
    tags=["EB"],
    summary="Get specific Execution Block by identifier with status appended",
    response_model=EBStatusModel,
    responses=GET_ID_EB_MODEL,
)
def get_eb_with_status(eb_id: str) -> EBStatusModel:
    """
    Function that a GET /ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :return: The ExecutionBlock with status wrapped in a Response,
        or appropriate error Response
    """
    with oda.uow() as uow:
        eb = uow.ebs.get(eb_id)
        eb_json = eb.model_dump(mode="json")
        eb_json["status"] = _get_eb_status(
            uow=uow, eb_id=eb_id, version=eb_json["metadata"]["version"]
        ).current_status

    return eb_json


@eb_router.get(
    "/{eb_id}/status",
    tags=["EB"],
    summary="Get specific Execution Block status by the identifier",
    response_model=OSOEBStatusHistory,
    responses=GET_PUT_ID_EB_STATUS_MODEL,
)
def get_eb_status(eb_id: str, version: int = None) -> OSOEBStatusHistory:
    """
    Function that a GET /ebs/<eb_id>/status request is routed to.
    This method is used to GET the current status for the given eb_id

    :param eb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,OSOEBStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:
        eb_status = _get_eb_status(uow=uow, eb_id=eb_id, version=version)
    return eb_status


@eb_router.put(
    "/{eb_id}/status",
    tags=["EB"],
    summary="Update specific Execution Block status by identifier",
    response_model=OSOEBStatusHistory,
    responses=GET_PUT_ID_EB_STATUS_MODEL,
)
def put_eb_history(
    eb_id: str, eb_status_history: OSOEBStatusHistory
) -> OSOEBStatusHistory:
    """
    Function that a PUT /ebs/<eb_id>/status request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :param eb_status_history: Object of OSOEBStatusHistory
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(eb_id, eb_status_history.eb_ref):
        return response

    with oda.uow() as uow:
        if eb_id not in uow.ebs:
            raise ODANotFound(identifier=eb_id)
        persisted_eb = uow.ebs_status_history.add(eb_status_history)
        uow.commit()
    return persisted_eb


@eb_router.get(
    "/status/history",
    tags=["EB"],
    summary="Get specific Execution Block status history by identifier and version",
    response_model=List[OSOEBStatusHistory],
    responses=GET_ID_EB_STATUS_MODEL,
)
def get_eb_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> List[OSOEBStatusHistory]:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, OSOEBStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(query_params), QueryParams):
        return maybe_qry_params
    with oda.uow() as uow:
        ebs_status_history = uow.ebs_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not ebs_status_history:
            raise ODANotFound(identifier=query_params.entity_id)

    return ebs_status_history


def _get_eb_status(uow, eb_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an EB ID and Version and returns status
    :param: uow: ODA PostgresUnitOfWork
    :param eb_id: Execution Block ID
    :param version: EB version

    Returns retrieved EB status in Dictionary format

    """

    retrieved_eb = uow.ebs_status_history.get(
        entity_id=eb_id, version=version, is_status_history=False
    )

    return retrieved_eb
