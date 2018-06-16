from typing import Any, Type


class _Missing:
    """The type of missing values.
    """

    def __repr__(self) -> str:  # pragma: no cover
        return "Missing"


#: Canary value representing missing attributes or values.
Missing = _Missing()


def is_schema(ob: Type[Any]) -> bool:
    """Returns True if the given type is a schema.
    """
    return isinstance(ob, type) and \
        hasattr(ob, "_SCHEMA") and \
        hasattr(ob, "_FIELDS")
