"""
    .. module:: automojo.testbase.cli.cmdtree.agents.testresult
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Test result subgroup for agent commands.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.arcli import decorators as arcli

from automojo.testbase.cli.cmdtree.agents.testresult.extract import command_agents_testresult_extract
from automojo.testbase.cli.cmdtree.agents.testresult.list import command_agents_testresult_list
from automojo.testbase.cli.cmdtree.agents.testresult.failures import command_agents_testresult_failures

@arcli.group("testresult")
def group_testbase_agents_testresult():
    """
    Commands for extracting and listing individual test results.
    """
    return

group_testbase_agents_testresult.add_command(command_agents_testresult_extract)
group_testbase_agents_testresult.add_command(command_agents_testresult_list)
group_testbase_agents_testresult.add_command(command_agents_testresult_failures)
