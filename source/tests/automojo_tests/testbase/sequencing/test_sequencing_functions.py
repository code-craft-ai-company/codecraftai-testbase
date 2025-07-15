import os
import tempfile
import unittest
from collections import OrderedDict

from automojo.presence.contextpaths import ContextPaths
from automojo.presence.wellknown import ContextSingleton
from automojo.xmodules.jsos import CHAR_RECORD_SEPERATOR

from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import AM_RUNTIME_VARIABLES

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
        ctx = ContextSingleton()
        self.tempdir = tempfile.TemporaryDirectory()
        ctx.insert(ContextPaths.RESULT_PATH_FOR_TESTS, self.tempdir.name)
        AM_RUNTIME_VARIABLES.AM_JOB_TYPE = JobType.TestRun
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
