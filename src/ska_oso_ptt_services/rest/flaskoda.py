import json
import logging
import os

from connexion.apps.flask_app import FlaskJSONEncoder
from flask import _app_ctx_stack, current_app  # pylint: disable=no-name-in-module
from ska_db_oda.persistence.unitofwork.filesystemunitofwork import FilesystemUnitOfWork
from ska_db_oda.persistence.unitofwork.postgresunitofwork import (
    PostgresUnitOfWork,
    create_connection_pool,
)
from ska_oso_pdm import PdmObject

LOGGER = logging.getLogger(__name__)

BACKEND_VAR = "ODA_BACKEND_TYPE"


class PdmJsonEncoder(FlaskJSONEncoder):
    """
    JsonEncoder can handle the encoding of the responses
    which are instances of the generated models.
    This extension can also encode the hand written SBDefinition model.

    It does this by converting the SBDefinition to the generated version,
    which can be handled by the JsonEncoder.

    Once we have settled on a single SBDefinition, this class should be removed.
    """

    def default(self, o):
        if isinstance(o, PdmObject):
            # model_dump_json serialises the model as a string,
            # then we turn this into a dict
            #  so it is properly returned as json by the API
            return json.loads(o.model_dump_json())

        return FlaskJSONEncoder.default(self, o)


class FlaskODA(object):
    """
    FlaskODA is a small Flask extension that makes the ODA backend available to
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
        app.config[BACKEND_VAR] = os.environ.get(
            BACKEND_VAR, default=app.config.setdefault(BACKEND_VAR, "postgres")
        )

        app.extensions["oda"] = self

    @property
    def uow(self):
        # Lazy creation of one UnitOfWork instance per HTTP request
        # UoW instances are not shared as concurrent modification of a single
        # UoW could easily lead to corruption
        ctx = _app_ctx_stack.top
        if ctx is not None:
            if not hasattr(ctx, "uow"):
                if current_app.config[BACKEND_VAR] == "postgres":
                    uow = PostgresUnitOfWork(self.connection_pool)
                else:
                    uow = FilesystemUnitOfWork()
                ctx.uow = uow

            return ctx.uow

    @property
    def connection_pool(self):
        # Lazy creation of one psycopg ConnectionPool instance per Flask application
        if not hasattr(current_app, "connection_pool"):
            current_app.connection_pool = create_connection_pool()
        return current_app.connection_pool
