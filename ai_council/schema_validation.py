from __future__ import annotations

from typing import Any


class SchemaValidationError(ValueError):
    pass


def _fail(path: str, message: str) -> None:
    raise SchemaValidationError(f"{path}: {message}")


def validate_schema(instance: Any, schema: dict[str, Any], path: str = "$") -> None:
    """Validate the JSON-Schema subset used by AI Council.

    Supported keywords are deliberately small and deterministic: type, enum,
    properties, required, additionalProperties, items, maxItems, minLength and maxLength.
    This keeps local/Codex structured output validation independent of another
    package while still enforcing every schema contract used in this project.
    """
    if not isinstance(schema, dict):
        _fail(path, "schema must be an object")

    expected = schema.get("type")
    if expected:
        type_ok = {
            "object": isinstance(instance, dict),
            "array": isinstance(instance, list),
            "string": isinstance(instance, str),
            "boolean": isinstance(instance, bool),
            "integer": isinstance(instance, int) and not isinstance(instance, bool),
            "number": isinstance(instance, (int, float)) and not isinstance(instance, bool),
            "null": instance is None,
        }.get(str(expected), True)
        if not type_ok:
            _fail(path, f"expected {expected}, got {type(instance).__name__}")

    if "enum" in schema and instance not in schema["enum"]:
        _fail(path, f"value {instance!r} is not in enum")

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < int(schema["minLength"]):
            _fail(path, f"string is shorter than minLength={schema['minLength']}")
        if "maxLength" in schema and len(instance) > int(schema["maxLength"]):
            _fail(path, f"string exceeds maxLength={schema['maxLength']}")

    if isinstance(instance, list):
        if "maxItems" in schema and len(instance) > int(schema["maxItems"]):
            _fail(path, f"array exceeds maxItems={schema['maxItems']}")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for idx, value in enumerate(instance):
                validate_schema(value, item_schema, f"{path}[{idx}]")

    if isinstance(instance, dict):
        props = schema.get("properties") or {}
        required = schema.get("required") or []
        for key in required:
            if key not in instance:
                _fail(path, f"missing required property {key!r}")
        if schema.get("additionalProperties") is False:
            extras = sorted(set(instance) - set(props))
            if extras:
                _fail(path, f"unexpected properties: {', '.join(extras)}")
        for key, value in instance.items():
            child = props.get(key)
            if isinstance(child, dict):
                validate_schema(value, child, f"{path}.{key}")
