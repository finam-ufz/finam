import logging
import unittest

from finam.tools.log_helper import LogError


def raise_and_log(do_log):
    with LogError(logging.getLogger(None), do_log=do_log):
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
