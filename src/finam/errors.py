"""
FINAM-specific error types.

Errors
======

.. autosummary::
   :toctree: generated

    :noindex: FinamDataError
    :noindex: FinamLogError
    :noindex: FinamMetaDataError
    :noindex: FinamNoDataError
    :noindex: FinamStatusError
    :noindex: FinamTimeError
"""


class FinamStatusError(Exception):
    """Error for unexpected status in Components."""


class FinamTimeError(Exception):
    """Error for request time not matching available data timestamps."""


class FinamLogError(Exception):
    """Error for wrong logging configuration."""


class FinamNoDataError(Exception):
    """Error for data not yet being available."""


class FinamMetaDataError(Exception):
    """Error for missing but required metadata."""


class FinamDataError(Exception):
    """Error for wrong data."""


class FinamStaticDataError(Exception):
    """Error for operations that are not allowed on static inputs or outputs."""


class FinamConnectError(Exception):
    """Error for wrong connection setup."""


class FinamCircularCouplingError(Exception):
    """Error for unresolved circular or bidirectional coupling."""
