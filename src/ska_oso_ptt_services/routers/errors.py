"""
This module contains custom errors that are raised within the `rest` package.
"""

from http import HTTPStatus
from typing import Optional

from fastapi import HTTPException


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
