"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""
# pylint: disable=broad-except

import logging
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, Tuple, Union

from ska_db_oda.domain import StatusHistoryException
from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import (
    check_for_mismatch,
    error_response,
    validation_response,
)
from ska_oso_pdm.entity_status_history import OSOEBStatus, OSOEBStatusHistory

from ska_oso_ptt_services.rest import oda

LOGGER = logging.getLogger(__name__)

Response = Tuple[Union[dict, list], int]


class PTTQueryParamsFactory(QueryParamsFactory):
    pass


# for query params exyension
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


def error_handler(api_fn: Callable[[str], Response]) -> Callable[[str], Response]:
    """
    A decorator function to catch general errors and wrap in the correct HTTP response

    :param api_fn: A function which accepts an entity identifier and returns
        an HTTP response
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
                    "eb_id not being found in the ODA."
                )
                return error_response(err)

        except StatusHistoryException as e:
            return {"detail": str(e.args[0])}, HTTPStatus.UNPROCESSABLE_ENTITY

        except Exception as e:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper


@error_handler
def get_eb_with_status(eb_id: str) -> Response:
    """
    Function that a GET /ebs/<eb_id> request is routed to.

    :param eb_id: Requested identifier from the path parameter
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """
    with oda.uow as uow:
        eb = uow.ebs.get(eb_id)
        eb_json = eb.model_dump(mode="json")
        eb_json["status"] = _get_eb_status(eb_id, eb_json["metadata"]["version"])[
            "current_status"
        ]

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
                "status": _get_eb_status(eb.eb_id, eb.metadata.version)[
                    "current_status"
                ],
            }
            for eb in ebs
        ]
    return eb_with_status, HTTPStatus.OK


def _get_eb_status(eb_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an EB ID and Version and returns status
    """
    with oda.uow as uow:
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
    eb_status = _get_eb_status(eb_id=eb_id, version=version)
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

    return persisted_eb, HTTPStatus.OK


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
    :return: The SBDefinition with status wrapped in a Response,
         or appropriate error Response
    """
    with oda.uow as uow:
        sbi = uow.sbis.get(sbi_id)
        sbi_json = sbi.model_dump(mode="json")
        sbi_json["status"] = _get_sbi_status(sbi_id, sbi_json["metadata"]["version"])[
            "current_status"
        ]
    return sbi_json, HTTPStatus.OK


@error_handler
def get_sbis_with_status(**kwargs) -> Response:
    """
    Function that a GET /sbis request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All ExecutionBlocks present with status wrapped in a Response,
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
                "status": _get_sbi_status(sbi.sbi_id, sbi.metadata.version)[
                    "current_status"
                ],
            }
            for sbi in sbis
        ]
    return sbi_with_status, HTTPStatus.OK


def _get_sbi_status(sbi_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an EB ID and Version and returns status
    """
    with oda.uow as uow:
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
    :return: The current entity status,OSOEBStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    sbi_status = _get_sbi_status(sbi_id=sbi_id, version=version)
    return sbi_status, HTTPStatus.OK


@error_handler
def get_sbi_status_history(**kwargs) -> Response:
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
        sbis_status_history = uow.sbis_status_history.query(
            maybe_qry_params, is_status_history=True
        )
        if not sbis_status_history:
            raise KeyError("not found")

    return sbis_status_history, HTTPStatus.OK
