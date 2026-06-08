"""
    .. module:: test_scope_exception_handling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Tests for scope context manager exception handling.

    Tests for:
    - SkipError propagation through scope hierarchy (Requirements 16.4, 16.5, 17.4, 17.5)
    - AssertionError handling in test scope (Requirement 19.6)
    - Generic exception handling and error marking (Requirements 19.5, 19.7)

    .. moduleauthor:: CodeCraftX
"""

import os
import tempfile
import unittest
from collections import OrderedDict

from ccai.errors.exceptions import SkipError

from ccai.testbase.sequencing.sequencersessionscope import SequencerSessionScope
from ccai.testbase.sequencing.sequencermodulescope import SequencerModuleScope
from ccai.testbase.sequencing.sequencertestscope import SequencerTestScope
from ccai.testbase.sequencing.sequencertestsetupscope import SequencerTestSetupScope
from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.output.outputcontext import SimpleOutputContext


class MockResult:
    """Mock result object for testing."""
    
    def __init__(self, inst_id=None, name=None, parent_inst=None):
        self.inst_id = inst_id
        self.name = name
        self.parent_inst = parent_inst
        self.errors = []
        self.failures = []
        self.skipped = None
        self.passed = False
        self.finalized = False

    def add_error(self, tb):
        self.errors.append(tb)

    def add_failure(self, tb):
        self.failures.append(tb)

    def mark_skip(self, reason, bug):
        self.skipped = (reason, bug)

    def mark_passed(self):
        self.passed = True

    def finalize(self):
        self.finalized = True


class MockRecorder:
    """Mock recorder for testing."""
    
    def __init__(self):
        self.recorded = []
        self.previewed = []

    def record(self, result):
        self.recorded.append(result)

    def preview(self, result):
        self.previewed.append(result)


class MockJobContainer:
    """Mock job container for session scope testing."""
    
    def __init__(self, inst_id, name):
        self.inst_id = inst_id
        self.name = name


class MockSequencer:
    """Mock sequencer for testing scope context managers."""
    
    def __init__(self):
        self._scope_stack = []
        self._testtree = None
        self._created_results = []
        self._tree_nodes = {}
        # The scope resolves its by-products directory via the sequencer's output context.
        self.output_context = SimpleOutputContext(base_dir=tempfile.mkdtemp())

    def scope_id_create(self, ctx_name):
        parent = self._scope_stack[-1][1] if self._scope_stack else None
        sid = "scope-{}".format(len(self._scope_stack))
        self._scope_stack.append((ctx_name, sid))
        return (parent, sid)

    def scope_id_pop(self, scope_name):
        if self._scope_stack:
            self._scope_stack.pop()

    def scope_id_push(self, scope_name, scope_id):
        self._scope_stack.append((scope_name, scope_id))

    @property
    def testtree(self):
        return self._testtree

    def find_treenode_for_scope(self, scope_name):
        """Return a tree node from the registered nodes."""
        if scope_name in self._tree_nodes:
            return self._tree_nodes[scope_name]
        # Create a minimal mock for unregistered scopes
        return self._create_minimal_mock_node(scope_name)

    def _create_minimal_mock_node(self, name):
        """Create a minimal mock node for unregistered scopes."""
        class MinimalMockNode:
            def __init__(self, node_name):
                self.name = node_name
                self._finalized = False
                self._children = {}
            
            @property
            def finalized(self):
                return self._finalized
            
            @property
            def children(self):
                return self._children
            
            def finalize(self):
                self._finalized = True
        
        return MinimalMockNode(name)

    def create_test_result_node(self, inst_id, name, monikers, pivots, parent_inst=None):
        result = MockResult(inst_id, name, parent_inst)
        self._created_results.append(result)
        return result

    def create_test_result_container(self, inst_id, name, parent_inst=None):
        result = MockResult(inst_id, name, parent_inst)
        self._created_results.append(result)
        return result


def create_test_tree_with_real_refs():
    """Create a test tree with real TestRef and TestGroup objects for testing."""
    def dummy_test():
        pass
    
    root = TestGroup("root")
    
    # Add a test reference
    test_ref = TestRef(dummy_test)
    root._children["test_one"] = test_ref
    
    # Add a sub-group with tests
    sub_group = TestGroup("sub_module")
    sub_test = TestRef(dummy_test)
    sub_group._children["test_two"] = sub_test
    root._children["sub_module"] = sub_group
    
    return root


class TestSessionScopeSkipErrorHandling(unittest.TestCase):
    """
    Tests for SkipError handling in SequencerSessionScope.
    Validates Requirements 16.4, 16.5
    """

    def setUp(self):
        self.seq = MockSequencer()
        self.rec = MockRecorder()
        # Use real TestGroup and TestRef for proper isinstance checks
        self.seq._testtree = create_test_tree_with_real_refs()

    def test_session_scope_skip_error_marks_descendants_skipped(self):
        """
        Test that SkipError in session scope marks all descendants as skipped.
        Validates Requirement 16.4
        """
        root_result = MockJobContainer("root-id", "test-session")
        scope = SequencerSessionScope(self.seq, self.rec, root_result)
        
        # Enter scope
        scope.__enter__()
        
        # Create a SkipError with reason and bug
        skip_error = SkipError("Test skipped due to precondition")
        skip_error.reason = "Precondition not met"
        skip_error.bug = "BUG-123"
        
        # Exit with SkipError
        handled = scope.__exit__(SkipError, skip_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify descendants were marked as skipped
        self.assertGreater(len(self.rec.recorded), 0)
        
        # Check that at least one result was marked as skipped
        skipped_results = [r for r in self.rec.recorded if r.skipped is not None]
        self.assertGreater(len(skipped_results), 0)
        
        for result in skipped_results:
            self.assertEqual(result.skipped[0], "Precondition not met")
            self.assertEqual(result.skipped[1], "BUG-123")

    def test_session_scope_generic_exception_marks_descendants_errored(self):
        """
        Test that generic exception in session scope marks all descendants as errored.
        Validates Requirement 16.5
        """
        root_result = MockJobContainer("root-id", "test-session")
        scope = SequencerSessionScope(self.seq, self.rec, root_result)
        
        # Enter scope
        scope.__enter__()
        
        # Create a generic exception
        generic_error = RuntimeError("Setup failed")
        
        # Exit with generic exception
        handled = scope.__exit__(RuntimeError, generic_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify descendants were marked as errored
        self.assertGreater(len(self.rec.recorded), 0)
        
        # Check that at least one result was marked as errored
        errored_results = [r for r in self.rec.recorded if len(r.errors) > 0]
        self.assertGreater(len(errored_results), 0)


class TestModuleScopeSkipErrorHandling(unittest.TestCase):
    """
    Tests for SkipError handling in SequencerModuleScope.
    Validates Requirements 17.4, 17.5
    """

    def setUp(self):
        self.seq = MockSequencer()
        self.rec = MockRecorder()

    def test_module_scope_skip_error_marks_descendants_skipped(self):
        """
        Test that SkipError in module scope marks all descendants as skipped.
        Validates Requirement 17.4
        """
        # Create a real test tree for the module scope
        module_tree = create_test_tree_with_real_refs()
        self.seq._tree_nodes["test.module"] = module_tree
        
        scope = SequencerModuleScope(self.seq, self.rec, "test.module")
        
        # Enter scope
        scope.__enter__()
        
        # Clear recorded results from enter
        initial_count = len(self.rec.recorded)
        
        # Create a SkipError
        skip_error = SkipError("Module skipped")
        skip_error.reason = "Module precondition failed"
        skip_error.bug = "BUG-456"
        
        # Exit with SkipError
        handled = scope.__exit__(SkipError, skip_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify new results were recorded (descendants marked as skipped)
        self.assertGreater(len(self.rec.recorded), initial_count)
        
        # Verify the skipped results have correct reason and bug
        skipped_results = [r for r in self.rec.recorded[initial_count:] if r.skipped is not None]
        self.assertGreater(len(skipped_results), 0)
        
        for result in skipped_results:
            self.assertEqual(result.skipped[0], "Module precondition failed")
            self.assertEqual(result.skipped[1], "BUG-456")

    def test_module_scope_generic_exception_marks_descendants_errored(self):
        """
        Test that generic exception in module scope marks all descendants as errored.
        Validates Requirement 17.5
        """
        # Create a real test tree for the module scope
        module_tree = create_test_tree_with_real_refs()
        self.seq._tree_nodes["test.module"] = module_tree
        
        scope = SequencerModuleScope(self.seq, self.rec, "test.module")
        
        # Enter scope
        scope.__enter__()
        
        # Clear recorded results from enter
        initial_count = len(self.rec.recorded)
        
        # Create a generic exception
        generic_error = ValueError("Module setup failed")
        
        # Exit with generic exception
        handled = scope.__exit__(ValueError, generic_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify new results were recorded (descendants marked as errored)
        self.assertGreater(len(self.rec.recorded), initial_count)
        
        # Verify the errored results have errors
        errored_results = [r for r in self.rec.recorded[initial_count:] if len(r.errors) > 0]
        self.assertGreater(len(errored_results), 0)


class TestTestScopeExceptionHandling(unittest.TestCase):
    """
    Tests for exception handling in SequencerTestScope.
    Validates Requirements 19.5, 19.6, 19.7
    """

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self.seq = MockSequencer()
        self.rec = MockRecorder()

    def tearDown(self):
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()

    def test_test_scope_skip_error_marks_result_skipped(self):
        """
        Test that SkipError in test scope marks the result as skipped.
        Validates Requirement 19.5
        """
        scope = SequencerTestScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Create a SkipError
        skip_error = SkipError("Test skipped")
        skip_error.reason = "Test precondition not met"
        skip_error.bug = "BUG-789"
        
        # Exit with SkipError
        handled = scope.__exit__(SkipError, skip_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify result was marked as skipped
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertIsNotNone(result.skipped)
        self.assertEqual(result.skipped[0], "Test precondition not met")
        self.assertEqual(result.skipped[1], "BUG-789")
        self.assertTrue(result.finalized)

    def test_test_scope_assertion_error_marks_result_failed(self):
        """
        Test that AssertionError in test scope marks the result as failed.
        Validates Requirement 19.6
        """
        scope = SequencerTestScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Create an AssertionError
        assertion_error = AssertionError("Expected 1 but got 2")
        
        # Exit with AssertionError
        handled = scope.__exit__(AssertionError, assertion_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify result was marked as failed (not errored)
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertGreater(len(result.failures), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertTrue(result.finalized)

    def test_test_scope_generic_exception_marks_result_errored(self):
        """
        Test that generic exception in test scope marks the result as errored.
        Validates Requirement 19.7
        """
        scope = SequencerTestScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Create a generic exception
        generic_error = RuntimeError("Unexpected error during test")
        
        # Exit with generic exception
        handled = scope.__exit__(RuntimeError, generic_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify result was marked as errored (not failed)
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertGreater(len(result.errors), 0)
        self.assertEqual(len(result.failures), 0)
        self.assertTrue(result.finalized)

    def test_test_scope_no_exception_marks_result_passed(self):
        """
        Test that no exception in test scope marks the result as passed.
        Validates Requirement 19.8
        """
        scope = SequencerTestScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Exit without exception
        handled = scope.__exit__(None, None, None)
        
        # Verify result was marked as passed
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertTrue(result.passed)
        self.assertTrue(result.finalized)


class TestTestSetupScopeExceptionHandling(unittest.TestCase):
    """
    Tests for exception handling in SequencerTestSetupScope.
    """

    def setUp(self):
        self.seq = MockSequencer()
        self.rec = MockRecorder()

    def test_test_setup_scope_skip_error_marks_test_skipped(self):
        """
        Test that SkipError in test setup scope marks the test as skipped.
        """
        # Create a TestRef for the test setup scope to use
        def dummy_test():
            pass
        test_ref = TestRef(dummy_test)
        self.seq._tree_nodes["test_function"] = test_ref
        
        scope = SequencerTestSetupScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Create a SkipError
        skip_error = SkipError("Setup skipped")
        skip_error.reason = "Setup precondition not met"
        skip_error.bug = "BUG-101"
        
        # Exit with SkipError
        handled = scope.__exit__(SkipError, skip_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify test was marked as skipped
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertIsNotNone(result.skipped)

    def test_test_setup_scope_generic_exception_marks_test_errored(self):
        """
        Test that generic exception in test setup scope marks the test as errored.
        """
        # Create a TestRef for the test setup scope to use
        def dummy_test():
            pass
        test_ref = TestRef(dummy_test)
        self.seq._tree_nodes["test_function"] = test_ref
        
        scope = SequencerTestSetupScope(self.seq, self.rec, "test_function")
        
        # Enter scope
        scope.__enter__()
        
        # Create a generic exception
        generic_error = RuntimeError("Setup failed")
        
        # Exit with generic exception
        handled = scope.__exit__(RuntimeError, generic_error, None)
        
        # Verify exception was handled
        self.assertTrue(handled)
        
        # Verify test was marked as errored
        self.assertEqual(len(self.rec.recorded), 1)
        result = self.rec.recorded[0]
        self.assertGreater(len(result.errors), 0)


if __name__ == "__main__":
    unittest.main()
