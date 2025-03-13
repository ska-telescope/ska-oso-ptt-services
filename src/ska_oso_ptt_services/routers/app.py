"""
ska_oso_services app.py
"""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ska_db_oda.persistence import oda
from ska_db_oda.persistence.domain.errors import (
    ODANotFound,
    QueryParameterError,
    StatusHistoryException,
)

from ska_oso_ptt_services.routers.api.ebs import eb_router
from ska_oso_ptt_services.routers.api.prjs import prj_router
from ska_oso_ptt_services.routers.api.sbds import sbd_router
from ska_oso_ptt_services.routers.api.sbis import sbi_router
from ska_oso_ptt_services.routers.error_handling import (
    dangerous_internal_server_handler,
    oda_not_found_handler,
    oda_status_error_handler,
    oda_validation_error_handler,
)

KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-db-oda")
# FIXME: Find a good way to avoid hardcoding this...
# Previously from importlib.metadata import version("ska-db-oda")
ODA_MAJOR_VERSION = "7"
API_PREFIX = f"/{KUBE_NAMESPACE}/oda/api/v{ODA_MAJOR_VERSION}"

PRODUCTION = os.getenv("PRODUCTION", "false").lower() == "true"

LOGGER = logging.getLogger(__name__)


def create_app(production=PRODUCTION) -> FastAPI:
    """
    Create the Connexion application with required config
    """
    LOGGER.info("Creating FastAPI app")

    app = FastAPI(openapi_url=f"{API_PREFIX}/openapi.json", docs_url=f"{API_PREFIX}/ui")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    # Assemble the constituent APIs:
    app.include_router(base_router, prefix=API_PREFIX)
    app.include_router(sbd_router, prefix=API_PREFIX)
    app.include_router(sbi_router, prefix=API_PREFIX)
    app.include_router(eb_router, prefix=API_PREFIX)
    app.include_router(prj_router, prefix=API_PREFIX)
    app.include_router(prsl_router, prefix=API_PREFIX)

    # Add handles for different types of error
    app.exception_handler(ODANotFound)(oda_not_found_handler)
    app.exception_handler(ValueError)(oda_validation_error_handler)
    app.exception_handler(QueryParameterError)(oda_validation_error_handler)
    app.exception_handler(StatusHistoryException)(oda_status_error_handler)

    if not production:
        app.exception_handler(Exception)(dangerous_internal_server_handler)
    return app


main = create_app()
oda.init_app(main)
