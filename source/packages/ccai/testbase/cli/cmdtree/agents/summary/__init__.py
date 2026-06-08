"""
    .. module:: ccai.testbase.cli.cmdtree.agents.summary
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Summary subgroup for agent commands.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.agents.summary.extract import command_agents_summary_extract
from ccai.testbase.cli.cmdtree.agents.summary.compare import command_agents_summary_compare

@arcli.group("summary")
def group_testbase_agents_summary():
    """
    Commands for extracting and comparing test run summaries.
    """
    return

group_testbase_agents_summary.add_command(command_agents_summary_extract)
group_testbase_agents_summary.add_command(command_agents_summary_compare)
