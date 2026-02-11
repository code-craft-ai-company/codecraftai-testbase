"""
    .. module:: automojo.testbase.cli.cmdtree.testing.run
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for run.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import List, Union, Optional

import os
import sys
import argparse

from automojo.arcli import decorators as arcli

from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from automojo.interfaces.itestjob import ITestJob

from automojo.testbase.cli.options import (
    RootOptionGroup,
    OutputOptionGroup,
    BuildOptionGroup,
    JobOptionGroup,
    LoggingOptionGroup,
    DiagnosticOptionGroup,
    FilteringOptionGroup,
    HELP_ROOT,
    HELP_EXCLUDES,
    HELP_INCLUDES,
    HELP_OUTPUT,
    HELP_START,
    HELP_BRANCH,
    HELP_BUILD,
    HELP_FLAVOR,
    HELP_JOB_ID,
    HELP_JOB_INITIATOR,
    HELP_JOB_LABEL,
    HELP_JOB_NAME,
    HELP_JOB_OWNER,
    HELP_RUNID,
    HELP_CONSOLE_LOG_LEVEL,
    HELP_FILE_LOG_LEVEL,
    HELP_DEBUGGER,
    HELP_BREAKPOINT,
    HELP_PRERUN_DIAGNOSTIC,
    HELP_POSTRUN_DIAGNOSTIC,
    HELP_INCLUDE_MARKER_EXP,
    HELP_EXCLUDE_MARKER_EXP
)

@RootOptionGroup.attach(help_fill={"action": "run"})
@FilteringOptionGroup.attach(help_fill={"action": "run"})
@OutputOptionGroup.attach()
@BuildOptionGroup.attach()
@JobOptionGroup.attach()
@LoggingOptionGroup.attach()
@DiagnosticOptionGroup.attach()
@arcli.command("run")
def command_testbase_testing_run(root: Optional[str], includes: Optional[List[str]], excludes: Optional[List[str]], output: Optional[str],
                                 start: Optional[str], runid: Optional[str], branch: Optional[str], build: Optional[str], flavor: Optional[str],
                                 job_id: Optional[str], job_initiator: Optional[str], job_label: Optional[str], job_name: Optional[str],
                                 job_owner: Optional[str], console_level: Optional[str], logfile_level: Optional[str],
                                 debugger: Optional[str], breakpoints: Optional[List[str]], prerun_diagnostic: bool, postrun_diagnostic: bool,
                                 include_marker_exp: Optional[List[str]], exclude_marker_exp: Optional[List[str]]):
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

    from automojo.xmodules.xpython import prepend_python_path

    from automojo.runtime.runtimevariables import RuntimeVariables
    
    from automojo.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES

    # STEP 1 - Initialize the Runtime (Performed by the root command)

    # STEP 2 - Resolve the configuration variables (Performed by the root command)

    # STEP 3 - Apply any "Command Line" option overrides

    from automojo.testbase.markers import MetaFilter, parse_marker_expression

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

    if prerun_diagnostic:
        AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_prerun({})
    
    if postrun_diagnostic:
        AM_RUNTIME_OPTION_OVERRIDES.override_diagnostics_postrun({})

    if root is None:
        if RuntimeVariables.AM_TESTROOT is not None:
            root = RuntimeVariables.AM_TESTROOT
        else:
            root = "."

    test_root = os.path.abspath(os.path.expandvars(os.path.expanduser(root)))
    if not os.path.isdir(test_root):
        errmsg = "The specified root folder does not exist. root=%s" % root
        if test_root != root:
            errmsg += " expanded=%s" % test_root
        raise ValueError(errmsg)

    AM_RUNTIME_OPTION_OVERRIDES.override_testroot(test_root)

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
        imexp = imexp.strip("'")
        mfilter = parse_marker_expression("-" + imexp)
        metafilters.append(mfilter)


    # STEP 5 - Initialize the Results Output

    # Initialize testbase results and logging
    from automojo.testbase.initialize import initialize_testbase_results
    from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger

    initialize_testbase_results()

    logger = getEnhancedLogger()

    # STEP 6 - Create and kick off the job

    from automojo.thisapp.wellknown import ConfiguredSuperFactorySingleton
    from automojo.testbase.factoryprotocols import TestBaseFactoryProtocol

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
