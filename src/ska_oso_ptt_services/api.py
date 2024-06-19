"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-except
import logging
import traceback
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, Union

from pydantic import ValidationError

LOGGER = logging.getLogger(__name__)

Response = Tuple[Union[dict], int]


def error_handler(api_fn: Callable[[str], Response]):
    """
    A decorator function to catch general errors and wrap in the
    correct HTTP response.

    :param api_fn: A function which accepts an entity identifier and
        returns an HTTP response
    """

    @wraps(api_fn)
    def wrapper(*args, **kwargs):
        try:
            LOGGER.debug(
                "Request to %s with args: %s and kwargs: %s", api_fn, args, kwargs
            )
            return api_fn(*args, **kwargs)
        except KeyError as err:
            return error_response(err)
        except (ValueError, ValidationError) as error:
            LOGGER.exception(
                "ValueError occurred when adding entity, likely some semantic"
                " validation failed"
            )
            return error_response(error, HTTPStatus.UNPROCESSABLE_ENTITY)
        except Exception as error:
            LOGGER.exception(
                "Exception occurred when calling the API function %s", api_fn
            )
            return error_response(error)

    return wrapper


@error_handler
def get_sbds(**kwargs):
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    return f"{kwargs} OK", HTTPStatus.OK


def error_response(
    err: Exception, http_status: HTTPStatus = HTTPStatus.INTERNAL_SERVER_ERROR
):
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
