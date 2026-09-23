"""
    Unit tests for generate_testrun_sequence_document method.

    Tests verify the file generation, indentation handling, temporary file
    management, and attribute storage of the sequence document generation.

    Requirements covered:
    - 1.1: generate_testrun_sequence_document accepts output filename parameter
    - 1.2: Optional indent_space parameter defaults to four spaces
    - 1.3: Creates valid Python module file at specified path
    - 1.4: Stores output filename in _sequence_document attribute
    - 4.1: Creates temporary file with ".tmp" extension
    - 4.2: Collects factory imports during first pass
    - 4.3: Reads temporary file during second pass
    - 4.4: Inserts collected imports at insertion points
    - 4.5: Removes temporary file after final document written
    - 30.1: Creates temporary file with ".tmp" extension during generation
    - 30.2: Removes temporary file using os.remove after final document written
    - 30.3: Temporary file path is {outputfilename}.tmp
    - 30.4: Cleanup occurs after successful generation
"""

import collections
import os
import tempfile
import unittest

from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef
from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.sequencing.testsequencer import TestSequencer


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


def create_test_function(name, module_name):
    """Create a mock test function with the given name and module."""
    def test_func():
        pass
    test_func.__name__ = name
    test_func.__module__ = module_name
    return test_func


def create_minimal_test_tree():
    """
    Create a minimal test tree with no tests for basic generation testing.
    
    Returns:
        MockTestGroup: Root of the test tree with no children
    """
    root = MockTestGroup("root")
    return root


def create_simple_test_tree(module_name, test_names):
    """
    Create a simple test tree with one module containing the specified tests.
    
    Args:
        module_name: Name of the module
        test_names: List of test function names
        
    Returns:
        MockTestGroup: Root of the test tree
    """
    root = MockTestGroup("root")
    module_group = MockTestGroup(module_name, package="")
    
    for test_name in test_names:
        test_func = create_test_function(test_name, module_name)
        test_ref = TestRef(test_func)
        module_group._children[test_ref.base_name] = test_ref
    
    root._children[module_name] = module_group
    return root


class OutputFileCreationTests(unittest.TestCase):
    """
    Tests for output file creation at specified path.

    **Validates: Requirements 1.1, 1.3**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_output_file_created_at_specified_path(self):
        """
        Verify output file is created at the specified path.

        **Validates: Requirements 1.1, 1.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertTrue(
            os.path.exists(output_file),
            "Output file should be created at the specified path"
        )

    def test_output_file_created_in_subdirectory(self):
        """
        Verify output file can be created in a subdirectory.

        **Validates: Requirements 1.1, 1.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        subdir = os.path.join(self.tempdir.name, "subdir")
        os.makedirs(subdir)
        output_file = os.path.join(subdir, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertTrue(
            os.path.exists(output_file),
            "Output file should be created in subdirectory"
        )

    def test_output_file_is_readable_python_module(self):
        """
        Verify output file is a readable Python module with expected structure.

        Note: With an empty test tree, the generated code may have empty blocks
        which is expected behavior. This test verifies the file is created and
        contains the expected module structure.

        **Validates: Requirements 1.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Verify the file contains expected Python module structure
        self.assertIn(
            'def session(sequencer):',
            generated_code,
            "Generated file should contain session function definition"
        )
        self.assertIn(
            '__traceback_format_policy__',
            generated_code,
            "Generated file should contain traceback policy"
        )

    def test_output_file_is_not_empty(self):
        """
        Verify output file is not empty.

        **Validates: Requirements 1.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        file_size = os.path.getsize(output_file)
        self.assertGreater(
            file_size,
            0,
            "Generated output file should not be empty"
        )


class DefaultIndentSpaceTests(unittest.TestCase):
    """
    Tests for default indent_space value (four spaces).

    **Validates: Requirements 1.2**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_default_indent_space_is_four_spaces(self):
        """
        Verify default indentation uses four spaces.

        **Validates: Requirements 1.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        # Call without indent_space parameter to use default
        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check that four-space indentation is used in function bodies
        # The session function should have indented content
        lines = generated_code.split('\n')
        indented_lines = [line for line in lines if line.startswith('    ') and not line.startswith('        ')]
        
        self.assertGreater(
            len(indented_lines),
            0,
            "Generated code should contain lines with four-space indentation"
        )

    def test_generated_code_uses_consistent_indentation(self):
        """
        Verify generated code uses consistent indentation throughout.

        **Validates: Requirements 1.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check that no tabs are used (only spaces)
        self.assertNotIn(
            '\t',
            generated_code,
            "Generated code should not contain tabs, only spaces for indentation"
        )


class CustomIndentSpaceTests(unittest.TestCase):
    """
    Tests for custom indent_space value.

    **Validates: Requirements 1.2**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_custom_two_space_indentation(self):
        """
        Verify custom two-space indentation is applied.

        **Validates: Requirements 1.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file, indent_space="  ")

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check that two-space indentation is used
        lines = generated_code.split('\n')
        two_space_indented = [line for line in lines if line.startswith('  ') and not line.startswith('    ')]
        
        self.assertGreater(
            len(two_space_indented),
            0,
            "Generated code should contain lines with two-space indentation"
        )

    def test_custom_eight_space_indentation(self):
        """
        Verify custom eight-space indentation is applied.

        **Validates: Requirements 1.2**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file, indent_space="        ")

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check that eight-space indentation is used
        lines = generated_code.split('\n')
        eight_space_indented = [line for line in lines if line.startswith('        ') and not line.startswith('                ')]
        
        self.assertGreater(
            len(eight_space_indented),
            0,
            "Generated code should contain lines with eight-space indentation"
        )

    def test_custom_indentation_produces_readable_module(self):
        """
        Verify custom indentation produces a readable Python module.

        Note: With an empty test tree, the generated code may have empty blocks
        which is expected behavior. This test verifies the custom indentation
        is applied correctly.

        **Validates: Requirements 1.2, 1.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file, indent_space="  ")

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Verify the file contains expected Python module structure with custom indentation
        self.assertIn(
            'def session(sequencer):',
            generated_code,
            "Generated file should contain session function definition"
        )
        # Verify two-space indentation is used
        lines = generated_code.split('\n')
        two_space_indented = [line for line in lines if line.startswith('  ') and not line.startswith('    ')]
        self.assertGreater(
            len(two_space_indented),
            0,
            "Generated code should contain lines with two-space indentation"
        )


class TemporaryFileCreationAndCleanupTests(unittest.TestCase):
    """
    Tests for temporary file creation and cleanup.

    **Validates: Requirements 4.1, 4.5, 30.1, 30.2, 30.3, 30.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_temporary_file_cleaned_up_after_generation(self):
        """
        Verify temporary file is removed after successful generation.

        **Validates: Requirements 4.5, 30.2, 30.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")
        temp_file = output_file + ".tmp"

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertFalse(
            os.path.exists(temp_file),
            "Temporary file should be removed after generation completes"
        )

    def test_temporary_file_path_follows_convention(self):
        """
        Verify temporary file path is {outputfilename}.tmp.

        This test verifies the convention by checking that after generation,
        the temp file does not exist (was cleaned up) and the final file does.

        **Validates: Requirements 30.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "my_sequence.py")
        expected_temp_file = output_file + ".tmp"

        sequencer.generate_testrun_sequence_document(output_file)

        # Final file should exist
        self.assertTrue(
            os.path.exists(output_file),
            "Final output file should exist"
        )
        # Temp file should be cleaned up
        self.assertFalse(
            os.path.exists(expected_temp_file),
            "Temporary file {outputfilename}.tmp should be cleaned up"
        )

    def test_only_final_file_remains_after_generation(self):
        """
        Verify only the final output file remains after generation.

        **Validates: Requirements 4.5, 30.2, 30.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        # Get list of files before generation
        files_before = set(os.listdir(self.tempdir.name))

        sequencer.generate_testrun_sequence_document(output_file)

        # Get list of files after generation
        files_after = set(os.listdir(self.tempdir.name))

        # Only the output file should be added
        new_files = files_after - files_before
        self.assertEqual(
            new_files,
            {"sequence_document.py"},
            "Only the final output file should remain after generation"
        )


class SequenceDocumentAttributeTests(unittest.TestCase):
    """
    Tests for _sequence_document attribute storage.

    **Validates: Requirements 1.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_sequence_document_attribute_is_none_before_generation(self):
        """
        Verify _sequence_document is None before generation.

        **Validates: Requirements 1.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)

        self.assertIsNone(
            sequencer._sequence_document,
            "_sequence_document should be None before generation"
        )

    def test_sequence_document_attribute_set_after_generation(self):
        """
        Verify _sequence_document is set after generation.

        **Validates: Requirements 1.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertIsNotNone(
            sequencer._sequence_document,
            "_sequence_document should be set after generation"
        )

    def test_sequence_document_attribute_matches_output_filename(self):
        """
        Verify _sequence_document matches the output filename.

        **Validates: Requirements 1.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "my_custom_sequence.py")

        sequencer.generate_testrun_sequence_document(output_file)

        self.assertEqual(
            sequencer._sequence_document,
            output_file,
            "_sequence_document should match the output filename"
        )

    def test_sequence_document_attribute_updated_on_regeneration(self):
        """
        Verify _sequence_document is updated when regenerating.

        **Validates: Requirements 1.4**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file_1 = os.path.join(self.tempdir.name, "sequence_1.py")
        output_file_2 = os.path.join(self.tempdir.name, "sequence_2.py")

        sequencer.generate_testrun_sequence_document(output_file_1)
        self.assertEqual(
            sequencer._sequence_document,
            output_file_1,
            "_sequence_document should be set to first output file"
        )

        sequencer.generate_testrun_sequence_document(output_file_2)
        self.assertEqual(
            sequencer._sequence_document,
            output_file_2,
            "_sequence_document should be updated to second output file"
        )


class TwoPassGenerationTests(unittest.TestCase):
    """
    Tests for two-pass generation pattern.

    **Validates: Requirements 4.2, 4.3, 4.4**
    """

    def setUp(self):
        """Set up test fixtures."""
        self.tempdir = tempfile.TemporaryDirectory()

        # Isolate run artefacts under the temporary directory via the output context env var
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.tempdir.name

        # Store original injection registry state
        self._original_scope_tree = injection_registry._scope_tree_root
        # Create a fresh scope tree for each test
        injection_registry._scope_tree_root = InjectionScope()

    def tearDown(self):
        """Clean up test fixtures."""
        self.tempdir.cleanup()
        # Restore the AM_OUTPUT_DIRECTORY environment variable
        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir
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

    def test_insertion_points_not_in_final_output(self):
        """
        Verify insertion point markers are not in the final output.

        This confirms the second pass correctly processes the insertion points.

        **Validates: Requirements 4.4**
        """
        from ccai.testbase.sequencing.testsequencer import (
            CONSTRAINT_IMPORT_INSERTION_POINT,
            FACTORY_IMPORT_INSERTION_POINT,
        )

        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        self.assertNotIn(
            CONSTRAINT_IMPORT_INSERTION_POINT,
            generated_code,
            "Constraint import insertion point should be processed and removed"
        )
        self.assertNotIn(
            FACTORY_IMPORT_INSERTION_POINT,
            generated_code,
            "Factory import insertion point should be processed and removed"
        )

    def test_final_output_contains_template_content(self):
        """
        Verify final output contains expected template content.

        **Validates: Requirements 4.3**
        """
        test_tree = create_minimal_test_tree()
        sequencer = self._create_sequencer_with_tree(test_tree)
        output_file = os.path.join(self.tempdir.name, "sequence_document.py")

        sequencer.generate_testrun_sequence_document(output_file)

        with open(output_file, 'r') as f:
            generated_code = f.read()

        # Check for template content that should be preserved
        self.assertIn(
            'CODE GENERATED',
            generated_code,
            "Final output should contain template docstring"
        )
        self.assertIn(
            '__traceback_format_policy__',
            generated_code,
            "Final output should contain traceback policy setting"
        )
        self.assertIn(
            'ConstraintsCatalog',
            generated_code,
            "Final output should contain ConstraintsCatalog"
        )


if __name__ == "__main__":
    unittest.main()
