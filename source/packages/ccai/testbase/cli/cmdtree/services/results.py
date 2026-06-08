"""
    .. module:: ccai.testbase.cli.cmdtree.services.results
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for results.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []

from typing import Optional

import os

from ccai.arcli import decorators as arcli
from ccai.arcli.model.parameters.integerparameter import IntegerParameter

from ccai.thisapp.wellknown import ThisApplicationSingleton

from ccai.runtime.activation import activate_profile_service
from ccai.runtime.paths import get_presence_directory
from ccai.runtime.runtimevariables import RuntimeVariablesDesc

from ccai.testbase.server.resultserver import TestResultServer, TestResultRequestHandler, try_create_bug_server_interface_from_environment


HELP_DIRECTORY = "The root directory to serve the test results from."
HELP_BIND = "The IP address to bind the server to."
HELP_PORT = "The port to bind the server to."

@arcli.option("--port", default=8880, ptype=IntegerParameter, help=HELP_PORT)
@arcli.option("--bind", default="", help=HELP_BIND)
@arcli.option("--directory", default=None, help=HELP_DIRECTORY)
@arcli.command("results")
def command_testbase_services_results(directory: Optional[str], bind: str, port: int):
    """
    Command used to launch the test results server.
    """
    
    this_app = ThisApplicationSingleton()

    this_app.override_variable_value(RuntimeVariablesDesc.AM_SERVICE_NAME, "Test-Result-Service")
    
    activate_profile_service()

    svc_endpoint = (bind, port)
    
    svc_directory = None
    if directory is not None:
        svc_directory = os.path.abspath(os.path.expandvars(os.path.expanduser(directory)))
    else:
        presence_dir = get_presence_directory()
        svc_directory = os.path.join(presence_dir, "results")

    bug_svc = try_create_bug_server_interface_from_environment()

    print(f"Serving test results on port={port} from folder='{svc_directory}'")

    server = TestResultServer(svc_directory, svc_endpoint, TestResultRequestHandler, bug_svc)
    server.serve_forever()

    return
