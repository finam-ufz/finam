import logging
import sys
import unittest

from finam.tools.log_helper import ErrorLogger, LogCStdOutStdErr, LogStdOutStdErr
from finam.tools.wurlitzer import libc


def raise_and_log(do_log):
    with ErrorLogger(logging.getLogger(None), do_log=do_log):
        raise ValueError("This is an Error!")


class TestLog(unittest.TestCase):
    def test_error_log(self):
        with self.assertLogs() as captured:
            with self.assertRaises(ValueError):
                raise_and_log(do_log=True)
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(captured.records[0].levelno, logging.ERROR)
        # suppress logging
        with self.assertLogs(level=logging.WARN) as captured:
            with self.assertRaises(ValueError):
                raise_and_log(do_log=False)
            # "assertNoLogs" is only available in python >=3.10
            # so we need to at least log something to prove,
            # nothing else was logged
            logging.getLogger(None).warning("Dummy warning.")
        # check that we only got the one dummy log
        self.assertEqual(len(captured.records), 1)

    def test_log_levels(self):
        with self.assertLogs("foo", level="TRACE") as captured:
            logging.getLogger("foo").trace("A")
            logging.getLogger("foo").profile("B")

        self.assertEqual(len(captured.records), 2)
        self.assertEqual(captured.records[0].levelno, logging.TRACE)
        self.assertEqual(captured.records[0].message, "A")
        self.assertEqual(captured.records[1].levelno, logging.PROFILE)
        self.assertEqual(captured.records[1].message, "B")

    def test_redirect(self):
        with self.assertLogs() as captured:
            with LogStdOutStdErr():
                print("Hi from Python")
                print("Boo from Python", file=sys.stderr)
        self.assertEqual(len(captured.records), 2)
        self.assertEqual(captured.records[0].levelno, logging.INFO)
        self.assertEqual(captured.records[0].message, "Hi from Python")
        self.assertEqual(captured.records[1].levelno, logging.WARNING)
        self.assertEqual(captured.records[1].message, "Boo from Python")

    def test_c_redirect(self):
        with self.assertLogs() as captured:
            with LogCStdOutStdErr():
                libc.puts(b"Hi from C")
        self.assertEqual(len(captured.records), 1)
        self.assertEqual(captured.records[0].levelno, logging.INFO)
        self.assertEqual(captured.records[0].message, "Hi from C")


if __name__ == "__main__":
    unittest.main()
