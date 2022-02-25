"""
Specialized data types for exchanges between models/modules.
"""


def assert_type(cls, slot, obj, types):
    """Type assertion."""
    for t in types:
        if isinstance(obj, t):
            return
    raise Exception(
        f"Unsupported data type for {slot} in {cls.__class__.__name__}: {obj.__class__.__name__}. "
        f"Expected one of [{', '.join(map(lambda tp: tp.__name__, types))}]"
    )
