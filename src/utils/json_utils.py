"""
JSON Serialization Utilities

Provides orjson-backed JSON operations with stdlib json-compatible interface.
orjson is ~10x faster than the standard library json module.

Usage:
    from src.utils.json_utils import dumps, loads, dump, load

    # Standard json-like API
    data = {"key": "value"}
    json_str = dumps(data)
    parsed = loads(json_str)
"""

from __future__ import annotations

try:
    import orjson

    def dumps(obj, *, indent: int | None = None, **kwargs) -> str:
        """Serialize obj to JSON string using orjson."""
        if indent is not None:
            return orjson.dumps(obj, option=orjson.OPT_INDENT_2).decode("utf-8")
        return orjson.dumps(obj).decode("utf-8")

    def loads(s) -> dict | list:
        """Deserialize JSON string to Python object."""
        if isinstance(s, str):
            return orjson.loads(s)
        return orjson.loads(s)

    def dump(obj, fp, **kwargs) -> None:
        """Serialize obj to JSON and write to file-like object."""
        fp.write(dumps(obj, **kwargs))

    def load(fp) -> dict | list:
        """Deserialize JSON from file-like object."""
        return loads(fp.read())

except ImportError:
    import json

    def dumps(obj, *, indent: int | None = None, **kwargs) -> str:
        """Fallback to stdlib json if orjson not available."""
        return json.dumps(obj, indent=indent, **kwargs)

    def loads(s) -> dict | list:
        """Fallback to stdlib json if orjson not available."""
        return json.loads(s)

    def dump(obj, fp, **kwargs) -> None:
        """Fallback to stdlib json if orjson not available."""
        json.dump(obj, fp, **kwargs)

    def load(fp) -> dict | list:
        """Fallback to stdlib json if orjson not available."""
        return json.load(fp)
