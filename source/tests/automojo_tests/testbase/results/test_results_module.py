import json
import os
import tempfile
import unittest
from datetime import datetime

from automojo.testbase.results.utilities import catalog_tree
from automojo.testbase.results.model.progressinfo import ProgressInfo
from automojo.testbase.results.model.progresstype import ProgressType
from automojo.testbase.results.model.progresscode import ProgressCode
from automojo.testbase.results.recorders.jsonresultrecorder import JsonResultEncoder
from automojo.testbase.results.model.taskingresult import (
    TaskingResult,
    default_tasking_result_formatter,
    verify_tasking_results,
)
from automojo.testbase.results.model.resultcode import ResultCode
from automojo.testbase.results.model.resultnode import ResultNode
from automojo.testbase.results.model.testresult import TestResult
from automojo.testbase.results.model.resulttype import ResultType
from automojo.errors.exceptions import (
    TaskingGroupRuntimeError,
    TaskingGroupAssertionError,
)
from automojo.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail


class CatalogTreeTests(unittest.TestCase):
    def test_catalog_tree_creates_catalog_files(self):
        with tempfile.TemporaryDirectory() as root:
            os.mkdir(os.path.join(root, "sub1"))
            os.mkdir(os.path.join(root, "diagnostics"))
            open(os.path.join(root, "file1.txt"), "w").close()
            open(os.path.join(root, "sub1", "filea.txt"), "w").close()
            open(os.path.join(root, "diagnostics", "skip.txt"), "w").close()

            catalog_tree(root)

            with open(os.path.join(root, "catalog.json")) as fh:
                catalog = json.load(fh)
            self.assertEqual(catalog["files"], ["file1.txt"])
            self.assertEqual(sorted(catalog["folders"]), ["diagnostics", "sub1"])

            sub_cat = os.path.join(root, "sub1", "catalog.json")
            self.assertTrue(os.path.exists(sub_cat))
            with open(sub_cat) as fh:
                scatalog = json.load(fh)
            self.assertEqual(scatalog["files"], ["filea.txt"])
            self.assertEqual(scatalog["folders"], [])

            self.assertFalse(os.path.exists(os.path.join(root, "diagnostics", "catalog.json")))


class ProgressInfoTests(unittest.TestCase):
    def test_dict_conversion(self):
        when = datetime(2023, 1, 1, 12, 0, 0)
        info = ProgressInfo(
            id="pid",
            category="cat",
            moniker="mon",
            ptype=ProgressType.NumericRange,
            range_min="0",
            range_max="10",
            position="5",
            status=ProgressCode.Running,
            when=when,
            data={"k": "v"},
        )
        asd = info.as_dict()
        self.assertEqual(asd["status"], "Running")
        self.assertEqual(asd["ptype"], "NumericRange")

        inst = ProgressInfo.from_dict.__func__(asd)
        self.assertEqual(inst, info)
        self.assertEqual(repr(info), repr(asd))


class JsonResultEncoderTests(unittest.TestCase):
    def test_datetime_encoding(self):
        dt = datetime(2024, 1, 2, 3, 4, 5)
        enc = JsonResultEncoder()
        self.assertEqual(enc.default(dt), dt.isoformat())


class TaskingResultFormatterTests(unittest.TestCase):
    def test_default_tasking_result_formatter(self):
        res = TaskingResult("tid", "task", "parent", "worker", result_code=ResultCode.PASSED)
        res.finalize()
        lines = default_tasking_result_formatter(res)
        self.assertIn("Task - task (worker)", lines[0])
        self.assertIn("instance: tid", lines)
        self.assertIn("parent: parent", lines)
        self.assertIn("result: PASSED", lines)


class VerifyTaskingResultsTests(unittest.TestCase):
    def test_verify_passes(self):
        res = TaskingResult("1", "t", "p", "w", result_code=ResultCode.PASSED)
        verify_tasking_results([res], "ctx")

    def test_unknown_raises(self):
        res = TaskingResult("1", "t", "p", "w", result_code=ResultCode.UNSET)
        with self.assertRaises(TaskingGroupRuntimeError):
            verify_tasking_results([res], "ctx", group_name="grp")

    def test_failed_raises(self):
        res = TaskingResult("1", "t", "p", "w", result_code=ResultCode.FAILED)
        with self.assertRaises(TaskingGroupAssertionError):
            verify_tasking_results([res], "ctx", group_name="grp")


class ResultNodeFinalizeTests(unittest.TestCase):
    def test_finalize_sets_result_code(self):
        origin = OriginDetail(file="f", lineno=1, scope="s")
        trace = TraceDetail(origin=origin, call="call", code=["c"], context={})
        tb = TracebackDetail(extype="ValueError", exargs=["msg"], traces=[trace])

        node = ResultNode("id", "name", "parent", ResultType.TEST, ResultCode.UNSET)
        node.add_failure(tb)
        node.finalize()
        self.assertEqual(node.result_code, ResultCode.FAILED)

        node2 = ResultNode("id2", "name2", "parent", ResultType.TEST, ResultCode.UNSET)
        node2.add_error(tb)
        node2.finalize()
        self.assertEqual(node2.result_code, ResultCode.ERRORED)

        node3 = ResultNode("id3", "name3", "parent", ResultType.TEST, ResultCode.CANCELLED)
        node3.finalize()
        self.assertEqual(node3.result_code, ResultCode.UNKOWN)


class TestResultTests(unittest.TestCase):
    def test_mark_skip_and_as_dict(self):
        tr = TestResult("1", "tname", "parent", [], {}, result_code=ResultCode.UNSET)
        tr.mark_skip("reason", "bug")
        dct = tr.as_dict()
        self.assertEqual(dct["result"], "SKIPPED")
        self.assertIn("reason", dct["detail"])
        self.assertIn("bug", dct["detail"])


if __name__ == "__main__":
    unittest.main()
