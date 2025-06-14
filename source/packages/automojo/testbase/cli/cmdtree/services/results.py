"""
    .. module:: automojo.testbase.cli.cmdtree.services.results
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

import click


from automojo.testbase.server.resultserver import TestResultServer, TestResultRequestHandler, try_create_bug_server_interface_from_environment
from automojo.foundation.runtime.activation import activate_profile_service
from automojo.foundation.runtime.paths import get_presence_directory
from automojo.foundation.runtime.runtimevariables import AM_RUNTIME_VARIABLES


HELP_DIRECTORY = "The root directory to serve the test results from."
HELP_BIND = "The IP address to bind the server to."
HELP_PORT = "The port to bind the server to."

@click.command("results", help="Command used to launch the test results server.")
@click.option("--directory", default=None, type=str, help=HELP_DIRECTORY)
@click.option("--bind", default="", help=HELP_BIND)
@click.option("--port", default=8880, help=HELP_PORT)
def command_testbase_services_results(directory, bind, port):
    
    AM_RUNTIME_VARIABLES.AM_SERVICE_NAME = "Test-Result-Service"
    activate_profile_service()

    svc_endpoint = (bind, port)
    
    svc_directory = None
    if directory is not None:
        svc_directory = os.path.abspath(os.path.expandvars(os.path.expanduser(directory)))
    else:
        presence_dir = get_presence_directory()
        svc_directory = os.path.join(presence_dir, "results")

    bug_svc = try_create_bug_server_interface_from_environment()

    server = TestResultServer(svc_directory, svc_endpoint, TestResultRequestHandler, bug_svc)
    server.serve_forever()

    return
