"""
    .. module:: ccai.testbase.cli.options
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for reusable CLI option groups.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

This module defines reusable CLI option groups for the TestBase framework.
Each option group encapsulates related command-line options that can be
composed into CLI commands.

The option groups include:

- **RootOptionGroup**: Options for specifying the test root directory
- **OutputOptionGroup**: Options for output directory and run identification
- **BuildOptionGroup**: Options for build metadata (branch, build, flavor)
- **JobOptionGroup**: Options for job identification and ownership
- **LoggingOptionGroup**: Options for console and file logging levels
- **DiagnosticOptionGroup**: Options for debugging and diagnostics
- **FilteringOptionGroup**: Options for test inclusion/exclusion filtering
- **DebugOptionGroup**: Options for debug output

Example Usage::

    from ccai.testbase.cli.options import DiagnosticOptionGroup, RootOptionGroup

    # Option groups are used in CLI command definitions
    # to compose related options together

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.arcli.model.optiongroup import OptionGroup
from ccai.arcli.model.fields.optionfield import OptionField, OptionMode
from ccai.arcli.model.parameters.validators import Choice
from ccai.arcli.model.parameters.booleanparameter import BooleanParameter
from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES

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
HELP_JOB_SEED = "A seed value to associate with the job for reproducibility."
HELP_JOB_TAG = "A correlation tag to associate with the job."
HELP_RUNID = "A uuid to use for the run id for the testrun."
HELP_CONSOLE_LOG_LEVEL = "The logging level for console output."
HELP_FILE_LOG_LEVEL = "The logging level for logfile output."
HELP_DEBUG = "Output debug information to the console."
HELP_DEBUGGER = "Debugger to active during the test run."
HELP_BREAKPOINT = "The breakpoint to activate for the test run."
HELP_DEBUG_PORT = "The port to use for debugpy remote debugging. Default is 5678."
HELP_DEBUG_PORT_RANGE = "A port range for multiple debug sessions (e.g., '5678-5688'). When specified, the system will find an available port within the range."
HELP_DEBUG_LOG_LEVEL = "The logging level for debug events (debug, info, warning, error, disabled). Default is 'info'."
HELP_PRERUN_DIAGNOSTIC = "Flag indicating that a pre run diagnostic should be performed."
HELP_POSTRUN_DIAGNOSTIC = "Flag indicating that a post run diagnostic should be performed."
HELP_DIAGNOSTIC_LEVEL = "The diagnostic level (1-9) controlling verbosity. Levels 1-3: basic, 4-6: standard, 7-9: detailed. Default is 9."
HELP_INCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will include a test."
HELP_EXCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will exclude a test."
HELP_FILTER = "Add a job filter expression."
HELP_JOB = "The identifier of the job to {action}."
HELP_TIMEOUT = "The maximum duration in seconds for the test execution phase. When exceeded, the test run is terminated and remaining tests are marked as errored."


class RootOptionGroup(OptionGroup):
    """
    Option group for specifying the test root directory.

    This group provides the ``--root`` option for specifying the directory
    to scan for tests.

    Attributes:
        name (str): Group identifier, set to ``"root"``.
        root (OptionField): The ``--root`` option for test directory specification.
    """
    name = "root"
    root = OptionField("--root", default=None, required=False, help=HELP_ROOT)


class OutputOptionGroup(OptionGroup):
    """
    Option group for output directory and run identification.

    This group provides options for specifying where test results and
    artifacts are collected, along with run identification metadata.

    Attributes:
        name (str): Group identifier, set to ``"output"``.
        output (OptionField): The ``-o``/``--output`` option for output directory.
        start (OptionField): The ``--start`` option for run start timestamp.
        runid (OptionField): The ``--runid`` option for unique run identifier.
    """
    name = "output"
    output = OptionField("-o", "--output", default=None, required=False, help=HELP_OUTPUT)
    start = OptionField("--start", default=None, required=False, help=HELP_START)
    runid = OptionField("--runid", default=None, required=False, help=HELP_RUNID)


class BuildOptionGroup(OptionGroup):
    """
    Option group for build metadata.

    This group provides options for associating build information with
    test run results, useful for CI/CD integration.

    Attributes:
        name (str): Group identifier, set to ``"build"``.
        branch (OptionField): The ``--branch`` option for source branch name.
        build (OptionField): The ``--build`` option for build identifier.
        flavor (OptionField): The ``--flavor`` option for build flavor/variant.
    """
    name = "build"
    branch = OptionField("--branch", default=None, required=False, help=HELP_BRANCH)
    build = OptionField("--build", default=None, required=False, help=HELP_BUILD)
    flavor = OptionField("--flavor", default=None, required=False, help=HELP_FLAVOR)


class JobOptionGroup(OptionGroup):
    """
    Option group for job identification and ownership.

    This group provides options for identifying and tracking test jobs,
    including job ownership and labeling for organizational purposes.

    Attributes:
        name (str): Group identifier, set to ``"job"``.
        job_id (OptionField): The ``--job-id`` option for unique job identifier.
        job_initiator (OptionField): The ``--job-initiator`` option for who started the job.
        job_label (OptionField): The ``--job-label`` option for job categorization.
        job_name (OptionField): The ``--job-name`` option for human-readable job name.
        job_owner (OptionField): The ``--job-owner`` option for job ownership.
        job_seed (OptionField): The ``--job-seed`` option for job reproducibility seed.
        job_tag (OptionField): The ``--job-tag`` option for job correlation tag.
    """
    name = "job"
    job_id = OptionField("--job-id", default=None, required=False, help=HELP_JOB_ID)
    job_initiator = OptionField("--job-initiator", default=None, required=False, help=HELP_JOB_INITIATOR)
    job_label = OptionField("--job-label", default=None, required=False, help=HELP_JOB_LABEL)
    job_name = OptionField("--job-name", default=None, required=False, help=HELP_JOB_NAME)
    job_owner = OptionField("--job-owner", default=None, required=False, help=HELP_JOB_OWNER)
    job_seed = OptionField("--job-seed", default=None, required=False, help=HELP_JOB_SEED)
    job_tag = OptionField("--job-tag", default=None, required=False, help=HELP_JOB_TAG)


class LoggingOptionGroup(OptionGroup):
    """
    Option group for logging configuration.

    This group provides options for controlling the verbosity of console
    and file logging output during test execution.

    Attributes:
        name (str): Group identifier, set to ``"logging"``.
        console_level (OptionField): The ``--console-level`` option for console log verbosity.
        logfile_level (OptionField): The ``--logfile-level`` option for file log verbosity.
    """
    name = "logging"
    console_level = OptionField("--console-level", default=None, required=False,
                              ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_CONSOLE_LOG_LEVEL)
    logfile_level = OptionField("--logfile-level", default=None, required=False,
                              ptype=Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_FILE_LOG_LEVEL)


class DiagnosticOptionGroup(OptionGroup):
    """
    Option group for debugging and diagnostic options.

    This group provides CLI options for controlling debugger behavior and
    breakpoint activation during test execution. It enables developers to
    pause test execution at well-known breakpoints using either the built-in
    Python debugger (pdb) or the remote debugging protocol (debugpy) for
    IDE integration.

    When the ``--debugger`` option is specified, the system sets the
    ``AM_DEBUG_DEBUGGER`` runtime variable. When ``--breakpoint`` is specified,
    the system sets the ``AM_DEBUG_BREAKPOINTS`` runtime variable.

    Attributes:
        name (str): Group identifier, set to ``"diagnostic"``.
        debugger (OptionField): The ``--debugger`` option for selecting the debugger backend.
            Choices: ``'pdb'`` (local terminal debugging) or ``'debugpy'`` (remote/IDE debugging).
        breakpoints (OptionField): The ``--breakpoint`` option for specifying breakpoints to activate.
            Choices: ``'test-discovery'`` or ``'testrun-start'``. Supports multiple values.
        debug_port (OptionField): The ``--debug-port`` option for specifying the debugpy port.
            Default is 5678. Allows custom port configuration for remote debugging.
        debug_port_range (OptionField): The ``--debug-port-range`` option for specifying a port range.
            Format: 'start-end' (e.g., '5678-5688'). The system will find an available port.
        debug_log_level (OptionField): The ``--debug-log-level`` option for controlling debug event logging.
            Choices: ``'debug'``, ``'info'``, ``'warning'``, ``'error'``, ``'disabled'``. Default is 'info'.
        prerun_diagnostic (OptionField): The ``--prerun-diagnostic`` flag for pre-run diagnostics.
        postrun_diagnostic (OptionField): The ``--postrun-diagnostic`` flag for post-run diagnostics.
        diagnostic_level (OptionField): The ``--diagnostic-level`` option for controlling diagnostic verbosity.
            Integer value from 1-9. Levels 1-3: basic, 4-6: standard, 7-9: detailed. Default is 9.

    Example CLI Usage::

        # Enable testrun-start breakpoint with pdb (terminal debugging)
        testbase testing run --root ./tests --debugger pdb --breakpoint testrun-start

        # Enable testrun-start breakpoint with debugpy (remote/IDE debugging)
        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start

        # Enable debugpy with custom port
        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-port 5680

        # Enable debugpy with port range (auto-select available port)
        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-port-range 5678-5688

        # Enable verbose debug logging
        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-log-level debug

        # Disable debug logging
        testbase testing run --root ./tests --debugger debugpy --breakpoint testrun-start --debug-log-level disabled

        # Enable test-discovery breakpoint with debugpy
        testbase testing run --root ./tests --debugger debugpy --breakpoint test-discovery

        # Enable multiple breakpoints
        testbase testing run --root ./tests --debugger debugpy \\
            --breakpoint test-discovery \\
            --breakpoint testrun-start

        # Enable diagnostics with specific level
        testbase testing run --root ./tests --prerun-diagnostic --diagnostic-level 5

        # Enable both pre and post diagnostics with basic level
        testbase testing run --root ./tests --prerun-diagnostic --postrun-diagnostic --diagnostic-level 3

    Debugger Options:
        - **pdb**: The built-in Python debugger. Provides local terminal debugging
          with no additional setup required. When a breakpoint is hit, execution
          pauses and the pdb prompt appears in the terminal.

        - **debugpy**: The remote debugging protocol library. Enables IDE integration
          and remote debugging. When a breakpoint is hit, the process waits for a
          debugger client (e.g., VS Code) to attach before continuing.

    Breakpoint Options:
        - **test-discovery**: Pauses execution during the test discovery phase,
          before test collection begins. Useful for debugging test collection issues.

        - **testrun-start**: Pauses execution at the start of test execution,
          at the entry point of the session() method in the sequence document.
          Useful for debugging test setup and initialization.

    Port Configuration:
        - **--debug-port**: Specify a single port for debugpy to listen on.
          Default is 5678. Use this when you know a specific port is available.

        - **--debug-port-range**: Specify a range of ports (e.g., '5678-5688').
          The system will automatically find an available port within the range.
          Useful when running multiple debug sessions or when the default port
          may be in use.

    Debug Logging:
        - **--debug-log-level**: Control the verbosity of debug event logging.
          - ``debug``: Most verbose, logs all debug events including session start/end.
          - ``info``: Standard level, logs breakpoint triggers and connection events.
          - ``warning``: Logs only warning-level debug events.
          - ``error``: Logs only error-level debug events.
          - ``disabled``: Disables all debug event logging.

    Diagnostic Level:
        - **--diagnostic-level**: Control the verbosity of diagnostic capture.
          - Levels 1-3: Basic diagnostic information (quick status checks)
          - Levels 4-6: Standard diagnostic information (normal debugging)
          - Levels 7-9: Detailed diagnostic information (deep investigation)
          - Default is 9 (maximum detail) when not specified.

    VS Code Integration:
        When using debugpy, configure VS Code to attach to the debug session::

            {
                "name": "TestBase: Attach",
                "type": "debugpy",
                "request": "attach",
                "connect": {
                    "host": "localhost",
                    "port": 5678
                }
            }

    See Also:
        - :class:`ccai.testbase.breakpoints.WELLKNOWN_BREAKPOINTS`: Breakpoint enumeration
        - :mod:`ccai.xmodules.debugging`: Core debugging infrastructure
        - :mod:`ccai.testbase.debugports`: Port utilities for conflict detection
        - :mod:`ccai.testbase.debuglogging`: Debug event logging infrastructure
    """
    name = "diagnostic"
    debugger = OptionField("--debugger", default=None, required=False,
                         ptype=Choice(['pdb', 'debugpy']), help=HELP_DEBUGGER)
    breakpoints = OptionField("--breakpoint", alias="breakpoints", default=None, required=False,
                            mode=OptionMode.Multiple, ptype=Choice(['test-discovery', 'testrun-start']), help=HELP_BREAKPOINT)
    debug_port = OptionField("--debug-port", default=None, required=False, help=HELP_DEBUG_PORT)
    debug_port_range = OptionField("--debug-port-range", default=None, required=False, help=HELP_DEBUG_PORT_RANGE)
    debug_log_level = OptionField("--debug-log-level", default=None, required=False,
                                 ptype=Choice(['debug', 'info', 'warning', 'error', 'disabled']), help=HELP_DEBUG_LOG_LEVEL)
    prerun_diagnostic = OptionField("--prerun-diagnostic", default=False, required=False, ptype=BooleanParameter, help=HELP_PRERUN_DIAGNOSTIC)
    postrun_diagnostic = OptionField("--postrun-diagnostic", default=False, required=False, ptype=BooleanParameter, help=HELP_POSTRUN_DIAGNOSTIC)
    diagnostic_level = OptionField("--diagnostic-level", default=None, required=False, help=HELP_DIAGNOSTIC_LEVEL)


class FilteringOptionGroup(OptionGroup):
    """
    Option group for test filtering options.

    This group provides options for including or excluding tests based on
    patterns and marker expressions.

    Attributes:
        name (str): Group identifier, set to ``"filtering"``.
        includes (OptionField): The ``-i``/``--includes`` option for test inclusion patterns.
        excludes (OptionField): The ``-x``/``--excludes`` option for test exclusion patterns.
        include_marker_exp (OptionField): The ``--include-marker-exp`` option for marker-based inclusion.
        exclude_marker_exp (OptionField): The ``--exclude-marker-exp`` option for marker-based exclusion.
    """
    name = "filtering"
    includes = OptionField("-i", "--includes", default=None, required=False, mode=OptionMode.Multiple, help=HELP_INCLUDES)
    excludes = OptionField("-x", "--excludes", default=None, required=False, mode=OptionMode.Multiple, help=HELP_EXCLUDES)
    include_marker_exp = OptionField("--include-marker-exp", default=None, required=False, mode=OptionMode.Multiple, help=HELP_INCLUDE_MARKER_EXP)
    exclude_marker_exp = OptionField("--exclude-marker-exp", default=None, required=False, mode=OptionMode.Multiple, help=HELP_EXCLUDE_MARKER_EXP)


class DebugOptionGroup(OptionGroup):
    """
    Option group for debug output control.

    This group provides a simple flag for enabling debug output to the console.

    Attributes:
        name (str): Group identifier, set to ``"debug"``.
        debug (OptionField): The ``--debug`` flag for enabling debug output.
    """
    name = "debug"
    debug = OptionField("--debug", default=False, ptype=BooleanParameter, help=HELP_DEBUG)


class TimeoutOptionGroup(OptionGroup):
    """
    Option group for test run timeout configuration.

    This group provides the ``--timeout`` option for specifying the maximum
    allowed duration of the test execution phase. When the timeout is exceeded,
    the test run is terminated gracefully and remaining tests are marked as errored.

    Attributes:
        name (str): Group identifier, set to ``"timeout"``.
        timeout (OptionField): The ``--timeout`` option for maximum run duration in seconds.

    Example CLI Usage::

        # Set a 5-minute timeout for the test run
        testbase testing run --root ./tests --timeout 300

        # Set a 1-hour timeout
        testbase testing run --root ./tests --timeout 3600
    """
    name = "timeout"
    timeout = OptionField("--timeout", default=None, required=False, help=HELP_TIMEOUT)
