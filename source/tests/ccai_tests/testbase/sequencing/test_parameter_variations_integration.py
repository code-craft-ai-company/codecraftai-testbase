"""
    Integration tests for parameter variations in sequence document generation.

    These tests verify the complete flow of parameter handling at different scope
    levels: session-only, module-level, test-local, and mixed parameter scopes.

    Requirements covered:
    - 6.1-6.5: Session-level parameter loops
    - 10.1-10.5: Module-level parameter loops
    - 14.1-14.5: Test-local parameter generation
"""

import ast
import collections
import os
import tempfile
import unittest

from ccai.xmodules.ximport import import_file

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.sources.sourcebase import SourceBase
from ccai.testbase.sequencing.testsequencer import TestSequencer


# ============================================================================
# MOCK CLASSES FOR TESTING
# ============================================================================

class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class MockInjectionScope:
    """Mock InjectionScope for testing sequence document generation."""
    
    def __init__(self):
        self.parameter_originations = collections.OrderedDict()
        self.validator_originations = collections.OrderedDict()


class MockTestGroup(TestGroup):
    """Mock TestGroup that returns a mock injection scope."""
    
    def __init__(self, name, package=None):
        super().__init__(name, package)
        self._mock_scope = MockInjectionScope()
    
    def get_resource_scope(self):
        return self._mock_scope


# ============================================================================
# FACTORY FUNCTIONS FOR TESTING
# ============================================================================

def session_factory_func():
    """Session-level factory function for testing."""
    yield "session_resource"


def module_factory_func():
    """Module-level factory function for testing."""
    yield "module_resource"


def test_local_factory_func():
    """Test-local factory function for testing."""
    yield "test_local_resource"


def another_session_factory():
    """Another session-level factory for multiple parameter testing."""
    yield "another_session_resource"


def another_module_factory():
    """Another module-level factory for multiple parameter testing."""
    yield "another_module_resource"


def another_test_local_factory():
    """Another test-local factory for multiple parameter testing."""
    yield "another_test_local_resource"


# ============================================================================
# TEST FUNCTIONS
# ============================================================================

def test_with_session_param(session_param):
    """Test function that uses a session parameter."""
    pass


def test_with_module_param(module_param):
    """Test function that uses a module parameter."""
    pass


def test_with_test_local_param(test_local_param):
    """Test function that uses a test-local parameter."""
    pass


def test_with_mixed_params(session_param, module_param, test_local_param):
    """Test function that uses parameters from all scopes."""
    pass


def test_with_multiple_session_params(session_param_a, session_param_b):
    """Test function that uses multiple session parameters."""
    pass


def test_with_multiple_module_params(module_param_a, module_param_b):
    """Test function that uses multiple module parameters."""
    pass


def test_with_multiple_test_local_params(test_local_param_a, test_local_param_b):
    """Test function that uses multiple test-local parameters."""
    pass


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_test_tree_with_test_func(test_func, module_name=None):
    """
    Create a test tree with a single test function.
    
    Args:
        test_func: The test function to include
        module_name: Optional module name override
        
    Returns:
        tuple: (root MockTestGroup, module MockTestGroup)
    """
    if module_name is None:
        module_name = test_func.__module__
    
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package="")
    test_ref = TestRef(test_func)
    module_group._children[test_ref.base_name] = test_ref
    root._children[module_name] = module_group
    
    return root, module_group


def add_session_parameter(root, param_name, factory_func, implied=False):
    """
    Add a session-level parameter origination to the root node.
    
    Args:
        root: The root MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        "<session>",
        param_name,
        ResourceLifespan.Session,
        source,
        implied=implied
    )
    root._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_module_parameter(module_group, param_name, factory_func, implied=False):
    """
    Add a module-level parameter origination to the module node.
    
    Args:
        module_group: The module MockTestGroup
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        module_group.name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=implied
    )
    module_group._mock_scope.parameter_originations[param_name] = origin
    return origin


def add_test_local_parameter(test_func, param_name, factory_func, implied=False):
    """
    Add a test-local parameter origination to the injection registry.
    
    Args:
        test_func: The test function
        param_name: Name of the parameter
        factory_func: The factory function to use
        implied: Whether the parameter is implied
        
    Returns:
        ResourceOrigin: The created resource origin
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    source = MockSourceBase(factory_func)
    origin = ResourceOrigin(
        scope_name,
        param_name,
        ResourceLifespan.Test,
        source,
        implied=implied
    )
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, origin)
    return origin


def register_test_scope(test_func):
    """
    Register a test scope in the injection registry without parameters.
    
    Args:
        test_func: The test function
    """
    scope_name = "{}#{}".format(test_func.__module__, test_func.__name__)
    injection_registry._scope_tree_root.add_descendent_resource_origination(scope_name, None)


# ============================================================================
# TEST CLASSES
# ============================================================================

class SessionOnlyParameterIntegrationTests(unittest.TestCase):
    """
    Integration tests for session-only parameter generation.

    **Validates: Requirements 6.1-6.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_session_only_parameter_generates_valid_document(self):
        """
        Test that a document with session-only parameters is valid Python.

        **Validates: Requirements 6.1-6.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_session_param)
        add_session_parameter(root, "session_param", session_factory_func)
        register_test_scope(test_with_session_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with session-only parameters should be valid Python"
        )

    def test_session_only_parameter_is_importable(self):
        """
        Test that a document with session-only parameters can be imported.

        **Validates: Requirements 6.1-6.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_session_param)
        add_session_parameter(root, "session_param", session_factory_func)
        register_test_scope(test_with_session_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("session_only_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with session-only parameters should be importable: {e}")

    def test_session_parameter_loop_in_session_function(self):
        """
        Test that session parameter loop appears in session function.

        **Validates: Requirements 6.2, 6.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_session_param)
        add_session_parameter(root, "session_param", session_factory_func)
        register_test_scope(test_with_session_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "for session_param in",
            generated_code,
            "Session parameter loop should be in generated code"
        )
        self.assertIn(
            session_factory_func.__name__,
            generated_code,
            "Session factory function should be called"
        )

    def test_session_parameter_passed_to_scope_function(self):
        """
        Test that session parameter is passed to scope function.

        **Validates: Requirements 6.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_session_param)
        add_session_parameter(root, "session_param", session_factory_func)
        register_test_scope(test_with_session_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check that scope function is called with session parameter
        self.assertIn(
            "sequencer, session_param",
            generated_code,
            "Scope function should be called with session parameter"
        )

    def test_multiple_session_parameters_generates_valid_document(self):
        """
        Test that multiple session parameters generate valid Python.

        **Validates: Requirements 6.1-6.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_session_params)
        add_session_parameter(root, "session_param_a", session_factory_func)
        add_session_parameter(root, "session_param_b", another_session_factory)
        register_test_scope(test_with_multiple_session_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with multiple session parameters should be valid Python"
        )
        self.assertIn("for session_param_a in", generated_code)
        self.assertIn("for session_param_b in", generated_code)


class ModuleLevelParameterIntegrationTests(unittest.TestCase):
    """
    Integration tests for module-level parameter generation.

    **Validates: Requirements 10.1-10.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_module_level_parameter_generates_valid_document(self):
        """
        Test that a document with module-level parameters is valid Python.

        **Validates: Requirements 10.1-10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_module_param)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_module_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with module-level parameters should be valid Python"
        )

    def test_module_level_parameter_is_importable(self):
        """
        Test that a document with module-level parameters can be imported.

        **Validates: Requirements 10.1-10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_module_param)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_module_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("module_level_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
        except Exception as e:
            self.fail(f"Document with module-level parameters should be importable: {e}")

    def test_module_parameter_loop_in_scope_function(self):
        """
        Test that module parameter loop appears in scope function.

        **Validates: Requirements 10.2, 10.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_module_param)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_module_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "for module_param in",
            generated_code,
            "Module parameter loop should be in generated code"
        )
        self.assertIn(
            module_factory_func.__name__,
            generated_code,
            "Module factory function should be called"
        )

    def test_module_parameter_factory_import_added(self):
        """
        Test that module parameter factory import is added to document.

        **Validates: Requirements 10.1, 10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_module_param)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_module_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        expected_import = "from {} import {}".format(
            module_factory_func.__module__,
            module_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            generated_code,
            "Module factory import should be in generated code"
        )

    def test_multiple_module_parameters_generates_valid_document(self):
        """
        Test that multiple module parameters generate valid Python.

        **Validates: Requirements 10.1-10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_module_params)
        add_module_parameter(module_group, "module_param_a", module_factory_func)
        add_module_parameter(module_group, "module_param_b", another_module_factory)
        register_test_scope(test_with_multiple_module_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with multiple module parameters should be valid Python"
        )
        self.assertIn("for module_param_a in", generated_code)
        self.assertIn("for module_param_b in", generated_code)


class TestLocalParameterIntegrationTests(unittest.TestCase):
    """
    Integration tests for test-local parameter generation.

    **Validates: Requirements 14.1-14.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_test_local_parameter_generates_valid_document(self):
        """
        Test that a document with test-local parameters is valid Python.

        **Validates: Requirements 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with test-local parameters should be valid Python"
        )

    def test_test_local_parameter_is_importable(self):
        """
        Test that a document with test-local parameters can be imported.

        **Validates: Requirements 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("test_local_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
        except Exception as e:
            self.fail(f"Document with test-local parameters should be importable: {e}")

    def test_test_local_parameter_has_setup_context(self):
        """
        Test that test-local parameter has test setup context.

        **Validates: Requirements 14.1, 14.2**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "enter_test_setup_context(",
            generated_code,
            "Test setup context should be in generated code"
        )

    def test_test_local_parameter_loop_generated(self):
        """
        Test that test-local parameter loop is generated.

        **Validates: Requirements 14.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "for test_local_param in",
            generated_code,
            "Test-local parameter loop should be in generated code"
        )

    def test_test_local_parameter_factory_import_added(self):
        """
        Test that test-local parameter factory import is added.

        **Validates: Requirements 14.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        expected_import = "from {} import {}".format(
            test_local_factory_func.__module__,
            test_local_factory_func.__name__
        )
        self.assertIn(
            expected_import,
            generated_code,
            "Test-local factory import should be in generated code"
        )

    def test_multiple_test_local_parameters_generates_valid_document(self):
        """
        Test that multiple test-local parameters generate valid Python.

        **Validates: Requirements 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_multiple_test_local_params)
        add_test_local_parameter(test_with_multiple_test_local_params, "test_local_param_a", test_local_factory_func)
        add_test_local_parameter(test_with_multiple_test_local_params, "test_local_param_b", another_test_local_factory)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with multiple test-local parameters should be valid Python"
        )
        self.assertIn("for test_local_param_a in", generated_code)
        self.assertIn("for test_local_param_b in", generated_code)




class MixedParameterScopesIntegrationTests(unittest.TestCase):
    """
    Integration tests for mixed parameter scopes.

    Tests verify that parameters from different scopes (session, module, test-local)
    can be combined in a single test and generate valid, importable documents.

    **Validates: Requirements 6.1-6.5, 10.1-10.5, 14.1-14.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_session_and_module_parameters_generates_valid_document(self):
        """
        Test that session and module parameters together generate valid Python.

        **Validates: Requirements 6.1-6.5, 10.1-10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with session and module parameters should be valid Python"
        )
        self.assertIn("for session_param in", generated_code)
        self.assertIn("for module_param in", generated_code)

    def test_session_and_test_local_parameters_generates_valid_document(self):
        """
        Test that session and test-local parameters together generate valid Python.

        **Validates: Requirements 6.1-6.5, 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with session and test-local parameters should be valid Python"
        )
        self.assertIn("for session_param in", generated_code)
        self.assertIn("for test_local_param in", generated_code)

    def test_module_and_test_local_parameters_generates_valid_document(self):
        """
        Test that module and test-local parameters together generate valid Python.

        **Validates: Requirements 10.1-10.5, 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_module_parameter(module_group, "module_param", module_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with module and test-local parameters should be valid Python"
        )
        self.assertIn("for module_param in", generated_code)
        self.assertIn("for test_local_param in", generated_code)

    def test_all_three_parameter_scopes_generates_valid_document(self):
        """
        Test that all three parameter scopes together generate valid Python.

        **Validates: Requirements 6.1-6.5, 10.1-10.5, 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with all three parameter scopes should be valid Python"
        )
        self.assertIn("for session_param in", generated_code)
        self.assertIn("for module_param in", generated_code)
        self.assertIn("for test_local_param in", generated_code)

    def test_all_three_parameter_scopes_is_importable(self):
        """
        Test that document with all three parameter scopes can be imported.

        **Validates: Requirements 6.1-6.5, 10.1-10.5, 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        try:
            sequence_mod = import_file("mixed_params_doc", output_file)
            self.assertIsNotNone(sequence_mod)
            self.assertTrue(hasattr(sequence_mod, 'session'))
            self.assertTrue(callable(sequence_mod.session))
        except Exception as e:
            self.fail(f"Document with all three parameter scopes should be importable: {e}")

    def test_mixed_parameters_have_correct_nesting_order(self):
        """
        Test that mixed parameters are nested in correct order.

        Session parameters should be outermost, then module, then test-local.

        **Validates: Requirements 6.3, 10.3, 14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Find positions of each parameter loop
        session_pos = generated_code.find("for session_param in")
        module_pos = generated_code.find("for module_param in")
        test_local_pos = generated_code.find("for test_local_param in")

        self.assertNotEqual(session_pos, -1, "Session parameter loop should exist")
        self.assertNotEqual(module_pos, -1, "Module parameter loop should exist")
        self.assertNotEqual(test_local_pos, -1, "Test-local parameter loop should exist")

        # Session should come before module (in session function)
        # Module should come before test-local (in scope function)
        # Note: Session is in session(), module and test-local are in scope_*()
        self.assertLess(
            session_pos,
            module_pos,
            "Session parameter loop should appear before module parameter loop"
        )
        self.assertLess(
            module_pos,
            test_local_pos,
            "Module parameter loop should appear before test-local parameter loop"
        )

    def test_mixed_parameters_all_factory_imports_present(self):
        """
        Test that all factory imports are present for mixed parameters.

        **Validates: Requirements 6.1, 10.1, 14.3**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        add_test_local_parameter(test_with_mixed_params, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check all factory imports are present
        session_import = "from {} import {}".format(
            session_factory_func.__module__,
            session_factory_func.__name__
        )
        module_import = "from {} import {}".format(
            module_factory_func.__module__,
            module_factory_func.__name__
        )
        test_local_import = "from {} import {}".format(
            test_local_factory_func.__module__,
            test_local_factory_func.__name__
        )

        self.assertIn(session_import, generated_code, "Session factory import should be present")
        self.assertIn(module_import, generated_code, "Module factory import should be present")
        self.assertIn(test_local_import, generated_code, "Test-local factory import should be present")

    def test_session_parameter_passed_through_to_scope_with_module_param(self):
        """
        Test that session parameter is passed through scope function with module param.

        **Validates: Requirements 6.4, 10.4**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", module_factory_func)
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # The scope function should accept session_param as argument
        self.assertIn(
            "session_param",
            generated_code,
            "Session parameter should be passed to scope function"
        )

    def test_test_local_parameter_generates_notables_map(self):
        """
        Test that test-local parameter generates notables map.

        **Validates: Requirements 14.1-14.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_test_local_param)
        add_test_local_parameter(test_with_test_local_param, "test_local_param", test_local_factory_func)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            "notables",
            generated_code,
            "Notables map should be generated for test-local parameters"
        )


class ParameterScopeEdgeCasesTests(unittest.TestCase):
    """
    Edge case tests for parameter scope handling.

    **Validates: Requirements 6.1-6.5, 10.1-10.5, 14.1-14.5**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        self._original_scope_tree = injection_registry._scope_tree_root
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

        self.tempdir.cleanup()
        injection_registry._scope_tree_root = self._original_scope_tree

    def _create_sequencer_with_tree(self, test_tree):
        """Create a TestSequencer with the given test tree."""
        sequencer = TestSequencer(
            jobtitle="Test Job",
            root=self.tempdir.name,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )
        sequencer._testtree = test_tree
        return sequencer

    def _is_valid_python(self, code):
        """Check if the given code is valid Python syntax."""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def test_implied_session_parameter_is_skipped(self):
        """
        Test that implied session parameters are skipped.

        **Validates: Requirements 6.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_session_param)
        add_session_parameter(root, "implied_param", session_factory_func, implied=True)
        add_session_parameter(root, "session_param", another_session_factory, implied=False)
        register_test_scope(test_with_session_param)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document should be valid Python"
        )
        # Implied parameter should not have a for loop
        self.assertNotIn(
            "for implied_param in",
            generated_code,
            "Implied parameter should not have a for loop"
        )
        # Non-implied parameter should have a for loop
        self.assertIn(
            "for session_param in",
            generated_code,
            "Non-implied parameter should have a for loop"
        )

    def test_no_parameters_generates_valid_document(self):
        """
        Test that a test with no parameters generates valid Python.

        **Validates: Requirements 6.1-6.5, 10.1-10.5, 14.1-14.5**
        """
        def test_no_params():
            """Test function with no parameters."""
            pass

        root, module_group = create_test_tree_with_test_func(test_no_params)
        register_test_scope(test_no_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with no parameters should be valid Python"
        )

    def test_same_factory_used_at_different_scopes(self):
        """
        Test that the same factory can be used at different scopes.

        **Validates: Requirements 6.1-6.5, 10.1-10.5**
        """
        root, module_group = create_test_tree_with_test_func(test_with_mixed_params)
        # Use the same factory at session and module level
        add_session_parameter(root, "session_param", session_factory_func)
        add_module_parameter(module_group, "module_param", session_factory_func)  # Same factory
        register_test_scope(test_with_mixed_params)
        
        sequencer = self._create_sequencer_with_tree(root)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Document with same factory at different scopes should be valid Python"
        )
        self.assertIn("for session_param in", generated_code)
        self.assertIn("for module_param in", generated_code)


if __name__ == '__main__':
    unittest.main()
