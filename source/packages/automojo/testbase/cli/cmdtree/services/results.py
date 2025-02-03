
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []

import contextlib
import os

import click

from automojo.testbase.server.resultserver import TestResultServer, TestResultRequestHandler

HELP_DIRECTORY = "The root directory to serve the test results from."
HELP_BIND = "The IP address to bind the server to."
HELP_PORT = "The port to bind the server to."

@click.command("results", help="Command used to launch the test results server.")
@click.option("--directory", default=None, type=str, help=HELP_DIRECTORY)
@click.option("--bind", default="", help=HELP_BIND)
@click.option("--port", default=8880, help=HELP_PORT)
def command_testbase_services_results(directory, bind, port):
    
    svc_endpoint = (bind, port)
    svc_directory = os.path.abspath(os.path.expandvars(os.path.expanduser(directory)))

    server = TestResultServer(svc_directory, svc_endpoint, TestResultRequestHandler)
    server.serve_forever()

    return
