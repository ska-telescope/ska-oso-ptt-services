"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-except
import logging
from functools import wraps
from http import HTTPStatus
from typing import Any, Callable, Dict, Tuple, Union

from prance import ValidationError
from ska_db_oda.domain import StatusHistoryException
from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import (
    check_for_mismatch,
    error_response,
    validation_response,
)
from ska_oso_pdm import SBDStatusHistory
from ska_oso_pdm.entity_status_history import SBDStatus, SBIStatusHistory, SBIStatus

from ska_oso_ptt_services.rest import oda

LOGGER = logging.getLogger(__name__)

Response = Tuple[Union[dict, list], int]


class PTTQueryParamsFactory(QueryParamsFactory):
    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        result = QueryParamsFactory.from_dict(kwargs=kwargs)
        return result


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

    :param api_fn: A function which accepts an entity identifier and returns an HTTP response
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

        except Exception as e:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(e)

    return wrapper


@error_handler
def get_sbd_with_status(sbd_id: str) -> Response:
    """
    Function that a GET /sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBDefinition with status wrapped in a Response, or appropriate error Response
    """
    with oda.uow as uow:
        import pdb

        pdb.set_trace()
        print("$!!!!!!!!!!! in get_sbd_with_status !!!!!!")
        sbd = uow.sbds.get(sbd_id)
        print(f"@@@@@@@@@@@@@@@@@@@@@@@ \n\n\n {sbd=}")
        sbd_json = sbd.model_dump(mode="json")
        print(f"@@@@@@@@@@@@@@@@@@@@@@@ \n\n\n {sbd_json=}")
        sbd_json["status"] = _get_sbd_status(sbd_id, sbd_json["metadata"]["version"])[
            "current_status"
        ]
        print(f"@@@@@@@@@@@@@@@@@@@@@@@ \n\n\n {sbd_json=}")
    return sbd_json, HTTPStatus.OK


@error_handler
def get_sbds_with_status(**kwargs) -> Response:
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: All SBDefinitions present with status wrapped in a Response, or appropriate error Response
    """
    maybe_qry_params = get_qry_params(kwargs)
    if not isinstance(maybe_qry_params, QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        sbds = uow.sbds.query(maybe_qry_params)
        print(f"@@@@@@@@@@@@@@@@@@@@@@@ \n\n\n {sbds=}")
        sbd_with_status = [
            {
                **sbd.model_dump(mode="json"),
                "status": _get_sbd_status(sbd.sbd_id, sbd.metadata.version)[
                    "current_status"
                ],
            }
            for sbd in sbds
        ]
    return sbd_with_status, HTTPStatus.OK


def _get_sbd_status(sbd_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an SBDefinition ID and Version and returns status
    """
    with oda.uow as uow:
        retrieved_sbd = uow.sbds_status_history.get(
            entity_id=sbd_id, version=version, is_status_history=False
        )
        print(f"##############################{type(retrieved_sbd)=} {retrieved_sbd}")
        return retrieved_sbd.model_dump()


@error_handler
def get_sbd_status(sbd_id: str, version: str = None) -> Dict[str, Any]:
    sbd_status = _get_sbd_status(sbd_id=sbd_id, version=version)

    # if not sbd_status:
    #     raise KeyError("not found")
    print(f"##############################{type(sbd_status)=}")
    return sbd_status, HTTPStatus.OK


@error_handler
def put_sbd_history(sbd_id: str, version: int, body: dict) -> Response:
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: ExecutionBlock to persist from the request body
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """
    try:
        sbd_status_history = SBDStatusHistory(
            sbd_ref=sbd_id,
            previous_status=SBDStatus(body["previous_status"]),
            current_status=SBDStatus(body["current_status"]),
            metadata={"version": version},
        )
        print(
            f"##############################{type(sbd_status_history)=} \n"
            f" {sbd_status_history=}\n\n\n"
        )
    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(sbd_id, sbd_status_history.sbd_ref):
        return response

    with oda.uow as uow:
        import pdb

        pdb.set_trace()
        print(f"##############################{type(uow.sbds)=} \n {uow.sbds=}\n\n\n")
        if sbd_id not in uow.sbds:
            raise KeyError(
                f"Not found. The requested sbd_id {sbd_id} could not be found."
            )

        persisted_sbd = uow.sbds_status_history.add(sbd_status_history)
        print(
            f"##############################{type(persisted_sbd)=} \n"
            f" {persisted_sbd=}\n\n\n"
        )
        uow.commit()

    return persisted_sbd, HTTPStatus.OK


@error_handler
def get_sbd_status_history(**kwargs) -> Response:
    """
    Function that a GET /status/sbds request is routed to.
    This method is used to GET status history for the given entity

    :param kwargs: Parameters to query the ODA by.
    :return: The status history, SBDStatusHistory wrapped in a Response, or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        print("$$$$$$$$$$$$$$$$$$$ Inside UOW $$$$$$$$$$$$$$$$$$$")
        sbds_status_history = uow.sbds_status_history.query(
            maybe_qry_params, is_status_history=True
        )

        if not sbds_status_history:
            raise KeyError("not found")
        print(
            f"##############################{type(sbds_status_history)=} {sbds_status_history}"
        )
    return sbds_status_history, HTTPStatus.OK
    # return jsonify({"a": 1}), HTTPStatus.OK


############SBI#######################


@error_handler
def put_sbi_history(sbi_id: str, version: int, body: dict) -> Response:
    """
    Function that a PUT status/sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :param version: Requested identifier from the path parameter
    :param body: ExecutionBlock to persist from the request body
    :return: The ExecutionBlock wrapped in a Response, or appropriate error Response
    """
    try:
        sbi_status_history = SBIStatusHistory(
            sbi_ref=sbi_id,
            previous_status=SBIStatus(body["previous_status"]),
            current_status=SBIStatus(body["current_status"]),
            metadata={"version": version},
        )
        print(f"##############################{type(sbi_status_history)=} \n {sbi_status_history=}\n\n\n")
    except ValueError as err:
        raise StatusHistoryException(err)  # pylint: disable=W0707

    if response := check_for_mismatch(sbi_id, sbi_status_history.sbi_ref):
        return response

    with oda.uow as uow:
        import pdb

        pdb.set_trace()
        print(f"##############################{type(uow.sbis)=} \n {uow.sbis=}\n\n\n")
        if sbi_id not in uow.sbis:
            raise KeyError(
                f"Not found. The requested sbi_id {sbi_id} could not be found."
            )

        persisted_sbi = uow.sbis_status_history.add(sbi_status_history)
        print(
            f"##############################{type(persisted_sbi)=} \n"
            f" {persisted_sbi=}\n\n\n"
        )
        uow.commit()

    return persisted_sbi, HTTPStatus.OK