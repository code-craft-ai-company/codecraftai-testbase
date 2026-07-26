"""
    .. module:: ccai.testbase.cli.cmdtree.testing.jobs
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for jobs.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Union, Optional

import argparse
import os
import sys

from ccai.arcli import decorators as arcli
from ccai.arcli.model.fields.optionfield import OptionMode
from ccai.arcli.model.parameters.booleanparameter import BooleanParameter

from ccai.testbase.cli.options import (
    RootOptionGroup,
    OutputOptionGroup,
    BuildOptionGroup,
    LoggingOptionGroup,
    DebugOptionGroup,
    TimeoutOptionGroup,
    HELP_ROOT,
    HELP_FILTER,
    HELP_JOB,
    HELP_OUTPUT,
    HELP_START,
    HELP_BRANCH,
    HELP_BUILD,
    HELP_FLAVOR,
    HELP_CONSOLE_LOG_LEVEL,
    HELP_FILE_LOG_LEVEL,
    HELP_DEBUG,
    HELP_TIMEOUT
)

@arcli.group("jobs")
def group_testbase_testing_jobs():
    """
    Contains commands for working with test jobs.
    """
    return

@arcli.option("--filter", "-f", required=False, help=HELP_FILTER)
@RootOptionGroup.attach(help_fill={"action": "list"})
@DebugOptionGroup.attach()
@arcli.command("list")
def command_testing_jobs_list(root: Optional[str], filter: Optional[str], debug: bool):
    raise NotImplementedError("The 'jobs list' command is not yet implemented.")

@arcli.option("--job", "-j", required=True, help=HELP_JOB.format(action="show"))
@RootOptionGroup.attach(help_fill={"action": "show"})
@DebugOptionGroup.attach()
@arcli.command("show")
def command_testbase_testing_jobs_show(root: Optional[str], job: str, debug: bool):
    raise NotImplementedError("The 'jobs show' command is not yet implemented.")

@arcli.option("--job", "-j", required=True, help=HELP_JOB.format(action="run"))
@RootOptionGroup.attach(help_fill={"action": "run"})
@OutputOptionGroup.attach()
@BuildOptionGroup.attach()
@LoggingOptionGroup.attach()
@TimeoutOptionGroup.attach()
@arcli.command("run")
def command_testbase_testing_jobs_run(root: Optional[str], job: str, output: Optional[str], start: Optional[str], runid: Optional[str],
                                      branch: Optional[str], build: Optional[str], flavor: Optional[str],
                                      console_level: Optional[str], logfile_level: Optional[str],
                                      timeout: Optional[str]):

    # pylint: disable=unused-import,import-outside-toplevel

    # We do the imports of the automation framework code inside the action functions because
    # we don't want to startup loggin and the processing of inputs and environment variables
    # until we have entered an action method.  Thats way we know how to setup the environment.

    # IMPORTANT: We need to load the context first because it will trigger the loading
    # of the default user configuration

    from ccai.xmodules.ximport import import_by_name
    from ccai.xmodules.xpython import prepend_python_path

    try:
        from ccai.testbase.cli.utilities import resolve_test_root
        test_root = resolve_test_root(root)

        # Make sure we extend PATH to include the test root parent folder
        test_root_parent = os.path.dirname(test_root)
        prepend_python_path(test_root_parent)

        # We perform activation a little later in the testrunner.py file so we can
        # handle exceptions in the context of testrunner_main function
        from ccai.thisapp.activation import activate_profile_console
        activate_profile_console()

        from ccai.runtime.optionoverrides import AM_RUNTIME_OPTION_OVERRIDES

        if branch is not None:
            AM_RUNTIME_OPTION_OVERRIDES.override_build_branch(branch)
        if build is not None:
            AM_RUNTIME_OPTION_OVERRIDES.override_build_name(build)
        if flavor is not None:
            AM_RUNTIME_OPTION_OVERRIDES.override_build_flavor(flavor)
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

        from ccai.testbase.initialize import initialize_testbase_results
        initialize_testbase_results()

        # Initialize logging
        from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger
        logger = getEnhancedLogger()

        import ccai.testbase
        tpmod = sys.modules["ccai.testbase"]
        tpmod.logger = logger

        from ccai.thisapp.wellknown import ConfiguredSuperFactorySingleton
        from ccai.testbase.factoryprotocols import TestBaseExtensionProtocol

        # At this point in the code, we either lookup an existing test job or we create a test job
        # from the includes, excludes or test_module
        sfactory = ConfiguredSuperFactorySingleton()
        TestJobType = sfactory.get_override_types_by_order(TestBaseExtensionProtocol.get_testbase_default_job_type)

        if job is not None:
            job_parts = job.split("@")
            if len(job_parts) != 2:
                errmsg = "A --job parameter must be of the form 'package.module@JobClass'"
                raise ValueError(errmsg)

            job_package, job_class = job_parts

            try:
                job_mod = import_by_name(job_package)
            except ImportError as imperr:
                errmsg = "Failure while importing job package %r"  % job_package
                raise RuntimeError(errmsg) from imperr

            if not hasattr(job_mod, job_class):
                errmsg = "The job package %r does not have a job type %r." % (job_package, job_class)
                raise argparse.ArgumentError(None, errmsg)

            TestJobType = getattr(job_mod, job_class)

        result_code = 0
        with TestJobType(logger, test_root) as tjob:
            result_code = tjob.execute()

        sys.exit(result_code)

    finally:
        pass

    return

# Only wire commands that are implemented. 'jobs list' and 'jobs show' remain
# unimplemented placeholders and are intentionally NOT registered so the CLI does
# not advertise subcommands that always raise NotImplementedError.
group_testbase_testing_jobs.add_command(command_testbase_testing_jobs_run)
