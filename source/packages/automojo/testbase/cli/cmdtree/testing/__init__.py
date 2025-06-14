"""
    .. module:: automojo.testbase.cli.cmdtree.testing
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testing.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import click

from automojo.testbase.cli.cmdtree.testing.jobs import group_testbase_testing_jobs
from automojo.testbase.cli.cmdtree.testing.query import command_testbase_testing_query
from automojo.testbase.cli.cmdtree.testing.run import command_testbase_testing_run

@click.group("testing", help="Contains command for working with tests and test results.")
def group_testbase_testing():
    return

group_testbase_testing.add_command(group_testbase_testing_jobs)
group_testbase_testing.add_command(command_testbase_testing_query)
group_testbase_testing.add_command(command_testbase_testing_run)
