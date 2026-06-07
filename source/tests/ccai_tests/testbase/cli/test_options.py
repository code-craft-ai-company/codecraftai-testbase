"""
    .. module:: ccai_tests.testbase.cli.test_options
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Unit tests for CLI option groups.

    .. moduleauthor:: CodeCraftX

    Tests for the reusable CLI option groups defined in ccai.testbase.cli.options.
    These tests verify the field definitions for each option group as specified in
    Requirements 18.1-18.8.
"""

__author__ = "CodeCraftX"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

import unittest

from ccai.testbase.cli.options import (
    RootOptionGroup,
    OutputOptionGroup,
    BuildOptionGroup,
    JobOptionGroup,
    LoggingOptionGroup,
    DiagnosticOptionGroup,
    FilteringOptionGroup,
    DebugOptionGroup,
    HELP_ROOT,
    HELP_OUTPUT,
    HELP_START,
    HELP_RUNID,
    HELP_BRANCH,
    HELP_BUILD,
    HELP_FLAVOR,
    HELP_JOB_ID,
    HELP_JOB_INITIATOR,
    HELP_JOB_LABEL,
    HELP_JOB_NAME,
    HELP_JOB_OWNER,
    HELP_CONSOLE_LOG_LEVEL,
    HELP_FILE_LOG_LEVEL,
    HELP_DEBUGGER,
    HELP_BREAKPOINT,
    HELP_PRERUN_DIAGNOSTIC,
    HELP_POSTRUN_DIAGNOSTIC,
    HELP_INCLUDES,
    HELP_EXCLUDES,
    HELP_INCLUDE_MARKER_EXP,
    HELP_EXCLUDE_MARKER_EXP,
    HELP_DEBUG,
)
from ccai.arcli.model.optiongroup import OptionGroup
from ccai.arcli.model.fields.optionfield import OptionField, OptionMode
from ccai.arcli.model.parameters.booleanparameter import BooleanParameter


class RootOptionGroupTests(unittest.TestCase):
    """Tests for RootOptionGroup field definitions (Requirement 18.1)."""

    def test_inherits_from_option_group(self):
        """Test RootOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(RootOptionGroup, OptionGroup))

    def test_group_name_is_root(self):
        """Test RootOptionGroup has name 'root'."""
        self.assertEqual(RootOptionGroup.name, "root")

    def test_root_field_exists(self):
        """Test RootOptionGroup has 'root' field."""
        self.assertTrue(hasattr(RootOptionGroup, 'root'))
        self.assertIsInstance(RootOptionGroup.root, OptionField)

    def test_root_field_flag_long(self):
        """Test root field has correct long flag."""
        self.assertEqual(RootOptionGroup.root.flag_long, "--root")

    def test_root_field_default_is_none(self):
        """Test root field default value is None."""
        self.assertIsNone(RootOptionGroup.root.default)

    def test_root_field_is_not_required(self):
        """Test root field is not required."""
        self.assertFalse(RootOptionGroup.root.required)

    def test_root_field_help_text(self):
        """Test root field has correct help text."""
        self.assertEqual(RootOptionGroup.root.help, HELP_ROOT)


class OutputOptionGroupTests(unittest.TestCase):
    """Tests for OutputOptionGroup field definitions (Requirement 18.2)."""

    def test_inherits_from_option_group(self):
        """Test OutputOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(OutputOptionGroup, OptionGroup))

    def test_group_name_is_output(self):
        """Test OutputOptionGroup has name 'output'."""
        self.assertEqual(OutputOptionGroup.name, "output")

    def test_output_field_exists(self):
        """Test OutputOptionGroup has 'output' field."""
        self.assertTrue(hasattr(OutputOptionGroup, 'output'))
        self.assertIsInstance(OutputOptionGroup.output, OptionField)

    def test_output_field_flag_short(self):
        """Test output field has short flag '-o'."""
        self.assertEqual(OutputOptionGroup.output.flag_short, "-o")

    def test_output_field_flag_long(self):
        """Test output field has correct long flag."""
        self.assertEqual(OutputOptionGroup.output.flag_long, "--output")

    def test_output_field_default_is_none(self):
        """Test output field default value is None."""
        self.assertIsNone(OutputOptionGroup.output.default)

    def test_output_field_help_text(self):
        """Test output field has correct help text."""
        self.assertEqual(OutputOptionGroup.output.help, HELP_OUTPUT)

    def test_start_field_exists(self):
        """Test OutputOptionGroup has 'start' field."""
        self.assertTrue(hasattr(OutputOptionGroup, 'start'))
        self.assertIsInstance(OutputOptionGroup.start, OptionField)

    def test_start_field_flag_long(self):
        """Test start field has correct long flag."""
        self.assertEqual(OutputOptionGroup.start.flag_long, "--start")

    def test_start_field_default_is_none(self):
        """Test start field default value is None."""
        self.assertIsNone(OutputOptionGroup.start.default)

    def test_start_field_help_text(self):
        """Test start field has correct help text."""
        self.assertEqual(OutputOptionGroup.start.help, HELP_START)

    def test_runid_field_exists(self):
        """Test OutputOptionGroup has 'runid' field."""
        self.assertTrue(hasattr(OutputOptionGroup, 'runid'))
        self.assertIsInstance(OutputOptionGroup.runid, OptionField)

    def test_runid_field_flag_long(self):
        """Test runid field has correct long flag."""
        self.assertEqual(OutputOptionGroup.runid.flag_long, "--runid")

    def test_runid_field_default_is_none(self):
        """Test runid field default value is None."""
        self.assertIsNone(OutputOptionGroup.runid.default)

    def test_runid_field_help_text(self):
        """Test runid field has correct help text."""
        self.assertEqual(OutputOptionGroup.runid.help, HELP_RUNID)


class BuildOptionGroupTests(unittest.TestCase):
    """Tests for BuildOptionGroup field definitions (Requirement 18.3)."""

    def test_inherits_from_option_group(self):
        """Test BuildOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(BuildOptionGroup, OptionGroup))

    def test_group_name_is_build(self):
        """Test BuildOptionGroup has name 'build'."""
        self.assertEqual(BuildOptionGroup.name, "build")

    def test_branch_field_exists(self):
        """Test BuildOptionGroup has 'branch' field."""
        self.assertTrue(hasattr(BuildOptionGroup, 'branch'))
        self.assertIsInstance(BuildOptionGroup.branch, OptionField)

    def test_branch_field_flag_long(self):
        """Test branch field has correct long flag."""
        self.assertEqual(BuildOptionGroup.branch.flag_long, "--branch")

    def test_branch_field_default_is_none(self):
        """Test branch field default value is None."""
        self.assertIsNone(BuildOptionGroup.branch.default)

    def test_branch_field_help_text(self):
        """Test branch field has correct help text."""
        self.assertEqual(BuildOptionGroup.branch.help, HELP_BRANCH)

    def test_build_field_exists(self):
        """Test BuildOptionGroup has 'build' field."""
        self.assertTrue(hasattr(BuildOptionGroup, 'build'))
        self.assertIsInstance(BuildOptionGroup.build, OptionField)

    def test_build_field_flag_long(self):
        """Test build field has correct long flag."""
        self.assertEqual(BuildOptionGroup.build.flag_long, "--build")

    def test_build_field_default_is_none(self):
        """Test build field default value is None."""
        self.assertIsNone(BuildOptionGroup.build.default)

    def test_build_field_help_text(self):
        """Test build field has correct help text."""
        self.assertEqual(BuildOptionGroup.build.help, HELP_BUILD)

    def test_flavor_field_exists(self):
        """Test BuildOptionGroup has 'flavor' field."""
        self.assertTrue(hasattr(BuildOptionGroup, 'flavor'))
        self.assertIsInstance(BuildOptionGroup.flavor, OptionField)

    def test_flavor_field_flag_long(self):
        """Test flavor field has correct long flag."""
        self.assertEqual(BuildOptionGroup.flavor.flag_long, "--flavor")

    def test_flavor_field_default_is_none(self):
        """Test flavor field default value is None."""
        self.assertIsNone(BuildOptionGroup.flavor.default)

    def test_flavor_field_help_text(self):
        """Test flavor field has correct help text."""
        self.assertEqual(BuildOptionGroup.flavor.help, HELP_FLAVOR)


class JobOptionGroupTests(unittest.TestCase):
    """Tests for JobOptionGroup field definitions (Requirement 18.4)."""

    def test_inherits_from_option_group(self):
        """Test JobOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(JobOptionGroup, OptionGroup))

    def test_group_name_is_job(self):
        """Test JobOptionGroup has name 'job'."""
        self.assertEqual(JobOptionGroup.name, "job")

    def test_job_id_field_exists(self):
        """Test JobOptionGroup has 'job_id' field."""
        self.assertTrue(hasattr(JobOptionGroup, 'job_id'))
        self.assertIsInstance(JobOptionGroup.job_id, OptionField)

    def test_job_id_field_flag_long(self):
        """Test job_id field has correct long flag."""
        self.assertEqual(JobOptionGroup.job_id.flag_long, "--job-id")

    def test_job_id_field_default_is_none(self):
        """Test job_id field default value is None."""
        self.assertIsNone(JobOptionGroup.job_id.default)

    def test_job_id_field_help_text(self):
        """Test job_id field has correct help text."""
        self.assertEqual(JobOptionGroup.job_id.help, HELP_JOB_ID)

    def test_job_initiator_field_exists(self):
        """Test JobOptionGroup has 'job_initiator' field."""
        self.assertTrue(hasattr(JobOptionGroup, 'job_initiator'))
        self.assertIsInstance(JobOptionGroup.job_initiator, OptionField)

    def test_job_initiator_field_flag_long(self):
        """Test job_initiator field has correct long flag."""
        self.assertEqual(JobOptionGroup.job_initiator.flag_long, "--job-initiator")

    def test_job_initiator_field_help_text(self):
        """Test job_initiator field has correct help text."""
        self.assertEqual(JobOptionGroup.job_initiator.help, HELP_JOB_INITIATOR)

    def test_job_label_field_exists(self):
        """Test JobOptionGroup has 'job_label' field."""
        self.assertTrue(hasattr(JobOptionGroup, 'job_label'))
        self.assertIsInstance(JobOptionGroup.job_label, OptionField)

    def test_job_label_field_flag_long(self):
        """Test job_label field has correct long flag."""
        self.assertEqual(JobOptionGroup.job_label.flag_long, "--job-label")

    def test_job_label_field_help_text(self):
        """Test job_label field has correct help text."""
        self.assertEqual(JobOptionGroup.job_label.help, HELP_JOB_LABEL)

    def test_job_name_field_exists(self):
        """Test JobOptionGroup has 'job_name' field."""
        self.assertTrue(hasattr(JobOptionGroup, 'job_name'))
        self.assertIsInstance(JobOptionGroup.job_name, OptionField)

    def test_job_name_field_flag_long(self):
        """Test job_name field has correct long flag."""
        self.assertEqual(JobOptionGroup.job_name.flag_long, "--job-name")

    def test_job_name_field_help_text(self):
        """Test job_name field has correct help text."""
        self.assertEqual(JobOptionGroup.job_name.help, HELP_JOB_NAME)

    def test_job_owner_field_exists(self):
        """Test JobOptionGroup has 'job_owner' field."""
        self.assertTrue(hasattr(JobOptionGroup, 'job_owner'))
        self.assertIsInstance(JobOptionGroup.job_owner, OptionField)

    def test_job_owner_field_flag_long(self):
        """Test job_owner field has correct long flag."""
        self.assertEqual(JobOptionGroup.job_owner.flag_long, "--job-owner")

    def test_job_owner_field_help_text(self):
        """Test job_owner field has correct help text."""
        self.assertEqual(JobOptionGroup.job_owner.help, HELP_JOB_OWNER)


class LoggingOptionGroupTests(unittest.TestCase):
    """Tests for LoggingOptionGroup field definitions (Requirement 18.5)."""

    def test_inherits_from_option_group(self):
        """Test LoggingOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(LoggingOptionGroup, OptionGroup))

    def test_group_name_is_logging(self):
        """Test LoggingOptionGroup has name 'logging'."""
        self.assertEqual(LoggingOptionGroup.name, "logging")

    def test_console_level_field_exists(self):
        """Test LoggingOptionGroup has 'console_level' field."""
        self.assertTrue(hasattr(LoggingOptionGroup, 'console_level'))
        self.assertIsInstance(LoggingOptionGroup.console_level, OptionField)

    def test_console_level_field_flag_long(self):
        """Test console_level field has correct long flag."""
        self.assertEqual(LoggingOptionGroup.console_level.flag_long, "--console-level")

    def test_console_level_field_default_is_none(self):
        """Test console_level field default value is None."""
        self.assertIsNone(LoggingOptionGroup.console_level.default)

    def test_console_level_field_has_choice_ptype(self):
        """Test console_level field has Choice ptype with _choices attribute."""
        self.assertTrue(hasattr(LoggingOptionGroup.console_level.ptype, '_choices'))

    def test_console_level_field_help_text(self):
        """Test console_level field has correct help text."""
        self.assertEqual(LoggingOptionGroup.console_level.help, HELP_CONSOLE_LOG_LEVEL)

    def test_logfile_level_field_exists(self):
        """Test LoggingOptionGroup has 'logfile_level' field."""
        self.assertTrue(hasattr(LoggingOptionGroup, 'logfile_level'))
        self.assertIsInstance(LoggingOptionGroup.logfile_level, OptionField)

    def test_logfile_level_field_flag_long(self):
        """Test logfile_level field has correct long flag."""
        self.assertEqual(LoggingOptionGroup.logfile_level.flag_long, "--logfile-level")

    def test_logfile_level_field_default_is_none(self):
        """Test logfile_level field default value is None."""
        self.assertIsNone(LoggingOptionGroup.logfile_level.default)

    def test_logfile_level_field_has_choice_ptype(self):
        """Test logfile_level field has Choice ptype with _choices attribute."""
        self.assertTrue(hasattr(LoggingOptionGroup.logfile_level.ptype, '_choices'))

    def test_logfile_level_field_help_text(self):
        """Test logfile_level field has correct help text."""
        self.assertEqual(LoggingOptionGroup.logfile_level.help, HELP_FILE_LOG_LEVEL)


class DiagnosticOptionGroupTests(unittest.TestCase):
    """Tests for DiagnosticOptionGroup field definitions (Requirement 18.6)."""

    def test_inherits_from_option_group(self):
        """Test DiagnosticOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(DiagnosticOptionGroup, OptionGroup))

    def test_group_name_is_diagnostic(self):
        """Test DiagnosticOptionGroup has name 'diagnostic'."""
        self.assertEqual(DiagnosticOptionGroup.name, "diagnostic")

    def test_debugger_field_exists(self):
        """Test DiagnosticOptionGroup has 'debugger' field."""
        self.assertTrue(hasattr(DiagnosticOptionGroup, 'debugger'))
        self.assertIsInstance(DiagnosticOptionGroup.debugger, OptionField)

    def test_debugger_field_flag_long(self):
        """Test debugger field has correct long flag."""
        self.assertEqual(DiagnosticOptionGroup.debugger.flag_long, "--debugger")

    def test_debugger_field_default_is_none(self):
        """Test debugger field default value is None."""
        self.assertIsNone(DiagnosticOptionGroup.debugger.default)

    def test_debugger_field_has_choice_ptype_with_pdb_and_debugpy(self):
        """Test debugger field has Choice ptype with pdb and debugpy choices."""
        self.assertTrue(hasattr(DiagnosticOptionGroup.debugger.ptype, '_choices'))
        self.assertIn('pdb', DiagnosticOptionGroup.debugger.ptype._choices)
        self.assertIn('debugpy', DiagnosticOptionGroup.debugger.ptype._choices)

    def test_debugger_field_help_text(self):
        """Test debugger field has correct help text."""
        self.assertEqual(DiagnosticOptionGroup.debugger.help, HELP_DEBUGGER)

    def test_breakpoints_field_exists(self):
        """Test DiagnosticOptionGroup has 'breakpoints' field."""
        self.assertTrue(hasattr(DiagnosticOptionGroup, 'breakpoints'))
        self.assertIsInstance(DiagnosticOptionGroup.breakpoints, OptionField)

    def test_breakpoints_field_flag_long(self):
        """Test breakpoints field has correct long flag."""
        self.assertEqual(DiagnosticOptionGroup.breakpoints.flag_long, "--breakpoint")

    def test_breakpoints_field_has_multiple_mode(self):
        """Test breakpoints field has Multiple mode."""
        self.assertEqual(DiagnosticOptionGroup.breakpoints.mode, OptionMode.Multiple)

    def test_breakpoints_field_has_choice_ptype_with_correct_choices(self):
        """Test breakpoints field has Choice ptype with test-discovery and testrun-start."""
        self.assertTrue(hasattr(DiagnosticOptionGroup.breakpoints.ptype, '_choices'))
        self.assertIn('test-discovery', DiagnosticOptionGroup.breakpoints.ptype._choices)
        self.assertIn('testrun-start', DiagnosticOptionGroup.breakpoints.ptype._choices)

    def test_breakpoints_field_help_text(self):
        """Test breakpoints field has correct help text."""
        self.assertEqual(DiagnosticOptionGroup.breakpoints.help, HELP_BREAKPOINT)

    def test_breakpoints_field_default_is_none(self):
        """Test breakpoints field default value is None when not specified."""
        self.assertIsNone(DiagnosticOptionGroup.breakpoints.default)

    def test_breakpoints_field_is_not_required(self):
        """Test breakpoints field is not required."""
        self.assertFalse(DiagnosticOptionGroup.breakpoints.required)

    def test_debugger_field_is_not_required(self):
        """Test debugger field is not required."""
        self.assertFalse(DiagnosticOptionGroup.debugger.required)

    def test_debugger_field_choices_are_exactly_pdb_and_debugpy(self):
        """Test debugger field choices are exactly 'pdb' and 'debugpy'."""
        choices = DiagnosticOptionGroup.debugger.ptype._choices
        self.assertEqual(len(choices), 2)
        self.assertIn('pdb', choices)
        self.assertIn('debugpy', choices)

    def test_breakpoints_field_choices_are_exactly_test_discovery_and_testrun_start(self):
        """Test breakpoints field choices are exactly 'test-discovery' and 'testrun-start'."""
        choices = DiagnosticOptionGroup.breakpoints.ptype._choices
        self.assertEqual(len(choices), 2)
        self.assertIn('test-discovery', choices)
        self.assertIn('testrun-start', choices)

    def test_prerun_diagnostic_field_exists(self):
        """Test DiagnosticOptionGroup has 'prerun_diagnostic' field."""
        self.assertTrue(hasattr(DiagnosticOptionGroup, 'prerun_diagnostic'))
        self.assertIsInstance(DiagnosticOptionGroup.prerun_diagnostic, OptionField)

    def test_prerun_diagnostic_field_flag_long(self):
        """Test prerun_diagnostic field has correct long flag."""
        self.assertEqual(DiagnosticOptionGroup.prerun_diagnostic.flag_long, "--prerun-diagnostic")

    def test_prerun_diagnostic_field_default_is_false(self):
        """Test prerun_diagnostic field default value is False."""
        self.assertFalse(DiagnosticOptionGroup.prerun_diagnostic.default)

    def test_prerun_diagnostic_field_has_boolean_ptype(self):
        """Test prerun_diagnostic field has BooleanParameter ptype."""
        self.assertEqual(DiagnosticOptionGroup.prerun_diagnostic.ptype, BooleanParameter)

    def test_prerun_diagnostic_field_help_text(self):
        """Test prerun_diagnostic field has correct help text."""
        self.assertEqual(DiagnosticOptionGroup.prerun_diagnostic.help, HELP_PRERUN_DIAGNOSTIC)

    def test_postrun_diagnostic_field_exists(self):
        """Test DiagnosticOptionGroup has 'postrun_diagnostic' field."""
        self.assertTrue(hasattr(DiagnosticOptionGroup, 'postrun_diagnostic'))
        self.assertIsInstance(DiagnosticOptionGroup.postrun_diagnostic, OptionField)

    def test_postrun_diagnostic_field_flag_long(self):
        """Test postrun_diagnostic field has correct long flag."""
        self.assertEqual(DiagnosticOptionGroup.postrun_diagnostic.flag_long, "--postrun-diagnostic")

    def test_postrun_diagnostic_field_default_is_false(self):
        """Test postrun_diagnostic field default value is False."""
        self.assertFalse(DiagnosticOptionGroup.postrun_diagnostic.default)

    def test_postrun_diagnostic_field_has_boolean_ptype(self):
        """Test postrun_diagnostic field has BooleanParameter ptype."""
        self.assertEqual(DiagnosticOptionGroup.postrun_diagnostic.ptype, BooleanParameter)

    def test_postrun_diagnostic_field_help_text(self):
        """Test postrun_diagnostic field has correct help text."""
        self.assertEqual(DiagnosticOptionGroup.postrun_diagnostic.help, HELP_POSTRUN_DIAGNOSTIC)


class FilteringOptionGroupTests(unittest.TestCase):
    """Tests for FilteringOptionGroup field definitions (Requirement 18.7)."""

    def test_inherits_from_option_group(self):
        """Test FilteringOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(FilteringOptionGroup, OptionGroup))

    def test_group_name_is_filtering(self):
        """Test FilteringOptionGroup has name 'filtering'."""
        self.assertEqual(FilteringOptionGroup.name, "filtering")

    def test_includes_field_exists(self):
        """Test FilteringOptionGroup has 'includes' field."""
        self.assertTrue(hasattr(FilteringOptionGroup, 'includes'))
        self.assertIsInstance(FilteringOptionGroup.includes, OptionField)

    def test_includes_field_flag_short(self):
        """Test includes field has short flag '-i'."""
        self.assertEqual(FilteringOptionGroup.includes.flag_short, "-i")

    def test_includes_field_flag_long(self):
        """Test includes field has correct long flag."""
        self.assertEqual(FilteringOptionGroup.includes.flag_long, "--includes")

    def test_includes_field_has_multiple_mode(self):
        """Test includes field has Multiple mode."""
        self.assertEqual(FilteringOptionGroup.includes.mode, OptionMode.Multiple)

    def test_includes_field_default_is_none(self):
        """Test includes field default value is None."""
        self.assertIsNone(FilteringOptionGroup.includes.default)

    def test_includes_field_help_text(self):
        """Test includes field has correct help text."""
        self.assertEqual(FilteringOptionGroup.includes.help, HELP_INCLUDES)

    def test_excludes_field_exists(self):
        """Test FilteringOptionGroup has 'excludes' field."""
        self.assertTrue(hasattr(FilteringOptionGroup, 'excludes'))
        self.assertIsInstance(FilteringOptionGroup.excludes, OptionField)

    def test_excludes_field_flag_short(self):
        """Test excludes field has short flag '-x'."""
        self.assertEqual(FilteringOptionGroup.excludes.flag_short, "-x")

    def test_excludes_field_flag_long(self):
        """Test excludes field has correct long flag."""
        self.assertEqual(FilteringOptionGroup.excludes.flag_long, "--excludes")

    def test_excludes_field_has_multiple_mode(self):
        """Test excludes field has Multiple mode."""
        self.assertEqual(FilteringOptionGroup.excludes.mode, OptionMode.Multiple)

    def test_excludes_field_default_is_none(self):
        """Test excludes field default value is None."""
        self.assertIsNone(FilteringOptionGroup.excludes.default)

    def test_excludes_field_help_text(self):
        """Test excludes field has correct help text."""
        self.assertEqual(FilteringOptionGroup.excludes.help, HELP_EXCLUDES)

    def test_include_marker_exp_field_exists(self):
        """Test FilteringOptionGroup has 'include_marker_exp' field."""
        self.assertTrue(hasattr(FilteringOptionGroup, 'include_marker_exp'))
        self.assertIsInstance(FilteringOptionGroup.include_marker_exp, OptionField)

    def test_include_marker_exp_field_flag_long(self):
        """Test include_marker_exp field has correct long flag."""
        self.assertEqual(FilteringOptionGroup.include_marker_exp.flag_long, "--include-marker-exp")

    def test_include_marker_exp_field_has_multiple_mode(self):
        """Test include_marker_exp field has Multiple mode."""
        self.assertEqual(FilteringOptionGroup.include_marker_exp.mode, OptionMode.Multiple)

    def test_include_marker_exp_field_default_is_none(self):
        """Test include_marker_exp field default value is None."""
        self.assertIsNone(FilteringOptionGroup.include_marker_exp.default)

    def test_include_marker_exp_field_help_text(self):
        """Test include_marker_exp field has correct help text."""
        self.assertEqual(FilteringOptionGroup.include_marker_exp.help, HELP_INCLUDE_MARKER_EXP)

    def test_exclude_marker_exp_field_exists(self):
        """Test FilteringOptionGroup has 'exclude_marker_exp' field."""
        self.assertTrue(hasattr(FilteringOptionGroup, 'exclude_marker_exp'))
        self.assertIsInstance(FilteringOptionGroup.exclude_marker_exp, OptionField)

    def test_exclude_marker_exp_field_flag_long(self):
        """Test exclude_marker_exp field has correct long flag."""
        self.assertEqual(FilteringOptionGroup.exclude_marker_exp.flag_long, "--exclude-marker-exp")

    def test_exclude_marker_exp_field_has_multiple_mode(self):
        """Test exclude_marker_exp field has Multiple mode."""
        self.assertEqual(FilteringOptionGroup.exclude_marker_exp.mode, OptionMode.Multiple)

    def test_exclude_marker_exp_field_default_is_none(self):
        """Test exclude_marker_exp field default value is None."""
        self.assertIsNone(FilteringOptionGroup.exclude_marker_exp.default)

    def test_exclude_marker_exp_field_help_text(self):
        """Test exclude_marker_exp field has correct help text."""
        self.assertEqual(FilteringOptionGroup.exclude_marker_exp.help, HELP_EXCLUDE_MARKER_EXP)


class DebugOptionGroupTests(unittest.TestCase):
    """Tests for DebugOptionGroup field definitions (Requirement 18.8)."""

    def test_inherits_from_option_group(self):
        """Test DebugOptionGroup inherits from OptionGroup."""
        self.assertTrue(issubclass(DebugOptionGroup, OptionGroup))

    def test_group_name_is_debug(self):
        """Test DebugOptionGroup has name 'debug'."""
        self.assertEqual(DebugOptionGroup.name, "debug")

    def test_debug_field_exists(self):
        """Test DebugOptionGroup has 'debug' field."""
        self.assertTrue(hasattr(DebugOptionGroup, 'debug'))
        self.assertIsInstance(DebugOptionGroup.debug, OptionField)

    def test_debug_field_flag_long(self):
        """Test debug field has correct long flag."""
        self.assertEqual(DebugOptionGroup.debug.flag_long, "--debug")

    def test_debug_field_default_is_false(self):
        """Test debug field default value is False."""
        self.assertFalse(DebugOptionGroup.debug.default)

    def test_debug_field_has_boolean_ptype(self):
        """Test debug field has BooleanParameter ptype."""
        self.assertEqual(DebugOptionGroup.debug.ptype, BooleanParameter)

    def test_debug_field_help_text(self):
        """Test debug field has correct help text."""
        self.assertEqual(DebugOptionGroup.debug.help, HELP_DEBUG)


if __name__ == '__main__':
    unittest.main()
