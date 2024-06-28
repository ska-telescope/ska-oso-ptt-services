"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-except
import logging
from functools import wraps
from http import HTTPStatus
from typing import Callable, Tuple, Union

from ska_db_oda.domain.query import QueryParams
from ska_db_oda.rest.api.resources import get_qry_params

from ska_oso_ptt_services.rest import oda

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
def get_sbd(sbd_id: str) -> Response:
    """
    Function that a GET /sbds/<sbd_id> request is routed to.

    :param sbd_id: Requested identifier from the path parameter
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    with oda.uow as uow:
        retrieved_sbd = uow.sbds.get(sbd_id)
        get_sbd_status(retrieved_sbd)
    return retrieved_sbd, HTTPStatus.OK

@error_handler
def get_sbds(**kwargs) -> Response:
    """
    Function that a GET /sbds request is routed to.

    :param kwargs: Parameters to query the ODA by.
    :return: The SBDefinition wrapped in a Response, or appropriate error Response
    """
    if not isinstance(maybe_qry_params := get_qry_params(kwargs), QueryParams):
        return maybe_qry_params

    with oda.uow as uow:
        import pdb
        pdb.set_trace()
        sbds = uow.sbds.query(maybe_qry_params)

        for sbd in sbds:
            get_sbd_status(sbd)

    return sbds, HTTPStatus.OK


def get_sbd_status(sbd):
    with oda.uow as uow:
        retrieved_sbd = uow.sbds_status_history.get(entity_id=sbd.sbd_id, version=sbd.metadata.version, is_status_history=False)
        sbd["status"] =  retrieved_sbd if retrieved_sbd else None