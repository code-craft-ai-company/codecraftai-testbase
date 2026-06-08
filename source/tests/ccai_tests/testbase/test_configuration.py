"""
    Unit tests for the configuration module.
    
    Tests verify:
    - Loading configuration from YAML files
    - User-level configuration file discovery
    - Project-level configuration file discovery
    - Configuration merging and precedence
"""

import os
import tempfile
import unittest
from unittest.mock import patch

from ccai.testbase.configuration import (
    EntryPointConfiguration,
    find_user_config_file,
    find_project_config_file,
    load_user_configuration,
    load_project_configuration,
    load_entrypoint_configuration,
    _load_yaml_file,
    _parse_config_dict,
    CONFIG_FILE_NAMES,
    USER_CONFIG_DIR,
    USER_CONFIG_FILE_NAMES,
)


class TestEntryPointConfiguration(unittest.TestCase):
    """Tests for the EntryPointConfiguration class."""

    def test_init_creates_empty_configuration(self):
        """Test that initialization creates an empty configuration."""
        config = EntryPointConfiguration()
        
        self.assertEqual(config.includes, [])
        self.assertEqual(config.excludes, [])
        self.assertIsNone(config.console_level)
        self.assertIsNone(config.logfile_level)

    def test_merge_overwrites_includes_when_other_has_values(self):
        """Test that merge overwrites includes when other has values."""
        config1 = EntryPointConfiguration()
        config1.includes = ["test_*"]
        
        config2 = EntryPointConfiguration()
        config2.includes = ["test_unit_*", "test_integration_*"]
        
        config1.merge(config2)
        
        self.assertEqual(config1.includes, ["test_unit_*", "test_integration_*"])

    def test_merge_preserves_includes_when_other_is_empty(self):
        """Test that merge preserves includes when other is empty."""
        config1 = EntryPointConfiguration()
        config1.includes = ["test_*"]
        
        config2 = EntryPointConfiguration()
        
        config1.merge(config2)
        
        self.assertEqual(config1.includes, ["test_*"])

    def test_merge_overwrites_excludes_when_other_has_values(self):
        """Test that merge overwrites excludes when other has values."""
        config1 = EntryPointConfiguration()
        config1.excludes = ["test_slow_*"]
        
        config2 = EntryPointConfiguration()
        config2.excludes = ["test_flaky_*"]
        
        config1.merge(config2)
        
        self.assertEqual(config1.excludes, ["test_flaky_*"])

    def test_merge_overwrites_console_level_when_other_has_value(self):
        """Test that merge overwrites console_level when other has value."""
        config1 = EntryPointConfiguration()
        config1.console_level = "INFO"
        
        config2 = EntryPointConfiguration()
        config2.console_level = "DEBUG"
        
        config1.merge(config2)
        
        self.assertEqual(config1.console_level, "DEBUG")

    def test_merge_preserves_console_level_when_other_is_none(self):
        """Test that merge preserves console_level when other is None."""
        config1 = EntryPointConfiguration()
        config1.console_level = "INFO"
        
        config2 = EntryPointConfiguration()
        
        config1.merge(config2)
        
        self.assertEqual(config1.console_level, "INFO")

    def test_repr_returns_readable_string(self):
        """Test that __repr__ returns a readable string."""
        config = EntryPointConfiguration()
        config.includes = ["test_*"]
        config.console_level = "DEBUG"
        
        repr_str = repr(config)
        
        self.assertIn("EntryPointConfiguration", repr_str)
        self.assertIn("test_*", repr_str)
        self.assertIn("DEBUG", repr_str)


class TestParseConfigDict(unittest.TestCase):
    """Tests for the _parse_config_dict function."""

    def test_parse_includes_as_list(self):
        """Test parsing includes as a list."""
        config_dict = {"includes": ["test_unit_*", "test_integration_*"]}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.includes, ["test_unit_*", "test_integration_*"])

    def test_parse_includes_as_string(self):
        """Test parsing includes as a single string."""
        config_dict = {"includes": "test_*"}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.includes, ["test_*"])

    def test_parse_excludes_as_list(self):
        """Test parsing excludes as a list."""
        config_dict = {"excludes": ["test_slow_*", "test_flaky_*"]}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.excludes, ["test_slow_*", "test_flaky_*"])

    def test_parse_excludes_as_string(self):
        """Test parsing excludes as a single string."""
        config_dict = {"excludes": "test_slow_*"}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.excludes, ["test_slow_*"])

    def test_parse_console_level(self):
        """Test parsing console_level."""
        config_dict = {"console_level": "debug"}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.console_level, "DEBUG")

    def test_parse_logfile_level(self):
        """Test parsing logfile_level."""
        config_dict = {"logfile_level": "warning"}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.logfile_level, "WARNING")

    def test_parse_empty_dict(self):
        """Test parsing an empty dictionary."""
        config_dict = {}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.includes, [])
        self.assertEqual(config.excludes, [])
        self.assertIsNone(config.console_level)
        self.assertIsNone(config.logfile_level)

    def test_parse_filters_none_values_from_lists(self):
        """Test that None values are filtered from lists."""
        config_dict = {"includes": ["test_*", None, "test_unit_*"]}
        
        config = _parse_config_dict(config_dict)
        
        self.assertEqual(config.includes, ["test_*", "test_unit_*"])


class TestFindUserConfigFile(unittest.TestCase):
    """Tests for the find_user_config_file function."""

    def test_find_user_config_file_returns_none_when_dir_not_exists(self):
        """Test that None is returned when config directory doesn't exist."""
        with patch('os.path.expanduser') as mock_expanduser:
            mock_expanduser.return_value = "/nonexistent/home"
            
            result = find_user_config_file()
            
            self.assertIsNone(result)

    def test_find_user_config_file_finds_yaml_file(self):
        """Test finding testbase.yaml in user config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, USER_CONFIG_DIR)
            os.makedirs(config_dir)
            config_file = os.path.join(config_dir, "testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("includes:\n  - test_*\n")
            
            with patch('os.path.expanduser', return_value=tmpdir):
                result = find_user_config_file()
            
            self.assertEqual(result, config_file)

    def test_find_user_config_file_finds_yml_file(self):
        """Test finding testbase.yml in user config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, USER_CONFIG_DIR)
            os.makedirs(config_dir)
            config_file = os.path.join(config_dir, "testbase.yml")
            with open(config_file, 'w') as f:
                f.write("includes:\n  - test_*\n")
            
            with patch('os.path.expanduser', return_value=tmpdir):
                result = find_user_config_file()
            
            self.assertEqual(result, config_file)


class TestFindProjectConfigFile(unittest.TestCase):
    """Tests for the find_project_config_file function."""

    def test_find_project_config_file_in_current_dir(self):
        """Test finding config file in current directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, ".testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("includes:\n  - test_*\n")
            
            result = find_project_config_file(tmpdir)
            
            self.assertEqual(result, config_file)

    def test_find_project_config_file_in_parent_dir(self):
        """Test finding config file in parent directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            config_file = os.path.join(tmpdir, ".testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("includes:\n  - test_*\n")
            
            result = find_project_config_file(subdir)
            
            self.assertEqual(result, config_file)

    def test_find_project_config_file_returns_none_when_not_found(self):
        """Test that None is returned when no config file is found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = find_project_config_file(tmpdir)
            
            self.assertIsNone(result)

    def test_find_project_config_file_prefers_yaml_over_yml(self):
        """Test that .testbase.yaml is preferred over .testbase.yml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yaml_file = os.path.join(tmpdir, ".testbase.yaml")
            yml_file = os.path.join(tmpdir, ".testbase.yml")
            with open(yaml_file, 'w') as f:
                f.write("includes:\n  - test_yaml_*\n")
            with open(yml_file, 'w') as f:
                f.write("includes:\n  - test_yml_*\n")
            
            result = find_project_config_file(tmpdir)
            
            self.assertEqual(result, yaml_file)


class TestLoadYamlFile(unittest.TestCase):
    """Tests for the _load_yaml_file function."""

    def test_load_yaml_file_returns_dict(self):
        """Test loading a valid YAML file returns a dictionary."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("includes:\n  - test_*\nconsole_level: DEBUG\n")
            f.flush()
            
            try:
                result = _load_yaml_file(f.name)
                
                self.assertIsInstance(result, dict)
                self.assertEqual(result["includes"], ["test_*"])
                self.assertEqual(result["console_level"], "DEBUG")
            finally:
                os.unlink(f.name)

    def test_load_yaml_file_returns_none_for_nonexistent_file(self):
        """Test that None is returned for nonexistent file."""
        result = _load_yaml_file("/nonexistent/file.yaml")
        
        self.assertIsNone(result)

    def test_load_yaml_file_returns_none_for_invalid_yaml(self):
        """Test that None is returned for invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            try:
                result = _load_yaml_file(f.name)
                
                self.assertIsNone(result)
            finally:
                os.unlink(f.name)


class TestLoadEntrypointConfiguration(unittest.TestCase):
    """Tests for the load_entrypoint_configuration function."""

    def test_load_entrypoint_configuration_merges_user_and_project(self):
        """Test that user and project configurations are merged."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create user config
            user_config_dir = os.path.join(tmpdir, "home", USER_CONFIG_DIR)
            os.makedirs(user_config_dir)
            user_config_file = os.path.join(user_config_dir, "testbase.yaml")
            with open(user_config_file, 'w') as f:
                f.write("includes:\n  - test_user_*\nconsole_level: INFO\n")
            
            # Create project config
            project_dir = os.path.join(tmpdir, "project")
            os.makedirs(project_dir)
            project_config_file = os.path.join(project_dir, ".testbase.yaml")
            with open(project_config_file, 'w') as f:
                f.write("includes:\n  - test_project_*\n")
            
            with patch('os.path.expanduser', return_value=os.path.join(tmpdir, "home")):
                config = load_entrypoint_configuration(project_dir)
            
            # Project config should override user config for includes
            self.assertEqual(config.includes, ["test_project_*"])
            # User config console_level should be preserved
            self.assertEqual(config.console_level, "INFO")

    def test_load_entrypoint_configuration_returns_empty_when_no_files(self):
        """Test that empty configuration is returned when no files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch('os.path.expanduser', return_value=os.path.join(tmpdir, "nonexistent")):
                config = load_entrypoint_configuration(tmpdir)
            
            self.assertEqual(config.includes, [])
            self.assertEqual(config.excludes, [])
            self.assertIsNone(config.console_level)
            self.assertIsNone(config.logfile_level)


if __name__ == '__main__':
    unittest.main()



class TestConfigurationIntegrationWithEntrypoint(unittest.TestCase):
    """Tests for configuration file integration with the entry point."""

    def test_configuration_loaded_before_argument_parsing(self):
        """Test that configuration is loaded and available for argument defaults."""
        from ccai.testbase.configuration import load_entrypoint_configuration
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, ".testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("console_level: WARNING\nlogfile_level: ERROR\n")
            
            config = load_entrypoint_configuration(tmpdir)
            
            self.assertEqual(config.console_level, "WARNING")
            self.assertEqual(config.logfile_level, "ERROR")

    def test_configuration_includes_used_when_no_cli_includes(self):
        """Test that configuration file includes are used when no CLI includes provided."""
        from ccai.testbase.configuration import load_entrypoint_configuration
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, ".testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("includes:\n  - test_unit_*\n  - test_integration_*\n")
            
            config = load_entrypoint_configuration(tmpdir)
            
            self.assertEqual(config.includes, ["test_unit_*", "test_integration_*"])

    def test_configuration_excludes_used_when_no_cli_excludes(self):
        """Test that configuration file excludes are used when no CLI excludes provided."""
        from ccai.testbase.configuration import load_entrypoint_configuration
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, ".testbase.yaml")
            with open(config_file, 'w') as f:
                f.write("excludes:\n  - test_slow_*\n  - test_flaky_*\n")
            
            config = load_entrypoint_configuration(tmpdir)
            
            self.assertEqual(config.excludes, ["test_slow_*", "test_flaky_*"])

    def test_project_config_overrides_user_config(self):
        """Test that project-level config overrides user-level config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create user config
            user_config_dir = os.path.join(tmpdir, "home", USER_CONFIG_DIR)
            os.makedirs(user_config_dir)
            user_config_file = os.path.join(user_config_dir, "testbase.yaml")
            with open(user_config_file, 'w') as f:
                f.write("console_level: DEBUG\nlogfile_level: DEBUG\n")
            
            # Create project config with different values
            project_dir = os.path.join(tmpdir, "project")
            os.makedirs(project_dir)
            project_config_file = os.path.join(project_dir, ".testbase.yaml")
            with open(project_config_file, 'w') as f:
                f.write("console_level: WARNING\n")
            
            with patch('os.path.expanduser', return_value=os.path.join(tmpdir, "home")):
                config = load_entrypoint_configuration(project_dir)
            
            # Project config should override user config for console_level
            self.assertEqual(config.console_level, "WARNING")
            # User config logfile_level should be preserved
            self.assertEqual(config.logfile_level, "DEBUG")

    def test_yaml_not_available_returns_empty_config(self):
        """Test that empty configuration is returned when YAML is not available."""
        from ccai.testbase import configuration
        
        # Save original YAML_AVAILABLE value
        original_yaml_available = configuration.YAML_AVAILABLE
        
        try:
            # Simulate YAML not being available
            configuration.YAML_AVAILABLE = False
            
            with tempfile.TemporaryDirectory() as tmpdir:
                config_file = os.path.join(tmpdir, ".testbase.yaml")
                with open(config_file, 'w') as f:
                    f.write("console_level: DEBUG\n")
                
                config = load_entrypoint_configuration(tmpdir)
                
                # Should return empty config when YAML is not available
                self.assertEqual(config.includes, [])
                self.assertIsNone(config.console_level)
        finally:
            # Restore original value
            configuration.YAML_AVAILABLE = original_yaml_available
