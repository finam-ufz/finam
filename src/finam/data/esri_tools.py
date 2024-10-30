"""Common ESRI ASCII grid routines."""

import warnings

import numpy as np

ESRI_TYPES = {
    "ncols": int,
    "nrows": int,
    "xllcorner": float,
    "yllcorner": float,
    "xllcenter": float,
    "yllcenter": float,
    "cellsize": float,
    "nodata_value": float,
}
"""types for ESRI ASCII grid header information."""

ESRI_REQ = {"ncols", "nrows", "xllcorner", "yllcorner", "cellsize"}
"""Required ESRI ASCII grid header information."""


def _is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False


def _extract_header(file):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return np.genfromtxt(
            file, dtype=str, max_rows=6, usecols=(0, 1), invalid_raise=False
        )


def standardize_header(header):
    """
    Standardize an ASCII grid header dictionary.

    Parameters
    ----------
    header : :class:`dict`
        Raw header as dictionary.

    Returns
    -------
    :class:`dict`
        Standardized header as dictionary.

    Raises
    ------
    ValueError
        If the header is missing required information.
        See :any:`ESRI_REQ`
    """
    header = {n: ESRI_TYPES[n](v) for (n, v) in header.items() if n in ESRI_TYPES}
    # convert cell center to corner information
    if "xllcenter" in header:
        header["xllcorner"] = header["xllcenter"] - 0.5 * header.get("cellsize", 1)
        del header["xllcenter"]
    if "yllcenter" in header:
        header["yllcorner"] = header["yllcenter"] - 0.5 * header.get("cellsize", 1)
        del header["yllcenter"]
    # check required header items
    missing = ESRI_REQ - (set(header) & ESRI_REQ)
    if missing:
        msg = f"standardize_header: missing header information {missing}"
        raise ValueError(msg)
    return header


def read_header(file):
    """
    Read an ASCII grid header from file.

    Parameters
    ----------
    file : :class:`~os.PathLike`
        File containing the ASCII grid header.

    Returns
    -------
    :class:`dict`
        Standardized header as dictionary.

    Notes
    -----
    "xllcenter" and "yllcenter" will be converted to
    "xllcorner" and "yllcorner" resepectively.
    """
    header_lines = _extract_header(file)
    return standardize_header(dict(header_lines))


def read_grid(file, dtype=None):
    """
    Read an ASCII grid from file.

    Parameters
    ----------
    file : :class:`~os.PathLike`
        File containing the ASCII grid.
    dtype : str/type, optional
        Data type.
        Needs to be integer or float and compatible with np.dtype
        (i.e. "i4", "f4", "f8"), by default None

    Returns
    -------
    header : dict
        Header describing the grid.
    data : numpy.ndarray
        Data of the grid.

    Raises
    ------
    ValueError
        If data shape is not matching the given header.
    """
    header_lines = _extract_header(file)
    header = standardize_header(dict(header_lines))
    # last line could already be data if "nodata_value" is missing
    numeric_last = _is_number(header_lines[-1][0])
    header_size = len(header_lines) - int(numeric_last)
    data = np.loadtxt(file, dtype=dtype, skiprows=header_size, ndmin=2)
    nrows, ncols = header["nrows"], header["ncols"]
    if data.shape[0] != nrows or data.shape[1] != ncols:
        msg = (
            f"read_grid: data shape {data.shape} "
            f"not matching given header ({nrows=}, {ncols=})."
        )
        raise ValueError(msg)
    if "nodata_value" in header and np.issubdtype(data.dtype, np.integer):
        header["nodata_value"] = int(header["nodata_value"])
    return header, data
