import logging
from typing import List

from fastapi import APIRouter, Depends
from ska_db_oda.persistence import oda
from ska_db_oda.rest.api import check_for_mismatch, get_qry_params
from ska_db_oda.rest.model import ApiQueryParameters, ApiStatusQueryParameters
from ska_oso_pdm.entity_status_history import SBDStatusHistory

from ska_oso_ptt_services.common.error_handling import ODANotFound
from ska_oso_ptt_services.common.utils import common_get_entity_status, get_responses
from ska_oso_ptt_services.models.models import SBDefinitionStatusModel

LOGGER = logging.getLogger(__name__)

sbd_router = APIRouter(prefix="/sbds")


@sbd_router.get(
    "",
    tags=["SBD"],
    summary="Get All SB Definition with status appended, filter by the query parameter"
    " like created_before, created_after and user namer",
    response_model=List[SBDefinitionStatusModel],
    responses=get_responses(List[SBDefinitionStatusModel]),
)
def get_sbds_with_status(
    query_params: ApiQueryParameters = Depends(),
) -> List[SBDefinitionStatusModel]:
    """
    Function that a GET /sbds request is routed to.

    :param query_params: Parameters to query the ODA by.
    :return: All SBDefinitions present with status wrapped in a Response, or appropriate
     error Response
    """

    query_params = get_qry_params(query_params)

    with oda.uow() as uow:
        sbds = uow.sbds.query(query_params)
        sbd_with_status = [
            {
                **sbd.model_dump(mode="json"),
                "status": common_get_entity_status(
                    entity_object=uow.sbds_status_history,
                    entity_id=sbd.sbd_id,
                    entity_version=sbd.metadata.version,
                ).current_status,
            }
            for sbd in sbds
        ]
    return sbd_with_status


@sbd_router.get(
    "/{sbd_id}",
    tags=["SBD"],
    summary="Get specific SB Definition by identifier with status appended",
    response_model=SBDefinitionStatusModel,
    responses=get_responses(SBDefinitionStatusModel),
)
def get_sbd_with_status(sbd_id: str) -> SBDefinitionStatusModel:
    """
    Function that a GET /sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBDefinition with status wrapped in a Response, or appropriate error
     Response
    """
    with oda.uow() as uow:
        sbd = uow.sbds.get(sbd_id)
        sbd_json = sbd.model_dump(mode="json")
        sbd_json["status"] = common_get_entity_status(
            entity_object=uow.sbds_status_history,
            entity_id=sbd_id,
            entity_version=sbd_json["metadata"]["version"],
        ).current_status
    return sbd_json


@sbd_router.get(
    "/{sbd_id}/status",
    tags=["SBD"],
    summary="Get specific SB Definition status by the identifier",
    response_model=SBDStatusHistory,
    responses=get_responses(SBDStatusHistory),
)
def get_sbd_status(sbd_id: str, version: str = None) -> SBDStatusHistory:
    """
    Function that a GET /sbds/<sbd_id>/status request is routed to.
    This method is used to GET the current status for the given sbd_id

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status, SBDStatusHistory wrapped in a Response, or
    appropriate error Response
    """
    with oda.uow() as uow:
        sbd_status = common_get_entity_status(
            entity_object=uow.sbds_status_history,
            entity_id=sbd_id,
            entity_version=version,
        )

    return sbd_status


@sbd_router.put(
    "/{sbd_id}/status",
    tags=["SBD"],
    summary="Update specific SB Definition status by identifier",
    response_model=SBDStatusHistory,
    responses=get_responses(SBDStatusHistory),
)
def put_sbd_history(
    sbd_id: str, sbd_status_history: SBDStatusHistory
) -> SBDStatusHistory:
    """
    Function that a PUT /sbds/<sbd_id>/status request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param sbd_status_history: Object of SBDStatusHistory
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """

    if response := check_for_mismatch(sbd_id, sbd_status_history.sbd_ref):
        return response

    with oda.uow() as uow:
        if sbd_id not in uow.sbds:
            raise ODANotFound(identifier=sbd_id)

        persisted_sbd = uow.sbds_status_history.add(sbd_status_history)

        uow.commit()
    return persisted_sbd


@sbd_router.get(
    "/status/history",
    tags=["SBD"],
    summary="Get specific SB Definition status history by identifier and version",
    response_model=List[SBDStatusHistory],
    responses=get_responses(List[SBDStatusHistory]),
)
def get_sbd_status_history(
    query_params: ApiStatusQueryParameters = Depends(),
) -> SBDStatusHistory:
    """
    Function that a GET /status/history request is routed to.
    This method is used to GET status history for the given entity

    :param query_params: Parameters to query the ODA by.
    :return: The status history, SBDStatusHistory wrapped in a Response, or appropriate
     error Response
    """

    query_params = get_qry_params(query_params)

    with oda.uow() as uow:
        sbds_status_history = uow.sbds_status_history.query(
            query_params, is_status_history=True
        )

        if not sbds_status_history:
            raise ODANotFound(identifier=query_params.entity_id)
    return sbds_status_history
