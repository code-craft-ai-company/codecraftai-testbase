"""
    .. module:: automojo.testbase.cli.cmdtree.agents.config
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Config subgroup for agent commands.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

from automojo.arcli import decorators as arcli

from automojo.testbase.cli.cmdtree.agents.config.extract import command_agents_config_extract

@arcli.group("config")
def group_testbase_agents_config():
    """
    Commands for extracting test run configuration.
    """
    return

group_testbase_agents_config.add_command(command_agents_config_extract)
