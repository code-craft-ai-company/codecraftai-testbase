"""
    Unit tests for sequence document generation.

    Tests cover:
    - Valid test trees produce valid Python modules (Requirements 10.1, 10.2, 10.3)
    - Parameter factory imports are correctly generated (Requirements 10.4)

    **Feature: execution, Property 1: Valid test trees produce valid Python modules**
    **Validates: Requirements 10.1, 10.2, 10.3**

    **Feature: execution, Property 2: Parameter factory imports are correctly generated**
    **Validates: Requirements 10.4**
"""

import ast
import os
import tempfile
import unittest

from automojo.thisapp.persona import APP_PERSONA_ESTABLISHED, establish_app_persona
from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.runtime.enumerations import JobType
from automojo.runtime.runtimevariables import RuntimeVariablesDesc
import automojo.runtime.paths as runtime_paths

from automojo.testbase.testgroup import TestGroup
from automojo.testbase.testref import TestRef
from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.sequencing.testsequencer import (
    TestSequencer,
    CONSTRAINT_IMPORT_INSERTION_POINT,
    FACTORY_IMPORT_INSERTION_POINT,
)


def create_test_function(name, module_name):
    """Create a mock test function with the given name and module."""
    def test_func():
        pass
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def create_simple_test_tree(module_name, test_names):
    """
    Create a simple test tree with one module containing the specified tests.
    
    Args:
        module_name: Name of the module
        test_names: List of test function names
        
    Returns:
        TestGroup: Root of the test tree
    """
    root = TestGroup("root")
    module_group = TestGroup(module_name, package="")
    
    for test_name in test_names:
        test_func = create_test_function(test_name, module_name)
        test_ref = TestRef(test_func)
        module_group._children[test_ref.base_name] = test_ref
    
    root._children[module_name] = module_group
    return root


def create_multi_module_test_tree(modules_config):
    """
    Create a test tree with multiple modules.
    
    Args:
        modules_config: Dict mapping module names to lists of test names
        
    Returns:
        TestGroup: Root of the test tree
    """
    root = TestGroup("root")
    
    for module_name, test_names in modules_config.items():
        module_group = TestGroup(module_name, package="")
        
        for test_name in test_names:
            test_func = create_test_function(test_name, module_name)
            test_ref = TestRef(test_func)
            module_group._children[test_ref.base_name] = test_ref
        
        root._children[module_name] = module_group
    
    return root


def create_nested_test_tree(package_name, module_name, test_names):
    """
    Create a nested test tree with a package containing a module.
    
    Args:
        package_name: Name of the package
        module_name: Name of the module within the package
        test_names: List of test function names
        
    Returns:
        TestGroup: Root of the test tree
    """
    root = TestGroup("root")
    pkg_group = TestGroup(package_name, package="")
    
    full_module_name = f"{package_name}.{module_name}"
    module_group = TestGroup(module_name, package=package_name)
    
    for test_name in test_names:
        test_func = create_test_function(test_name, full_module_name)
        test_ref = TestRef(test_func)
        module_group._children[test_ref.base_name] = test_ref
    
    pkg_group._children[module_name] = module_group
    root._children[package_name] = pkg_group
    
    return root


class SequenceDocumentGenerationTests(unittest.TestCase):
    """
    Unit tests for sequence document generation.
    
    **Feature: execution, Property 1: Valid test trees produce valid Python modules**
    **Validates: Requirements 10.1, 10.2, 10.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        # Reset cached runtime paths so overrides take effect for each test
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore original injection registry state
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

    def _get_function_names(self, code):
        """Extract function names from Python code."""
        try:
            tree = ast.parse(code)
            return [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        except SyntaxError:
            return []

    def test_simple_tree_produces_valid_python(self):
        """
        Test that a simple test tree produces valid Python code.
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one", "test_two"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated sequence document should be valid Python syntax"
        )

    def test_multi_module_tree_produces_valid_python(self):
        """
        Test that a multi-module test tree produces valid Python code.
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        modules_config = {
            "module_a": ["test_a1", "test_a2"],
            "module_b": ["test_b1"],
            "module_c": ["test_c1", "test_c2", "test_c3"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated sequence document for multi-module tree should be valid Python syntax"
        )

    def test_nested_tree_produces_valid_python(self):
        """
        Test that a nested test tree with packages produces valid Python code.
        
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        test_tree = create_nested_test_tree("mypackage", "mymodule", ["test_nested"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertTrue(
            self._is_valid_python(generated_code),
            "Generated sequence document for nested tree should be valid Python syntax"
        )

    def test_session_function_always_generated(self):
        """
        Test that the generated document contains a 'session' function.
        
        **Validates: Requirements 10.1, 10.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        function_names = self._get_function_names(generated_code)
        self.assertIn(
            'session',
            function_names,
            "Generated sequence document should contain a 'session' function"
        )

    def test_scope_functions_generated_for_each_module(self):
        """
        Test that scope functions are generated for each module in the tree.
        
        **Validates: Requirements 10.3**
        """
        modules_config = {
            "alpha_module": ["test_alpha"],
            "beta_module": ["test_beta"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        function_names = self._get_function_names(generated_code)

        self.assertIn(
            'scope_alpha_module',
            function_names,
            "Generated document should contain scope function for alpha_module"
        )
        self.assertIn(
            'scope_beta_module',
            function_names,
            "Generated document should contain scope function for beta_module"
        )


class SequenceDocumentImportsTests(unittest.TestCase):
    """
    Unit tests for sequence document import generation.
    
    **Feature: execution, Property 2: Parameter factory imports are correctly generated**
    **Validates: Requirements 10.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        # Reset cached runtime paths so overrides take effect for each test
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore original injection registry state
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

    def test_document_contains_logging_import(self):
        """
        Test that the generated document imports the logging module.
        
        **Validates: Requirements 10.4**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'import logging',
            generated_code,
            "Generated sequence document should import logging"
        )

    def test_document_contains_constraints_catalog_import(self):
        """
        Test that the generated document imports ConstraintsCatalog.
        
        **Validates: Requirements 10.4**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertIn(
            'ConstraintsCatalog',
            generated_code,
            "Generated sequence document should import ConstraintsCatalog"
        )

    def test_insertion_points_are_processed(self):
        """
        Test that insertion point markers are not present in the final output.
        
        **Validates: Requirements 10.4**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            CONSTRAINT_IMPORT_INSERTION_POINT,
            generated_code,
            "Constraint import insertion point should be processed"
        )
        self.assertNotIn(
            FACTORY_IMPORT_INSERTION_POINT,
            generated_code,
            "Factory import insertion point should be processed"
        )


class SequenceDocumentStructureTests(unittest.TestCase):
    """
    Unit tests for sequence document structure.
    
    **Feature: execution, Property 1: Valid test trees produce valid Python modules**
    **Validates: Requirements 10.1, 10.2, 10.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        if not APP_PERSONA_ESTABLISHED:
            establish_app_persona(
                name="automojo-testbase",
                logger_name="automojo-testbase",
                log_basename="automojo-testbase"
            )

        self.tempdir = tempfile.TemporaryDirectory()

        # Reset cached runtime paths so overrides take effect for each test
        runtime_paths.DIR_TESTRESULTS_DIRECTORY = None
        runtime_paths.DIR_TESTCASE_BYPRODUCTS_DIRECTORY = None

        this_app = ThisApplicationSingleton()
        this_app.override_variable_value(RuntimeVariablesDesc.AM_JOB_TYPE, JobType.TestRun)
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULT_PATH_FOR_TESTS, self.tempdir.name)

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore original injection registry state
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

    def test_single_session_scope_context_entry(self):
        """
        Test that there is exactly one session scope context entry.
        
        **Validates: Requirements 10.1, 10.2**
        """
        test_tree = create_simple_test_tree("test_module", ["test_one", "test_two"])
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertEqual(
            generated_code.count('enter_session_scope_context'),
            1,
            "Should have exactly one session scope context entry"
        )

    def test_module_scope_context_entries_match_module_count(self):
        """
        Test that module scope context entries match the number of modules.
        
        **Validates: Requirements 10.3**
        """
        modules_config = {
            "module_a": ["test_a1"],
            "module_b": ["test_b1"],
            "module_c": ["test_c1"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertEqual(
            generated_code.count('enter_module_scope_context'),
            3,
            "Should have 3 module scope context entries"
        )

    def test_test_scope_context_entries_match_test_count(self):
        """
        Test that test scope context entries match the number of tests.
        
        **Validates: Requirements 10.3**
        """
        modules_config = {
            "module_a": ["test_a1", "test_a2"],
            "module_b": ["test_b1"]
        }
        test_tree = create_multi_module_test_tree(modules_config)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertEqual(
            generated_code.count('enter_test_scope_context'),
            3,
            "Should have 3 test scope context entries (2 + 1)"
        )

    def test_test_imports_present_for_all_tests(self):
        """
        Test that import statements are generated for all test functions.
        
        **Validates: Requirements 10.1, 10.3**
        """
        test_names = ["test_alpha", "test_beta", "test_gamma"]
        test_tree = create_simple_test_tree("test_module", test_names)
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_doc.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        for test_name in test_names:
            self.assertIn(
                f"import {test_name}",
                generated_code,
                f"Test function '{test_name}' should be imported in the sequence document"
            )


if __name__ == "__main__":
    unittest.main()
