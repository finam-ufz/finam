"""Date and time helper functions"""
from datetime import timedelta

try:
    from dateutil.relativedelta import relativedelta

    _DATEUTIL_INSTALLED = True
except ImportError:
    _DATEUTIL_INSTALLED = False


def is_timedelta(value):
    """
    Tests if a value is an instance of
    :class:`timedelta <datetime.timedelta>` or
    :class:`relativedelta <dateutil.relativedelta.relativedelta>`.
    """
    if isinstance(value, timedelta):
        return True

    if _DATEUTIL_INSTALLED and isinstance(value, relativedelta):
        return True

    return False
