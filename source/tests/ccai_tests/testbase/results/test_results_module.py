import json
import os
import tempfile
import unittest
from datetime import datetime

from ccai.testbase.results.utilities import catalog_tree
from ccai.testbase.results.model.progressinfo import ProgressInfo
from ccai.testbase.results.model.progresstype import ProgressType
from ccai.testbase.results.model.progresscode import ProgressCode
from ccai.testbase.results.recorders.jsonresultrecorder import JsonResultEncoder
from ccai.testbase.results.model.taskingresult import (
    TaskingResult,
    default_tasking_result_formatter,
    verify_tasking_results,
)
from ccai.testbase.results.model.resultcode import ResultCode
from ccai.testbase.results.model.resultnode import ResultNode
from ccai.testbase.results.model.testresult import TestResult
from ccai.testbase.results.model.resulttype import ResultType
from ccai.testbase.results.model.resultcontainer import ResultContainer
from ccai.testbase.results.model.jobcontainer import JobContainer
from ccai.testbase.results.model.testcontainer import TestContainer
from ccai.testbase.results.model.taskinggroup import TaskingGroup
from ccai.errors.exceptions import (
    TaskingGroupRuntimeError,
    TaskingGroupAssertionError,
)
from ccai.errors.xtraceback import OriginDetail, TraceDetail, TracebackDetail


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

        inst = ProgressInfo.from_dict(asd)
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

    def test_cancelled_raises_runtime_error(self):
        """Test that CANCELLED result code raises TaskingGroupRuntimeError (Req 14.3)."""
        res = TaskingResult("cancelled-1", "cancelled-task", "parent", "worker", result_code=ResultCode.CANCELLED)
        
        with self.assertRaises(TaskingGroupRuntimeError) as ctx:
            verify_tasking_results([res], "context message", group_name="test-group")
        
        error_message = str(ctx.exception)
        self.assertIn("cancelled", error_message.lower())
        self.assertIn("test-group", error_message)

    def test_errored_raises_runtime_error_with_details(self):
        """Test that ERRORED result code raises TaskingGroupRuntimeError with formatted details (Req 14.4)."""
        origin = OriginDetail(file="test_file.py", lineno=42, scope="test_scope")
        trace = TraceDetail(origin=origin, call="test_call()", code=["code line"], context={})
        tb = TracebackDetail(extype="RuntimeError", exargs=["test error"], traces=[trace])
        
        res = TaskingResult("errored-1", "errored-task", "parent", "worker", result_code=ResultCode.UNSET)
        res.add_error(tb)
        res.finalize()
        
        self.assertEqual(res.result_code, ResultCode.ERRORED)
        
        with self.assertRaises(TaskingGroupRuntimeError) as ctx:
            verify_tasking_results([res], "context message", group_name="error-group")
        
        error_message = str(ctx.exception)
        self.assertIn("error-group", error_message)
        self.assertIn("errored-task", error_message)

    def test_custom_result_formatter_is_used(self):
        """Test that custom result_formatter parameter is used for formatting (Req 43.5)."""
        origin = OriginDetail(file="test_file.py", lineno=42, scope="test_scope")
        trace = TraceDetail(origin=origin, call="test_call()", code=["code line"], context={})
        tb = TracebackDetail(extype="RuntimeError", exargs=["test error"], traces=[trace])
        
        res = TaskingResult("fmt-1", "formatted-task", "parent", "worker", result_code=ResultCode.UNSET)
        res.add_error(tb)
        res.finalize()
        
        custom_format_called = []
        
        def custom_formatter(result: TaskingResult):
            custom_format_called.append(result.inst_id)
            return [f"CUSTOM: {result.name}", f"ID: {result.inst_id}"]
        
        with self.assertRaises(TaskingGroupRuntimeError) as ctx:
            verify_tasking_results([res], "context", group_name="grp", result_formatter=custom_formatter)
        
        self.assertEqual(len(custom_format_called), 1)
        self.assertEqual(custom_format_called[0], "fmt-1")
        
        error_message = str(ctx.exception)
        self.assertIn("CUSTOM: formatted-task", error_message)
        self.assertIn("ID: fmt-1", error_message)

    def test_custom_formatter_used_for_failed_results(self):
        """Test that custom result_formatter is used when formatting failed results."""
        origin = OriginDetail(file="test_file.py", lineno=42, scope="test_scope")
        trace = TraceDetail(origin=origin, call="test_call()", code=["code line"], context={})
        tb = TracebackDetail(extype="AssertionError", exargs=["test failure"], traces=[trace])
        
        res = TaskingResult("fail-fmt-1", "failed-task", "parent", "worker", result_code=ResultCode.UNSET)
        res.add_failure(tb)
        res.finalize()
        
        custom_format_called = []
        
        def custom_formatter(result: TaskingResult):
            custom_format_called.append(result.inst_id)
            return [f"FAILED_CUSTOM: {result.name}"]
        
        with self.assertRaises(TaskingGroupAssertionError) as ctx:
            verify_tasking_results([res], "context", group_name="grp", result_formatter=custom_formatter)
        
        self.assertEqual(len(custom_format_called), 1)
        error_message = str(ctx.exception)
        self.assertIn("FAILED_CUSTOM: failed-task", error_message)


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


class TestResultPropertyMetadataTests(unittest.TestCase):
    """Tests for property-test metadata on TestResult (property-testing Requirements 8.4, 8.5, 13.6)."""

    def setUp(self):
        self.metadata = {
            "is_property_test": True,
            "examples_run": 37,
            "max_examples": 100,
            "seed": 839271,
            "job_seed": 12345,
            "assumptions_rejected": 0,
            "counterexample": {"xs": [1, 0, -1]},
            "strategy_descriptions": {"xs": "lists(integers())"},
        }
        return

    def test_property_metadata_defaults_to_none(self):
        tr = TestResult("1", "tname", "parent", [], {})
        self.assertIsNone(tr.property_metadata)
        return

    def test_as_dict_omits_property_metadata_when_not_set(self):
        tr = TestResult("1", "tname", "parent", [], {})
        tr.finalize()
        dct = tr.as_dict()
        self.assertNotIn("property_metadata", dct)
        return

    def test_set_property_metadata_is_returned_by_property(self):
        tr = TestResult("1", "tname", "parent", [], {})
        tr.set_property_metadata(self.metadata)
        self.assertEqual(tr.property_metadata, self.metadata)
        return

    def test_as_dict_includes_property_metadata_at_top_level(self):
        tr = TestResult("1", "tname", "parent", [], {})
        tr.set_property_metadata(self.metadata)
        tr.finalize()
        dct = tr.as_dict()
        self.assertEqual(dct["property_metadata"], self.metadata)
        self.assertNotIn("property_metadata", dct["detail"])
        return

    def test_to_json_serializes_property_metadata(self):
        tr = TestResult("1", "tname", "parent", [], {})
        tr.set_property_metadata(self.metadata)
        tr.finalize()
        dct = json.loads(tr.to_json())
        self.assertEqual(dct["property_metadata"]["counterexample"], {"xs": [1, 0, -1]})
        return

    def test_set_property_metadata_rejects_non_dict(self):
        tr = TestResult("1", "tname", "parent", [], {})
        with self.assertRaises(TypeError):
            tr.set_property_metadata(["not", "a", "dict"])
        return


class ResultContainerTests(unittest.TestCase):
    """Tests for the ResultContainer base class."""

    def test_constructor_sets_properties(self):
        """Test that constructor properly initializes all properties."""
        container = ResultContainer(
            inst_id="test-inst-123",
            name="test-container",
            result_type=ResultType.TEST_CONTAINER,
            parent_inst="parent-inst-456"
        )
        
        self.assertEqual(container.inst_id, "test-inst-123")
        self.assertEqual(container.name, "test-container")
        self.assertEqual(container.result_type, ResultType.TEST_CONTAINER)
        self.assertEqual(container.parent_inst, "parent-inst-456")

    def test_constructor_with_none_parent(self):
        """Test that constructor handles None parent_inst."""
        container = ResultContainer(
            inst_id="test-inst",
            name="test-name",
            result_type=ResultType.JOB,
            parent_inst=None
        )
        
        self.assertIsNone(container.parent_inst)

    def test_as_dict_returns_ordered_dict(self):
        """Test that as_dict returns an OrderedDict with correct fields."""
        container = ResultContainer(
            inst_id="inst-id",
            name="container-name",
            result_type=ResultType.PACKAGE,
            parent_inst="parent-id"
        )
        
        result = container.as_dict()
        
        self.assertEqual(result["name"], "container-name")
        self.assertEqual(result["instance"], "inst-id")
        self.assertEqual(result["parent"], "parent-id")
        self.assertEqual(result["rtype"], "PACKAGE")

    def test_to_json_returns_valid_json(self):
        """Test that to_json returns valid JSON string."""
        container = ResultContainer(
            inst_id="json-inst",
            name="json-container",
            result_type=ResultType.SCOPE,
            parent_inst="json-parent"
        )
        
        json_str = container.to_json()
        parsed = json.loads(json_str)
        
        self.assertEqual(parsed["name"], "json-container")
        self.assertEqual(parsed["instance"], "json-inst")
        self.assertEqual(parsed["parent"], "json-parent")
        self.assertEqual(parsed["rtype"], "SCOPE")


class JobContainerTests(unittest.TestCase):
    """Tests for the JobContainer class - Requirements 9.1-9.4."""

    def test_inherits_from_result_container(self):
        """Test that JobContainer inherits from ResultContainer (Req 9.1)."""
        job = JobContainer(inst_id="job-inst", name="job-name")
        self.assertIsInstance(job, ResultContainer)

    def test_constructor_accepts_inst_id_and_name(self):
        """Test that constructor accepts inst_id and name parameters (Req 9.2)."""
        job = JobContainer(inst_id="job-123", name="test-job")
        
        self.assertEqual(job.inst_id, "job-123")
        self.assertEqual(job.name, "test-job")

    def test_result_type_is_job(self):
        """Test that result_type is set to ResultType.JOB (Req 9.3)."""
        job = JobContainer(inst_id="job-inst", name="job-name")
        self.assertEqual(job.result_type, ResultType.JOB)

    def test_parent_inst_is_none(self):
        """Test that parent_inst is None for root node (Req 9.4)."""
        job = JobContainer(inst_id="job-inst", name="job-name")
        self.assertIsNone(job.parent_inst)

    def test_as_dict_includes_correct_fields(self):
        """Test that as_dict returns correct fields for JobContainer."""
        job = JobContainer(inst_id="job-dict-inst", name="job-dict-name")
        
        result = job.as_dict()
        
        self.assertEqual(result["name"], "job-dict-name")
        self.assertEqual(result["instance"], "job-dict-inst")
        self.assertIsNone(result["parent"])
        self.assertEqual(result["rtype"], "JOB")


class TestContainerTests(unittest.TestCase):
    """Tests for the TestContainer class - Requirements 10.1-10.3."""

    def test_inherits_from_result_container(self):
        """Test that TestContainer inherits from ResultContainer (Req 10.1)."""
        tc = TestContainer(inst_id="tc-inst", name="tc-name", parent_inst="parent-inst")
        self.assertIsInstance(tc, ResultContainer)

    def test_constructor_accepts_required_parameters(self):
        """Test that constructor accepts inst_id, name, and parent_inst (Req 10.2)."""
        tc = TestContainer(
            inst_id="tc-123",
            name="test-container-name",
            parent_inst="parent-456"
        )
        
        self.assertEqual(tc.inst_id, "tc-123")
        self.assertEqual(tc.name, "test-container-name")
        self.assertEqual(tc.parent_inst, "parent-456")

    def test_result_type_is_test_container(self):
        """Test that result_type is set to ResultType.TEST_CONTAINER (Req 10.3)."""
        tc = TestContainer(inst_id="tc-inst", name="tc-name", parent_inst="parent")
        self.assertEqual(tc.result_type, ResultType.TEST_CONTAINER)

    def test_as_dict_includes_correct_fields(self):
        """Test that as_dict returns correct fields for TestContainer."""
        tc = TestContainer(
            inst_id="tc-dict-inst",
            name="tc-dict-name",
            parent_inst="tc-parent"
        )
        
        result = tc.as_dict()
        
        self.assertEqual(result["name"], "tc-dict-name")
        self.assertEqual(result["instance"], "tc-dict-inst")
        self.assertEqual(result["parent"], "tc-parent")
        self.assertEqual(result["rtype"], "TEST_CONTAINER")


class TaskingResultTests(unittest.TestCase):
    """Tests for the TaskingResult class - Requirements 13.5-13.8."""

    def test_add_return_value_sets_rvalue(self):
        """Test that add_return_value method sets the rvalue property (Req 13.5)."""
        res = TaskingResult(
            inst_id="task-1",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        
        self.assertIsNone(res.rvalue)
        
        res.add_return_value("test-return-value")
        
        self.assertEqual(res.rvalue, "test-return-value")

    def test_add_return_value_with_dict(self):
        """Test that add_return_value works with dictionary values."""
        res = TaskingResult(
            inst_id="task-2",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        
        return_data = {"key": "value", "count": 42}
        res.add_return_value(return_data)
        
        self.assertEqual(res.rvalue, return_data)
        self.assertEqual(res.rvalue["key"], "value")
        self.assertEqual(res.rvalue["count"], 42)

    def test_add_return_value_overwrites_previous(self):
        """Test that add_return_value overwrites any previous value."""
        res = TaskingResult(
            inst_id="task-3",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        
        res.add_return_value("first-value")
        self.assertEqual(res.rvalue, "first-value")
        
        res.add_return_value("second-value")
        self.assertEqual(res.rvalue, "second-value")

    def test_as_dict_includes_rvalue_simple(self):
        """Test that as_dict includes rvalue field for simple values (Req 13.6)."""
        res = TaskingResult(
            inst_id="task-4",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        res.add_return_value("simple-string-value")
        res.finalize()
        
        result = res.as_dict()
        
        self.assertIn("rvalue", result)
        self.assertEqual(result["rvalue"], "simple-string-value")

    def test_as_dict_includes_rvalue_none(self):
        """Test that as_dict includes rvalue field when None."""
        res = TaskingResult(
            inst_id="task-5",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        res.finalize()
        
        result = res.as_dict()
        
        self.assertIn("rvalue", result)
        self.assertIsNone(result["rvalue"])

    def test_as_dict_calls_rvalue_as_dict_method(self):
        """Test that as_dict calls rvalue.as_dict() when available (Req 13.7)."""
        
        class MockReturnValue:
            def __init__(self, data):
                self._data = data
            
            def as_dict(self):
                return {"serialized": self._data}
        
        res = TaskingResult(
            inst_id="task-6",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        mock_rvalue = MockReturnValue("test-data")
        res.add_return_value(mock_rvalue)
        res.finalize()
        
        result = res.as_dict()
        
        self.assertIn("rvalue", result)
        self.assertEqual(result["rvalue"], {"serialized": "test-data"})

    def test_as_dict_includes_prefix_and_worker(self):
        """Test that as_dict includes prefix and worker fields (Req 13.6)."""
        res = TaskingResult(
            inst_id="task-7",
            name="test-task",
            parent_inst="parent-1",
            worker="test-worker",
            prefix="custom-prefix"
        )
        res.finalize()
        
        result = res.as_dict()
        
        self.assertEqual(result["prefix"], "custom-prefix")
        self.assertEqual(result["worker"], "test-worker")

    def test_as_dict_default_prefix(self):
        """Test that as_dict uses default prefix 'tasking' when not specified."""
        res = TaskingResult(
            inst_id="task-8",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1"
        )
        res.finalize()
        
        result = res.as_dict()
        
        self.assertEqual(result["prefix"], "tasking")

    def test_format_result_returns_list_of_strings(self):
        """Test that format_result returns a list of formatted strings (Req 13.8)."""
        res = TaskingResult(
            inst_id="task-9",
            name="format-test-task",
            parent_inst="parent-1",
            worker="format-worker"
        )
        res.finalize()
        
        lines = res.format_result()
        
        self.assertIsInstance(lines, list)
        self.assertTrue(all(isinstance(line, str) for line in lines))

    def test_format_result_includes_task_info(self):
        """Test that format_result includes task name and worker (Req 13.8)."""
        res = TaskingResult(
            inst_id="task-10",
            name="my-task-name",
            parent_inst="parent-1",
            worker="my-worker"
        )
        res.finalize()
        
        lines = res.format_result()
        
        self.assertIn("Task - my-task-name (my-worker)", lines[0])
        self.assertIn("instance: task-10", lines)
        self.assertIn("parent: parent-1", lines)

    def test_format_result_includes_result_code(self):
        """Test that format_result includes the result code."""
        res = TaskingResult(
            inst_id="task-11",
            name="test-task",
            parent_inst="parent-1",
            worker="worker-1",
            result_code=ResultCode.PASSED
        )
        res.finalize()
        
        lines = res.format_result()
        
        self.assertIn("result: PASSED", lines)


class TaskingGroupTests(unittest.TestCase):
    """Tests for the TaskingGroup class - Requirements 11.1-11.7."""

    def test_inherits_from_result_container(self):
        """Test that TaskingGroup inherits from ResultContainer (Req 11.1)."""
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        self.assertIsInstance(tg, ResultContainer)

    def test_constructor_accepts_required_parameters(self):
        """Test that constructor accepts inst_id, name, and parent_inst (Req 11.2)."""
        tg = TaskingGroup(
            inst_id="tg-123",
            name="tasking-group-name",
            parent_inst="parent-789"
        )
        
        self.assertEqual(tg.inst_id, "tg-123")
        self.assertEqual(tg.name, "tasking-group-name")
        self.assertEqual(tg.parent_inst, "parent-789")

    def test_result_type_is_tasking_group(self):
        """Test that result_type is set to ResultType.TASKING_GROUP (Req 11.3)."""
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        self.assertEqual(tg.result_type, ResultType.TASKING_GROUP)

    def test_start_timestamp_initialized_on_construction(self):
        """Test that start timestamp is initialized to datetime.now() (Req 11.4)."""
        before = datetime.now()
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        after = datetime.now()
        
        self.assertIsNotNone(tg.start)
        self.assertGreaterEqual(tg.start, before)
        self.assertLessEqual(tg.start, after)

    def test_stop_timestamp_initialized_to_none(self):
        """Test that stop timestamp is initialized to None (Req 11.5)."""
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        self.assertIsNone(tg.stop)

    def test_finalize_sets_stop_timestamp(self):
        """Test that finalize method sets stop timestamp (Req 11.6)."""
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        self.assertIsNone(tg.stop)
        
        before = datetime.now()
        tg.finalize()
        after = datetime.now()
        
        self.assertIsNotNone(tg.stop)
        self.assertGreaterEqual(tg.stop, before)
        self.assertLessEqual(tg.stop, after)

    def test_as_dict_includes_timestamps(self):
        """Test that as_dict includes start and stop timestamps (Req 11.7)."""
        tg = TaskingGroup(inst_id="tg-dict-inst", name="tg-dict-name", parent_inst="tg-parent")
        tg.finalize()
        
        result = tg.as_dict()
        
        self.assertEqual(result["name"], "tg-dict-name")
        self.assertEqual(result["instance"], "tg-dict-inst")
        self.assertEqual(result["parent"], "tg-parent")
        self.assertEqual(result["rtype"], "TASKING_GROUP")
        self.assertIn("start", result)
        self.assertIn("stop", result)
        self.assertNotEqual(result["start"], "")
        self.assertNotEqual(result["stop"], "")

    def test_as_dict_stop_empty_before_finalize(self):
        """Test that as_dict returns empty stop before finalize is called."""
        tg = TaskingGroup(inst_id="tg-inst", name="tg-name", parent_inst="parent")
        
        result = tg.as_dict()
        
        self.assertNotEqual(result["start"], "")
        self.assertEqual(result["stop"], "")


if __name__ == "__main__":
    unittest.main()
