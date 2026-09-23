"""
    .. module:: testbase_command
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: The script entrypoint for the 'testbase' command.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.arcli import decorators as arcli
from ccai.arcli.model.fields.optionfield import OptionMode

from ccai.thisapp.wellknown import ThisApplicationSingleton

from ccai.runtime.runtimevariables import RuntimeVariablesDesc

from ccai.testbase.initialize import initialize_testbase_runtime

from ccai.testbase.cli.cmdtree.agents import group_testbase_agents
from ccai.testbase.cli.cmdtree.services import group_testbase_services
from ccai.testbase.cli.cmdtree.testing import group_testbase_testing
from ccai.testbase.cli.cmdtree.utilities import group_testbase_utilities


@arcli.option('-v', '--verbose', default=0, mode=OptionMode.Counter, help="Set the verbosity level.")
@arcli.entry("testbase")
def testbase_root_command(verbose: int):

    initialize_testbase_runtime()
    
    interactive_console = False
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


testbase_root_command.add_command(group_testbase_agents)
testbase_root_command.add_command(group_testbase_services)
testbase_root_command.add_command(group_testbase_testing)
testbase_root_command.add_command(group_testbase_utilities)


if __name__ == '__main__':
    testbase_root_command()
