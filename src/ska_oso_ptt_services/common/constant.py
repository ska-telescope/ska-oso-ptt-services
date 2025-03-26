from enum import EnumMeta
from typing import Dict, List

from fastapi import status
from ska_oso_pdm.entity_status_history import (
    OSOEBStatus,
    OSOEBStatusHistory,
    ProjectStatus,
    ProjectStatusHistory,
    SBDStatus,
    SBDStatusHistory,
    SBIStatus,
    SBIStatusHistory,
)

from ska_oso_ptt_services.models.models import (
    EBStatusModel,
    EntityStatusResponse,
    ProjectStatusModel,
    SBDefinitionStatusModel,
    SBInstanceStatusModel,
)

GET_ALL_EB_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[EBStatusModel],
    }
}


GET_ALL_PRJ_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[ProjectStatusModel],
    }
}


GET_ALL_SBD_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[SBDefinitionStatusModel],
    }
}


GET_ALL_SBI_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[SBInstanceStatusModel],
    }
}


GET_ID_EB_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": EBStatusModel,
    }
}


GET_ID_PRJ_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": ProjectStatusModel,
    }
}


GET_ID_SBD_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": SBDefinitionStatusModel,
    }
}


GET_ID_SBI_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": SBInstanceStatusModel,
    }
}


GET_PUT_ID_EB_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": OSOEBStatusHistory,
    }
}


GET_PUT_ID_PRJ_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": ProjectStatusHistory,
    }
}


GET_PUT_ID_SBD_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": SBDStatusHistory,
    }
}


GET_PUT_ID_SBI_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": SBIStatusHistory,
    }
}


GET_ID_EB_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[OSOEBStatusHistory],
    }
}


GET_ID_PRJ_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[ProjectStatusHistory],
    }
}


GET_ID_SBD_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[SBDStatusHistory],
    }
}

GET_ID_SBI_STATUS_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": List[SBIStatusHistory],
    }
}


GET_ALL_ENTITY_MODEL = {
    status.HTTP_200_OK: {
        "description": "Successful Response",
        "model": EntityStatusResponse,
    }
}


entity_map: Dict[str, EnumMeta] = {
    "sbi": SBIStatus,
    "eb": OSOEBStatus,
    "prj": ProjectStatus,
    "sbd": SBDStatus,
}
