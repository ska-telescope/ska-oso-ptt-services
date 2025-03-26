from typing import Any, Dict


def common_get_entity_status(
    entity_object, entity_id: str, entity_version: str = None
) -> Dict[str, Any]:
    """
    Takes an entity ID and version and returns status
    :param: entity_object: entity_object
    :param entity_id: Execution Block ID
    :param entity_version: entity_version

    Returns retrieved entity status in Dictionary format

    """

    retrieved_entity = entity_object.get(
        entity_id=entity_id, version=entity_version, is_status_history=False
    )

    return retrieved_entity
