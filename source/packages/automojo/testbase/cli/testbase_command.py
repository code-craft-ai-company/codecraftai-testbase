#!/usr/bin/env python3
"""
.. module:: testbase_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The script entrypoint for the 'testbase' command.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import click

from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.runtime.runtimevariables import RuntimeVariablesDesc

from automojo.testbase.initialize import initialize_testbase_runtime

from automojo.testbase.cli.cmdtree.services import group_testbase_services
from automojo.testbase.cli.cmdtree.testing import group_testbase_testing
from automojo.testbase.cli.cmdtree.utilities import group_testbase_utilities


@click.group("testbase")
@click.option('-v', '--verbose', count=True)
def testbase_root_command(verbose):

    initialize_testbase_runtime()
    
    interactive_console = None
    log_level_console = "WARNING"

    if verbose == 0:
        interactive_console = True
    else:
        interactive_console = False

        if verbose == 1:
            log_level_console = "INFO"
        elif verbose == 2:
            log_level_console = "DEBUG"
        elif verbose > 2:
            log_level_console = "NOTSET"

    this_app = ThisApplicationSingleton()

    this_app.override_variable_value(RuntimeVariablesDesc.AM_INTERACTIVE_CONSOLE, interactive_console)
    this_app.override_variable_value(RuntimeVariablesDesc.AM_LOG_LEVEL_CONSOLE, log_level_console)

    return


testbase_root_command.add_command(group_testbase_services)
testbase_root_command.add_command(group_testbase_testing)
testbase_root_command.add_command(group_testbase_utilities)


if __name__ == '__main__':
    testbase_root_command()
