"""
    .. module:: automojo.testbase.cli.cmdtree.utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for utilities.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []
__version__ = "1.0.0"

import click

from automojo.testbase.cli.cmdtree.utilities.timestamp import command_testbase_utilities_timestamp


@click.group("utilities", help="Contains various automation pipeline utility commands.")
def group_testbase_utilities():
    return

group_testbase_utilities.add_command(command_testbase_utilities_timestamp)