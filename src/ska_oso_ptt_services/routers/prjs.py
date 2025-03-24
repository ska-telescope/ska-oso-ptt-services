import json
import logging
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import ProjectStatusHistory

# Get the directory of the current script
current_dir = Path(__file__).parent

LOGGER = logging.getLogger(__name__)

# Ideally would prefix this with ebs but the status entities do not follow the pattern
prj_router = APIRouter(prefix="/prjs")


@prj_router.get(
    "/",
    tags=["PRJ"],
    summary="Get Project filter by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/prj_with_status_response.json"
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
def get_prjs_with_status(query_params: ApiQueryParameters = Depends()):
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
                )["current_status"],
            }
            for prj in prjs
        ]
    return prj_with_status, HTTPStatus.OK


@prj_router.get(
    "/{prj_id}",
    tags=["PRJ"],
    summary="Get Project by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/prj_with_status_response.json"
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
def get_prj_with_status(prj_id: str):
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
        )["current_status"]

    return prj_json, HTTPStatus.OK


@prj_router.get(
    "/{prj_id}/status",
    tags=["PRJ"],
    summary="Get Project by identifier",
    response_model=ProjectStatusHistory,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": ProjectStatusHistory,
        }
    },
)
def get_prj_status(prj_id: str, version: int = None) -> ProjectStatusHistory:
    """
    Function that a GET status/prjs/<prj_id> request is routed to.
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
    "/prjs/{prj_id}/status",
    tags=["PRJ"],
    summary="Update Project status by identifier",
    response_model=ProjectStatusHistory,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": ProjectStatusHistory,
        }
    },
)
def put_prj_history(
    prj_id: str, prj_status_history: ProjectStatusHistory
) -> ProjectStatusHistory:
    """
    Function that a PUT status/prjs/<prj_id> request is routed to.

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
    summary="Get Project status history by the query parameter",
    response_model=List[ProjectStatusHistory],
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": List[ProjectStatusHistory],
        }
    },
)
def get_prj_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> List[ProjectStatusHistory]:
    """
    Function that a GET /status/prjs request is routed to.
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
