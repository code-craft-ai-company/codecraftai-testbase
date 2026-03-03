"""
    .. module:: automojo.testbase.cli.cmdtree.agents
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Agent tooling command group for AI agent consumption.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.arcli import decorators as arcli

from automojo.testbase.cli.cmdtree.agents.summary import group_testbase_agents_summary
from automojo.testbase.cli.cmdtree.agents.testresult import group_testbase_agents_testresult
from automojo.testbase.cli.cmdtree.agents.config import group_testbase_agents_config

@arcli.group("agents")
def group_testbase_agents():
    """
    Commands for AI agents to extract and analyze test result data.
    """
    return

group_testbase_agents.add_command(group_testbase_agents_summary)
group_testbase_agents.add_command(group_testbase_agents_testresult)
group_testbase_agents.add_command(group_testbase_agents_config)
