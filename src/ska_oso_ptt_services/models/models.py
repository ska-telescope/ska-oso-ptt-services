from typing import Dict, Literal

from pydantic import BaseModel
from ska_oso_pdm import OSOExecutionBlock, Project, SBDefinition, SBInstance
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    ProjectStatus,
    SBDStatus,
    SBIStatus,
)


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
