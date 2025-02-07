

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

from automojo.testbase.cli.cmdtree.services import group_testbase_services
from automojo.testbase.cli.cmdtree.testing import group_testbase_testing
from automojo.testbase.cli.cmdtree.utilities import group_testbase_utilities


@click.group("testbase")
@click.option('-v', '--verbose', count=True)
def testbase_root_command(verbose):

    from automojo.foundation.runtime.runtimevariables import AM_RUNTIME_VARIABLES

    if verbose == 0:
        AM_RUNTIME_VARIABLES.AM_INTERACTIVE_CONSOLE = True
    else:
        AM_RUNTIME_VARIABLES.AM_INTERACTIVE_CONSOLE = False

        if verbose == 1:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "INFO"
        elif verbose == 2:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "DEBUG"
        elif verbose > 2:
            AM_RUNTIME_VARIABLES.AM_LOG_LEVEL_CONSOLE = "NOTSET"

    from automojo.testbase.initialize import initialize_testbase_runtime
    initialize_testbase_runtime()

    return


testbase_root_command.add_command(group_testbase_services)
testbase_root_command.add_command(group_testbase_testing)
testbase_root_command.add_command(group_testbase_utilities)


if __name__ == '__main__':
    testbase_root_command()
