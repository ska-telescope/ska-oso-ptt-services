import json
import logging
from http import HTTPStatus
from pathlib import Path
from typing import Dict, Union

from fastapi import APIRouter, Depends
from ska_db_oda.constant import EBS
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.errors import ODANotFound, StatusHistoryException
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params, identifier_check
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import OSOEBStatus, OSOEBStatusHistory

# Get the directory of the current script
current_dir = Path(__file__).parent

LOGGER = logging.getLogger(__name__)

# Ideally would prefix this with ebs but the status entities do not follow the pattern
eb_router = APIRouter()


@eb_router.get(
    "/ebs/{eb_id}",
    tags=["EB"],
    summary="Get Execution Block by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
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
                "application/json": {"example": {"message": "Invalid Shift Id"}}
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
def get_eb_with_status(eb_id: str) -> Response:
    """
    Function that a GET /ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :return: The ExecutionBlock with status wrapped in a Response,
        or appropriate error Response
    """
    with oda.uow as uow:
        eb = uow.ebs.get(eb_id)
        eb_json = eb.model_dump(mode="json")
        eb_json["status"] = _get_eb_status(
            uow=uow, eb_id=eb_id, version=eb_json["metadata"]["version"]
        )["current_status"]

    return eb_json, HTTPStatus.OK


eb_router.get(
    "/ebs",
    tags=["EBS"],
    summary="Get Execution Block filter by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
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
                "application/json": {"example": {"message": "Invalid Shift Id"}}
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


def get_ebs_with_status(**kwargs) -> Response:
    """
    Function that a GET /ebs request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(kwargs)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        ebs = uow.ebs.query(maybe_qry_params)
        eb_with_status = [
            {
                **eb.model_dump(mode="json"),
                "status": _get_eb_status(
                    uow=uow, eb_id=eb.eb_id, version=eb.metadata.version
                )["current_status"],
            }
            for eb in ebs
        ]
    return eb_with_status, HTTPStatus.OK


def _get_eb_status(uow, eb_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an EB ID and Version and returns status
    :param: uow: ODA PostgresUnitOfWork
    :param sbd_id: Execution Block ID
    :param version: EB version

    Returns retrieved EB status in Dictionary format

    """

    retrieved_eb = uow.ebs_status_history.get(
        entity_id=eb_id, version=version, is_status_history=False
    )

    return retrieved_eb.model_dump()


eb_router.get(
    "/status/history/eb",
    tags=["EB"],
    summary="Get Execution Block status history by the query parameter",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
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
                "application/json": {"example": {"message": "Invalid Shift Id"}}
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


def get_eb_status(eb_id: str, version: int = None) -> Response:
    """
    Function that a GET status/ebs/<eb_id> request is routed to.
    This method is used to GET the current status for the given eb_id

    :param eb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,OSOEBStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow as uow:
        eb_status = _get_eb_status(uow=uow, eb_id=eb_id, version=version)
    return eb_status, HTTPStatus.OK


eb_router.get(
    "/ebs/{eb_id}",
    tags=["EB"],
    summary="Get Execution Block by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
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
                "application/json": {"example": {"message": "Invalid Shift Id"}}
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


def put_eb_history(eb_id: str, body: dict) -> Response:
    """
    Function that a PUT status/ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: ExecutionBlock to persist from the request body
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """

    try:
        eb_status_history = OSOEBStatusHistory(
            eb_ref=eb_id,
            eb_version=body["eb_version"],
            previous_status=OSOEBStatus(body["previous_status"]),
            current_status=OSOEBStatus(body["current_status"]),
        )

    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(eb_id, eb_status_history.eb_ref):
        return response

    with oda.uow as uow:
        if eb_id not in uow.ebs:
            raise KeyError(
                f"Not found. The requested eb_id {eb_id} could not be found."
            )
        persisted_eb = uow.ebs_status_history.add(eb_status_history)
        uow.commit()
    return (persisted_eb, HTTPStatus.OK)


eb_router.get(
    "/ebs/{eb_id}",
    tags=["EB"],
    summary="Get Execution Block by identifier",
    responses={
        200: {
            "description": "Successful Response",
            "content": {
                "application/json": {
                    "example": [
                        json.loads(
                            (
                                current_dir / "response_files/shift_response.json"
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
                "application/json": {"example": {"message": "Invalid Shift Id"}}
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
def get_eb_status_history(**kwargs) -> Response:
    """
    Function that a GET /status/ebs request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, OSOEBStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        ebs_status_history = uow.ebs_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not ebs_status_history:
            raise KeyError("not found")

    return ebs_status_history, HTTPStatus.OK
