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

from automojo.foundation.collections.contextpaths import ContextPaths
from automojo.foundation.collections.wellknown import ContextSingleton

from automojo.foundation.xlogging.foundations import logging_initialize
    
from automojo.foundation.runtime.initialize import initialize_runtime, AM_RUNTIME_STATE
from automojo.foundation.runtime.runtimevariables import AM_RUNTIME_VARIABLES

TESTPLUS_DIR = os.path.dirname(__file__)

class TestBaseVariables:
    TESTPLUS_TEMPLATES_DIR = os.path.join(TESTPLUS_DIR, "templates")
    TESTPLUS_RESOURCE_DEST_LEAF = os.path.join("static", "v2")
    TESTPLUS_RESOURCE_SRC_DIR = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "static")
    TESTPLUS_SUMMARY_TEMPLATE = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "testsummary.html")
    

def initialize_testbase_runtime():
    if not AM_RUNTIME_STATE.INITIALIZED:
        name="automojo"
        home_dir = os.path.join(os.path.expanduser("~"), name)
        initialize_runtime(name=name, home_dir=home_dir, logger_name="TP")
    return

def initialize_testbase_results():
    dest_static_dir = os.path.join(AM_RUNTIME_VARIABLES.AM_PRESENCE_DIRECTORY, "results", TestBaseVariables.TESTPLUS_RESOURCE_DEST_LEAF)

    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR = TestBaseVariables.TESTPLUS_RESOURCE_SRC_DIR
    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR = dest_static_dir
    if AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE is None:
        AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE = TestBaseVariables.TESTPLUS_SUMMARY_TEMPLATE

    ctx = ContextSingleton()
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_SRC, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_SRC_DIR)
    ctx.insert(ContextPaths.DIR_RESULTS_RESOURCE_DEST, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_RESOURCE_DEST_DIR)
    ctx.insert(ContextPaths.FILE_RESULTS_TEMPLATE, AM_RUNTIME_VARIABLES.AM_RESULTS_STATIC_SUMMARY_TEMPLATE)
    
    logging_initialize()

    return
