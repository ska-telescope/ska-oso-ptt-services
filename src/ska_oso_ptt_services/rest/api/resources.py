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
    :param Response: This is HTTP Response

    Returns: Returns an HTTP response

    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError as err:
            is_not_found_in_ptt = any(
                "not found" in str(arg).lower() for arg in err.args
            )
            if is_not_found_in_ptt:
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

    :param err: This is Error Exception
    :param http_status: This is HTTP status

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

    :param title: This is title of response
    :param detail: This is detail of response
    :param http_status: This is http status
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
