"""Logging helpers."""
import logging
import sys
from contextlib import AbstractContextManager


class LogWriter:
    """
    Log writer.

    Parameters
    ----------
    logger_name : string or None, optional
        Logger name for this writer. Will be the root logger by default.
    level : integer, optional
        Logging level, by default logging.INFO
    """

    def __init__(self, logger_name=None, level=logging.INFO):
        self.logger_name = logger_name
        self.level = level

    def write(self, msg):
        """
        Write a given message to the logger.

        Parameters
        ----------
        msg : string
            Message to log.
        """
        logger = logging.getLogger(self.logger_name)
        logger.log(self.level, f"{msg}") if msg != "\n" else None


class LogStdOutStdErr(AbstractContextManager):
    """
    Context manager to redirect stdout and stderr to a logger.

    Parameters
    ----------
    logger_name : string or None, optional
        Logger name for this writer. Will be the root logger by default.

    level_stdout : integer, optional
        Logging level for stdout, by default logging.INFO

    level_stderr : integer, optional
        Logging level for stderr, by default logging.WARN
    """

    def __init__(
        self, logger_name=None, level_stdout=logging.INFO, level_stderr=logging.WARN
    ):
        self._stdout_target = LogWriter(logger_name=logger_name, level=level_stdout)
        self._stderr_target = LogWriter(logger_name=logger_name, level=level_stderr)
        self._old_stdout = getattr(sys, "stdout")
        self._old_stderr = getattr(sys, "stderr")

    def __enter__(self):
        setattr(sys, "stdout", self._stdout_target)
        setattr(sys, "stderr", self._stderr_target)

    def __exit__(self, *args, **kwargs):
        setattr(sys, "stdout", self._old_stdout)
        setattr(sys, "stderr", self._old_stderr)
