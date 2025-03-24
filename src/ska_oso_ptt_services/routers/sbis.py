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
from ska_oso_pdm.entity_status_history import SBIStatusHistory

# Get the directory of the current script
current_dir = Path(__file__).parent

LOGGER = logging.getLogger(__name__)

# Ideally would prefix this with ebs but the status entities do not follow the pattern
sbi_router = APIRouter(prefix="/sbis")


@sbi_router.get(
    "/",
    tags=["SBI"],
    summary="Get SB Instance filter by the query parameter",
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
def get_sbis_with_status(
    query_params: ApiQueryParameters = Depends(),
):
    """
    Function that a GET /sbis request is routed to.

    :param kwargs: Parameters to query the ODA by.
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
                "status": _get_sbi_status(
                    uow=uow, sbi_id=sbi.sbi_id, version=sbi.metadata.version
                )["current_status"],
            }
            for sbi in sbis
        ]
    return sbi_with_status, HTTPStatus.OK


@sbi_router.get(
    "/{sbi_id}",
    tags=["SBI"],
    summary="Get SB Instance by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/sbi_status_response.json"
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
def get_sbi_with_status(sbi_id: str):
    """
    Function that a GET /sbis/<sbi_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBInstance with status wrapped in a Response,
         or appropriate error Response
    """
    with oda.uow() as uow:
        sbi = uow.sbis.get(sbi_id)
        sbi_json = sbi.model_dump(mode="json")
        sbi_json["status"] = _get_sbi_status(
            uow=uow, sbi_id=sbi_id, version=sbi_json["metadata"]["version"]
        )["current_status"]
    return sbi_json, HTTPStatus.OK


@sbi_router.get(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Get SB Instance status history by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/sbi_status_response.json"
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
def get_sbi_status(sbi_id: str, version: int = None):
    """
    Function that a GET status/sbi/<sbi_id> request is routed to.
    This method is used to GET the current status for the given sbi_id

    :param sb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,SBIStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow() as uow:
        sbi_status = _get_sbi_status(uow=uow, sbi_id=sbi_id, version=version)
    return sbi_status, HTTPStatus.OK


@sbi_router.put(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Update SB Instance status by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/sbi_status_response.json"
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
def put_sbi_history(sbi_id: str, sbi_status_history: SBIStatusHistory):
    """
    Function that a PUT  /status/sbis/<sbi_id> request is routed to.

    :param sbi_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: SBInstance to persist from the request body
    :return: The SBInstance wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(sbi_id, sbi_status_history.sbi_ref):
        return response

    with oda.uow() as uow:
        if sbi_id not in uow.sbis:
            raise KeyError(
                f"Not found. The requested sbi_id {sbi_id} could not be found."
            )

        persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
        uow.commit()
    return (persisted_sbi, HTTPStatus.OK)


@sbi_router.get(
    "/status/history",
    tags=["SBI"],
    summary="Get SB Instance status history by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir
                                / "response_files/sbi_status_history_response.json"
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
def get_sbi_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
):
    """
    Function that a GET /status/history/sbis request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
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
            raise KeyError("not found")

    return sbis_status_history, HTTPStatus.OK


def _get_sbi_status(uow, sbi_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an SBInstance ID and Version and returns status
    param sbd_id: SBInstance ID
    :param version: SBI version

    Returns retrieved SBI status in Dictionary format

    """

    retrieved_sbi = uow.sbis_status_history.get(
        entity_id=sbi_id, version=version, is_status_history=False
    )
    return retrieved_sbi.model_dump()
