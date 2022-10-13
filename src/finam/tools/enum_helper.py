"""IOList for Components."""

from enum import Enum


def get_enum_value(value, enum_cls):
    """
    Convert value to corresponding enum value.

    Parameters
    ----------
    value : any
        Value to convert to enum value.
    enum_cls : Enum
        Enumeration class to get value from.

    Returns
    -------
    enum
        Corresponding Enum value.

    Raises
    ------
    ValueError
        If enum_cls is not a subclass of Enum
    ValueError
        If value couldn't be found in given enum class.
    """
    if not isinstance(enum_cls, type) or not issubclass(enum_cls, Enum):
        raise ValueError(f"Class is not of type Enum: {enum_cls}")
    if value in list(enum_cls) and not issubclass(enum_cls, int):
        return value
    if value in [e.value for e in enum_cls]:
        return enum_cls(value)
    if value in [e.name for e in enum_cls]:
        return enum_cls[value]
    raise ValueError(f"Unknown {enum_cls.__name__} value '{value}'")
