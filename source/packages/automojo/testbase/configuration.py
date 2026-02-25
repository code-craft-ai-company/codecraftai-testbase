"""
    .. module:: automojo.testbase.configuration
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for loading test entry point configuration from files.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module provides functionality for loading default test entry point options
from configuration files. It supports a hierarchical configuration system with
user-level and project-level configuration files.

Configuration File Locations:
    - User-level: ``~/.automojo/testbase.yaml`` or ``~/.automojo/testbase.yml``
    - Project-level: ``.testbase.yaml`` or ``.testbase.yml`` in the current directory
      or any parent directory up to the filesystem root

Configuration Precedence (highest to lowest):
    1. Command-line arguments (always override)
    2. Project-level configuration (closer to current directory wins)
    3. User-level configuration
    4. Built-in defaults

Supported Configuration Options:
    - ``includes``: List of include expressions for test filtering
    - ``excludes``: List of exclude expressions for test filtering
    - ``console_level``: Logging level for console output
    - ``logfile_level``: Logging level for file output

Example Configuration File::

    # .testbase.yaml
    includes:
      - "test_unit_*"
      - "test_integration_*"
    excludes:
      - "test_slow_*"
    console_level: INFO
    logfile_level: DEBUG

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Dict, List, Optional

import os

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# Configuration file names to search for
CONFIG_FILE_NAMES = [".testbase.yaml", ".testbase.yml"]

# User-level configuration directory and file names
USER_CONFIG_DIR = ".automojo"
USER_CONFIG_FILE_NAMES = ["testbase.yaml", "testbase.yml"]


class EntryPointConfiguration:
    """
        Container for test entry point configuration options.

        This class holds the configuration values loaded from configuration files
        and provides a clean interface for accessing them.

        Attributes:
            includes (List[str]): List of include expressions for test filtering.
            excludes (List[str]): List of exclude expressions for test filtering.
            console_level (Optional[str]): Logging level for console output.
            logfile_level (Optional[str]): Logging level for file output.
    """

    def __init__(self):
        """Initialize an empty configuration."""
        self.includes: List[str] = []
        self.excludes: List[str] = []
        self.console_level: Optional[str] = None
        self.logfile_level: Optional[str] = None

    def merge(self, other: "EntryPointConfiguration") -> None:
        """
            Merge another configuration into this one.

            Values from the other configuration override values in this configuration
            only if they are set (non-empty for lists, non-None for scalars).

            :param other: The configuration to merge into this one.
            :type other: EntryPointConfiguration
        """
        if other.includes:
            self.includes = other.includes
        if other.excludes:
            self.excludes = other.excludes
        if other.console_level is not None:
            self.console_level = other.console_level
        if other.logfile_level is not None:
            self.logfile_level = other.logfile_level

    def __repr__(self) -> str:
        return (
            f"EntryPointConfiguration(includes={self.includes}, "
            f"excludes={self.excludes}, console_level={self.console_level}, "
            f"logfile_level={self.logfile_level})"
        )


def _load_yaml_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
        Load and parse a YAML configuration file.

        :param filepath: Path to the YAML file to load.
        :type filepath: str

        :returns: Parsed YAML content as a dictionary, or None if the file
            cannot be loaded or parsed.
        :rtype: Optional[Dict[str, Any]]
    """
    if not YAML_AVAILABLE:
        return None

    if not os.path.isfile(filepath):
        return None

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)
            if isinstance(content, dict):
                return content
    except (yaml.YAMLError, IOError, OSError):
        # Silently ignore configuration file errors
        pass

    return None


def _parse_config_dict(config_dict: Dict[str, Any]) -> EntryPointConfiguration:
    """
        Parse a configuration dictionary into an EntryPointConfiguration object.

        :param config_dict: Dictionary containing configuration values.
        :type config_dict: Dict[str, Any]

        :returns: Parsed configuration object.
        :rtype: EntryPointConfiguration
    """
    config = EntryPointConfiguration()

    # Parse includes
    includes = config_dict.get("includes")
    if isinstance(includes, list):
        config.includes = [str(item) for item in includes if item is not None]
    elif isinstance(includes, str):
        config.includes = [includes]

    # Parse excludes
    excludes = config_dict.get("excludes")
    if isinstance(excludes, list):
        config.excludes = [str(item) for item in excludes if item is not None]
    elif isinstance(excludes, str):
        config.excludes = [excludes]

    # Parse console_level
    console_level = config_dict.get("console_level")
    if isinstance(console_level, str):
        config.console_level = console_level.upper()

    # Parse logfile_level
    logfile_level = config_dict.get("logfile_level")
    if isinstance(logfile_level, str):
        config.logfile_level = logfile_level.upper()

    return config


def find_user_config_file() -> Optional[str]:
    """
        Find the user-level configuration file.

        Searches for configuration files in the user's home directory under
        the ``.automojo`` directory.

        :returns: Path to the user configuration file if found, None otherwise.
        :rtype: Optional[str]
    """
    home_dir = os.path.expanduser("~")
    config_dir = os.path.join(home_dir, USER_CONFIG_DIR)

    if not os.path.isdir(config_dir):
        return None

    for filename in USER_CONFIG_FILE_NAMES:
        filepath = os.path.join(config_dir, filename)
        if os.path.isfile(filepath):
            return filepath

    return None


def find_project_config_file(start_dir: Optional[str] = None) -> Optional[str]:
    """
        Find the project-level configuration file.

        Searches for configuration files starting from the specified directory
        (or current working directory) and walking up to the filesystem root.

        :param start_dir: Directory to start searching from. Defaults to the
            current working directory.
        :type start_dir: Optional[str]

        :returns: Path to the project configuration file if found, None otherwise.
        :rtype: Optional[str]
    """
    if start_dir is None:
        start_dir = os.getcwd()

    current_dir = os.path.abspath(start_dir)

    while True:
        for filename in CONFIG_FILE_NAMES:
            filepath = os.path.join(current_dir, filename)
            if os.path.isfile(filepath):
                return filepath

        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached filesystem root
            break
        current_dir = parent_dir

    return None


def load_user_configuration() -> EntryPointConfiguration:
    """
        Load user-level configuration.

        Searches for and loads the user-level configuration file from
        ``~/.automojo/testbase.yaml`` or ``~/.automojo/testbase.yml``.

        :returns: Configuration loaded from the user config file, or an empty
            configuration if no file is found.
        :rtype: EntryPointConfiguration
    """
    config = EntryPointConfiguration()

    config_file = find_user_config_file()
    if config_file is not None:
        config_dict = _load_yaml_file(config_file)
        if config_dict is not None:
            config = _parse_config_dict(config_dict)

    return config


def load_project_configuration(start_dir: Optional[str] = None) -> EntryPointConfiguration:
    """
        Load project-level configuration.

        Searches for and loads the project-level configuration file from
        ``.testbase.yaml`` or ``.testbase.yml`` in the current directory
        or any parent directory.

        :param start_dir: Directory to start searching from. Defaults to the
            current working directory.
        :type start_dir: Optional[str]

        :returns: Configuration loaded from the project config file, or an empty
            configuration if no file is found.
        :rtype: EntryPointConfiguration
    """
    config = EntryPointConfiguration()

    config_file = find_project_config_file(start_dir)
    if config_file is not None:
        config_dict = _load_yaml_file(config_file)
        if config_dict is not None:
            config = _parse_config_dict(config_dict)

    return config


def load_entrypoint_configuration(start_dir: Optional[str] = None) -> EntryPointConfiguration:
    """
        Load merged configuration from all sources.

        Loads configuration from user-level and project-level configuration files
        and merges them according to the precedence rules. Project-level configuration
        takes precedence over user-level configuration.

        :param start_dir: Directory to start searching for project configuration.
            Defaults to the current working directory.
        :type start_dir: Optional[str]

        :returns: Merged configuration from all sources.
        :rtype: EntryPointConfiguration

        Example:
            Loading configuration for use in the entry point::

                from automojo.testbase.configuration import load_entrypoint_configuration

                config = load_entrypoint_configuration()

                # Use configuration values
                includes = config.includes or ["*"]
                excludes = config.excludes or []
                console_level = config.console_level or "INFO"
                logfile_level = config.logfile_level or "DEBUG"
    """
    # Start with user-level configuration
    config = load_user_configuration()

    # Merge project-level configuration (takes precedence)
    project_config = load_project_configuration(start_dir)
    config.merge(project_config)

    return config
