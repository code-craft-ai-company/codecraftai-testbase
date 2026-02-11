"""
    .. module:: automojo.testbase.cli.options
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for reusable CLI option groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.arcli.model.optiongroup import OptionGroup
from automojo.arcli.model.fields.optionfield import OptionField, OptionMode
from automojo.arcli.model.parameters.validators import Choice
from automojo.arcli.model.parameters.booleanparameter import BooleanParameter
from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES

HELP_ROOT = "The root directory to use when scanning for tests to {action}."
HELP_EXCLUDES = "Add a test exclusion expression for the {action}."
HELP_INCLUDES = "Add a test inclusion expression for the {action}."
HELP_OUTPUT = "The output directory where results and artifacts are collected."
HELP_START = r"A time stamp to associate with the start of the run. Example: 2020-10-17T15:30:11.989120  Bash: date +%Y-%m-%dT%H:%M:%S.%N"
HELP_BRANCH = "The name of the branch to associate with the test run results."
HELP_BUILD = "The name of the build to associate with the test run results."
HELP_FLAVOR = "The name of the flavor to associate with the test run results."
HELP_JOB_ID = "A unique identifier for the job with respect to the job runner."
HELP_JOB_INITIATOR = "The name of the initiator of the job."
HELP_JOB_LABEL = "The label associated with the job."
HELP_JOB_NAME = "The name of the job."
HELP_JOB_OWNER = "The ownerid and possibly appended ';(display name)' of the test run result owner."
HELP_RUNID = "A uuid to use for the run id for the testrun."
HELP_CONSOLE_LOG_LEVEL = "The logging level for console output."
HELP_FILE_LOG_LEVEL = "The logging level for logfile output."
HELP_DEBUG = "Output debug information to the console."
HELP_DEBUGGER = "Debugger to active during the test run."
HELP_BREAKPOINT = "The breakpoint to activate for the test run."
HELP_PRERUN_DIAGNOSTIC = "Flag indicating that a pre run diagnostic should be performed."
HELP_POSTRUN_DIAGNOSTIC = "Flag indicating that a post run diagnostic should be performed."
HELP_INCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will include a test."
HELP_EXCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will exclude a test."
HELP_FILTER = "Add a job filter expression."
HELP_JOB = "The identifier of the job to {action}."

class RootOptionGroup(OptionGroup):
    name = "root"
    root = OptionField("--root", default=None, required=False, help=HELP_ROOT)

class OutputOptionGroup(OptionGroup):
    name = "output"
    output = OptionField("-o", "--output", default=None, required=False, help=HELP_OUTPUT)
    start = OptionField("--start", default=None, required=False, help=HELP_START)
    runid = OptionField("--runid", default=None, required=False, help=HELP_RUNID)

class BuildOptionGroup(OptionGroup):
    name = "build"
    branch = OptionField("--branch", default=None, required=False, help=HELP_BRANCH)
    build = OptionField("--build", default=None, required=False, help=HELP_BUILD)
    flavor = OptionField("--flavor", default=None, required=False, help=HELP_FLAVOR)

class JobOptionGroup(OptionGroup):
    name = "job"
    job_id = OptionField("--job-id", default=None, required=False, help=HELP_JOB_ID)
    job_initiator = OptionField("--job-initiator", default=None, required=False, help=HELP_JOB_INITIATOR)
    job_label = OptionField("--job-label", default=None, required=False, help=HELP_JOB_LABEL)
    job_name = OptionField("--job-name", default=None, required=False, help=HELP_JOB_NAME)
    job_owner = OptionField("--job-owner", default=None, required=False, help=HELP_JOB_OWNER)

class LoggingOptionGroup(OptionGroup):
    name = "logging"
    console_level = OptionField("--console-level", default=None, required=False,
                              ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_CONSOLE_LOG_LEVEL)
    logfile_level = OptionField("--logfile-level", default=None, required=False,
                              ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_FILE_LOG_LEVEL)

class DiagnosticOptionGroup(OptionGroup):
    name = "diagnostic"
    debugger = OptionField("--debugger", default=None, required=False,
                         ptype=Choice(['pdb', 'debugpy']), help=HELP_DEBUGGER)
    breakpoints = OptionField("--breakpoint", alias="breakpoints", default=None, required=False,
                            mode=OptionMode.Multiple, ptype=Choice(['test-discovery', 'testrun-start']), help=HELP_BREAKPOINT)
    prerun_diagnostic = OptionField("--prerun-diagnostic", default=False, required=False, ptype=BooleanParameter, help=HELP_PRERUN_DIAGNOSTIC)
    postrun_diagnostic = OptionField("--postrun-diagnostic", default=False, required=False, ptype=BooleanParameter, help=HELP_POSTRUN_DIAGNOSTIC)

class FilteringOptionGroup(OptionGroup):
    name = "filtering"
    includes = OptionField("-i", "--includes", default=None, required=False, mode=OptionMode.Multiple, help=HELP_INCLUDES)
    excludes = OptionField("-x", "--excludes", default=None, required=False, mode=OptionMode.Multiple, help=HELP_EXCLUDES)
    include_marker_exp = OptionField("--include-marker-exp", default=None, required=False, mode=OptionMode.Multiple, help=HELP_INCLUDE_MARKER_EXP)
    exclude_marker_exp = OptionField("--exclude-marker-exp", default=None, required=False, mode=OptionMode.Multiple, help=HELP_EXCLUDE_MARKER_EXP)

class DebugOptionGroup(OptionGroup):
    name = "debug"
    debug = OptionField("--debug", default=False, ptype=BooleanParameter, help=HELP_DEBUG)
