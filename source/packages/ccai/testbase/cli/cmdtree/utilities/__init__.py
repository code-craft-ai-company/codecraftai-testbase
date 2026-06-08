"""
    .. module:: ccai.testbase.cli.cmdtree.utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for utilities.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []
__version__ = "1.0.0"

from ccai.arcli import decorators as arcli

from ccai.testbase.cli.cmdtree.utilities.timestamp import command_testbase_utilities_timestamp


@arcli.group("utilities")
def group_testbase_utilities():
    """
    Contains various automation pipeline utility commands.
    """
    return

group_testbase_utilities.add_command(command_testbase_utilities_timestamp)
