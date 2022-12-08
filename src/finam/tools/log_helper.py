"""Logging helpers."""
# pylint: disable=E1101
import logging
import sys
from contextlib import AbstractContextManager

from finam.interfaces import Loggable

from . import wurlitzer


def is_loggable(obj):
    """
    Check if given object is loggable.

    Parameters
    ----------
    obj : object
        Object to check for loggability

    Returns
    -------
    bool
        Loggability of the object.
    """
    return isinstance(obj, Loggable)


class LogWriter:
    """
    Log writer.

    Parameters
    ----------
    logger : string, None or logging.Logger instance, optional
        Logger name for this writer. Will be the root logger by default.
    level : integer, optional
        Logging level, by default logging.INFO
    """

    def __init__(self, logger=None, level=logging.INFO):
        self.logger = logger.name if isinstance(logger, logging.Logger) else logger
        self.level = level

    def write(self, msg):
        """
        Write a given message to the logger.

        Parameters
        ----------
        msg : string
            Message to log.
        """
        logger = logging.getLogger(self.logger)
        if msg != "\n":
            logger.log(self.level, msg)


class LogStdOutStdErr(AbstractContextManager):
    """
    Context manager to redirect stdout and stderr to a logger.

    Parameters
    ----------
    logger : string, None or logging.Logger instance, optional
        Logger name for this writer. Will be the root logger by default.

    level_stdout : integer, optional
        Logging level for stdout, by default logging.INFO

    level_stderr : integer, optional
        Logging level for stderr, by default logging.WARN
    """

    def __init__(
        self, logger=None, level_stdout=logging.INFO, level_stderr=logging.WARN
    ):
        self._stdout_target = LogWriter(logger=logger, level=level_stdout)
        self._stderr_target = LogWriter(logger=logger, level=level_stderr)
        self._old_stdout = getattr(sys, "stdout")
        self._old_stderr = getattr(sys, "stderr")

    def __enter__(self):
        setattr(sys, "stdout", self._stdout_target)
        setattr(sys, "stderr", self._stderr_target)

    def __exit__(self, *args, **kwargs):
        setattr(sys, "stdout", self._old_stdout)
        setattr(sys, "stderr", self._old_stderr)


class LogCStdOutStdErr(AbstractContextManager):
    """
    Context manager to redirect low-level C stdout and stderr to a logger.

    Parameters
    ----------
    logger : string, None or logging.Logger instance, optional
        Logger name for this writer. Will be the root logger by default.

    level_stdout : integer, optional
        Logging level for stdout, by default logging.INFO

    level_stderr : integer, optional
        Logging level for stderr, by default logging.WARN
    """

    def __init__(
        self, logger=None, level_stdout=logging.INFO, level_stderr=logging.WARN
    ):
        self.logger = logger.name if isinstance(logger, logging.Logger) else logger
        self.level_stdout = level_stdout
        self.level_stderr = level_stderr
        self.stdout = None
        self.stderr = None
        self.pipes = wurlitzer.pipes()

    def __enter__(self):
        self.stdout, self.stderr = self.pipes.__enter__()

    def __exit__(self, *args, **kwargs):
        self.pipes.__exit__(*args, **kwargs)
        logger = logging.getLogger(self.logger)
        for line in self.stdout.read().splitlines():
            logger.log(self.level_stdout, line)
        for line in self.stderr.read().splitlines():
            logger.log(self.level_stderr, line)


class ErrorLogger(AbstractContextManager):
    """
    Context manager to log Exceptions.

    Parameters
    ----------
    logger : string, None or logging.Logger instance, optional
        Logger name to use. Will be the root logger by default.
    do_log : Bool, optional
        Whether to really log errors. Will be true by default.
    """

    def __init__(self, logger=None, do_log=True):
        self.logger = logger.name if isinstance(logger, logging.Logger) else logger
        self.do_log = do_log

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_value is not None and self.do_log:
            logging.getLogger(self.logger).exception(exc_value)


def add_logging_level(name, num, method=None):
    """
    Adds a logging level to the :mod:`logging` module.

    Examples
    --------

    .. code-block:: Python

        add_logging_level("TRACE", logging.DEBUG - 5)

    Parameters
    ----------
    name : str
        The name of the new logging level.
    num : int
        The numeric severity of the new logging level.
    method : str, optional
        The method name for the new logging level.
        Defaults to lowercase of ``name``.
    """
    if not method:
        method = name.lower()

    if hasattr(logging, name):
        raise AttributeError(f"{name} already defined in logging module")
    if hasattr(logging.getLoggerClass(), name):
        raise AttributeError(f"{name} already defined in logger class")

    def log_for_level(self, message, *args, **kwargs):
        if self.isEnabledFor(num):
            # pylint: disable=protected-access
            self._log(num, message, args, **kwargs)

    def log_to_root(message, *args, **kwargs):
        logging.log(num, message, *args, **kwargs)

    logging.addLevelName(num, name)
    setattr(logging, name, num)
    setattr(logging.getLoggerClass(), method, log_for_level)
    setattr(logging, method, log_to_root)
