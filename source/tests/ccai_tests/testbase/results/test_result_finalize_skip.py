"""
    .. module:: test_result_finalize_skip
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for result code finalization, especially skips.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2026, Code Craft AI LLC"
__credits__ = []


import unittest

from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.testresult import TestResult


def _make_result():
    """
        Build a TestResult to exercise finalize against.

        :returns: A TestResult with an UNSET result code.
    """
    return TestResult("inst-1", "some.module#test_thing", "parent-1", [], {})


class TestFinalizePreservesSkip(unittest.TestCase):
    """
        Verifies a skip survives finalization.
    """

    def test_a_skip_is_still_a_skip_after_finalize(self):

        # mark_skip runs when the test raises SkipError; finalize runs after.
        # Overwriting the code here dropped the result from every tally — not
        # passed, not skipped, just absent from a total that still counted it.
        result = _make_result()
        result.mark_skip("credentials are not configured", None)

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.SKIPPED)
        return

    def test_the_skip_reason_survives_finalize(self):

        result = _make_result()
        result.mark_skip("RUN_LIVE_NEBIUS != 1", None)

        result.finalize()

        # The reason is exposed through serialization, not as a property.
        self.assertEqual(result.as_dict()["detail"]["reason"],
                         "RUN_LIVE_NEBIUS != 1")
        return

    def test_a_skip_serializes_as_skipped(self):

        result = _make_result()
        result.mark_skip("not configured", None)
        result.finalize()

        as_dict = result.as_dict()

        self.assertEqual(as_dict["result"], "SKIPPED")
        return

    def test_a_failure_still_beats_a_skip(self):

        # A test that skipped and also recorded a failure is a failure: the
        # failure is the more serious signal and must not be hidden.
        result = _make_result()
        result.mark_skip("skipped late", None)
        result.add_failure(["something asserted false"])

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.FAILED)
        return

    def test_an_error_still_beats_a_skip(self):

        result = _make_result()
        result.mark_skip("skipped late", None)
        result.add_error(["something blew up"])

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.ERRORED)
        return


class TestFinalizeOtherOutcomes(unittest.TestCase):
    """
        Verifies finalization of the outcomes that are not skips.
    """

    def test_an_unset_result_with_nothing_recorded_passes(self):

        result = _make_result()

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.PASSED)
        return

    def test_a_failure_finalizes_as_failed(self):

        result = _make_result()
        result.add_failure(["assert failed"])

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.FAILED)
        return

    def test_an_error_finalizes_as_errored(self):

        result = _make_result()
        result.add_error(["raised"])

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.ERRORED)
        return

    def test_a_failure_outranks_an_error(self):

        result = _make_result()
        result.add_error(["raised"])
        result.add_failure(["assert failed"])

        result.finalize()

        self.assertEqual(result.result_code, ResultCode.FAILED)
        return

if __name__ == "__main__":
    unittest.main()
