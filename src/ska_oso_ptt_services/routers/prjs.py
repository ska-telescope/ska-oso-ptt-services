import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

from ska_oso_ptt_services.common.constant import (
    GET_ALL_PRJ_MODEL,
    GET_ID_PRJ_MODEL,
    GET_ID_PRJ_STATUS_MODEL,
    GET_PUT_ID_PRJ_STATUS_MODEL,
)
from ska_oso_ptt_services.models.models import ProjectStatusModel

LOGGER = logging.getLogger(__name__)

prj_router = APIRouter(prefix="/prjs")


@prj_router.get(
    "/",
    tags=["PRJ"],
    summary="Get All Project with status appended, filter by the query parameter"
    " like created_before, created_after and user name",
    response_model=List[ProjectStatusModel],
    responses=GET_ALL_PRJ_MODEL,
)
def get_prjs_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> List[ProjectStatusModel]:
    """
    Function that a GET /prjs request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All Project present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(query_params)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        prjs = uow.prjs.query(maybe_qry_params)
        prj_with_status = [
            {
                **prj.model_dump(mode="json"),
                "status": _get_prj_status(
                    uow=uow, prj_id=prj.prj_id, version=prj.metadata.version
                ).current_status,
            }
            for prj in prjs
        ]
    return prj_with_status


@prj_router.get(
    "/{prj_id}",
    tags=["PRJ"],
    summary="Get specific Project by identifier with status appended",
    response_model=ProjectStatusModel,
    responses=GET_ID_PRJ_MODEL,
)
def get_prj_with_status(prj_id: str) -> ProjectStatusModel:
    """
    Function that a GET /prjs/<prj_id> request is routed to.

    :param prj_id: Requested identifier from the path parameter
    :return: The Project with status wrapped in a Response,
        or appropriate error Response
    """
    with oda.uow() as uow:
        prj = uow.prjs.get(prj_id)
        prj_json = prj.model_dump(mode="json")
        prj_json["status"] = _get_prj_status(
            uow=uow, prj_id=prj_id, version=prj_json["metadata"]["version"]
        ).current_status

    return prj_json


@prj_router.get(
    "/{prj_id}/status",
    tags=["PRJ"],
    summary="Get specific Project status by the identifier",
    response_model=ProjectStatusHistory,
    responses=GET_PUT_ID_PRJ_STATUS_MODEL,
)
def get_prj_status(prj_id: str, version: int = None) -> ProjectStatusHistory:
    """
    Function that a GET /prjs/<prj_id>/status request is routed to.
    This method is used to GET the current status for the given prj_id

    :param prj_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,ProjectStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:
        prj_status = _get_prj_status(uow=uow, prj_id=prj_id, version=version)
    return prj_status


@prj_router.put(
    "/{prj_id}/status",
    tags=["PRJ"],
    summary="Update specific Project status by identifier",
    response_model=ProjectStatusHistory,
    responses=GET_PUT_ID_PRJ_STATUS_MODEL,
)
def put_prj_history(
    prj_id: str, prj_status_history: ProjectStatusHistory
) -> ProjectStatusHistory:
    """
    Function that a PUT /prjs/<prj_id>/status request is routed to.

    :param prj_id: Requested identifier from the path parameter
    :param prj_status_history: Object of ProjectStatusHistory
    :return: The Project wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(prj_id, prj_status_history.prj_ref):
        return response

    with oda.uow() as uow:
        if prj_id not in uow.prjs:
            raise KeyError(
                f"Not found. The requested prj_id {prj_id} could not be found."
            )

        persisted_prj = uow.prjs_status_history.add(prj_status_history)
        uow.commit()
    return persisted_prj


@prj_router.get(
    "/status/history",
    tags=["PRJ"],
    summary="Get specific Project status history by identifier and version",
    response_model=List[ProjectStatusHistory],
    responses=GET_ID_PRJ_STATUS_MODEL,
)
def get_prj_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> List[ProjectStatusHistory]:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, ProjectStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(query_params), QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        prjs_status_history = uow.prjs_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not prjs_status_history:
            raise KeyError("not found")

    return prjs_status_history


def _get_prj_status(uow, prj_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an Project ID and Version and returns status
    :param: uow: ODA PostgresUnitOfWork
    :param prj_id: project ID
    :param version: project version

    Returns retrieved project status in Dictionary format

    """

    retrieved_prj = uow.prjs_status_history.get(
        entity_id=prj_id, version=version, is_status_history=False
    )

    return retrieved_prj
