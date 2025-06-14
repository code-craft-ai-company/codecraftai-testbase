"""
    .. module:: automojo.testbase.cli.cmdtree.services
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for services.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import click

from automojo.testbase.cli.cmdtree.services.results import command_testbase_services_results


@click.group("services", help="Contains commands for running testing services.")
def group_testbase_services():
    return

group_testbase_services.add_command(command_testbase_services_results)
