from http import HTTPStatus
from typing import Dict, Generic, List, Literal, TypeVar

from pydantic import BaseModel
from ska_oso_pdm import OSOExecutionBlock, Project, SBDefinition, SBInstance
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    ProjectStatus,
    SBDStatus,
    SBIStatus,
)

T = TypeVar("T")


class EBStatusModel(OSOExecutionBlock):
    status: OSOEBStatus


class SBDefinitionStatusModel(SBDefinition):
    status: SBDStatus


class SBInstanceStatusModel(SBInstance):
    status: SBIStatus


class ProjectStatusModel(Project):
    status: ProjectStatus


class EntityStatusResponse(BaseModel):
    entity_type: Literal["sbi", "eb", "prj", "sbd"]
    statuses: Dict[str, str]


class ApiResponse(BaseModel, Generic[T]):
    result_data: List[T] | Dict[str, T] | str
    result_status: str
    result_code: HTTPStatus = HTTPStatus.OK
