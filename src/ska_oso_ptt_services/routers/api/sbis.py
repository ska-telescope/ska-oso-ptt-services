from ska_db_oda.persistence.domain.errors import StatusHistoryException
from ska_oso_pdm.entity_status_history import SBIStatus, SBIStatusHistory

# Ideally would prefix this with ebs but the status entities do not follow the pattern
sbi_router = APIRouter()


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
