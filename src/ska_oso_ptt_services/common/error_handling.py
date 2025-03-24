"""
This module contains FastAPI error handlers which should handle all errors raised by the
ODA, returning a consistent, formatted API response.
"""

import logging
from http import HTTPStatus
from traceback import format_exc
from typing import Optional

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from ska_db_oda.persistence.domain.errors import StatusHistoryException
from ska_db_oda.rest.model import ErrorResponseDetail

LOGGER = logging.getLogger(__name__)


class BadRequestError(HTTPException):
    """Custom class to ensure our errors are formatted consistently"""

    code = HTTPStatus.BAD_REQUEST

    def __init__(
        self,
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        status_code = status_code or self.code
        detail = detail or self.code.description

        super().__init__(status_code=status_code, detail=detail)


class UnprocessableEntityError(BadRequestError):
    code = HTTPStatus.UNPROCESSABLE_ENTITY

    def __init__(self, detail: Optional[str] = None):
        super().__init__(detail=detail)


class NotFoundError(BadRequestError):
    code = HTTPStatus.NOT_FOUND

    def __init__(self, detail: Optional[str] = None):
        super().__init__(detail=detail)


class ODAError(RuntimeError):
    """
    General exception raised by the ODA when other errors aren't applicable
    """

    def __init__(self, message: Optional[str] = None) -> None:
        if message:
            self.message = message


class QueryParameterError(ODAError):
    """
    Exception raised when there is a problem with the query parameters,
    e.g. the combination is not allowed
    """

    def __init__(
        self, *, qry_params: Optional[type] = None, message: Optional[str] = None
    ) -> None:
        if message:
            pass
        elif qry_params:
            message = f"Unsupported query type {qry_params.__class__.__name__}"
        else:
            message = "Exception raised while handling query parameters"

        super().__init__(message)


class ODANotFound(ODAError):
    """
    Exception raised when an entity cannot be found in the data store
    """

    def __init__(
        self, *, identifier: Optional[str] = None, message: Optional[str] = None
    ) -> None:
        if message:
            pass
        elif identifier:
            message = f"The requested identifier {identifier} could not be found."
        else:
            message = "The requested identifier could not be found."

        super().__init__(message)


async def oda_not_found_handler(request: Request, err: ODANotFound) -> JSONResponse:
    """
    A custom handler function to deal with NotFoundInODA raised by the ODA and
    return the correct HTTP 404 response.
    """
    LOGGER.debug("NotFoundInODA for path parameters %s", request.path_params)
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND, content={"detail": err.message}
    )


async def oda_validation_error_handler(
    _: Request, err: ValueError | QueryParameterError
) -> JSONResponse:
    """
    A custom handler function to deal with ValueError raised by the ODA and
    return the correct HTTP response.
    """
    LOGGER.exception(
        "ValueError occurred when adding entity, likely some semantic validation failed"
    )

    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"detail": err.message},
    )


async def oda_status_error_handler(
    _: Request, err: StatusHistoryException
) -> JSONResponse:
    """
    A custom handler function to deal with StatusHistoryException raised by the ODA and
    return the correct HTTP response.
    """
    return JSONResponse(
        status_code=HTTPStatus.UNPROCESSABLE_ENTITY,
        content={"detail": str(err.args[0])},
    )


async def dangerous_internal_server_handler(
    _: Request, err: Exception, status=HTTPStatus.INTERNAL_SERVER_ERROR
) -> JSONResponse:
    """
    A custom handler function that returns a verbose HTTP 500 response containing
    detailed traceback information.

    This is a 'DANGEROUS' handler because it exposes internal implementation details to
    clients. Do not use in production systems!
    """
    json_response_detail = ErrorResponseDetail(
        title=err.__class__.__name__, description=repr(err), traceback=format_exc()
    )
    return JSONResponse(
        status_code=status,
        content={
            "detail": json_response_detail.model_dump(mode="json", exclude_none=True)
        },
    )
