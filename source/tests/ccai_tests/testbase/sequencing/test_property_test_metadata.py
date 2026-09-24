"""
    .. module:: ccai_tests.testbase.sequencing.test_property_test_metadata
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests that property-test metadata reaches the recorded TestResult through the sequencer.

    Covers property-testing Requirements 8.4, 8.5 and 13.6: the TestResult of a property test carries
    ``property_metadata`` (``is_property_test``, ``examples_run``, ``max_examples``, ``seed``,
    ``job_seed``, ``counterexample``, ``strategy_descriptions``).

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

import os
import tempfile
import unittest

from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.output.outputcontext import SimpleOutputContext
from ccai.testbase.properties.decorators import given
from ccai.testbase.properties.strategies import integers
from ccai.testbase.results.model.testresult import TestResult
from ccai.testbase.sequencing.sequencertestscope import SequencerTestScope
from ccai.testbase.sequencing.testsequencer import TestSequencer


class _MockRecorder:
    """
        Recorder stand-in that captures previewed and recorded result nodes.
    """

    def __init__(self):
        self.previewed = []
        self.recorded = []
        return

    def preview(self, result_node):
        self.previewed.append(result_node)
        return

    def record(self, result_node):
        self.recorded.append(result_node)
        return


class _MockTreeNode:
    """
        Minimal test-tree node that the test scope finalizes on exit.
    """

    def __init__(self, name):
        self.name = name
        self.finalized = False
        return

    def finalize(self):
        self.finalized = True
        return


class _MockSequencer:
    """
        Sequencer stand-in for :class:`SequencerTestScope` that creates real :class:`TestResult` nodes.
    """

    def __init__(self, output_dir):
        self.output_context = SimpleOutputContext(base_dir=output_dir)
        self._scope_stack = []
        return

    def scope_id_create(self, ctx_name):
        parent = None
        if len(self._scope_stack) > 0:
            parent = self._scope_stack[-1][1]
        scope_id = "scope-{}".format(len(self._scope_stack))
        self._scope_stack.append((ctx_name, scope_id))
        return parent, scope_id

    def scope_id_pop(self, scope_name):
        if len(self._scope_stack) > 0:
            self._scope_stack.pop()
        return

    def find_treenode_for_scope(self, scope_name):
        node = _MockTreeNode(scope_name)
        return node

    def create_test_result_node(self, scope_id, name, monikers, pivots, parent_inst=None):
        result = TestResult(scope_id, name, parent_inst, monikers, pivots)
        return result


@given(x=integers(0, 100), constraints={"max_examples": 100})
def _falsifiable_property(x):
    assert x < 50
    return


@given(x=integers(0, 100), constraints={"max_examples": 7})
def _passing_property(x):
    return


class RunPropertyTestMetadataTests(unittest.TestCase):
    """
        Tests for :meth:`TestSequencer.run_property_test` attaching metadata to the TestResult.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

        self.sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        self.recorder = _MockRecorder()
        self.test_result = TestResult("test-inst", "pkg.mod#_passing_property", "module-inst", [], {})
        return

    def tearDown(self):
        injection_registry._scope_tree_root = self._original_scope_tree

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        return

    def test_run_property_test_attaches_metadata_to_test_result(self):
        """The metadata returned by run_property_test is attached to the passed TestResult."""
        metadata = self.sequencer.run_property_test(
            _passing_property, "pkg.mod#_passing_property", self.recorder, "test-inst", {},
            test_result=self.test_result
        )

        self.assertEqual(self.test_result.property_metadata, metadata)
        self.assertEqual(metadata["examples_run"], 7)
        self.assertEqual(metadata["job_seed"], self.sequencer.job_seed)
        return

    def test_run_property_test_without_test_result_returns_metadata(self):
        """run_property_test keeps working when no TestResult is passed (backward compatible call)."""
        metadata = self.sequencer.run_property_test(
            _passing_property, "pkg.mod#_passing_property", self.recorder, "test-inst", {}
        )

        self.assertTrue(metadata["is_property_test"])
        self.assertIsNone(self.test_result.property_metadata)
        return


class SequencerTestScopePropertyMetadataTests(unittest.TestCase):
    """
        Tests that the recorded TestResult of a property test scope carries ``property_metadata``.
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.sequencer = _MockSequencer(self.tempdir.name)
        self.recorder = _MockRecorder()
        return

    def tearDown(self):
        self.tempdir.cleanup()
        return

    def test_result_is_none_before_enter(self):
        """The scope exposes no TestResult before it is entered."""
        scope = SequencerTestScope(self.sequencer, self.recorder, "pkg.mod#_passing_property")
        self.assertIsNone(scope.result)
        return

    def test_result_is_previewed_test_result(self):
        """The scope exposes the TestResult it created and previewed on enter."""
        with SequencerTestScope(self.sequencer, self.recorder, "pkg.mod#_passing_property") as tscope:
            self.assertIsInstance(tscope.result, TestResult)
            self.assertIs(tscope.result, self.recorder.previewed[0])
        return

    def test_recorded_falsified_result_carries_property_metadata(self):
        """A falsified property test records a FAILED TestResult whose dict has property_metadata."""
        from ccai.testbase.properties.propertyrunner import PropertyRunner

        with SequencerTestScope(self.sequencer, self.recorder, "pkg.mod#_falsifiable_property") as tscope:
            prop_meta = _falsifiable_property._property_
            runner = PropertyRunner(
                constraints=prop_meta["constraints"],
                job_seed="job-seed-1",
                test_name="pkg.mod#_falsifiable_property",
                recorder=tscope.recorder,
                parent_inst=tscope.scope_id,
                test_result=tscope.result
            )
            runner.run(_falsifiable_property, prop_meta["strategies"], {})

        recorded_tests = [r for r in self.recorder.recorded if isinstance(r, TestResult)]
        self.assertEqual(len(recorded_tests), 1)

        dct = recorded_tests[0].as_dict()
        self.assertEqual(dct["result"], "FAILED")
        self.assertEqual(dct["property_metadata"]["job_seed"], "job-seed-1")
        self.assertIn("counterexample", dct["property_metadata"])
        return


if __name__ == '__main__':
    unittest.main()
