"""
    .. module:: ccai.testbase.diagnostics
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing diagnostic constants and configuration paths for the TestBase
        framework's diagnostic capture system.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module provides constants and configuration paths used by the TestBase diagnostic capture
system. The diagnostic system enables integration couplings to collect and store diagnostic
information about the test environment, devices, and system state at predefined stages of
the test run lifecycle.

The module includes:

* :class:`DiagnosticLabel` - Constants identifying diagnostic capture stages
* :class:`RuntimeConfigPaths` - Configuration paths for diagnostic runtime settings
* :class:`DiagnosticLabelRegistry` - Registry for custom diagnostic labels
* :class:`DiagnosticFilter` - Filter for controlling diagnostic capture
* :class:`DiagnosticCompression` - Utility for compressing diagnostic files

For streaming diagnostics to external systems, see the :mod:`ccai.testbase.diagnostic_streaming`
module which provides:

* :class:`DiagnosticStreamManager` - Manager for coordinating diagnostic streaming
* :class:`DiagnosticStreamConfig` - Configuration for streaming settings
* :class:`DiagnosticStreamProtocol` - Supported streaming protocols (HTTP, WebSocket, File)

Diagnostic Capture Points:

* **Pre-run diagnostics**: Captured before test execution begins, useful for recording
  initial system state, device configurations, and environment conditions.
* **Post-run diagnostics**: Captured after test execution completes, useful for recording
  final system state, logs, and any changes that occurred during testing.
* **Custom diagnostics**: User-defined diagnostic capture points for specialized needs.

Example Usage::

    from ccai.testbase.diagnostics import DiagnosticLabel, RuntimeConfigPaths
    from ccai.testbase.diagnostics import DiagnosticLabelRegistry

    # Check which diagnostic stage is being processed
    if label == DiagnosticLabel.PRERUN_DIAGNOSTIC:
        print("Capturing pre-run diagnostics")
    elif label == DiagnosticLabel.POSTRUN_DIAGNOSTIC:
        print("Capturing post-run diagnostics")

    # Access configuration paths for runtime settings
    prerun_config_path = RuntimeConfigPaths.DIAGNOSTIC_PRERUN
    postrun_config_path = RuntimeConfigPaths.DIAGNOSTIC_POSTRUN

    # Register a custom diagnostic label
    DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Checkpoint during test execution")
    
    # Get all registered labels
    all_labels = DiagnosticLabelRegistry.get_all_labels()

    # Stream diagnostics to external system
    from ccai.testbase.diagnostic_streaming import (
        DiagnosticStreamManager, DiagnosticStreamConfig, DiagnosticStreamProtocol
    )
    
    config = DiagnosticStreamConfig(
        enabled=True,
        protocol=DiagnosticStreamProtocol.HTTP,
        endpoint="https://diagnostics.example.com/api/stream"
    )
    DiagnosticStreamManager.configure(config)

See Also:
    - :class:`ccai.testbase.coupling.integrationcoupling.IntegrationCoupling`: Base class
      for integration couplings that implement diagnostic capture
    - :class:`ccai.testbase.cli.options.DiagnosticOptionGroup`: CLI options for enabling
      diagnostic capture
    - :class:`ccai.testbase.sequencing.testsequencer.TestSequencer`: Orchestrates diagnostic
      capture during test execution
    - :mod:`ccai.testbase.diagnostic_streaming`: Streaming diagnostics to external systems
"""


from typing import Dict, List, Optional

import gzip
import os
import shutil
import tarfile
import zipfile

from enum import Enum


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


class CompressionFormat(Enum):
    """
    Enumeration of supported compression formats for diagnostic files.

    The :class:`CompressionFormat` enum defines the available compression formats
    that can be used when compressing diagnostic output files. Each format has
    different characteristics in terms of compression ratio, speed, and compatibility.

    Attributes:
        GZIP: GNU zip compression (.gz extension). Good balance of speed and compression.
        ZIP: ZIP archive format (.zip extension). Widely compatible across platforms.
        TAR_GZ: Tar archive with gzip compression (.tar.gz extension). Preserves directory structure.
        TAR_BZ2: Tar archive with bzip2 compression (.tar.bz2 extension). Better compression ratio.
        NONE: No compression. Files are left uncompressed.

    Example Usage::

        from ccai.testbase.diagnostics import CompressionFormat

        # Select a compression format
        format = CompressionFormat.GZIP

        # Check format extension
        if format == CompressionFormat.ZIP:
            print("Using ZIP compression")

    See Also:
        - :class:`DiagnosticCompression`: Utility class for compressing diagnostic files
    """
    GZIP = "gzip"
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    TAR_BZ2 = "tar.bz2"
    NONE = "none"


class DiagnosticCompression:
    """
    Utility class for compressing diagnostic output files.

    The :class:`DiagnosticCompression` class provides methods for compressing
    diagnostic files and directories to reduce storage requirements. It supports
    multiple compression formats and can be configured to automatically compress
    diagnostic output after capture.

    The class supports the following compression formats:

    * **GZIP**: Compresses individual files with .gz extension
    * **ZIP**: Creates ZIP archives containing files or directories
    * **TAR_GZ**: Creates tar archives with gzip compression
    * **TAR_BZ2**: Creates tar archives with bzip2 compression (better ratio)
    * **NONE**: No compression (pass-through)

    Class Attributes:
        DEFAULT_FORMAT (CompressionFormat): The default compression format (GZIP).
        _configured_format (CompressionFormat): The currently configured compression format.

    Example Usage::

        from ccai.testbase.diagnostics import DiagnosticCompression, CompressionFormat

        # Compress a single file
        compressed_path = DiagnosticCompression.compress_file(
            "/path/to/diagnostic.json",
            format=CompressionFormat.GZIP
        )

        # Compress a directory
        archive_path = DiagnosticCompression.compress_directory(
            "/path/to/diagnostics/prerun-diagnostic",
            format=CompressionFormat.TAR_GZ
        )

        # Configure default compression format
        DiagnosticCompression.set_format(CompressionFormat.ZIP)

        # Get file extension for a format
        ext = DiagnosticCompression.get_extension(CompressionFormat.GZIP)  # Returns ".gz"

    Note:
        Compression is performed in-place by default, meaning the original files
        are replaced with compressed versions. Use the ``keep_original`` parameter
        to preserve original files.

    See Also:
        - :class:`CompressionFormat`: Enumeration of supported compression formats
        - :class:`DiagnosticLabel`: Diagnostic stage labels
    """

    DEFAULT_FORMAT: CompressionFormat = CompressionFormat.GZIP
    _configured_format: CompressionFormat = CompressionFormat.GZIP

    # Extension mappings for each compression format
    _EXTENSIONS: Dict[CompressionFormat, str] = {
        CompressionFormat.GZIP: ".gz",
        CompressionFormat.ZIP: ".zip",
        CompressionFormat.TAR_GZ: ".tar.gz",
        CompressionFormat.TAR_BZ2: ".tar.bz2",
        CompressionFormat.NONE: "",
    }

    @classmethod
    def set_format(cls, format: CompressionFormat) -> None:
        """
        Set the default compression format for diagnostic files.

        This method configures the default compression format that will be used
        when compressing diagnostic files without explicitly specifying a format.

        :param format: The compression format to use as default.

        :returns: None

        Example Usage::

            from ccai.testbase.diagnostics import DiagnosticCompression, CompressionFormat

            # Set default format to ZIP
            DiagnosticCompression.set_format(CompressionFormat.ZIP)

            # Now compress_file will use ZIP by default
            DiagnosticCompression.compress_file("/path/to/file.json")
        """
        cls._configured_format = format

    @classmethod
    def get_format(cls) -> CompressionFormat:
        """
        Get the currently configured compression format.

        :returns: The currently configured compression format.

        Example Usage::

            current_format = DiagnosticCompression.get_format()
            print(f"Current format: {current_format.value}")
        """
        return cls._configured_format

    @classmethod
    def get_extension(cls, format: Optional[CompressionFormat] = None) -> str:
        """
        Get the file extension for a compression format.

        :param format: The compression format to get the extension for.
            If None, uses the currently configured format.

        :returns: The file extension string (e.g., ".gz", ".zip", ".tar.gz").

        Example Usage::

            ext = DiagnosticCompression.get_extension(CompressionFormat.GZIP)
            # Returns: ".gz"

            ext = DiagnosticCompression.get_extension(CompressionFormat.TAR_GZ)
            # Returns: ".tar.gz"
        """
        if format is None:
            format = cls._configured_format
        return cls._EXTENSIONS.get(format, "")

    @classmethod
    def compress_file(
        cls,
        file_path: str,
        format: Optional[CompressionFormat] = None,
        keep_original: bool = False,
        compression_level: int = 9
    ) -> Optional[str]:
        """
        Compress a single file using the specified compression format.

        This method compresses an individual file and optionally removes the
        original uncompressed file. The compressed file is created in the same
        directory as the original.

        :param file_path: The path to the file to compress.
        :param format: The compression format to use. If None, uses the
            currently configured format.
        :param keep_original: If True, keeps the original file after compression.
            If False (default), removes the original file.
        :param compression_level: Compression level (1-9). Higher values provide
            better compression but are slower. Default is 9 (maximum compression).

        :returns: The path to the compressed file, or None if compression failed
            or format is NONE.

        :raises FileNotFoundError: If the specified file does not exist.
        :raises PermissionError: If there are insufficient permissions to read
            the file or write the compressed output.

        Example Usage::

            # Compress with default format
            compressed = DiagnosticCompression.compress_file("/path/to/diagnostic.json")

            # Compress with specific format, keeping original
            compressed = DiagnosticCompression.compress_file(
                "/path/to/diagnostic.json",
                format=CompressionFormat.GZIP,
                keep_original=True
            )

        Note:
            For ZIP format, this method creates a ZIP archive containing the
            single file. For GZIP format, it creates a .gz compressed file.
        """
        if format is None:
            format = cls._configured_format

        if format == CompressionFormat.NONE:
            return None

        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = cls._EXTENSIONS[format]
        compressed_path = file_path + extension

        try:
            if format == CompressionFormat.GZIP:
                with open(file_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb', compresslevel=compression_level) as f_out:
                        shutil.copyfileobj(f_in, f_out)

            elif format == CompressionFormat.ZIP:
                compression = zipfile.ZIP_DEFLATED
                with zipfile.ZipFile(compressed_path, 'w', compression=compression, compresslevel=compression_level) as zf:
                    arcname = os.path.basename(file_path)
                    zf.write(file_path, arcname)

            elif format in (CompressionFormat.TAR_GZ, CompressionFormat.TAR_BZ2):
                mode = 'w:gz' if format == CompressionFormat.TAR_GZ else 'w:bz2'
                with tarfile.open(compressed_path, mode) as tf:
                    arcname = os.path.basename(file_path)
                    tf.add(file_path, arcname)

            if not keep_original:
                os.remove(file_path)

            return compressed_path

        except Exception:
            # Clean up partial compressed file if it exists
            if os.path.exists(compressed_path):
                os.remove(compressed_path)
            raise

    @classmethod
    def compress_directory(
        cls,
        dir_path: str,
        format: Optional[CompressionFormat] = None,
        keep_original: bool = False,
        compression_level: int = 9,
        output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Compress a directory into an archive using the specified compression format.

        This method creates an archive containing all files and subdirectories
        within the specified directory. The archive is created in the parent
        directory of the source directory by default.

        :param dir_path: The path to the directory to compress.
        :param format: The compression format to use. If None, uses the
            currently configured format. Note: GZIP format is not supported
            for directories; TAR_GZ will be used instead.
        :param keep_original: If True, keeps the original directory after
            compression. If False (default), removes the original directory.
        :param compression_level: Compression level (1-9). Higher values provide
            better compression but are slower. Default is 9 (maximum compression).
        :param output_path: Optional custom path for the output archive. If None,
            the archive is created in the parent directory with the directory name.

        :returns: The path to the compressed archive, or None if compression failed
            or format is NONE.

        :raises FileNotFoundError: If the specified directory does not exist.
        :raises PermissionError: If there are insufficient permissions to read
            the directory or write the compressed output.
        :raises ValueError: If the path is not a directory.

        Example Usage::

            # Compress diagnostic directory with default format
            archive = DiagnosticCompression.compress_directory(
                "/path/to/diagnostics/prerun-diagnostic"
            )

            # Compress with specific format and custom output path
            archive = DiagnosticCompression.compress_directory(
                "/path/to/diagnostics/prerun-diagnostic",
                format=CompressionFormat.TAR_GZ,
                output_path="/path/to/archives/prerun.tar.gz"
            )

        Note:
            For GZIP format, this method automatically uses TAR_GZ since GZIP
            cannot compress directories directly.
        """
        if format is None:
            format = cls._configured_format

        if format == CompressionFormat.NONE:
            return None

        if not os.path.isdir(dir_path):
            if not os.path.exists(dir_path):
                raise FileNotFoundError(f"Directory not found: {dir_path}")
            raise ValueError(f"Path is not a directory: {dir_path}")

        # GZIP cannot compress directories, use TAR_GZ instead
        if format == CompressionFormat.GZIP:
            format = CompressionFormat.TAR_GZ

        extension = cls._EXTENSIONS[format]
        
        if output_path is None:
            dir_name = os.path.basename(dir_path.rstrip(os.sep))
            parent_dir = os.path.dirname(dir_path.rstrip(os.sep))
            output_path = os.path.join(parent_dir, dir_name + extension)

        try:
            if format == CompressionFormat.ZIP:
                compression = zipfile.ZIP_DEFLATED
                with zipfile.ZipFile(output_path, 'w', compression=compression, compresslevel=compression_level) as zf:
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, dir_path)
                            zf.write(file_path, arcname)

            elif format in (CompressionFormat.TAR_GZ, CompressionFormat.TAR_BZ2):
                mode = 'w:gz' if format == CompressionFormat.TAR_GZ else 'w:bz2'
                with tarfile.open(output_path, mode) as tf:
                    dir_name = os.path.basename(dir_path.rstrip(os.sep))
                    tf.add(dir_path, arcname=dir_name)

            if not keep_original:
                shutil.rmtree(dir_path)

            return output_path

        except Exception:
            # Clean up partial archive if it exists
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

    @classmethod
    def compress_diagnostic_folder(
        cls,
        diagnostic_root: str,
        label: str,
        format: Optional[CompressionFormat] = None,
        keep_original: bool = False,
        compression_level: int = 9
    ) -> Optional[str]:
        """
        Compress a diagnostic folder for a specific diagnostic label.

        This is a convenience method that compresses the diagnostic folder
        for a specific diagnostic stage (e.g., prerun-diagnostic, postrun-diagnostic).
        It constructs the full path from the diagnostic root and label.

        :param diagnostic_root: The root diagnostics directory path
            (typically ``<test_results_dir>/diagnostics/``).
        :param label: The diagnostic label identifying the folder to compress
            (e.g., "prerun-diagnostic", "postrun-diagnostic").
        :param format: The compression format to use. If None, uses the
            currently configured format.
        :param keep_original: If True, keeps the original folder after
            compression. If False (default), removes the original folder.
        :param compression_level: Compression level (1-9). Default is 9.

        :returns: The path to the compressed archive, or None if compression
            failed, format is NONE, or the folder doesn't exist.

        Example Usage::

            from ccai.testbase.diagnostics import DiagnosticCompression, DiagnosticLabel

            # Compress pre-run diagnostics
            archive = DiagnosticCompression.compress_diagnostic_folder(
                "/path/to/results/diagnostics",
                DiagnosticLabel.PRERUN_DIAGNOSTIC,
                format=CompressionFormat.TAR_GZ
            )

        See Also:
            - :meth:`compress_directory`: Lower-level directory compression method
            - :class:`DiagnosticLabel`: Diagnostic stage label constants
        """
        if format is None:
            format = cls._configured_format

        if format == CompressionFormat.NONE:
            return None

        folder_path = os.path.join(diagnostic_root, label)
        
        if not os.path.isdir(folder_path):
            return None

        return cls.compress_directory(
            folder_path,
            format=format,
            keep_original=keep_original,
            compression_level=compression_level
        )

    @staticmethod
    def _is_within_directory(directory: str, target: str) -> bool:
        """
            Determines whether ``target`` resolves to a location inside ``directory``.

            :param directory: The base directory that must contain the target.
            :param target: The candidate path to validate.

            :returns: True if ``target`` is within ``directory``, otherwise False.
        """
        abs_directory = os.path.abspath(directory)
        abs_target = os.path.abspath(target)
        common_prefix = os.path.commonpath([abs_directory, abs_target])
        rtnval = common_prefix == abs_directory
        return rtnval

    @classmethod
    def _assert_safe_archive_members(cls, output_path: str, member_names: List[str]) -> None:
        """
            Validates that every archive member extracts inside ``output_path``,
            guarding against ``../`` / absolute-path traversal (CVE-2007-4559 class).

            :param output_path: The directory members will be extracted into.
            :param member_names: The member names declared by the archive.

            :raises: ValueError when a member would escape ``output_path``.
        """
        for member_name in member_names:
            member_target = os.path.join(output_path, member_name)
            if not cls._is_within_directory(output_path, member_target):
                err_msg = f"Refusing to extract unsafe archive member outside the target directory: {member_name}"
                raise ValueError(err_msg)
        return

    @classmethod
    def decompress_file(
        cls,
        compressed_path: str,
        output_path: Optional[str] = None,
        keep_compressed: bool = True
    ) -> str:
        """
        Decompress a compressed file.

        This method decompresses a file that was compressed using one of the
        supported compression formats. The format is automatically detected
        from the file extension.

        :param compressed_path: The path to the compressed file.
        :param output_path: Optional path for the decompressed output. If None,
            the output is created by removing the compression extension.
        :param keep_compressed: If True (default), keeps the compressed file
            after decompression. If False, removes the compressed file.

        :returns: The path to the decompressed file or directory.

        :raises FileNotFoundError: If the compressed file does not exist.
        :raises ValueError: If the compression format cannot be determined
            from the file extension.

        Example Usage::

            # Decompress a gzip file
            original = DiagnosticCompression.decompress_file("/path/to/file.json.gz")

            # Decompress to specific location
            original = DiagnosticCompression.decompress_file(
                "/path/to/archive.tar.gz",
                output_path="/path/to/output"
            )
        """
        if not os.path.exists(compressed_path):
            raise FileNotFoundError(f"Compressed file not found: {compressed_path}")

        # Detect format from extension
        format = None
        for fmt, ext in cls._EXTENSIONS.items():
            if ext and compressed_path.endswith(ext):
                format = fmt
                break

        if format is None:
            raise ValueError(f"Cannot determine compression format from: {compressed_path}")

        if output_path is None:
            output_path = compressed_path[:-len(cls._EXTENSIONS[format])]

        try:
            if format == CompressionFormat.GZIP:
                with gzip.open(compressed_path, 'rb') as f_in:
                    with open(output_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)

            elif format == CompressionFormat.ZIP:
                with zipfile.ZipFile(compressed_path, 'r') as zf:
                    # If single file, extract to output_path
                    # If multiple files, extract to directory
                    names = zf.namelist()
                    if len(names) == 1:
                        with zf.open(names[0]) as f_in:
                            with open(output_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                    else:
                        os.makedirs(output_path, exist_ok=True)
                        cls._assert_safe_archive_members(output_path, names)
                        zf.extractall(output_path)

            elif format in (CompressionFormat.TAR_GZ, CompressionFormat.TAR_BZ2):
                os.makedirs(output_path, exist_ok=True)
                with tarfile.open(compressed_path, 'r:*') as tf:
                    tar_members = tf.getmembers()
                    member_names = [member.name for member in tar_members]
                    cls._assert_safe_archive_members(output_path, member_names)
                    # Reject link members whose target escapes output_path (tar symlink/hardlink traversal).
                    for member in tar_members:
                        if member.issym() or member.islnk():
                            link_dir = os.path.dirname(member.name)
                            link_target = os.path.join(output_path, link_dir, member.linkname)
                            if not cls._is_within_directory(output_path, link_target):
                                link_err_msg = f"Refusing to extract unsafe archive link outside the target directory: {member.name} -> {member.linkname}"
                                raise ValueError(link_err_msg)
                    tf.extractall(output_path)

            if not keep_compressed:
                os.remove(compressed_path)

            return output_path

        except Exception:
            # Clean up partial output if it exists
            if os.path.exists(output_path):
                if os.path.isdir(output_path):
                    shutil.rmtree(output_path)
                else:
                    os.remove(output_path)
            raise

    @classmethod
    def get_compressed_size(cls, path: str) -> int:
        """
        Get the size of a compressed file in bytes.

        :param path: The path to the compressed file.

        :returns: The size of the file in bytes.

        :raises FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        return os.path.getsize(path)

    @classmethod
    def get_compression_ratio(cls, original_size: int, compressed_size: int) -> float:
        """
        Calculate the compression ratio.

        :param original_size: The original uncompressed size in bytes.
        :param compressed_size: The compressed size in bytes.

        :returns: The compression ratio as a float (e.g., 0.5 means 50% of original size).
            Returns 1.0 if original_size is 0.
        """
        if original_size == 0:
            return 1.0
        return compressed_size / original_size

    @classmethod
    def is_compression_enabled(cls) -> bool:
        """
        Check if compression is enabled (format is not NONE).

        :returns: True if compression is enabled, False otherwise.
        """
        return cls._configured_format != CompressionFormat.NONE

    @classmethod
    def reset_to_default(cls) -> None:
        """
        Reset the compression format to the default (GZIP).

        :returns: None
        """
        cls._configured_format = cls.DEFAULT_FORMAT


class DiagnosticLabel:
    """
    Constants that identify well-known diagnostic stages in the test execution lifecycle.

    The :class:`DiagnosticLabel` class provides string constants used to identify specific
    diagnostic capture points during test execution. These labels are passed to integration
    coupling diagnostic methods to indicate which stage of the test lifecycle is being
    captured.

    The diagnostic system supports two primary capture points:

    * **Pre-run**: Diagnostics captured before test execution begins
    * **Post-run**: Diagnostics captured after test execution completes

    Class Attributes:
        PRERUN_DIAGNOSTIC (str): Label for pre-run diagnostic capture stage.
            Value: ``"prerun-diagnostic"``
        POSTRUN_DIAGNOSTIC (str): Label for post-run diagnostic capture stage.
            Value: ``"postrun-diagnostic"``

    Example Usage::

        from ccai.testbase.diagnostics import DiagnosticLabel

        # Use labels in diagnostic capture logic
        def capture_diagnostics(label: str, output_folder: str):
            if label == DiagnosticLabel.PRERUN_DIAGNOSTIC:
                # Capture initial system state
                capture_initial_state(output_folder)
            elif label == DiagnosticLabel.POSTRUN_DIAGNOSTIC:
                # Capture final system state and logs
                capture_final_state(output_folder)

        # Labels are string values
        print(DiagnosticLabel.PRERUN_DIAGNOSTIC)   # Output: "prerun-diagnostic"
        print(DiagnosticLabel.POSTRUN_DIAGNOSTIC)  # Output: "postrun-diagnostic"

        # Labels can be used for folder naming
        import os
        diag_folder = os.path.join(results_dir, "diagnostics", DiagnosticLabel.PRERUN_DIAGNOSTIC)

    Note:
        These constants are used throughout the diagnostic system to ensure consistent
        identification of diagnostic stages. Custom diagnostic labels are not currently
        supported; only the pre-defined labels should be used.

    See Also:
        - :meth:`ccai.testbase.coupling.integrationcoupling.IntegrationCoupling.diagnostic`:
          Method that receives these labels during diagnostic capture
        - :class:`RuntimeConfigPaths`: Configuration paths that use these labels
    """

    # ============================================================================
    # DIAGNOSTIC FOLDER STRUCTURE CREATION
    # ============================================================================
    # These label constants are used to create the diagnostic folder hierarchy:
    #
    #   <test_results_dir>/
    #   └── diagnostics/                    <- Root diagnostics folder
    #       ├── prerun-diagnostic/          <- Created using PRERUN_DIAGNOSTIC label
    #       │   ├── <integration_1>/        <- Each integration creates its subfolder
    #       │   │   └── diagnostic_files...
    #       │   └── <integration_2>/
    #       │       └── diagnostic_files...
    #       └── postrun-diagnostic/         <- Created using POSTRUN_DIAGNOSTIC label
    #           ├── <integration_1>/
    #           │   └── diagnostic_files...
    #           └── <integration_2>/
    #               └── diagnostic_files...
    #
    # The folder creation flow:
    # 1. TestSequencer resolves the path via output_context.get_diagnostics_dir(label) with one of these labels
    # 2. IOutputContext.get_diagnostics_dir() creates: <test_results_dir>/diagnostics/<label>/
    # 3. Each IntegrationCoupling.diagnostic() creates its own subfolder within
    # 4. Integration writes diagnostic files to its subfolder
    #
    # The "diagnostics" folder is excluded from result traversal to prevent
    # diagnostic data from being processed as test results.
    # ============================================================================

    PRERUN_DIAGNOSTIC = "prerun-diagnostic"
    POSTRUN_DIAGNOSTIC = "postrun-diagnostic"


class RuntimeConfigPaths:
    """
    Configuration paths for diagnostic runtime information within the application's
    configuration tree.

    The :class:`RuntimeConfigPaths` class provides string constants representing
    hierarchical paths used to store and retrieve diagnostic configuration settings
    in the TestBase runtime configuration system. These paths follow a consistent
    format starting with ``/configuration/runtime/diagnostics/``.

    The configuration paths are used by the runtime variable system to determine
    whether diagnostic capture is enabled for each stage of test execution.

    Class Attributes:
        DIAGNOSTIC_PRERUN (str): Configuration path for pre-run diagnostic settings.
            Value: ``"/configuration/runtime/diagnostics/prerun-diagnostic"``
        DIAGNOSTIC_POSTRUN (str): Configuration path for post-run diagnostic settings.
            Value: ``"/configuration/runtime/diagnostics/postrun-diagnostic"``

    Path Format:
        All paths follow the hierarchical format::

            /configuration/runtime/diagnostics/{diagnostic-label}

        Where ``{diagnostic-label}`` corresponds to a :class:`DiagnosticLabel` constant.

    Example Usage::

        from ccai.testbase.diagnostics import RuntimeConfigPaths

        # Access configuration paths
        prerun_path = RuntimeConfigPaths.DIAGNOSTIC_PRERUN
        postrun_path = RuntimeConfigPaths.DIAGNOSTIC_POSTRUN

        # Use paths with configuration system
        config_tree.set_value(RuntimeConfigPaths.DIAGNOSTIC_PRERUN, True)
        config_tree.set_value(RuntimeConfigPaths.DIAGNOSTIC_POSTRUN, True)

        # Check if diagnostics are enabled
        prerun_enabled = config_tree.get_value(RuntimeConfigPaths.DIAGNOSTIC_PRERUN)
        if prerun_enabled:
            print("Pre-run diagnostics are enabled")

    Note:
        These paths are used internally by the TestBase framework to manage diagnostic
        settings. Direct manipulation of these configuration paths is typically not
        required; use the CLI options (``--prerun-diagnostic``, ``--postrun-diagnostic``)
        or runtime variables (``AM_DIAGNOSTICS_PRERUN``, ``AM_DIAGNOSTICS_POSTRUN``)
        instead.

    See Also:
        - :class:`DiagnosticLabel`: Labels used in the path hierarchy
        - :class:`ccai.testbase.cli.options.DiagnosticOptionGroup`: CLI options that
          set these configuration values
    """

    DIAGNOSTIC_PRERUN = "/configuration/runtime/diagnostics/prerun-diagnostic"
    DIAGNOSTIC_POSTRUN = "/configuration/runtime/diagnostics/postrun-diagnostic"


class DiagnosticLabelRegistry:
    """
    Registry for managing custom diagnostic labels in addition to the built-in labels.

    The :class:`DiagnosticLabelRegistry` provides a mechanism for registering custom
    diagnostic capture points beyond the standard pre-run and post-run stages. This
    enables integration couplings and test frameworks to define specialized diagnostic
    capture points for their specific needs.

    The registry maintains backward compatibility with the existing :class:`DiagnosticLabel`
    constants by automatically including them in the registry.

    Class Attributes:
        _custom_labels (Dict[str, str]): Internal dictionary storing custom label mappings.
            Keys are label identifiers, values are descriptions.

    Built-in Labels:
        The following labels are always available and cannot be overwritten:

        * ``prerun-diagnostic``: Pre-run diagnostic capture stage
        * ``postrun-diagnostic``: Post-run diagnostic capture stage

    Example Usage::

        from ccai.testbase.diagnostics import DiagnosticLabelRegistry

        # Register a custom diagnostic label
        DiagnosticLabelRegistry.register(
            "checkpoint-diagnostic",
            "Diagnostic capture at test checkpoint"
        )

        # Check if a label is registered
        if DiagnosticLabelRegistry.is_registered("checkpoint-diagnostic"):
            print("Checkpoint diagnostic is available")

        # Get all registered labels
        all_labels = DiagnosticLabelRegistry.get_all_labels()
        for label, description in all_labels.items():
            print(f"{label}: {description}")

        # Get a specific label's description
        desc = DiagnosticLabelRegistry.get_description("prerun-diagnostic")

        # Unregister a custom label (built-in labels cannot be unregistered)
        DiagnosticLabelRegistry.unregister("checkpoint-diagnostic")

    Note:
        Custom labels should follow the naming convention of lowercase words separated
        by hyphens (e.g., "checkpoint-diagnostic", "mid-test-diagnostic").

    See Also:
        - :class:`DiagnosticLabel`: Built-in diagnostic label constants
        - :class:`RuntimeConfigPaths`: Configuration paths for diagnostic settings
    """

    # Internal storage for custom diagnostic labels
    # Keys are label identifiers, values are descriptions
    _custom_labels: Dict[str, str] = {}

    # Built-in labels that are always available and cannot be modified
    _BUILTIN_LABELS: Dict[str, str] = {
        DiagnosticLabel.PRERUN_DIAGNOSTIC: "Pre-run diagnostic capture stage - captured before test execution begins",
        DiagnosticLabel.POSTRUN_DIAGNOSTIC: "Post-run diagnostic capture stage - captured after test execution completes"
    }

    @classmethod
    def register(cls, label: str, description: str = "") -> bool:
        """
        Register a custom diagnostic label.

        This method adds a new diagnostic label to the registry. Custom labels can be
        used to define specialized diagnostic capture points beyond the standard
        pre-run and post-run stages.

        :param label: The label identifier string. Should follow the naming convention
            of lowercase words separated by hyphens (e.g., "checkpoint-diagnostic").
        :param description: Optional description of the diagnostic label's purpose.
            Defaults to an empty string.

        :returns: True if the label was successfully registered, False if the label
            already exists (either as a built-in or custom label).

        :raises ValueError: If the label is empty or None.

        Example Usage::

            # Register a simple custom label
            success = DiagnosticLabelRegistry.register("checkpoint-diagnostic")

            # Register with description
            success = DiagnosticLabelRegistry.register(
                "mid-test-diagnostic",
                "Diagnostic capture during test execution"
            )

            # Attempting to register an existing label returns False
            success = DiagnosticLabelRegistry.register("prerun-diagnostic")  # Returns False

        Note:
            Built-in labels (prerun-diagnostic, postrun-diagnostic) cannot be
            overwritten. Attempting to register them will return False.
        """
        if not label:
            raise ValueError("Diagnostic label cannot be empty or None")

        # Check if label already exists (built-in or custom)
        if label in cls._BUILTIN_LABELS or label in cls._custom_labels:
            return False

        cls._custom_labels[label] = description
        return True

    @classmethod
    def unregister(cls, label: str) -> bool:
        """
        Unregister a custom diagnostic label.

        This method removes a custom diagnostic label from the registry. Built-in
        labels cannot be unregistered.

        :param label: The label identifier string to unregister.

        :returns: True if the label was successfully unregistered, False if the label
            does not exist or is a built-in label.

        Example Usage::

            # Unregister a custom label
            success = DiagnosticLabelRegistry.unregister("checkpoint-diagnostic")

            # Attempting to unregister a built-in label returns False
            success = DiagnosticLabelRegistry.unregister("prerun-diagnostic")  # Returns False

            # Attempting to unregister a non-existent label returns False
            success = DiagnosticLabelRegistry.unregister("nonexistent-label")  # Returns False
        """
        # Cannot unregister built-in labels
        if label in cls._BUILTIN_LABELS:
            return False

        if label in cls._custom_labels:
            del cls._custom_labels[label]
            return True

        return False

    @classmethod
    def is_registered(cls, label: str) -> bool:
        """
        Check if a diagnostic label is registered.

        This method checks whether a label exists in the registry, including both
        built-in and custom labels.

        :param label: The label identifier string to check.

        :returns: True if the label is registered (built-in or custom), False otherwise.

        Example Usage::

            # Check built-in labels
            is_prerun = DiagnosticLabelRegistry.is_registered("prerun-diagnostic")  # True

            # Check custom labels
            DiagnosticLabelRegistry.register("checkpoint-diagnostic")
            is_checkpoint = DiagnosticLabelRegistry.is_registered("checkpoint-diagnostic")  # True

            # Check non-existent labels
            is_unknown = DiagnosticLabelRegistry.is_registered("unknown-label")  # False
        """
        return label in cls._BUILTIN_LABELS or label in cls._custom_labels

    @classmethod
    def is_builtin(cls, label: str) -> bool:
        """
        Check if a diagnostic label is a built-in label.

        This method checks whether a label is one of the predefined built-in labels
        (prerun-diagnostic or postrun-diagnostic).

        :param label: The label identifier string to check.

        :returns: True if the label is a built-in label, False otherwise.

        Example Usage::

            # Check built-in labels
            is_builtin = DiagnosticLabelRegistry.is_builtin("prerun-diagnostic")  # True
            is_builtin = DiagnosticLabelRegistry.is_builtin("postrun-diagnostic")  # True

            # Check custom labels
            DiagnosticLabelRegistry.register("checkpoint-diagnostic")
            is_builtin = DiagnosticLabelRegistry.is_builtin("checkpoint-diagnostic")  # False
        """
        return label in cls._BUILTIN_LABELS

    @classmethod
    def get_description(cls, label: str) -> Optional[str]:
        """
        Get the description for a diagnostic label.

        This method retrieves the description associated with a registered label.

        :param label: The label identifier string.

        :returns: The description string if the label is registered, None otherwise.

        Example Usage::

            # Get description for built-in label
            desc = DiagnosticLabelRegistry.get_description("prerun-diagnostic")
            # Returns: "Pre-run diagnostic capture stage - captured before test execution begins"

            # Get description for custom label
            DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
            desc = DiagnosticLabelRegistry.get_description("checkpoint-diagnostic")
            # Returns: "Test checkpoint"

            # Get description for non-existent label
            desc = DiagnosticLabelRegistry.get_description("unknown-label")
            # Returns: None
        """
        if label in cls._BUILTIN_LABELS:
            return cls._BUILTIN_LABELS[label]
        return cls._custom_labels.get(label)

    @classmethod
    def get_all_labels(cls) -> Dict[str, str]:
        """
        Get all registered diagnostic labels.

        This method returns a dictionary containing all registered labels, including
        both built-in and custom labels.

        :returns: A dictionary where keys are label identifiers and values are
            descriptions. The dictionary includes both built-in and custom labels.

        Example Usage::

            # Get all labels
            all_labels = DiagnosticLabelRegistry.get_all_labels()
            for label, description in all_labels.items():
                print(f"{label}: {description}")

        Note:
            The returned dictionary is a copy; modifications to it will not affect
            the registry.
        """
        result = dict(cls._BUILTIN_LABELS)
        result.update(cls._custom_labels)
        return result

    @classmethod
    def get_custom_labels(cls) -> Dict[str, str]:
        """
        Get only the custom diagnostic labels.

        This method returns a dictionary containing only the custom labels that have
        been registered, excluding the built-in labels.

        :returns: A dictionary where keys are custom label identifiers and values are
            descriptions.

        Example Usage::

            # Register some custom labels
            DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")
            DiagnosticLabelRegistry.register("mid-test-diagnostic", "Mid-test capture")

            # Get only custom labels
            custom_labels = DiagnosticLabelRegistry.get_custom_labels()
            # Returns: {"checkpoint-diagnostic": "Test checkpoint", "mid-test-diagnostic": "Mid-test capture"}

        Note:
            The returned dictionary is a copy; modifications to it will not affect
            the registry.
        """
        return dict(cls._custom_labels)

    @classmethod
    def get_builtin_labels(cls) -> Dict[str, str]:
        """
        Get only the built-in diagnostic labels.

        This method returns a dictionary containing only the built-in labels
        (prerun-diagnostic and postrun-diagnostic).

        :returns: A dictionary where keys are built-in label identifiers and values
            are descriptions.

        Example Usage::

            # Get built-in labels
            builtin_labels = DiagnosticLabelRegistry.get_builtin_labels()
            # Returns: {"prerun-diagnostic": "...", "postrun-diagnostic": "..."}

        Note:
            The returned dictionary is a copy; modifications to it will not affect
            the registry.
        """
        return dict(cls._BUILTIN_LABELS)

    @classmethod
    def clear_custom_labels(cls) -> None:
        """
        Clear all custom diagnostic labels from the registry.

        This method removes all custom labels that have been registered, leaving
        only the built-in labels. This is useful for resetting the registry state
        between test runs or for cleanup purposes.

        :returns: None

        Example Usage::

            # Register some custom labels
            DiagnosticLabelRegistry.register("checkpoint-diagnostic")
            DiagnosticLabelRegistry.register("mid-test-diagnostic")

            # Clear all custom labels
            DiagnosticLabelRegistry.clear_custom_labels()

            # Only built-in labels remain
            all_labels = DiagnosticLabelRegistry.get_all_labels()
            # Returns only prerun-diagnostic and postrun-diagnostic

        Note:
            Built-in labels are never affected by this method.
        """
        cls._custom_labels.clear()

    @classmethod
    def get_config_path_for_label(cls, label: str) -> str:
        """
        Generate a configuration path for a diagnostic label.

        This method generates a hierarchical configuration path for a given label,
        following the same format as the built-in RuntimeConfigPaths constants.

        :param label: The label identifier string.

        :returns: A configuration path string in the format
            ``/configuration/runtime/diagnostics/{label}``.

        Example Usage::

            # Get config path for built-in label
            path = DiagnosticLabelRegistry.get_config_path_for_label("prerun-diagnostic")
            # Returns: "/configuration/runtime/diagnostics/prerun-diagnostic"

            # Get config path for custom label
            DiagnosticLabelRegistry.register("checkpoint-diagnostic")
            path = DiagnosticLabelRegistry.get_config_path_for_label("checkpoint-diagnostic")
            # Returns: "/configuration/runtime/diagnostics/checkpoint-diagnostic"

        Note:
            This method generates a path regardless of whether the label is registered.
            Use :meth:`is_registered` to verify label registration if needed.
        """
        return f"/configuration/runtime/diagnostics/{label}"


class DiagnosticFilter:
    """
    Filter for controlling which diagnostics are captured based on integration type and label.

    The :class:`DiagnosticFilter` class provides a mechanism for selectively enabling or
    disabling diagnostic capture based on integration type names and diagnostic labels.
    It supports include/exclude patterns using glob-style wildcards.

    The filter uses a whitelist/blacklist approach:
    
    * **Include patterns**: Only integrations/labels matching these patterns are captured
    * **Exclude patterns**: Integrations/labels matching these patterns are skipped
    
    Exclude patterns take precedence over include patterns.

    Class Attributes:
        _integration_include_patterns (List[str]): Patterns for integrations to include.
        _integration_exclude_patterns (List[str]): Patterns for integrations to exclude.
        _label_include_patterns (List[str]): Patterns for labels to include.
        _label_exclude_patterns (List[str]): Patterns for labels to exclude.

    Pattern Syntax:
        Patterns support glob-style wildcards:
        
        * ``*`` matches any sequence of characters
        * ``?`` matches any single character
        * ``[seq]`` matches any character in seq
        * ``[!seq]`` matches any character not in seq

    Example Usage::

        from ccai.testbase.diagnostics import DiagnosticFilter

        # Include only specific integrations
        DiagnosticFilter.add_integration_include_pattern("device*")
        DiagnosticFilter.add_integration_include_pattern("network*")

        # Exclude certain integrations
        DiagnosticFilter.add_integration_exclude_pattern("*debug*")

        # Filter by label
        DiagnosticFilter.add_label_include_pattern("prerun-diagnostic")

        # Check if an integration should be captured
        if DiagnosticFilter.should_capture_integration("device_coupling"):
            # Capture diagnostics for this integration
            pass

        # Check if a label should be captured
        if DiagnosticFilter.should_capture_label("prerun-diagnostic"):
            # Capture diagnostics for this label
            pass

        # Clear all filters
        DiagnosticFilter.clear_all_filters()

    Note:
        When no include patterns are specified, all integrations/labels are included
        by default. When include patterns are specified, only matching items are included.

    See Also:
        - :class:`DiagnosticLabel`: Diagnostic stage label constants
        - :class:`DiagnosticLabelRegistry`: Registry for custom diagnostic labels
        - :meth:`ccai.testbase.sequencing.testsequencer.TestSequencer.diagnostic_capture_pre_testrun`:
          Method that uses filtering during diagnostic capture
    """

    # Internal storage for filter patterns
    _integration_include_patterns: List[str] = []
    _integration_exclude_patterns: List[str] = []
    _label_include_patterns: List[str] = []
    _label_exclude_patterns: List[str] = []

    @classmethod
    def add_integration_include_pattern(cls, pattern: str) -> None:
        """
        Add a pattern for integrations to include in diagnostic capture.

        When include patterns are specified, only integrations matching at least one
        pattern will have their diagnostics captured. If no include patterns are
        specified, all integrations are included by default.

        :param pattern: A glob-style pattern to match integration type names.
            Supports wildcards: ``*`` (any sequence), ``?`` (single char),
            ``[seq]`` (char in seq), ``[!seq]`` (char not in seq).

        :returns: None

        Example Usage::

            # Include all device integrations
            DiagnosticFilter.add_integration_include_pattern("device*")

            # Include specific integration
            DiagnosticFilter.add_integration_include_pattern("NetworkCoupling")

            # Include integrations with specific suffix
            DiagnosticFilter.add_integration_include_pattern("*Coupling")
        """
        if pattern and pattern not in cls._integration_include_patterns:
            cls._integration_include_patterns.append(pattern)

    @classmethod
    def add_integration_exclude_pattern(cls, pattern: str) -> None:
        """
        Add a pattern for integrations to exclude from diagnostic capture.

        Integrations matching any exclude pattern will be skipped during diagnostic
        capture, even if they match an include pattern. Exclude patterns take
        precedence over include patterns.

        :param pattern: A glob-style pattern to match integration type names.
            Supports wildcards: ``*`` (any sequence), ``?`` (single char),
            ``[seq]`` (char in seq), ``[!seq]`` (char not in seq).

        :returns: None

        Example Usage::

            # Exclude debug integrations
            DiagnosticFilter.add_integration_exclude_pattern("*debug*")

            # Exclude specific integration
            DiagnosticFilter.add_integration_exclude_pattern("TestIntegration")

            # Exclude integrations with specific prefix
            DiagnosticFilter.add_integration_exclude_pattern("Mock*")
        """
        if pattern and pattern not in cls._integration_exclude_patterns:
            cls._integration_exclude_patterns.append(pattern)

    @classmethod
    def add_label_include_pattern(cls, pattern: str) -> None:
        """
        Add a pattern for diagnostic labels to include in capture.

        When include patterns are specified, only labels matching at least one
        pattern will trigger diagnostic capture. If no include patterns are
        specified, all labels are included by default.

        :param pattern: A glob-style pattern to match diagnostic label names.
            Supports wildcards: ``*`` (any sequence), ``?`` (single char),
            ``[seq]`` (char in seq), ``[!seq]`` (char not in seq).

        :returns: None

        Example Usage::

            # Include only pre-run diagnostics
            DiagnosticFilter.add_label_include_pattern("prerun-diagnostic")

            # Include all diagnostics with specific prefix
            DiagnosticFilter.add_label_include_pattern("pre*")

            # Include multiple label patterns
            DiagnosticFilter.add_label_include_pattern("*-diagnostic")
        """
        if pattern and pattern not in cls._label_include_patterns:
            cls._label_include_patterns.append(pattern)

    @classmethod
    def add_label_exclude_pattern(cls, pattern: str) -> None:
        """
        Add a pattern for diagnostic labels to exclude from capture.

        Labels matching any exclude pattern will be skipped during diagnostic
        capture, even if they match an include pattern. Exclude patterns take
        precedence over include patterns.

        :param pattern: A glob-style pattern to match diagnostic label names.
            Supports wildcards: ``*`` (any sequence), ``?`` (single char),
            ``[seq]`` (char in seq), ``[!seq]`` (char not in seq).

        :returns: None

        Example Usage::

            # Exclude checkpoint diagnostics
            DiagnosticFilter.add_label_exclude_pattern("checkpoint-*")

            # Exclude specific label
            DiagnosticFilter.add_label_exclude_pattern("debug-diagnostic")

            # Exclude labels with specific suffix
            DiagnosticFilter.add_label_exclude_pattern("*-debug")
        """
        if pattern and pattern not in cls._label_exclude_patterns:
            cls._label_exclude_patterns.append(pattern)

    @classmethod
    def remove_integration_include_pattern(cls, pattern: str) -> bool:
        """
        Remove an integration include pattern.

        :param pattern: The pattern to remove.

        :returns: True if the pattern was removed, False if it was not found.
        """
        if pattern in cls._integration_include_patterns:
            cls._integration_include_patterns.remove(pattern)
            return True
        return False

    @classmethod
    def remove_integration_exclude_pattern(cls, pattern: str) -> bool:
        """
        Remove an integration exclude pattern.

        :param pattern: The pattern to remove.

        :returns: True if the pattern was removed, False if it was not found.
        """
        if pattern in cls._integration_exclude_patterns:
            cls._integration_exclude_patterns.remove(pattern)
            return True
        return False

    @classmethod
    def remove_label_include_pattern(cls, pattern: str) -> bool:
        """
        Remove a label include pattern.

        :param pattern: The pattern to remove.

        :returns: True if the pattern was removed, False if it was not found.
        """
        if pattern in cls._label_include_patterns:
            cls._label_include_patterns.remove(pattern)
            return True
        return False

    @classmethod
    def remove_label_exclude_pattern(cls, pattern: str) -> bool:
        """
        Remove a label exclude pattern.

        :param pattern: The pattern to remove.

        :returns: True if the pattern was removed, False if it was not found.
        """
        if pattern in cls._label_exclude_patterns:
            cls._label_exclude_patterns.remove(pattern)
            return True
        return False

    @classmethod
    def _matches_any_pattern(cls, value: str, patterns: List[str]) -> bool:
        """
        Check if a value matches any of the given glob patterns.

        :param value: The value to check.
        :param patterns: List of glob patterns to match against.

        :returns: True if the value matches any pattern, False otherwise.
        """
        import fnmatch
        
        for pattern in patterns:
            if fnmatch.fnmatch(value, pattern):
                return True
        return False

    @classmethod
    def should_capture_integration(cls, integration_name: str) -> bool:
        """
        Determine if diagnostics should be captured for a given integration.

        This method checks the integration name against the configured include
        and exclude patterns to determine if diagnostic capture should proceed.

        The logic is:
        1. If the integration matches any exclude pattern, return False
        2. If include patterns are specified and the integration doesn't match any, return False
        3. Otherwise, return True

        :param integration_name: The name of the integration type to check.

        :returns: True if diagnostics should be captured for this integration,
            False otherwise.

        Example Usage::

            # Check if device integration should be captured
            if DiagnosticFilter.should_capture_integration("DeviceCoupling"):
                # Proceed with diagnostic capture
                pass

            # Check with patterns configured
            DiagnosticFilter.add_integration_include_pattern("Device*")
            DiagnosticFilter.add_integration_exclude_pattern("*Debug*")

            DiagnosticFilter.should_capture_integration("DeviceCoupling")  # True
            DiagnosticFilter.should_capture_integration("DeviceDebugCoupling")  # False
            DiagnosticFilter.should_capture_integration("NetworkCoupling")  # False
        """
        # Check exclude patterns first (they take precedence)
        if cls._integration_exclude_patterns:
            if cls._matches_any_pattern(integration_name, cls._integration_exclude_patterns):
                return False

        # If include patterns are specified, check if integration matches any
        if cls._integration_include_patterns:
            return cls._matches_any_pattern(integration_name, cls._integration_include_patterns)

        # No include patterns specified, include by default
        return True

    @classmethod
    def should_capture_label(cls, label: str) -> bool:
        """
        Determine if diagnostics should be captured for a given label.

        This method checks the label against the configured include and exclude
        patterns to determine if diagnostic capture should proceed.

        The logic is:
        1. If the label matches any exclude pattern, return False
        2. If include patterns are specified and the label doesn't match any, return False
        3. Otherwise, return True

        :param label: The diagnostic label to check.

        :returns: True if diagnostics should be captured for this label,
            False otherwise.

        Example Usage::

            # Check if prerun label should be captured
            if DiagnosticFilter.should_capture_label("prerun-diagnostic"):
                # Proceed with diagnostic capture
                pass

            # Check with patterns configured
            DiagnosticFilter.add_label_include_pattern("*-diagnostic")
            DiagnosticFilter.add_label_exclude_pattern("debug-*")

            DiagnosticFilter.should_capture_label("prerun-diagnostic")  # True
            DiagnosticFilter.should_capture_label("debug-diagnostic")  # False
        """
        # Check exclude patterns first (they take precedence)
        if cls._label_exclude_patterns:
            if cls._matches_any_pattern(label, cls._label_exclude_patterns):
                return False

        # If include patterns are specified, check if label matches any
        if cls._label_include_patterns:
            return cls._matches_any_pattern(label, cls._label_include_patterns)

        # No include patterns specified, include by default
        return True

    @classmethod
    def should_capture(cls, integration_name: str, label: str) -> bool:
        """
        Determine if diagnostics should be captured for a given integration and label.

        This is a convenience method that combines both integration and label filtering.
        Both must pass their respective filters for capture to proceed.

        :param integration_name: The name of the integration type to check.
        :param label: The diagnostic label to check.

        :returns: True if diagnostics should be captured for this combination,
            False otherwise.

        Example Usage::

            # Check if capture should proceed
            if DiagnosticFilter.should_capture("DeviceCoupling", "prerun-diagnostic"):
                # Proceed with diagnostic capture
                pass
        """
        return cls.should_capture_integration(integration_name) and cls.should_capture_label(label)

    @classmethod
    def get_integration_include_patterns(cls) -> List[str]:
        """
        Get the current integration include patterns.

        :returns: A copy of the integration include patterns list.
        """
        return list(cls._integration_include_patterns)

    @classmethod
    def get_integration_exclude_patterns(cls) -> List[str]:
        """
        Get the current integration exclude patterns.

        :returns: A copy of the integration exclude patterns list.
        """
        return list(cls._integration_exclude_patterns)

    @classmethod
    def get_label_include_patterns(cls) -> List[str]:
        """
        Get the current label include patterns.

        :returns: A copy of the label include patterns list.
        """
        return list(cls._label_include_patterns)

    @classmethod
    def get_label_exclude_patterns(cls) -> List[str]:
        """
        Get the current label exclude patterns.

        :returns: A copy of the label exclude patterns list.
        """
        return list(cls._label_exclude_patterns)

    @classmethod
    def clear_integration_filters(cls) -> None:
        """
        Clear all integration filter patterns (both include and exclude).

        :returns: None
        """
        cls._integration_include_patterns.clear()
        cls._integration_exclude_patterns.clear()

    @classmethod
    def clear_label_filters(cls) -> None:
        """
        Clear all label filter patterns (both include and exclude).

        :returns: None
        """
        cls._label_include_patterns.clear()
        cls._label_exclude_patterns.clear()

    @classmethod
    def clear_all_filters(cls) -> None:
        """
        Clear all filter patterns (integration and label, include and exclude).

        :returns: None

        Example Usage::

            # Reset all filters to default (no filtering)
            DiagnosticFilter.clear_all_filters()
        """
        cls.clear_integration_filters()
        cls.clear_label_filters()

    @classmethod
    def is_filtering_enabled(cls) -> bool:
        """
        Check if any filtering is currently enabled.

        :returns: True if any include or exclude patterns are configured,
            False otherwise.
        """
        return bool(
            cls._integration_include_patterns or
            cls._integration_exclude_patterns or
            cls._label_include_patterns or
            cls._label_exclude_patterns
        )

    @classmethod
    def get_filter_summary(cls) -> Dict[str, List[str]]:
        """
        Get a summary of all configured filter patterns.

        :returns: A dictionary containing all filter patterns organized by type.

        Example Usage::

            summary = DiagnosticFilter.get_filter_summary()
            # Returns:
            # {
            #     "integration_include": ["Device*", "Network*"],
            #     "integration_exclude": ["*Debug*"],
            #     "label_include": ["prerun-diagnostic"],
            #     "label_exclude": []
            # }
        """
        return {
            "integration_include": list(cls._integration_include_patterns),
            "integration_exclude": list(cls._integration_exclude_patterns),
            "label_include": list(cls._label_include_patterns),
            "label_exclude": list(cls._label_exclude_patterns)
        }
