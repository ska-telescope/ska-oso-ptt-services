"""
The flask_oda module contains code used to interface Flask applications with
the ODA.
"""
import logging

from flask import _app_ctx_stack, current_app  # pylint: disable=no-name-in-module
from ska_db_oda.unit_of_work.postgresunitofwork import (
    PostgresUnitOfWork,
    create_connection_pool,
)

LOGGER = logging.getLogger(__name__)


class FlaskODA(object):
    """
    FlaskODA is asmall Flask extension that makes the ODA backend available to
    Flask apps.

    This extension present two properties that can be used by Flask code to access
    the ODA. The extension should ensure that the correct scope is used; that is,
    one unique repository per Flask app and a unique UnitOfWork per HTTP request.

    The backend type is set by the ODA_BACKEND_TYPE environment variable.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """
        Initialise ODA Flask extension.
        """
        app.extensions["oda"] = self

    @property
    def uow(self):
        # Lazy creation of one UnitOfWork instance per HTTP request
        # UoW instances are not shared as concurrent modification of a single
        # UoW could easily lead to corruption
        ctx = _app_ctx_stack.top
        if ctx is not None:
            uow = PostgresUnitOfWork(self.connection_pool)
            ctx.uow = uow

            return ctx.uow

    @property
    def connection_pool(self):
        # Lazy creation of one psycopg ConnectionPool instance per Flask application
        if not hasattr(current_app, "connection_pool"):
            current_app.connection_pool = create_connection_pool()
        return current_app.connection_pool
