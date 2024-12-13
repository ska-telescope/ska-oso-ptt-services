"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

import logging
import traceback
from enum import EnumMeta
from functools import wraps
from http import HTTPStatus
from os import getenv
from typing import Any, Callable, Dict, Tuple, Union

from pydantic import ValidationError
from ska_db_oda.persistence.domain.errors import StatusHistoryException
from ska_db_oda.persistence.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api import check_for_mismatch
from ska_oso_pdm import SBDStatusHistory
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

ODA_BACKEND_TYPE = getenv("ODA_BACKEND_TYPE", "postgres")

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


def error_handler(api_fn: Callable[[str], Response]) -> Callable[[str], Response]:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity

     identifier and returns an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError as err:
            # TODO there is a risk that the KeyError is not from the
            #  ODA not being able to find the entity. After BTN-1502 the
            #  ODA should raise its own exceptions which we can catch here
            is_not_found_in_oda = any(
                "not found" in str(arg).lower() for arg in err.args
            )
            if is_not_found_in_oda:
                return {
                    "detail": (
                        "Not Found. The requested identifier"
                        f" {next(iter(kwargs.values()))} could not be found."
                    ),
                }, HTTPStatus.NOT_FOUND
            else:
                LOGGER.exception(
                    "KeyError raised by api function call, but not due to the "
                    "sbd_id not being found in the ODA."
                )
                return error_response(err)
        except (ValueError, ValidationError) as e:
            LOGGER.exception(
                "ValueError occurred when adding entity, likely some semantic"
                " validation failed"
            )

            return error_response(e, HTTPStatus.UNPROCESSABLE_ENTITY)

        except StatusHistoryException as e:
            return {"detail": str(e.args[0])}, HTTPStatus.UNPROCESSABLE_ENTITY

    return wrapper


def error_response(
    err: Exception, http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
) -> Response:
    """
    Creates a general server error response from an exception

    :return: HTTP response server error
    """
    response_body = {
        "title": http_status.phrase,
        "detail": f"{repr(err)} with args {err.args}",
        "traceback": {
            "key": "Internal Server Error",
            "type": str(type(err)),
            "full_traceback": traceback.format_exc(),
        },
    }

    return response_body, http_status


def validation_response(
    title: str, detail: str, http_status: HTTPStatus = HTTPStatus.UNPROCESSABLE_ENTITY
):
    """
    Creates an error response in the case that our validation has failed.
    """
    response_body = {"title": title, "detail": detail}

    return response_body, http_status


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
def put_sbd_history(sbd_id: str, body: dict) -> Response:
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param sbd_version: Requested identifier from the path parameter
    :param body: SBDefinition to persist from the request body
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    try:
        sbd_status_history = SBDStatusHistory(
            sbd_ref=sbd_id,
            sbd_version=body["sbd_version"],
            previous_status=SBDStatus(body["previous_status"]),
            current_status=SBDStatus(body["current_status"]),
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
def put_sbi_history(sbi_id: str, body: dict) -> Response:
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
            sbi_version=body["sbi_version"],
            previous_status=SBIStatus(body["previous_status"]),
            current_status=SBIStatus(body["current_status"]),
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


@error_handler
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
def put_prj_history(prj_id: str, body: dict) -> Response:
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
            prj_version=body["prj_version"],
            previous_status=ProjectStatus(body["previous_status"]),
            current_status=ProjectStatus(body["current_status"]),
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
    return persisted_prj, HTTPStatus.OK


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


@error_handler
def get_entity_status(entity_name: str) -> Tuple[Dict[str, str], HTTPStatus]:
    """
    Function that returns the status dictionary for a given entity type.

    Args:
        entity_name: The name of the entity type (sbi, eb, prj, or sbd)

    Returns:
        Tuple containing dictionary of status names and values, and HTTP status code

    Raises:
        ValueError: If an invalid entity name is provided
    """
    entity_map: Dict[str, EnumMeta] = {
        "sbi": SBIStatus,
        "eb": OSOEBStatus,
        "prj": ProjectStatus,
        "sbd": SBDStatus,
    }

    entity_class = entity_map.get(entity_name.lower())
    if not entity_class:
        raise ValueError(f"Invalid entity name: {entity_name}")

    return {status.name: status.value for status in entity_class}, HTTPStatus.OK
