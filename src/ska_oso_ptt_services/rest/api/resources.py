"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import json
import logging
from http import HTTPStatus
from os import getenv
from typing import Any, Dict, Tuple, Union

from ska_db_oda.domain import CODEC, StatusHistoryException
from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import (
    check_for_mismatch,
    error_handler,
    validation_response,
)
from ska_oso_pdm import OSOExecutionBlock, SBDStatusHistory
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    OSOEBStatusHistory,
    ProjectStatus,
    ProjectStatusHistory,
    SBDStatus,
    SBIStatus,
    SBIStatusHistory,
)

from ska_oso_ptt_services.rest import oda

LOGGER = logging.getLogger(__name__)

ODA_BACKEND_TYPE = getenv("ODA_BACKEND_TYPE", "rest")

Response = Tuple[Union[dict, list], int]


class PTTQueryParamsFactory(QueryParamsFactory):
    """
    Class for checking Query Parameters
    overrides QueryParamsFactory
    """

    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        """
        Returns QueryParams instance if validation successful
        param kwargs: Parameters Passed
        raises: ValueError for incorrect values
        """

        return QueryParamsFactory.from_dict(kwargs=kwargs)


def get_qry_params(kwargs: dict) -> Union[QueryParams, Response]:
    """
    Convert the parameters from the request into QueryParams.

    Currently only a single instance of QueryParams is supported, so
    subsequent parameters will be ignored.

    :param kwargs: Dict with parameters from HTTP GET request
    :return: An instance of QueryParams
    :raises: TypeError if a supported QueryParams cannot be extracted
    """

    try:
        return PTTQueryParamsFactory.from_dict(kwargs)
    except ValueError as err:
        return validation_response(
            "Not Supported",
            err.args[0],
            HTTPStatus.BAD_REQUEST,
        )


@error_handler
def get_sbd_with_status(sbd_id: str) -> Response:
    """
    Function that a GET /sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBDefinition with status wrapped in a Response, or appropriate error
     Response
    """
    with oda.uow as uow:
        sbd = uow.sbds.get(sbd_id)
        sbd_json = sbd.model_dump(mode="json")
        sbd_json["status"] = _get_sbd_status(
            uow=uow, sbd_id=sbd_id, version=sbd_json["metadata"]["version"]
        )["current_status"]
    return sbd_json, HTTPStatus.OK


@error_handler
def get_sbds_with_status(**kwargs) -> Response:
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All SBDefinitions present with status wrapped in a Response, or appropriate
     error Response
    """
    maybe_qry_params = get_qry_params(kwargs)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
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


@error_handler
def put_eb(eb_id: str, body: dict) -> Response:
    """
    Function that a PUT /ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :param body: ExecutionBlock to persist from the request body
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """
    LOGGER.info(
        " put_eb oda.uow  Initializing ODA filesystem backend. Working directory=%s",
        oda.uow,
    )
    eb = CODEC.loads(OSOExecutionBlock, json.dumps(body))
    if response := check_for_mismatch(eb_id, eb.eb_id):
        return response

    with oda.uow as uow:
        # Check the identifier already exists - after refactoring for BTN-3000
        # this check could be done within the add method
        if eb_id not in uow.ebs:
            raise KeyError(
                f"Not found. The requested eb_id {eb_id} could not be found."
            )
        persisted_eb = uow.ebs.add(eb, is_entity_update=True)
        uow.commit()

    return persisted_eb, HTTPStatus.OK


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


@error_handler
def get_sbd_status(sbd_id: str, version: str = None) -> Dict[str, Any]:
    """
    Function that a GET status/sbds/<sbd_id> request is routed to.
    This method is used to GET the current status for the given sbd_id

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status, SBDStatusHistory wrapped in a Response, or
    appropriate error Response
    """
    with oda.uow as uow:
        sbd_status = _get_sbd_status(uow=uow, sbd_id=sbd_id, version=version)

    return sbd_status, HTTPStatus.OK


@error_handler
def put_sbd_history(sbd_id: str, version: int, body: dict) -> Response:
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: SBDefinition to persist from the request body
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    try:
        sbd_status_history = SBDStatusHistory(
            sbd_ref=sbd_id,
            previous_status=SBDStatus(body["previous_status"]),
            current_status=SBDStatus(body["current_status"]),
            metadata={"version": version},
        )

    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(sbd_id, sbd_status_history.sbd_ref):
        return response

    with oda.uow as uow:
        if sbd_id not in uow.sbds:
            raise KeyError(
                f"Not found. The requested sbd_id {sbd_id} could not be found."
            )

        persisted_sbd = uow.sbds_status_history.add(sbd_status_history)

        uow.commit()
        if ODA_BACKEND_TYPE == "rest":
            persisted_sbd = _get_sbd_status(
                uow=uow, sbd_id=persisted_sbd.sbd_ref, version=version
            )
    return (persisted_sbd, HTTPStatus.OK)


@error_handler
def get_sbd_status_history(**kwargs) -> Response:
    """
    Function that a GET /status/sbds request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, SBDStatusHistory wrapped in a Response, or appropriate
     error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        sbds_status_history = uow.sbds_status_history.query(
            maybe_qry_params, is_status_history=True
        )

        if not sbds_status_history:
            raise KeyError("not found")
    return sbds_status_history, HTTPStatus.OK


@error_handler
def put_sbi_history(sbi_id: str, version: int, body: dict) -> Response:
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbi_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: SBInstance to persist from the request body
    :return: The SBInstance wrapped in a Response, or appropriate error Response
    """
    try:
        sbi_status_history = SBIStatusHistory(
            sbi_ref=sbi_id,
            previous_status=SBIStatus(body["previous_status"]),
            current_status=SBIStatus(body["current_status"]),
            metadata={"version": version},
        )
    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(sbi_id, sbi_status_history.sbi_ref):
        return response

    with oda.uow as uow:
        if sbi_id not in uow.sbis:
            raise KeyError(
                f"Not found. The requested sbi_id {sbi_id} could not be found."
            )

        persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
        uow.commit()
        if ODA_BACKEND_TYPE == "rest":
            persisted_sbi = _get_sbi_status(
                uow=uow, sbi_id=persisted_sbi.sbi_ref, version=version
            )
    return (persisted_sbi, HTTPStatus.OK)


@error_handler
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


@error_handler
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


@error_handler
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


@error_handler
def put_eb_history(eb_id: str, version: int, body: dict) -> Response:
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
            previous_status=OSOEBStatus(body["previous_status"]),
            current_status=OSOEBStatus(body["current_status"]),
            metadata={"version": version},
        )
        LOGGER.debug("eb_status_history repo_bridge %s", eb_status_history)

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
        if ODA_BACKEND_TYPE == "rest":
            persisted_eb = _get_eb_status(
                uow=uow, eb_id=persisted_eb.eb_ref, version=version
            )
    return (persisted_eb, HTTPStatus.OK)


@error_handler
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


@error_handler
def get_sbi_with_status(sbi_id: str) -> Response:
    """
    Function that a GET /sbis/<sbi_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBInstance with status wrapped in a Response,
         or appropriate error Response
    """
    with oda.uow as uow:
        sbi = uow.sbis.get(sbi_id)
        sbi_json = sbi.model_dump(mode="json")
        sbi_json["status"] = _get_sbi_status(
            uow=uow, sbi_id=sbi_id, version=sbi_json["metadata"]["version"]
        )["current_status"]
    return sbi_json, HTTPStatus.OK


@error_handler
def get_sbis_with_status(**kwargs) -> Response:
    """
    Function that a GET /sbis request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All SBInstance present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(kwargs)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
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


@error_handler
def get_sbi_status(sbi_id: str, version: int = None) -> Response:
    """
    Function that a GET status/sbi/<sbi_id> request is routed to.
    This method is used to GET the current status for the given sbi_id

    :param sb_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,SBIStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow as uow:
        sbi_status = _get_sbi_status(uow=uow, sbi_id=sbi_id, version=version)
    return sbi_status, HTTPStatus.OK


@error_handler
def get_sbi_status_history(**kwargs) -> Response:
    """
    Function that a GET /status/history/sbis request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, SBIStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        sbis_status_history = uow.sbis_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not sbis_status_history:
            raise KeyError("not found")

    return sbis_status_history, HTTPStatus.OK


@error_handler
def get_prj_with_status(prj_id: str) -> Response:
    """
    Function that a GET /prjs/<prj_id> request is routed to.

    :param prj_id: Requested identifier from the path parameter
    :return: The Project with status wrapped in a Response,
        or appropriate error Response
    """
    with oda.uow as uow:
        prj = uow.prjs.get(prj_id)
        prj_json = prj.model_dump(mode="json")
        prj_json["status"] = _get_prj_status(
            uow=uow, prj_id=prj_id, version=prj_json["metadata"]["version"]
        )["current_status"]

    return prj_json, HTTPStatus.OK


@error_handler
def get_prjs_with_status(**kwargs) -> Response:
    """
    Function that a GET /prjs request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All Project present with status wrapped in a Response,
         or appropriate error Response
    """
    maybe_qry_params = get_qry_params(kwargs)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
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

    return retrieved_prj.model_dump()


@error_handler
def get_prj_status(prj_id: str, version: int = None) -> Response:
    """
    Function that a GET status/prjs/<prj_id> request is routed to.
    This method is used to GET the current status for the given prj_id

    :param prj_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :return: The current entity status,ProjectStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    with oda.uow as uow:
        prj_status = _get_prj_status(uow=uow, prj_id=prj_id, version=version)
    return prj_status, HTTPStatus.OK


@error_handler
def put_prj_history(prj_id: str, version: int, body: dict) -> Response:
    """
    Function that a PUT status/prjs/<prj_id> request is routed to.

    :param prj_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: Project to persist from the request body
    :return: The Project wrapped in a Response, or appropriate error Response
    """

    try:
        prj_status_history = ProjectStatusHistory(
            prj_ref=prj_id,
            previous_status=ProjectStatus(body["previous_status"]),
            current_status=ProjectStatus(body["current_status"]),
            metadata={"version": version},
        )

    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(prj_id, prj_status_history.prj_ref):
        return response

    with oda.uow as uow:
        if prj_id not in uow.prjs:
            raise KeyError(
                f"Not found. The requested prj_id {prj_id} could not be found."
            )

        persisted_prj = uow.prjs_status_history.add(prj_status_history)
        uow.commit()
        if ODA_BACKEND_TYPE == "rest":
            persisted_prj = _get_prj_status(
                uow=uow, prj_id=persisted_prj.prj_ref, version=version
            )
    return (persisted_prj, HTTPStatus.OK)


@error_handler
def get_prj_status_history(**kwargs) -> Response:
    """
    Function that a GET /status/prjs request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, ProjectStatusHistory wrapped in a Response,
        or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        prjs_status_history = uow.prjs_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not prjs_status_history:
            raise KeyError("not found")

    return prjs_status_history, HTTPStatus.OK
