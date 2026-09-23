"""
    .. module:: ccai.testbase.cli.cmdtree.testing.run
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for run.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import List, Optional

import os
import sys

from ccai.arcli import decorators as arcli

from ccai.interfaces.itestjob import ITestJob

from ccai.testbase.cli.options import (
    RootOptionGroup,
    OutputOptionGroup,
    BuildOptionGroup,
    JobOptionGroup,
    LoggingOptionGroup,
    DiagnosticOptionGroup,
    FilteringOptionGroup,
    TimeoutOptionGroup,
)

@RootOptionGroup.attach(help_fill={"action": "run"})
@FilteringOptionGroup.attach(help_fill={"action": "run"})
@OutputOptionGroup.attach()
@BuildOptionGroup.attach()
@JobOptionGroup.attach()
@LoggingOptionGroup.attach()
@DiagnosticOptionGroup.attach()
@TimeoutOptionGroup.attach()
@arcli.command("run")
def command_testbase_testing_run(root: Optional[str], includes: Optional[List[str]], excludes: Optional[List[str]], output: Optional[str],
                                 start: Optional[str], runid: Optional[str], branch: Optional[str], build: Optional[str], flavor: Optional[str],
                                 job_id: Optional[str], job_initiator: Optional[str], job_label: Optional[str], job_name: Optional[str],
                                 job_owner: Optional[str], job_seed: Optional[str], job_tag: Optional[str],
                                 console_level: Optional[str], logfile_level: Optional[str],
                                 debugger: Optional[str], breakpoints: Optional[List[str]], debug_port: Optional[str],
                                 debug_port_range: Optional[str], debug_log_level: Optional[str], prerun_diagnostic: bool, postrun_diagnostic: bool,
                                 diagnostic_level: Optional[str], include_marker_exp: Optional[List[str]], exclude_marker_exp: Optional[List[str]],
                                 timeout: Optional[str]):
    """
    Command used to run collections of tests.
    """

    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    # Initialize lists
    if includes is None: includes = []
    if excludes is None: excludes = []
    if breakpoints is None: breakpoints = []
    if include_marker_exp is None: include_marker_exp = []
    if exclude_marker_exp is None: exclude_marker_exp = []

    from ccai.xmodules.xpython import prepend_python_path

    from ccai.runtime.runtimevariables import RuntimeVariables
    
    from ccai.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES

    # STEP 1 - Initialize the Runtime (Performed by the root command)

    # STEP 2 - Resolve the configuration variables (Performed by the root command)

    # STEP 3 - Apply any "Command Line" option overrides

    from ccai.testbase.markers import MetaFilter, parse_marker_expression

    if branch is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_branch(branch)

    if build is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_name(build)
    
    if flavor is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_flavor(flavor)

    if job_id is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_id(job_id)

    if job_initiator is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_initiator(job_initiator)
    
    if job_label is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_label(job_label)
    
    if job_name is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_name(job_name)

    if job_owner is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_owner(job_owner)

    if job_seed is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_seed(job_seed)

    if job_tag is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_job_tag(job_tag)

    if console_level is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_loglevel_console(console_level)

    if logfile_level is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_loglevel_file(logfile_level)

    if output is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_output_directory(output)

    if start is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_starttime(start)
    
    if runid is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_run_id(runid)

    # STEP 4 - Applying runtime options must happen after we have resolved configuration
    # maps because some of those settings will get overridden by the options.  So the runtime
    # needs to be loaded and set first before we apply runtime options

    # Process the commandline args here and then set the variables on the environment
    # as necessary.  We need to do this before we import activate.
    if breakpoints is not None and len(breakpoints) > 0:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints(breakpoints)

        # If a breakpoint was passed bug the debugger was not, use 'debugpy' for the
        # default debugger.
        if debugger is None:
            AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger('debugpy')

    if debugger is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger('debugpy')

    # Handle debug port configuration
    # Port range takes precedence over specific port
    if debug_port_range is not None or debug_port is not None:
        from ccai.testbase.debugports import (
            resolve_debug_port,
            set_configured_debug_port,
            PortConflictError,
            PortRangeError
        )

        try:
            # Convert debug_port to int if provided
            port_value = int(debug_port) if debug_port is not None else None
            resolved_port = resolve_debug_port(port=port_value, port_range=debug_port_range)
            set_configured_debug_port(resolved_port)
        except PortConflictError as e:
            raise ValueError(str(e))
        except PortRangeError as e:
            raise ValueError(str(e))

    # Handle debug log level configuration
    if debug_log_level is not None:
        from ccai.testbase.debuglogging import set_debug_log_level, DEBUG_LOG_LEVEL

        level_map = {
            'debug': DEBUG_LOG_LEVEL.DEBUG,
            'info': DEBUG_LOG_LEVEL.INFO,
            'warning': DEBUG_LOG_LEVEL.WARNING,
            'error': DEBUG_LOG_LEVEL.ERROR,
            'disabled': DEBUG_LOG_LEVEL.DISABLED
        }
        if debug_log_level.lower() in level_map:
            set_debug_log_level(level_map[debug_log_level.lower()])

    if prerun_diagnostic:
        AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun({})
    
    if postrun_diagnostic:
        AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_postrun({})

    if diagnostic_level is not None:
        # Validate and convert diagnostic level to integer
        from ccai.testbase.diagnostic_level import set_diagnostic_level
        try:
            level_value = int(diagnostic_level)
            if level_value < 1 or level_value > 9:
                raise ValueError(f"Diagnostic level must be between 1 and 9, got: {level_value}")
            set_diagnostic_level(level_value)
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Diagnostic level must be an integer between 1 and 9, got: {diagnostic_level}")
            raise

    from ccai.testbase.cli.utilities import resolve_test_root
    test_root = resolve_test_root(root)

    AM_RUNTIME_OPTION_OVERRIDES.override_testroot(test_root)

    if timeout is not None:
        try:
            timeout_value = int(timeout)
            if timeout_value <= 0:
                raise ValueError("Timeout must be a positive integer, got: %d" % timeout_value)
            AM_RUNTIME_OPTION_OVERRIDES.override_testrun_timeout(timeout_value)
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError("Timeout must be a positive integer, got: %s" % timeout)
            raise

    # Make sure we extend PATH to include the test roots parent folder so imports will
    # work properly.
    test_root_parent = os.path.dirname(test_root)
    prepend_python_path(test_root_parent)

    metafilters: List[MetaFilter] = []
    for imexp in include_marker_exp:
        imexp = imexp.strip("\"")
        imexp = imexp.strip("'")
        mfilter = parse_marker_expression("+" + imexp)
        metafilters.append(mfilter)

    for exmexp in exclude_marker_exp:
        exmexp = exmexp.strip("\"")
        exmexp = exmexp.strip("'")
        mfilter = parse_marker_expression("-" + exmexp)
        metafilters.append(mfilter)


    # STEP 5 - Initialize the Results Output

    # Initialize testbase results and logging
    from ccai.testbase.initialize import initialize_testbase_results
    from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

    initialize_testbase_results()

    logger = getEnhancedLogger()

    # STEP 6 - Create and kick off the job

    from ccai.thisapp.wellknown import ConfiguredSuperFactorySingleton
    from ccai.testbase.factoryprotocols import TestBaseFactoryProtocol

    # At this point in the code, we either lookup an existing test job or we create a test job
    # from the includes, excludes or test_module
    sfactory = ConfiguredSuperFactorySingleton()
    TestJobType = sfactory.get_override_types_by_order(TestBaseFactoryProtocol.get_testbase_default_job_type)

    result_code = 0
    tjob: ITestJob

    with TestJobType(logger, test_root, includes=includes, excludes=excludes, metafilters=metafilters) as tjob:
        result_code = tjob.execute()

    sys.exit(result_code)

    return
