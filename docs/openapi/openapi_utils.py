def get_param_type(param: dict) -> str:
    def resolve_schema(schema):
        if not isinstance(schema, dict):
            return "unknown"

        # type might be null or missing
        schema_type = schema.get("type", None)

        # Handle top-level compositions
        for key in ("oneOf", "anyOf", "allOf"):
            if key in schema:
                types = [resolve_schema(sub) for sub in schema[key]]
                return f"{key}[{', '.join(types)}]"

        # Handle $ref
        if "$ref" in schema:
            return "ref"

        # Handle arrays
        if schema_type == "array":
            items = schema.get("items")
            if items:
                item_type = resolve_schema(items)
                return f"array[{item_type}]"
            else:
                return "array[unknown]"

        # Return direct type (string, object, etc.)
        return schema_type or "unknown"

    return resolve_schema(param.get("schema", {}))
