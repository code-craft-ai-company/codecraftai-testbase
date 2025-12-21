"""
    .. module:: automojo.testbase.initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for initialize.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


import os

from automojo.thisapp.wellknown import ThisApplicationSingleton
from automojo.thisapp.persona import establish_app_persona

from automojo.runtime.enumerations import ActivationProfile, JobType
from automojo.runtime.activation import activate_profile_job
from automojo.runtime.runtimevariables import RuntimeVariables, RuntimeVariablesDesc, resolve_runtime_variables

TESTPLUS_DIR = os.path.dirname(__file__)


class TestBaseConstants:
    """
        Container for commonly referenced paths used by testbase.
    """

    TESTPLUS_TEMPLATES_DIR = os.path.join(TESTPLUS_DIR, "templates")
    TESTPLUS_RESOURCE_DEST_LEAF = os.path.join("static", "v2")
    TESTPLUS_RESOURCE_SRC_DIR = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "static")
    TESTPLUS_SUMMARY_TEMPLATE = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "testsummary.html")
    

def initialize_testbase_runtime():

    name="automojo"
    home_dir = os.path.join(os.path.expanduser("~"), name)
    
    establish_app_persona(name=name, home_dir=home_dir, logger_name="TB", log_basename="testrun")

    resolve_runtime_variables()

    return

def initialize_testbase_results():

    this_app = ThisApplicationSingleton()

    dest_static_dir = os.path.join(RuntimeVariables.AM_PRESENCE_DIR, "results", TestBaseConstants.TESTPLUS_RESOURCE_DEST_LEAF)

    if RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_SRC_DIR is None:
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULTS_STATIC_RESOURCE_SRC_DIR, TestBaseConstants.TESTPLUS_RESOURCE_SRC_DIR)
    if RuntimeVariables.AM_RESULTS_STATIC_RESOURCE_DEST_DIR is None:
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULTS_STATIC_RESOURCE_DEST_DIR, dest_static_dir)
    if RuntimeVariables.AM_RESULTS_STATIC_SUMMARY_TEMPLATE is None:
        this_app.override_variable_value(RuntimeVariablesDesc.AM_RESULTS_STATIC_SUMMARY_TEMPLATE, TestBaseConstants.TESTPLUS_SUMMARY_TEMPLATE)
    
    activate_profile_job(job_type=JobType.TestRun)

    return
