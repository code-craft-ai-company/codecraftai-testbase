"""
.. module:: test_diagnostic_compression
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for the DiagnosticCompression class and CompressionFormat enum.

.. moduleauthor:: CodeCraftX
"""

import gzip
import json
import os
import shutil
import tarfile
import tempfile
import unittest
import zipfile

from ccai.testbase.diagnostics import CompressionFormat, DiagnosticCompression


class CompressionFormatTests(unittest.TestCase):
    """
    Unit tests for the CompressionFormat enumeration.
    """

    def test_gzip_format_value(self):
        """Verify GZIP format has correct value."""
        self.assertEqual(CompressionFormat.GZIP.value, "gzip")

    def test_zip_format_value(self):
        """Verify ZIP format has correct value."""
        self.assertEqual(CompressionFormat.ZIP.value, "zip")

    def test_tar_gz_format_value(self):
        """Verify TAR_GZ format has correct value."""
        self.assertEqual(CompressionFormat.TAR_GZ.value, "tar.gz")

    def test_tar_bz2_format_value(self):
        """Verify TAR_BZ2 format has correct value."""
        self.assertEqual(CompressionFormat.TAR_BZ2.value, "tar.bz2")

    def test_none_format_value(self):
        """Verify NONE format has correct value."""
        self.assertEqual(CompressionFormat.NONE.value, "none")

    def test_all_formats_are_unique(self):
        """Verify all compression format values are unique."""
        values = [f.value for f in CompressionFormat]
        self.assertEqual(len(values), len(set(values)))


class DiagnosticCompressionConfigTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression configuration methods.
    """

    def setUp(self):
        """Reset compression format to default before each test."""
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Reset compression format to default after each test."""
        DiagnosticCompression.reset_to_default()

    def test_default_format_is_gzip(self):
        """Verify default compression format is GZIP."""
        self.assertEqual(DiagnosticCompression.DEFAULT_FORMAT, CompressionFormat.GZIP)

    def test_get_format_returns_configured_format(self):
        """Verify get_format returns the currently configured format."""
        self.assertEqual(DiagnosticCompression.get_format(), CompressionFormat.GZIP)

    def test_set_format_changes_configured_format(self):
        """Verify set_format changes the configured format."""
        DiagnosticCompression.set_format(CompressionFormat.ZIP)
        self.assertEqual(DiagnosticCompression.get_format(), CompressionFormat.ZIP)

    def test_reset_to_default_restores_gzip(self):
        """Verify reset_to_default restores GZIP format."""
        DiagnosticCompression.set_format(CompressionFormat.TAR_BZ2)
        DiagnosticCompression.reset_to_default()
        self.assertEqual(DiagnosticCompression.get_format(), CompressionFormat.GZIP)

    def test_is_compression_enabled_true_for_gzip(self):
        """Verify is_compression_enabled returns True for GZIP."""
        DiagnosticCompression.set_format(CompressionFormat.GZIP)
        self.assertTrue(DiagnosticCompression.is_compression_enabled())

    def test_is_compression_enabled_false_for_none(self):
        """Verify is_compression_enabled returns False for NONE."""
        DiagnosticCompression.set_format(CompressionFormat.NONE)
        self.assertFalse(DiagnosticCompression.is_compression_enabled())


class DiagnosticCompressionExtensionTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression extension methods.
    """

    def test_get_extension_gzip(self):
        """Verify get_extension returns correct extension for GZIP."""
        ext = DiagnosticCompression.get_extension(CompressionFormat.GZIP)
        self.assertEqual(ext, ".gz")

    def test_get_extension_zip(self):
        """Verify get_extension returns correct extension for ZIP."""
        ext = DiagnosticCompression.get_extension(CompressionFormat.ZIP)
        self.assertEqual(ext, ".zip")

    def test_get_extension_tar_gz(self):
        """Verify get_extension returns correct extension for TAR_GZ."""
        ext = DiagnosticCompression.get_extension(CompressionFormat.TAR_GZ)
        self.assertEqual(ext, ".tar.gz")

    def test_get_extension_tar_bz2(self):
        """Verify get_extension returns correct extension for TAR_BZ2."""
        ext = DiagnosticCompression.get_extension(CompressionFormat.TAR_BZ2)
        self.assertEqual(ext, ".tar.bz2")

    def test_get_extension_none(self):
        """Verify get_extension returns empty string for NONE."""
        ext = DiagnosticCompression.get_extension(CompressionFormat.NONE)
        self.assertEqual(ext, "")

    def test_get_extension_uses_configured_format_when_none_specified(self):
        """Verify get_extension uses configured format when no format specified."""
        DiagnosticCompression.set_format(CompressionFormat.ZIP)
        ext = DiagnosticCompression.get_extension()
        self.assertEqual(ext, ".zip")
        DiagnosticCompression.reset_to_default()


class DiagnosticCompressionFileTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression file compression methods.
    """

    def setUp(self):
        """Create temporary directory and test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_diagnostic.json")
        self.test_data = {"diagnostic": "test data", "level": 5, "items": [1, 2, 3]}
        
        with open(self.test_file, 'w') as f:
            json.dump(self.test_data, f)
        
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        DiagnosticCompression.reset_to_default()

    def test_compress_file_gzip_creates_gz_file(self):
        """Verify compress_file with GZIP creates .gz file."""
        compressed = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.GZIP,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".gz"))
        self.assertTrue(os.path.exists(compressed))

    def test_compress_file_gzip_content_is_valid(self):
        """Verify GZIP compressed file contains valid data."""
        compressed = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.GZIP,
            keep_original=True
        )
        
        with gzip.open(compressed, 'rt') as f:
            data = json.load(f)
        
        self.assertEqual(data, self.test_data)

    def test_compress_file_zip_creates_zip_file(self):
        """Verify compress_file with ZIP creates .zip file."""
        compressed = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.ZIP,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".zip"))
        self.assertTrue(os.path.exists(compressed))

    def test_compress_file_zip_content_is_valid(self):
        """Verify ZIP compressed file contains valid data."""
        compressed = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.ZIP,
            keep_original=True
        )
        
        with zipfile.ZipFile(compressed, 'r') as zf:
            names = zf.namelist()
            self.assertEqual(len(names), 1)
            with zf.open(names[0]) as f:
                data = json.load(f)
        
        self.assertEqual(data, self.test_data)

    def test_compress_file_tar_gz_creates_tar_gz_file(self):
        """Verify compress_file with TAR_GZ creates .tar.gz file."""
        compressed = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.TAR_GZ,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".tar.gz"))
        self.assertTrue(os.path.exists(compressed))

    def test_compress_file_removes_original_by_default(self):
        """Verify compress_file removes original file by default."""
        original_exists_before = os.path.exists(self.test_file)
        
        DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.GZIP,
            keep_original=False
        )
        
        self.assertTrue(original_exists_before)
        self.assertFalse(os.path.exists(self.test_file))

    def test_compress_file_keeps_original_when_specified(self):
        """Verify compress_file keeps original file when keep_original=True."""
        DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.GZIP,
            keep_original=True
        )
        
        self.assertTrue(os.path.exists(self.test_file))

    def test_compress_file_returns_none_for_none_format(self):
        """Verify compress_file returns None for NONE format."""
        result = DiagnosticCompression.compress_file(
            self.test_file,
            format=CompressionFormat.NONE
        )
        
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.test_file))

    def test_compress_file_raises_for_nonexistent_file(self):
        """Verify compress_file raises FileNotFoundError for nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            DiagnosticCompression.compress_file("/nonexistent/path/file.json")


class DiagnosticCompressionDirectoryTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression directory compression methods.
    """

    def setUp(self):
        """Create temporary directory with test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_dir = os.path.join(self.temp_dir, "diagnostics")
        os.makedirs(self.test_dir)
        
        # Create test files in directory
        self.test_files = []
        for i in range(3):
            file_path = os.path.join(self.test_dir, f"diagnostic_{i}.json")
            with open(file_path, 'w') as f:
                json.dump({"index": i, "data": f"test_{i}"}, f)
            self.test_files.append(file_path)
        
        # Create subdirectory with file
        self.sub_dir = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.sub_dir)
        sub_file = os.path.join(self.sub_dir, "nested.json")
        with open(sub_file, 'w') as f:
            json.dump({"nested": True}, f)
        
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        DiagnosticCompression.reset_to_default()

    def test_compress_directory_zip_creates_zip_archive(self):
        """Verify compress_directory with ZIP creates .zip archive."""
        compressed = DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.ZIP,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".zip"))
        self.assertTrue(os.path.exists(compressed))

    def test_compress_directory_tar_gz_creates_tar_gz_archive(self):
        """Verify compress_directory with TAR_GZ creates .tar.gz archive."""
        compressed = DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.TAR_GZ,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".tar.gz"))
        self.assertTrue(os.path.exists(compressed))

    def test_compress_directory_gzip_uses_tar_gz(self):
        """Verify compress_directory with GZIP uses TAR_GZ instead."""
        compressed = DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.GZIP,
            keep_original=True
        )
        
        self.assertIsNotNone(compressed)
        self.assertTrue(compressed.endswith(".tar.gz"))

    def test_compress_directory_removes_original_by_default(self):
        """Verify compress_directory removes original directory by default."""
        original_exists_before = os.path.exists(self.test_dir)
        
        DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.ZIP,
            keep_original=False
        )
        
        self.assertTrue(original_exists_before)
        self.assertFalse(os.path.exists(self.test_dir))

    def test_compress_directory_keeps_original_when_specified(self):
        """Verify compress_directory keeps original when keep_original=True."""
        DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.ZIP,
            keep_original=True
        )
        
        self.assertTrue(os.path.exists(self.test_dir))

    def test_compress_directory_returns_none_for_none_format(self):
        """Verify compress_directory returns None for NONE format."""
        result = DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.NONE
        )
        
        self.assertIsNone(result)
        self.assertTrue(os.path.exists(self.test_dir))

    def test_compress_directory_raises_for_nonexistent_directory(self):
        """Verify compress_directory raises FileNotFoundError for nonexistent directory."""
        with self.assertRaises(FileNotFoundError):
            DiagnosticCompression.compress_directory("/nonexistent/path/dir")

    def test_compress_directory_raises_for_file_path(self):
        """Verify compress_directory raises ValueError for file path."""
        file_path = self.test_files[0]
        with self.assertRaises(ValueError):
            DiagnosticCompression.compress_directory(file_path)

    def test_compress_directory_custom_output_path(self):
        """Verify compress_directory uses custom output path when specified."""
        custom_output = os.path.join(self.temp_dir, "custom_archive.zip")
        
        compressed = DiagnosticCompression.compress_directory(
            self.test_dir,
            format=CompressionFormat.ZIP,
            keep_original=True,
            output_path=custom_output
        )
        
        self.assertEqual(compressed, custom_output)
        self.assertTrue(os.path.exists(custom_output))


class DiagnosticCompressionDecompressTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression decompression methods.
    """

    def setUp(self):
        """Create temporary directory and compressed test files."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_data = {"diagnostic": "test data", "level": 5}
        
        # Create original file
        self.original_file = os.path.join(self.temp_dir, "original.json")
        with open(self.original_file, 'w') as f:
            json.dump(self.test_data, f)
        
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        DiagnosticCompression.reset_to_default()

    def test_decompress_gzip_file(self):
        """Verify decompress_file correctly decompresses GZIP file."""
        # Compress first
        compressed = DiagnosticCompression.compress_file(
            self.original_file,
            format=CompressionFormat.GZIP,
            keep_original=False
        )
        
        # Decompress
        decompressed = DiagnosticCompression.decompress_file(compressed)
        
        self.assertTrue(os.path.exists(decompressed))
        with open(decompressed, 'r') as f:
            data = json.load(f)
        self.assertEqual(data, self.test_data)

    def test_decompress_zip_file(self):
        """Verify decompress_file correctly decompresses ZIP file."""
        # Compress first
        compressed = DiagnosticCompression.compress_file(
            self.original_file,
            format=CompressionFormat.ZIP,
            keep_original=False
        )
        
        # Decompress
        decompressed = DiagnosticCompression.decompress_file(compressed)
        
        self.assertTrue(os.path.exists(decompressed))
        with open(decompressed, 'r') as f:
            data = json.load(f)
        self.assertEqual(data, self.test_data)

    def test_decompress_keeps_compressed_by_default(self):
        """Verify decompress_file keeps compressed file by default."""
        compressed = DiagnosticCompression.compress_file(
            self.original_file,
            format=CompressionFormat.GZIP,
            keep_original=False
        )
        
        DiagnosticCompression.decompress_file(compressed, keep_compressed=True)
        
        self.assertTrue(os.path.exists(compressed))

    def test_decompress_removes_compressed_when_specified(self):
        """Verify decompress_file removes compressed file when keep_compressed=False."""
        compressed = DiagnosticCompression.compress_file(
            self.original_file,
            format=CompressionFormat.GZIP,
            keep_original=False
        )
        
        DiagnosticCompression.decompress_file(compressed, keep_compressed=False)
        
        self.assertFalse(os.path.exists(compressed))

    def test_decompress_raises_for_nonexistent_file(self):
        """Verify decompress_file raises FileNotFoundError for nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            DiagnosticCompression.decompress_file("/nonexistent/file.gz")

    def test_decompress_raises_for_unknown_format(self):
        """Verify decompress_file raises ValueError for unknown format."""
        unknown_file = os.path.join(self.temp_dir, "file.unknown")
        with open(unknown_file, 'w') as f:
            f.write("test")
        
        with self.assertRaises(ValueError):
            DiagnosticCompression.decompress_file(unknown_file)


class DiagnosticCompressionUtilityTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression utility methods.
    """

    def setUp(self):
        """Create temporary directory and test files."""
        self.temp_dir = tempfile.mkdtemp()
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        DiagnosticCompression.reset_to_default()

    def test_get_compressed_size_returns_file_size(self):
        """Verify get_compressed_size returns correct file size."""
        test_file = os.path.join(self.temp_dir, "test.txt")
        test_content = "Test content for size check"
        with open(test_file, 'w') as f:
            f.write(test_content)
        
        size = DiagnosticCompression.get_compressed_size(test_file)
        
        self.assertEqual(size, os.path.getsize(test_file))

    def test_get_compressed_size_raises_for_nonexistent_file(self):
        """Verify get_compressed_size raises FileNotFoundError for nonexistent file."""
        with self.assertRaises(FileNotFoundError):
            DiagnosticCompression.get_compressed_size("/nonexistent/file.gz")

    def test_get_compression_ratio_calculates_correctly(self):
        """Verify get_compression_ratio calculates correct ratio."""
        ratio = DiagnosticCompression.get_compression_ratio(1000, 500)
        self.assertEqual(ratio, 0.5)

    def test_get_compression_ratio_handles_zero_original(self):
        """Verify get_compression_ratio returns 1.0 for zero original size."""
        ratio = DiagnosticCompression.get_compression_ratio(0, 100)
        self.assertEqual(ratio, 1.0)


class DiagnosticCompressionDiagnosticFolderTests(unittest.TestCase):
    """
    Unit tests for DiagnosticCompression.compress_diagnostic_folder method.
    """

    def setUp(self):
        """Create temporary diagnostic folder structure."""
        self.temp_dir = tempfile.mkdtemp()
        self.diagnostic_root = os.path.join(self.temp_dir, "diagnostics")
        os.makedirs(self.diagnostic_root)
        
        # Create prerun-diagnostic folder with files
        self.prerun_dir = os.path.join(self.diagnostic_root, "prerun-diagnostic")
        os.makedirs(self.prerun_dir)
        
        for i in range(2):
            file_path = os.path.join(self.prerun_dir, f"diag_{i}.json")
            with open(file_path, 'w') as f:
                json.dump({"index": i}, f)
        
        DiagnosticCompression.reset_to_default()

    def tearDown(self):
        """Clean up temporary directory."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        DiagnosticCompression.reset_to_default()

    def test_compress_diagnostic_folder_creates_archive(self):
        """Verify compress_diagnostic_folder creates archive for existing folder."""
        archive = DiagnosticCompression.compress_diagnostic_folder(
            self.diagnostic_root,
            "prerun-diagnostic",
            format=CompressionFormat.TAR_GZ,
            keep_original=True
        )
        
        self.assertIsNotNone(archive)
        self.assertTrue(os.path.exists(archive))

    def test_compress_diagnostic_folder_returns_none_for_nonexistent_folder(self):
        """Verify compress_diagnostic_folder returns None for nonexistent folder."""
        result = DiagnosticCompression.compress_diagnostic_folder(
            self.diagnostic_root,
            "nonexistent-diagnostic",
            format=CompressionFormat.TAR_GZ
        )
        
        self.assertIsNone(result)

    def test_compress_diagnostic_folder_returns_none_for_none_format(self):
        """Verify compress_diagnostic_folder returns None for NONE format."""
        result = DiagnosticCompression.compress_diagnostic_folder(
            self.diagnostic_root,
            "prerun-diagnostic",
            format=CompressionFormat.NONE
        )
        
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
