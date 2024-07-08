"""
Functions which the HTTP requests to individual resources are mapped to.

See the operationId fields of the Open API spec for the specific mappings.
"""

# pylint: disable=broad-except
import logging
from http import HTTPStatus
from typing import Any, Dict, Tuple, Union

from ska_db_oda.domain import StatusHistoryException
from ska_db_oda.domain.query import QueryParams, QueryParamsFactory
from ska_db_oda.rest.api.resources import (
    check_for_mismatch,
    error_handler,
    validation_response,
)
from ska_oso_pdm import SBDStatusHistory
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    OSOEBStatusHistory,
    SBDStatus,
    SBIStatus,
    SBIStatusHistory,
)

from ska_oso_ptt_services.rest import oda

LOGGER = logging.getLogger(__name__)

Response = Tuple[Union[dict, list], int]


class PTTQueryParamsFactory(QueryParamsFactory):
    """
    Class for checking Query Parameters
    overrides QueryParamsFactory
    """

    @staticmethod
    def from_dict(kwargs: dict) -> QueryParams:
        """
        Returns QueryParams instance if validation successfull
        raises: ValueError for incorrect values
        """
        result = QueryParamsFactory.from_dict(kwargs=kwargs)
        return result


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
        sbd_json["status"] = _get_sbd_status(sbd_id, sbd_json["metadata"]["version"])[
            "current_status"
        ]
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
                "status": _get_sbd_status(sbd.sbd_id, sbd.metadata.version)[
                    "current_status"
                ],
            }
            for sbd in sbds
        ]
    return sbd_with_status, HTTPStatus.OK


def _get_sbd_status(sbd_id: str, version: str = None) -> Dict[str, Any]:
    """
    Takes an SBDefinition ID and Version and returns statusz
    :param sbd_id: Scheduling Block ID
    :param version: SBD version

    Returns retrieved SBD status in Dictionary format
    """
    with oda.uow as uow:
        retrieved_sbd = uow.sbds_status_history.get(
            entity_id=sbd_id, version=version, is_status_history=False
        )
        return retrieved_sbd.model_dump()


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

    sbd_status = _get_sbd_status(sbd_id=sbd_id, version=version)

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

    return persisted_sbd, HTTPStatus.OK


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

    return persisted_sbi, HTTPStatus.OK


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
    :param sbd_id: Execution Block ID
    :param version: EB version

    Returns retrieved EB status in Dictionary format

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
    Takes an SBInstance ID and Version and returns status
    param sbd_id: SBInstance ID
    :param version: SBI version

    Returns retrieved SBI status in Dictionary format

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
    :return: The current entity status,SBIStatusHistory wrapped in a
        Response, or appropriate error Response
    """
    sbi_status = _get_sbi_status(sbi_id=sbi_id, version=version)
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
