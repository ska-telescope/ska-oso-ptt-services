"""ska-oso-ptt-services"""

import os
from importlib.metadata import version
from typing import Any, Dict

import prance
from connexion import App

KUBE_NAMESPACE = os.getenv("KUBE_NAMESPACE", "ska-oso-ptt-services")
PTT_MAJOR_VERSION = version("ska-oso-ptt-services").split(".")[0]
# The base path includes the namespace which is known at runtime
# to avoid clashes in deployments, for example in CICD
API_PATH = f"/{KUBE_NAMESPACE}/ptt/api/v{PTT_MAJOR_VERSION}"


def resolve_openapi_spec() -> Dict[str, Any]:
    """
    Resolves the $ref in the OpenAPI spec before it is used by Connexion,
    as Connexion can't parse them.
    See https://github.com/spec-first/connexion/issues/967
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, "./openapi/ptt-openapi-v1.yaml")
    parser = prance.ResolvingParser(path, lazy=True, strict=True)
    parser.parse()
    return parser.specification


class CustomRequestBodyValidator:  # pylint: disable=too-few-public-methods
    """
    There is a (another) issue with Connexion where it cannot validate against a
    spec with polymorphism, like the SBDefinition.
    See https://github.com/spec-first/connexion/issues/1569
    As a temporary hack, this basically turns off the validation
    """

    def __init__(self, *args, **kwargs):
        pass

    def __call__(self, function):
        return function


def create_app(open_api_spec=None):
    """
    Create the Connexion application with required config
    """

    if open_api_spec is None:
        open_api_spec = resolve_openapi_spec()

    validator_map = {
        "body": CustomRequestBodyValidator,
    }

    connexion = App(__name__, specification_dir="openapi/")

    connexion.add_api(
        open_api_spec,
        arguments={"title": "OpenAPI PTT"},
        base_path=API_PATH,
        pythonic_params=True,
        validator_map=validator_map,
    )

    app = connexion.app

    return app
