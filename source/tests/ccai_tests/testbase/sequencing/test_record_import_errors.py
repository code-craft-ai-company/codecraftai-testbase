"""
    Unit tests for TestSequencer.record_import_errors method.

    Tests verify the output file creation, JSON format of error records,
    record separator usage, and inclusion of module, filename, and traceback.

    Requirements covered:
    - 26.1: record_import_errors method accepts output filename
    - 26.2: Method writes import errors to specified file
    - 26.3: Each import error record includes module name, filename, and traceback
    - 26.4: Records are separated by JSOS CHAR_RECORD_SEPERATOR
    - 26.5: Import errors are formatted as JSON objects
"""

import json
import os
import tempfile
import unittest

from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR, load_jsos_stream_from_file

from ccai.testbase.sequencing.testsequencer import TestSequencer


class RecordImportErrorsOutputFileCreationTests(unittest.TestCase):
    """
    Tests for output file creation by record_import_errors method.

    **Validates: Requirements 26.1, 26.2**
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "import_errors.jsos")

        # Isolate run artefacts under the temp dir via the output context env var.
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.temp_dir

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer instance for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.temp_dir,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_record_import_errors_creates_output_file(self):
        """
        Verify record_import_errors creates output file at specified path.

        **Validates: Requirements 26.1, 26.2**
        """
        sequencer = self._create_sequencer()
        # Manually set import errors for testing
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", "ImportError: No module named 'missing'")
        }

        sequencer.record_import_errors(self.output_file)

        self.assertTrue(
            os.path.exists(self.output_file),
            "record_import_errors should create output file at specified path"
        )

    def test_record_import_errors_creates_empty_file_when_no_errors(self):
        """
        Verify record_import_errors creates empty file when no import errors exist.

        **Validates: Requirements 26.1, 26.2**
        """
        sequencer = self._create_sequencer()
        # No import errors set

        sequencer.record_import_errors(self.output_file)

        self.assertTrue(
            os.path.exists(self.output_file),
            "record_import_errors should create output file even when no errors"
        )
        with open(self.output_file, 'r') as f:
            content = f.read()
        self.assertEqual(
            content,
            "",
            "Output file should be empty when no import errors exist"
        )


class RecordImportErrorsJsonFormatTests(unittest.TestCase):
    """
    Tests for JSON format of error records in record_import_errors output.

    **Validates: Requirements 26.3, 26.5**
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "import_errors.jsos")

        # Isolate run artefacts under the temp dir via the output context env var.
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.temp_dir

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer instance for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.temp_dir,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_record_import_errors_writes_valid_json(self):
        """
        Verify record_import_errors writes valid JSON objects.

        **Validates: Requirements 26.5**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", "ImportError: No module named 'missing'")
        }

        sequencer.record_import_errors(self.output_file)

        with open(self.output_file, 'r') as f:
            content = f.read()

        # Strip the record separator and parse JSON
        json_content = content.lstrip(CHAR_RECORD_SEPERATOR)
        try:
            parsed = json.loads(json_content)
            self.assertIsInstance(parsed, dict, "Parsed content should be a dictionary")
        except json.JSONDecodeError as e:
            self.fail(f"record_import_errors should write valid JSON: {e}")

    def test_record_import_errors_includes_module_field(self):
        """
        Verify each error record includes module name field.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", "ImportError: No module named 'missing'")
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(len(records), 1, "Should have one error record")
        self.assertIn("module", records[0], "Error record should include 'module' field")
        self.assertEqual(
            records[0]["module"],
            "package.module",
            "Module field should contain the module name"
        )

    def test_record_import_errors_includes_filename_field(self):
        """
        Verify each error record includes filename field.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", "ImportError: No module named 'missing'")
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(len(records), 1, "Should have one error record")
        self.assertIn("filename", records[0], "Error record should include 'filename' field")
        self.assertEqual(
            records[0]["filename"],
            "/path/to/module.py",
            "Filename field should contain the file path"
        )

    def test_record_import_errors_includes_trace_field(self):
        """
        Verify each error record includes traceback field.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        error_traceback = "Traceback (most recent call last):\n  File \"test.py\", line 1\nImportError: No module"
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", error_traceback)
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(len(records), 1, "Should have one error record")
        self.assertIn("trace", records[0], "Error record should include 'trace' field")
        self.assertIsInstance(
            records[0]["trace"],
            list,
            "Trace field should be a list of strings"
        )

    def test_record_import_errors_trace_contains_splitlines(self):
        """
        Verify trace field contains traceback split into lines.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        error_traceback = "Line 1\nLine 2\nLine 3"
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", error_traceback)
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(
            records[0]["trace"],
            ["Line 1", "Line 2", "Line 3"],
            "Trace field should contain traceback split into lines"
        )


class RecordImportErrorsRecordSeparatorTests(unittest.TestCase):
    """
    Tests for record separator usage in record_import_errors output.

    **Validates: Requirements 26.4**
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "import_errors.jsos")

        # Isolate run artefacts under the temp dir via the output context env var.
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.temp_dir

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer instance for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.temp_dir,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_record_import_errors_starts_with_record_separator(self):
        """
        Verify output starts with JSOS record separator.

        **Validates: Requirements 26.4**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", "ImportError: test")
        }

        sequencer.record_import_errors(self.output_file)

        with open(self.output_file, 'r') as f:
            content = f.read()

        self.assertTrue(
            content.startswith(CHAR_RECORD_SEPERATOR),
            "Output should start with JSOS record separator"
        )

    def test_record_import_errors_separates_multiple_records(self):
        """
        Verify multiple error records are separated by JSOS record separator.

        **Validates: Requirements 26.4**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module1.py": ("package.module1", "/path/to/module1.py", "ImportError: error1"),
            "/path/to/module2.py": ("package.module2", "/path/to/module2.py", "ImportError: error2"),
        }

        sequencer.record_import_errors(self.output_file)

        with open(self.output_file, 'r') as f:
            content = f.read()

        # Count record separators - should be one per record
        separator_count = content.count(CHAR_RECORD_SEPERATOR)
        self.assertEqual(
            separator_count,
            2,
            "Should have one record separator per error record"
        )

    def test_record_import_errors_can_be_loaded_with_jsos_loader(self):
        """
        Verify output can be loaded using load_jsos_stream_from_file.

        **Validates: Requirements 26.4**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module1.py": ("package.module1", "/path/to/module1.py", "ImportError: error1"),
            "/path/to/module2.py": ("package.module2", "/path/to/module2.py", "ImportError: error2"),
        }

        sequencer.record_import_errors(self.output_file)

        # Should be able to load without errors
        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(
            len(records),
            2,
            "Should load two error records from JSOS file"
        )


class RecordImportErrorsMultipleErrorsTests(unittest.TestCase):
    """
    Tests for handling multiple import errors in record_import_errors.

    **Validates: Requirements 26.2, 26.3, 26.4, 26.5**
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "import_errors.jsos")

        # Isolate run artefacts under the temp dir via the output context env var.
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.temp_dir

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer instance for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.temp_dir,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_record_import_errors_writes_all_errors(self):
        """
        Verify all import errors are written to output file.

        **Validates: Requirements 26.2**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module1.py": ("package.module1", "/path/to/module1.py", "ImportError: error1"),
            "/path/to/module2.py": ("package.module2", "/path/to/module2.py", "SyntaxError: error2"),
            "/path/to/module3.py": ("package.module3", "/path/to/module3.py", "ModuleNotFoundError: error3"),
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        self.assertEqual(
            len(records),
            3,
            "Should write all three import errors"
        )

    def test_record_import_errors_preserves_error_details(self):
        """
        Verify each error record preserves its specific details.

        **Validates: Requirements 26.3, 26.5**
        """
        sequencer = self._create_sequencer()
        sequencer._import_errors = {
            "/path/to/module1.py": ("package.module1", "/path/to/module1.py", "ImportError: error1"),
            "/path/to/module2.py": ("package.module2", "/path/to/module2.py", "SyntaxError: error2"),
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)

        # Create a lookup by module name for easier verification
        records_by_module = {r["module"]: r for r in records}

        self.assertIn("package.module1", records_by_module)
        self.assertEqual(records_by_module["package.module1"]["filename"], "/path/to/module1.py")
        self.assertEqual(records_by_module["package.module1"]["trace"], ["ImportError: error1"])

        self.assertIn("package.module2", records_by_module)
        self.assertEqual(records_by_module["package.module2"]["filename"], "/path/to/module2.py")
        self.assertEqual(records_by_module["package.module2"]["trace"], ["SyntaxError: error2"])


class RecordImportErrorsTracebackFormattingTests(unittest.TestCase):
    """
    Tests for traceback formatting in record_import_errors output.

    **Validates: Requirements 26.3**
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "import_errors.jsos")

        # Isolate run artefacts under the temp dir via the output context env var.
        self._prev_output_dir = os.environ.get("AM_OUTPUT_DIRECTORY", None)
        os.environ["AM_OUTPUT_DIRECTORY"] = self.temp_dir

    def tearDown(self):
        """
        Clean up test fixtures.
        """
        if os.path.exists(self.output_file):
            os.remove(self.output_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)

        if self._prev_output_dir is None:
            os.environ.pop("AM_OUTPUT_DIRECTORY", None)
        else:
            os.environ["AM_OUTPUT_DIRECTORY"] = self._prev_output_dir

    def _create_sequencer(self):
        """Create a TestSequencer instance for testing."""
        return TestSequencer(
            jobtitle="Test Job",
            root=self.temp_dir,
            includes=["*"],
            excludes=[],
            metafilters=[]
        )

    def test_record_import_errors_handles_multiline_traceback(self):
        """
        Verify multiline tracebacks are properly split into list.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        multiline_traceback = """Traceback (most recent call last):
  File "/path/to/file.py", line 10, in <module>
    import missing_module
ModuleNotFoundError: No module named 'missing_module'"""

        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", multiline_traceback)
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        trace_lines = records[0]["trace"]

        self.assertEqual(len(trace_lines), 4, "Should have 4 lines in traceback")
        self.assertEqual(trace_lines[0], "Traceback (most recent call last):")
        self.assertIn("File", trace_lines[1])
        self.assertIn("import missing_module", trace_lines[2])
        self.assertIn("ModuleNotFoundError", trace_lines[3])

    def test_record_import_errors_handles_single_line_error(self):
        """
        Verify single line errors are properly formatted.

        **Validates: Requirements 26.3**
        """
        sequencer = self._create_sequencer()
        single_line_error = "ImportError: No module named 'missing'"

        sequencer._import_errors = {
            "/path/to/module.py": ("package.module", "/path/to/module.py", single_line_error)
        }

        sequencer.record_import_errors(self.output_file)

        records = load_jsos_stream_from_file(self.output_file)
        trace_lines = records[0]["trace"]

        self.assertEqual(len(trace_lines), 1, "Should have 1 line in traceback")
        self.assertEqual(trace_lines[0], "ImportError: No module named 'missing'")


if __name__ == "__main__":
    unittest.main()
