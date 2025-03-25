import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, status
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.query import QueryParams
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import SBIStatusHistory

from ska_oso_ptt_services.models.models import SBInstanceStatusModel

LOGGER = logging.getLogger(__name__)

# Ideally would prefix this with ebs but the status entities do not follow the pattern
sbi_router = APIRouter(prefix="/sbis")


@sbi_router.get(
    "/",
    tags=["SBI"],
    summary="Get All SB Instance with status appended, filter by the query parameter"
    " like created_before, created_after and user name",
    response_model=List[SBInstanceStatusModel],
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": List[SBInstanceStatusModel],
        }
    },
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
                "status": _get_sbi_status(
                    uow=uow, sbi_id=sbi.sbi_id, version=sbi.metadata.version
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
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": SBInstanceStatusModel,
        }
    },
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
        sbi_json["status"] = _get_sbi_status(
            uow=uow, sbi_id=sbi_id, version=sbi_json["metadata"]["version"]
        ).current_status
    return sbi_json


@sbi_router.get(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Get SB Instance status by the identifier",
    response_model=SBIStatusHistory,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": SBIStatusHistory,
        }
    },
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
        sbi_status = _get_sbi_status(uow=uow, sbi_id=sbi_id, version=version)
    return sbi_status


@sbi_router.put(
    "/{sbi_id}/status",
    tags=["SBI"],
    summary="Update specific SB Instance status by identifier",
    response_model=SBIStatusHistory,
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": SBIStatusHistory,
        }
    },
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
            raise KeyError(
                f"Not found. The requested sbi_id {sbi_id} could not be found."
            )

        persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
        uow.commit()
    return persisted_sbi


@sbi_router.get(
    "/status/history",
    tags=["SBI"],
    summary="Get specific SB Instance status history by identifier and version",
    response_model=List[SBIStatusHistory],
    responses={
        status.HTTP_200_OK: {
            "description": "Successful Response",
            "model": List[SBIStatusHistory],
        }
    },
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
            raise KeyError("not found")

    return sbis_status_history


def _get_sbi_status(uow, sbi_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an SB Instance ID and Version and returns status
    :param: uow: ODA PostgresUnitOfWork
    :param sbi_id: SB Instance ID
    :param version: SBI version

    Returns retrieved SBI status in Dictionary format

    """

    retrieved_sbi = uow.sbis_status_history.get(
        entity_id=sbi_id, version=version, is_status_history=False
    )
    return retrieved_sbi
