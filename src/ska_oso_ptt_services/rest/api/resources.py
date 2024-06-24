"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-except
import logging
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, Union

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
            return err

    return wrapper


@error_handler
def get_sbds(**kwargs):
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    return f"{kwargs} OK", HTTPStatus.OK
