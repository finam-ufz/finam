"""Working directory helpers."""
import os
from contextlib import contextmanager

from .log_helper import loggable


@contextmanager
def set_directory(path):
    """Sets the cwd within a context.

    Parameters
    ----------
    path : Path
        Path to the desired cwd.

    Yields
    ------
    None
    """
    origin = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


def execute_in_cwd(func):
    """Decorator to execute method in given cwd of containing class.

    Parameters
    ----------
    func : callable
        Method of a class.

    Returns
    -------
    callable
        Wrapped function to be executed in cwd.

    Notes
    -----
    The containing class of the given method needs to have a "cwd" property.
    """

    def cwd_wrapper(self, *args, **kwargs):
        """Wrapper function."""
        cwd = getattr(self, "cwd", None)
        try:
            if cwd is None:
                raise ValueError("No working directory given.")
        except ValueError as err:
            if loggable(self):
                self.logger.exception(err)
            raise
        with set_directory(cwd):
            return func(self, *args, **kwargs)

    return cwd_wrapper
