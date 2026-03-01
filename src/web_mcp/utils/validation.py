"""Shared validation utilities for MCP tool inputs."""


def normalize_query(query: str) -> str:
    """Normalize and validate a search query string.

    Strips extra whitespace and ensures the query is non-empty.
    """
    if not isinstance(query, str):
        raise ValueError("query must be a non-empty string")
    normalized = " ".join(query.split())
    if not normalized:
        raise ValueError("query must be a non-empty string")
    return normalized


def normalize_int_param(
    value: int | float | None,
    min_val: int,
    max_val: int,
    default: int,
    param_name: str,
) -> int:
    """Normalize and validate an integer parameter within a range.

    Handles None (returns default), rejects bools, converts whole floats,
    and enforces min/max bounds.
    """
    if value is None:
        return default

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{param_name} must be an integer between {min_val} and {max_val}")

    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{param_name} must be an integer between {min_val} and {max_val}")
        value = int(value)

    resolved = int(value)
    if resolved < min_val or resolved > max_val:
        raise ValueError(f"{param_name} must be between {min_val} and {max_val}")

    return resolved
