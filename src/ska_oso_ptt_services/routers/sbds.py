import json
import logging
from http import HTTPStatus
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import SBDStatusHistory

# Get the directory of the current script
current_dir = Path(__file__).parent

LOGGER = logging.getLogger(__name__)

# Ideally would prefix this with ebs but the status entities do not follow the pattern
sbd_router = APIRouter(prefix="/sbds")


file_name = "response_files/multiple_sbds_with_status_response.json"


@sbd_router.get(
    "/",
    tags=["SBD"],
    summary="Get SB Definition filter by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [json.loads((current_dir / file_name).read_text())]
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
def get_sbds_with_status(
    query_params: ApiQueryParameters = Depends(),
):
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All SBDefinitions present with status wrapped in a Response, or appropriate
     error Response
    """
    maybe_qry_params = get_qry_params(query_params)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        sbds = uow.sbds.query(maybe_qry_params)
        sbd_with_status = [
            {
                **sbd.model_dump(mode="json"),
                "status": _get_sbd_status(
                    uow=uow, sbd_id=sbd.sbd_id, version=sbd.metadata.version
                )["current_status"],
            }
            for sbd in sbds
        ]
    return sbd_with_status, HTTPStatus.OK


@sbd_router.get(
    "/{sbd_id}",
    tags=["SBD"],
    summary="Get SB Definition by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/sbds_with_status_response.json"
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
def get_sbd_with_status(sbd_id: str):
    """
    Function that a GET /sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBDefinition with status wrapped in a Response, or appropriate error
     Response
    """
    with oda.uow() as uow:
        sbd = uow.sbds.get(sbd_id)
        sbd_json = sbd.model_dump(mode="json")
        sbd_json["status"] = _get_sbd_status(
            uow=uow, sbd_id=sbd_id, version=sbd_json["metadata"]["version"]
        )["current_status"]
    return sbd_json, HTTPStatus.OK


@sbd_router.get(
    "/{sbd_id}/status",
    tags=["SBD"],
    summary="Get SBDefinition by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/sbd_status_response.json"
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
def get_sbd_status(sbd_id: str, version: str = None):
    """
    Function that a GET status/sbds/<sbd_id> request is routed to.
    This method is used to GET the current status for the given sbd_id

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status, SBDStatusHistory wrapped in a Response, or
    appropriate error Response
    """
    with oda.uow() as uow:
        sbd_status = _get_sbd_status(uow=uow, sbd_id=sbd_id, version=version)

    return sbd_status, HTTPStatus.OK


@sbd_router.put(
    "/{sbd_id}/status",
    tags=["SBD"],
    summary="Update SB Definition status by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/sbd_status_response.json"
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
def put_sbd_history(sbd_id: str, sbd_status_history: SBDStatusHistory):
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param sbd_version: Requested identifier from the path parameter
    :param body: SBDefinition to persist from the request body
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(sbd_id, sbd_status_history.sbd_ref):
        return response

    with oda.uow() as uow:
        if sbd_id not in uow.sbds:
            raise KeyError(
                f"Not found. The requested sbd_id {sbd_id} could not be found."
            )

        persisted_sbd = uow.sbds_status_history.add(sbd_status_history)

        uow.commit()
    return (persisted_sbd, HTTPStatus.OK)


@sbd_router.get(
    "/status/history",
    tags=["SBD"],
    summary="Get SB Definition status history by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/sbd_status_history_response.json"
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
def get_sbd_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
):
    """
    Function that a GET /status/sbds request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, SBDStatusHistory wrapped in a Response, or appropriate
     error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(query_params), QueryParams):
        return maybe_qry_params

    with oda.uow() as uow:
        sbds_status_history = uow.sbds_status_history.query(
            maybe_qry_params, is_status_history=True
        )

        if not sbds_status_history:
            raise KeyError("not found")
    return sbds_status_history, HTTPStatus.OK


def _get_sbd_status(uow, sbd_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an SBDefinition ID and Version and returns status
    :param: uow: ODA PostgresUnitOfWork
    :param sbd_id: Scheduling Block ID
    :param version: SBD version

    Returns retrieved SBD status in Dictionary format
    """

    retrieved_sbd = uow.sbds_status_history.get(
        entity_id=sbd_id, version=version, is_status_history=False
    ).model_dump(mode="json")
    return retrieved_sbd
