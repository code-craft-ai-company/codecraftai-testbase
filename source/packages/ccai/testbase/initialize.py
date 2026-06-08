"""
    .. module:: ccai.testbase.initialize
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for initialize.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import os

from ccai.thisapp.wellknown import ThisApplicationSingleton
from ccai.thisapp.persona import establish_app_persona

from ccai.runtime.enumerations import ActivationProfile, JobType
from ccai.runtime.activation import activate_profile_job
from ccai.runtime.runtimevariables import RuntimeVariables, RuntimeVariablesDesc, resolve_runtime_variables

TESTPLUS_DIR = os.path.dirname(__file__)


class TestBaseConstants:
    """
        Container for commonly referenced paths used by the TestBase framework.

        This class provides centralized access to standard directory paths and file locations
        used throughout the TestBase framework for templates, static resources, and result
        generation.

        Class Attributes:
            TESTPLUS_TEMPLATES_DIR (str): The absolute path to the templates directory
                within the testbase package. Contains HTML templates and static resources
                for result generation.

            TESTPLUS_RESOURCE_DEST_LEAF (str): The relative path leaf for static resource
                destination. Used to construct the full destination path for copying
                static resources during result generation. Value: ``"static/v2"``.

            TESTPLUS_RESOURCE_SRC_DIR (str): The absolute path to the source directory
                for static resources (CSS, JavaScript, images). Located within the
                templates/v2/static directory.

            TESTPLUS_SUMMARY_TEMPLATE (str): The absolute path to the HTML summary template
                file used for generating test result summaries. Located at
                templates/v2/testsummary.html.

        Example:
            Accessing template paths::

                from ccai.testbase.initialize import TestBaseConstants

                # Get the templates directory
                templates_dir = TestBaseConstants.TESTPLUS_TEMPLATES_DIR

                # Get the summary template path
                summary_template = TestBaseConstants.TESTPLUS_SUMMARY_TEMPLATE

        .. note::
            These paths are computed relative to the testbase package installation directory
            and are used by :func:`initialize_testbase_results` to configure the results
            recording system.
    """

    # NOTE (Phase 3 results split): the HTML ``templates/v2`` assets these paths point at have
    # relocated to codecraftai-integration-runtime (ccai.integrationruntime.templates.v2), resolved
    # there by ccai.integrationruntime.initialize.IntegrationResultResources. This module's
    # initialize_testbase_results is the SUPERSEDED integration-results init (its live replacement is
    # integration-runtime's initialize_integration_results, Phase 4a) and is scheduled for removal
    # with the rest of the integration CLI bootstrap in the Phase 2-tail CLI relocation. The
    # near-standalone testbase run path does not read these constants (it resolves output via the
    # IOutputContext seam, whose SimpleOutputContext returns no template), so these now point at a
    # directory that no longer ships in testbase.
    TESTPLUS_TEMPLATES_DIR = os.path.join(TESTPLUS_DIR, "templates")
    TESTPLUS_RESOURCE_DEST_LEAF = os.path.join("static", "v2")
    TESTPLUS_RESOURCE_SRC_DIR = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "static")
    TESTPLUS_SUMMARY_TEMPLATE = os.path.join(TESTPLUS_TEMPLATES_DIR, "v2", "testsummary.html")
    

def initialize_testbase_runtime():
    """
        Initializes the TestBase runtime environment.

        This function establishes the application persona and resolves all runtime variables
        from environment and configuration sources. It must be called before any other
        TestBase operations to ensure the framework is properly configured.

        :returns: None
        :rtype: None

        Initialization Steps:
            1. Set the application name to ``"ccai"``
            2. Set the home directory to ``~/ccai`` (user's home directory)
            3. Set the logger name prefix to ``"TB"`` for log message identification
            4. Set the log basename to ``"testrun"`` for log file naming
            5. Resolve all runtime variables from environment and configuration files

        Configuration:
            The following application persona settings are established:

            ==================  ================  ==========================================
            Setting             Value             Description
            ==================  ================  ==========================================
            name                ``"ccai"``    Application identifier
            home_dir            ``~/ccai``    Configuration and data directory
            logger_name         ``"TB"``          Prefix for log messages
            log_basename        ``"testrun"``     Base name for log files
            ==================  ================  ==========================================

        Example:
            Basic initialization::

                from ccai.testbase.initialize import initialize_testbase_runtime

                # Initialize the runtime environment
                initialize_testbase_runtime()

                # Now other TestBase operations can be performed

        .. note::
            This function should be called once at the start of test execution. It is
            automatically called by :func:`generic_test_entrypoint` and the CLI commands.

        .. seealso::
            :func:`initialize_testbase_results` : Initializes the results recording system
            :func:`generic_test_entrypoint` : Calls this function during entry point initialization
    """

    name="ccai"
    home_dir = os.path.join(os.path.expanduser("~"), name)
    
    establish_app_persona(name=name, home_dir=home_dir, logger_name="TB", log_basename="testrun")

    resolve_runtime_variables()

    return

def initialize_testbase_results():
    """
        Initializes the TestBase results recording system.

        This function configures the paths and templates used for recording and presenting
        test results. It sets up static resource directories and the HTML summary template
        if they have not already been configured, then activates the TestRun job profile.

        :returns: None
        :rtype: None

        Configuration Variables:
            The following runtime variables are configured if not already set:

            ======================================  ==========================================
            Variable                                Default Value
            ======================================  ==========================================
            AM_RESULTS_STATIC_RESOURCE_SRC_DIR      ``<testbase>/templates/v2/static``
            AM_RESULTS_STATIC_RESOURCE_DEST_DIR     ``<presence>/results/static/v2``
            AM_RESULTS_STATIC_SUMMARY_TEMPLATE      ``<testbase>/templates/v2/testsummary.html``
            ======================================  ==========================================

        Initialization Steps:
            1. Compute the destination directory for static resources based on the presence directory
            2. Set ``AM_RESULTS_STATIC_RESOURCE_SRC_DIR`` if not already configured
            3. Set ``AM_RESULTS_STATIC_RESOURCE_DEST_DIR`` if not already configured
            4. Set ``AM_RESULTS_STATIC_SUMMARY_TEMPLATE`` if not already configured
            5. Activate the TestRun job profile

        Example:
            Basic initialization (typically called after runtime initialization)::

                from ccai.testbase.initialize import (
                    initialize_testbase_runtime,
                    initialize_testbase_results
                )

                # Initialize runtime first
                initialize_testbase_runtime()

                # Then initialize results
                initialize_testbase_results()

        .. note::
            This function should be called after :func:`initialize_testbase_runtime` to ensure
            the application persona and runtime variables are properly established. It is
            automatically called by :func:`generic_test_entrypoint` and the CLI commands.

        .. seealso::
            :func:`initialize_testbase_runtime` : Initializes the runtime environment
            :class:`TestBaseConstants` : Provides the default paths used for configuration
            :func:`generic_test_entrypoint` : Calls this function during entry point initialization
    """

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
