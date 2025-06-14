"""
    .. module:: automojo.testbase.cli.cmdtree.utilities.timestamp
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for timestamp.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from datetime import datetime

import click

@click.command("timestamp")
def command_testbase_utilities_timestamp():

    from automojo.foundation.xdatetime import DATETIME_FORMAT_FILESYSTEM

    now = datetime.now()
    timestamp = now.strftime(DATETIME_FORMAT_FILESYSTEM).replace(" ", "T")
    
    print(timestamp)

    return