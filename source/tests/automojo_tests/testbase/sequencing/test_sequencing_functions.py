import os
import tempfile
import unittest
from collections import OrderedDict

import automojo.runtime.paths as runtime_paths
from automojo.xmodules.jsos import CHAR_RECORD_SEPERATOR

from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.testbase.sequencing.testactivity import TestActivity
from automojo.testbase.sequencing.sequencertestscope import SequencerTestScope
from automojo.testbase.sequencing.sequencerscopebase import SequencerScopeBase

class DummyResult:
    def __init__(self, inst_id=None, name=None, parent_inst=None):
        self.inst_id = inst_id
        self.name = name
        self.parent_inst = parent_inst
        self.errors = []
        self.skipped = None
        self.finalized = False

    def add_error(self, tb):
        self.errors.append(tb)

    def mark_skip(self, reason, bug):
        self.skipped = (reason, bug)

    def finalize(self):
        self.finalized = True

    def mark_passed(self):
        self.finalized = True


class DummyRecorder:
    def __init__(self):
        self.recorded = []
        self.previewed = []

    def record(self, result):
        self.recorded.append(result)

    def preview(self, result):
        self.previewed.append(result)


class DummySequencer:
    def __init__(self):
        self.calls = []
        self._scope_stack = []

    def scope_id_create(self, ctx_name):
        parent = self._scope_stack[-1][1] if self._scope_stack else None
        sid = "scope"
        self._scope_stack.append((ctx_name, sid))
        return (parent, sid)

    def scope_id_pop(self, scope_name):
        self._scope_stack.pop()

    def scope_id_push(self, scope_name, scope_id):
        self._scope_stack.append((scope_name, scope_id))

    def find_treenode_for_scope(self, scope_name):
        class Node:
            def finalize(self_inner):
                self_inner.finalized = True
        return Node()

    def create_test_result_node(self, inst_id, name, monikers, pivots, parent_inst=None):
        return DummyResult(inst_id, name, parent_inst)

    def create_test_result_container(self, inst_id, name, parent_inst=None):
        return DummyResult(inst_id, name, parent_inst)

class TestActivityTests(unittest.TestCase):

    def test_context_manager_writes_file(self):
        with tempfile.TemporaryDirectory() as tdir:
            afile = os.path.join(tdir, "activity.jsos")
            with TestActivity(afile, "act", "tgt", detail={"d":1}) as act:
                self.assertIsNone(act.end)
            # after context exit finalize called
            self.assertIsNotNone(act.end)
            with open(afile, 'r') as f:
                content = f.read()
            self.assertTrue(content.startswith(CHAR_RECORD_SEPERATOR))
            self.assertIn("\"activity-name\": \"act\"", content)


class SequencerTestScopeTests(unittest.TestCase):

    def setUp(self):
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(name="automojo-testbase", logger_name="automojo-testbase", log_basename="automojo-testbase")

        self.tempdir = tempfile.TemporaryDirectory()

        # Reset cached runtime paths so overrides take effect for each test
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)
        self.seq = DummySequencer()
        self.rec = DummyRecorder()

    def tearDown(self):
        self.tempdir.cleanup()

    def test_get_monikers_and_pivots(self):
        class NotableA:
            moniker = "A"
            pivots = {"p": 1}
        class NotableB:
            moniker = "B"
        nmap = OrderedDict([("a", NotableA()), ("b", NotableB()), ("c", 3)])
        scope = SequencerTestScope(self.seq, self.rec, "test", notables=nmap)
        mons, pivs = scope._get_monikers_and_pivots()
        self.assertEqual(mons, ["A", "B", "3"])
        self.assertEqual(pivs["a"], {"p": 1})
        self.assertEqual(pivs["b"], str(nmap["b"]))
        self.assertEqual(pivs["c"], "3")

    def test_moniker_extraction_with_moniker_attribute(self):
        """
        Test that moniker extraction uses the moniker attribute when present.
        Validates: Requirements 27.3
        """
        class NotableWithMoniker:
            moniker = "custom_moniker"
        
        nmap = OrderedDict([("param1", NotableWithMoniker())])
        scope = SequencerTestScope(self.seq, self.rec, "test_func", notables=nmap)
        monikers, _ = scope._get_monikers_and_pivots()
        
        self.assertEqual(monikers, ["custom_moniker"])

    def test_moniker_extraction_without_moniker_attribute(self):
        """
        Test that moniker extraction uses string representation when moniker attribute is absent.
        Validates: Requirements 27.4
        """
        class NotableWithoutMoniker:
            def __str__(self):
                return "string_representation"
        
        nmap = OrderedDict([("param1", NotableWithoutMoniker())])
        scope = SequencerTestScope(self.seq, self.rec, "test_func", notables=nmap)
        monikers, _ = scope._get_monikers_and_pivots()
        
        self.assertEqual(monikers, ["string_representation"])

    def test_moniker_extraction_with_primitive_values(self):
        """
        Test that moniker extraction handles primitive values correctly.
        Validates: Requirements 27.4
        """
        nmap = OrderedDict([
            ("int_param", 42),
            ("str_param", "hello"),
            ("float_param", 3.14)
        ])
        scope = SequencerTestScope(self.seq, self.rec, "test_func", notables=nmap)
        monikers, _ = scope._get_monikers_and_pivots()
        
        self.assertEqual(monikers, ["42", "hello", "3.14"])

    def test_context_identifier_format_with_monikers(self):
        """
        Test that context identifier follows the format {test_name}:{moniker1},{moniker2},...
        Validates: Requirements 27.1, 27.2
        """
        class NotableA:
            moniker = "mon_a"
        class NotableB:
            moniker = "mon_b"
        
        nmap = OrderedDict([("a", NotableA()), ("b", NotableB())])
        scope = SequencerTestScope(self.seq, self.rec, "test_function", notables=nmap)
        
        expected_context_id = "test_function:mon_a,mon_b"
        self.assertEqual(scope._context_identifier, expected_context_id)

    def test_context_identifier_format_without_monikers(self):
        """
        Test that context identifier is correctly formed when no notables are provided.
        Validates: Requirements 27.1, 27.2
        """
        scope = SequencerTestScope(self.seq, self.rec, "test_function", notables={})
        
        expected_context_id = "test_function:"
        self.assertEqual(scope._context_identifier, expected_context_id)

    def test_context_identifier_format_with_mixed_notables(self):
        """
        Test context identifier with a mix of objects with and without moniker attributes.
        Validates: Requirements 27.1, 27.2, 27.3, 27.4
        """
        class NotableWithMoniker:
            moniker = "has_moniker"
        
        nmap = OrderedDict([
            ("obj_with", NotableWithMoniker()),
            ("primitive", 123),
            ("string", "test_str")
        ])
        scope = SequencerTestScope(self.seq, self.rec, "my_test", notables=nmap)
        
        expected_context_id = "my_test:has_moniker,123,test_str"
        self.assertEqual(scope._context_identifier, expected_context_id)

    def test_context_identifier_used_for_scope_id_management(self):
        """
        Test that context identifier is used as the scope name for scope ID management.
        Validates: Requirements 27.5
        """
        class NotableA:
            moniker = "param_a"
        class NotableB:
            moniker = "param_b"
        
        nmap = OrderedDict([("a", NotableA()), ("b", NotableB())])
        scope = SequencerTestScope(self.seq, self.rec, "test_parameterized", notables=nmap)
        
        expected_context_id = "test_parameterized:param_a,param_b"
        
        # Verify context identifier is correctly formed
        self.assertEqual(scope._context_identifier, expected_context_id)
        
        # Enter the scope to trigger scope_id_create with context_identifier
        scope.__enter__()
        
        # Verify the scope stack contains the context identifier as the scope name
        self.assertEqual(len(self.seq._scope_stack), 1)
        scope_name, scope_id = self.seq._scope_stack[0]
        self.assertEqual(scope_name, expected_context_id)
        
        # Exit the scope
        scope.__exit__(None, None, None)
        
        # Verify scope was popped
        self.assertEqual(len(self.seq._scope_stack), 0)

    def test_mark_activity_creates_file(self):
        scope = SequencerTestScope(self.seq, self.rec, "test")
        scope.__enter__()
        scope.mark_activity("doit", target="device", detail={"v":2})
        scope.__exit__(None, None, None)
        self.assertTrue(os.path.exists(scope._activity_stream_filename))
        with open(scope._activity_stream_filename) as af:
            data = af.read()
        self.assertIn("doit", data)


class SequencerScopeBaseTests(unittest.TestCase):

    def test_mark_test_as_error_and_skip(self):
        seq = DummySequencer()
        rec = DummyRecorder()
        ssb = SequencerScopeBase(seq, rec)
        class Ref:
            name = "tname"
            monikers = []
            pivots = {}
        tb = object()
        ssb._mark_test_as_error(Ref, "pid", tb)
        ssb._mark_test_as_skip(Ref, "pid", "why", "bug")
        self.assertEqual(len(rec.recorded), 2)
        self.assertIs(rec.recorded[0].errors[0], tb)
        self.assertEqual(rec.recorded[1].skipped, ("why", "bug"))

    def test_mark_descendants(self):
        seq = DummySequencer()
        rec = DummyRecorder()
        ssb = SequencerScopeBase(seq, rec)
        from automojo.testbase.testgroup import TestGroup
        from automojo.testbase.testref import TestRef

        def dummy():
            pass

        root = TestGroup("root")
        root._children["r1"] = TestRef(dummy)

        sub = TestGroup("sub")
        sub._children["s1"] = TestRef(dummy)
        root._children["sub"] = sub
        tb = object()
        ssb._mark_descendants_as_error(root, "rid", tb)
        ssb._mark_descendants_skipped(root, "rid", "skip", "bug")
        self.assertEqual(len(rec.recorded), 6)


if __name__ == "__main__":
    unittest.main()
