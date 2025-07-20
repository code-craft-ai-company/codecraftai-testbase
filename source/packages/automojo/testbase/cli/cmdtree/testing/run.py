"""
    .. module:: automojo.testbase.cli.cmdtree.testing.run
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for run.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from typing import List, Union

import os
import sys

import click

from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from automojo.interfaces.itestjob import ITestJob

from automojo.testbase.cli.cmdtree.testing.constants import (
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


@click.command("run", help="Command used to run collections of tests.")
@click.option("--root", default=None,  type=str, required=False, help=HELP_ROOT)
@click.option("--excludes", "-x", multiple=True, required=False, help=HELP_EXCLUDES)
@click.option("--includes", "-i", multiple=True, help=HELP_INCLUDES)
@click.option("--output", "-o", default=None, required=False, help=HELP_OUTPUT)
@click.option("--start", default=None, required=False, help=HELP_START)
@click.option("--runid", default=None, required=False, help=HELP_RUNID)
@click.option("--branch", default=None, required=False, help=HELP_BRANCH)
@click.option("--build", default=None, required=False, help=HELP_BUILD)
@click.option("--flavor", default=None, required=False, help=HELP_FLAVOR)
@click.option("--job-id", default=None, required=False, help=HELP_JOB_ID)
@click.option("--job-initiator", default=None, required=False, help=HELP_JOB_INITIATOR)
@click.option("--job-label", default=None, required=False, help=HELP_JOB_LABEL)
@click.option("--job-name", default=None, required=False, help=HELP_JOB_NAME)
@click.option("--job-owner", default=None, required=False, help=HELP_JOB_OWNER)
@click.option("--console-level", default=None, required=False, type=click.Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_CONSOLE_LOG_LEVEL)
@click.option("--logfile-level", default=None, required=False, type=click.Choice(LOG_LEVEL_NAMES, case_sensitive=False), help=HELP_FILE_LOG_LEVEL)
@click.option("--debugger", default=None, required=False, type=click.Choice(['pdb', 'debugpy']), help=HELP_DEBUGGER)
@click.option("--breakpoint", "breakpoints", default=None, required=False, multiple=True, type=click.Choice(['test-discovery', 'testrun-start']), help=HELP_BREAKPOINT)
@click.option("--prerun-diagnostic", is_flag=True, default=False, required=False, help=HELP_PRERUN_DIAGNOSTIC)
@click.option("--postrun-diagnostic", is_flag=True, default=False, required=False, help=HELP_POSTRUN_DIAGNOSTIC)
@click.option("--include-marker-exp", required=False, multiple=True, help=HELP_INCLUDE_MARKER_EXP)
@click.option("--exclude-marker-exp", required=False, multiple=True, help=HELP_EXCLUDE_MARKER_EXP)
def command_testbase_testing_run(root: Union[str, None], includes: List[str], excludes: List[str], output: Union[str, None], start: Union[str, None],
                                 runid: Union[str, None], branch: Union[str, None], build: Union[str, None], flavor: Union[str, None], job_id: Union[str, None],
                                 job_initiator: Union[str, None], job_label: Union[str, None], job_name: Union[str, None], job_owner: Union[str, None],
                                 console_level: Union[str, None], logfile_level: Union[str, None], debugger: Union[str, None], breakpoints: List[str],
                                 prerun_diagnostic: bool, postrun_diagnostic: bool, include_marker_exp: List[str], exclude_marker_exp: List[str]):


    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    from automojo.presence.contextpaths import ContextPaths
    from automojo.presence.wellknown import ContextSingleton

    from automojo.xmodules.xpython import prepend_python_path

    from automojo.runtime.runtimevariables import AM_RUNTIME_VARIABLES
    
    from automojo.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES

    # STEP 1 - Initialize the Runtime (Performed by the root command)

    # STEP 2 - Resolve the configuration variables (Performed by the root command)
    
    ctx = ContextSingleton()

    # STEP 3 - Apply any "Command Line" option overrides

    from automojo.testbase.markers import MetaFilter, parse_marker_expression

    if branch is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_branch(branch)

    if build is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_name(build)
    
    if flavor is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_build_flavor(flavor)

    if job_initiator is not None:
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
    if breakpoints is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_breakpoints(breakpoints)

        # If a breakpoint was passed bug the debugger was not, use 'debugpy' for the
        # default debugger.
        if debugger is None:
            AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger('debugpy')

    if debugger is not None:
        AM_RUNTIME_OPTION_OVERRIDES.override_debug_debugger('debugpy')

    if prerun_diagnostic:
        ctx.insert(ContextPaths.DIAGNOSTICS_PRERUN, {})
    
    if postrun_diagnostic:
        ctx.insert(ContextPaths.DIAGNOSTICS_POSTRUN, {})

    if root is None:
        if AM_RUNTIME_VARIABLES.AM_TESTROOT is not None:
            root = AM_RUNTIME_VARIABLES.AM_TESTROOT
        elif ctx.lookup(ContextPaths.TESTROOT) is not None:
            root = ctx.lookup(ContextPaths.TESTROOT)
        else:
            root = "."

    test_root = os.path.abspath(os.path.expandvars(os.path.expanduser(root)))
    if not os.path.isdir(test_root):
        errmsg = "The specified root folder does not exist. root=%s" % root
        if test_root != root:
            errmsg += " expanded=%s" % test_root
        raise click.BadParameter(errmsg)

    AM_RUNTIME_OPTION_OVERRIDES.override_testroot(root)

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

    from automojo.presence.wellknown import ConfiguredSuperFactorySingleton
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