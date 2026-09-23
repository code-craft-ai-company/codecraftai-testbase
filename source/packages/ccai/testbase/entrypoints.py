"""
    .. module:: ccai.testbase.entrypoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for entrypoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Optional, Type

import argparse
import inspect
import sys

from ccai.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger
from ccai.xmodules.ximport import import_by_name

from ccai.testbase.injection.injectionregistry import InjectionRegistry

from ccai.testbase.utilities import find_testmodule_root, find_testmodule_fullname
from ccai.testbase.testjob import TestJob, DefaultTestJob
from ccai.testbase.configuration import load_entrypoint_configuration
from ccai.testbase.markers import parse_marker_expression


def validate_log_level(value: str) -> str:
    """
        Validate that a log level value is one of the allowed log level names.

        This function provides enhanced validation for command-line log level arguments,
        offering helpful error messages when invalid values are provided.

        :param value: The log level value to validate.
        :type value: str

        :returns: The validated log level value (uppercase).
        :rtype: str

        :raises argparse.ArgumentTypeError: If the value is not a valid log level name.
            The error message includes the invalid value and lists all valid options.

        Example:
            >>> validate_log_level("DEBUG")
            'DEBUG'
            >>> validate_log_level("debug")
            'DEBUG'
            >>> validate_log_level("INVALID")
            Traceback (most recent call last):
                ...
            argparse.ArgumentTypeError: Invalid log level 'INVALID'. Valid options are: ...
    """
    # Normalize to uppercase for case-insensitive comparison
    normalized_value = value.upper()
    
    if normalized_value not in LOG_LEVEL_NAMES:
        valid_options = ", ".join(LOG_LEVEL_NAMES)
        raise argparse.ArgumentTypeError(
            f"Invalid log level '{value}'. Valid options are: {valid_options}. "
            f"Log levels control the verbosity of output - use DEBUG for detailed "
            f"information, INFO for general messages, WARNING for potential issues, "
            f"ERROR for errors only, or CRITICAL for critical errors only."
        )
    
    return normalized_value


def validate_marker_expression(value: str) -> str:
    """
        Validate that a marker expression is syntactically correct.

        This function provides validation for command-line marker expression arguments,
        offering helpful error messages when invalid expressions are provided.

        Marker expressions must follow the format:
            (+|-)(group)(operator)(value)

        Where:
            - + indicates include, - indicates exclude
            - group is the metadata group name (e.g., categories, keywords, priority)
            - operator is one of: == (equals), ~= (contains), != (not equals)
            - value is the value to match against

        :param value: The marker expression to validate.
        :type value: str

        :returns: The validated marker expression.
        :rtype: str

        :raises argparse.ArgumentTypeError: If the expression is not valid.
            The error message includes the invalid expression and format guidance.

        Example:
            >>> validate_marker_expression("+categories~=unit")
            '+categories~=unit'
            >>> validate_marker_expression("-priority==1")
            '-priority==1'
            >>> validate_marker_expression("invalid")
            Traceback (most recent call last):
                ...
            argparse.ArgumentTypeError: Invalid marker expression 'invalid'. ...
    """
    from ccai.errors.exceptions import SemanticError
    
    # Application/CLI boundary: this is an argparse type-validator, so the
    # "API misuse" being reported is a malformed expression the operator typed.
    # Translating it into ArgumentTypeError still terminates the process (argparse
    # prints the message and exits), which is the application layer exercising the
    # flow control it owns.  Library code must NOT copy this pattern -- inside a
    # library a SemanticError has to bubble untouched.
    try:
        # Attempt to parse the expression to validate it
        parse_marker_expression(value)
        return value
    except SemanticError as ex:
        raise argparse.ArgumentTypeError(
            f"Invalid marker expression '{value}'. "
            f"Marker expressions must be in the format: (+|-)(group)(operator)(value). "
            f"Examples: '+categories~=unit', '-priority==1', '+keywords~=smoke'. "
            f"Operators: == (equals), ~= (contains), != (not equals). "
            f"Error: {str(ex)}"
        )
    except Exception as ex:
        raise argparse.ArgumentTypeError(
            f"Invalid marker expression '{value}'. "
            f"Marker expressions must be in the format: (+|-)(group)(operator)(value). "
            f"Examples: '+categories~=unit', '-priority==1', '+keywords~=smoke'. "
            f"Operators: == (equals), ~= (contains), != (not equals). "
            f"Error: {str(ex)}"
        )


def generic_test_entrypoint(job_type: Optional[Type[TestJob]] = DefaultTestJob):
    """
        Generic test entry point for running test modules as standalone scripts.

        This function provides a standardized mechanism for initiating test execution from
        individual test modules. It handles all critical initialization tasks including
        runtime environment setup, test module name resolution and registration, Python
        path management, command-line argument parsing, and test job execution orchestration.

        :param job_type: The TestJob class to use for test execution. This allows customization
            of test execution behavior by providing a custom TestJob subclass.
            Defaults to ``DefaultTestJob``.
        :type job_type: Optional[Type[TestJob]]

        :returns: This function does not return; it calls ``sys.exit()`` with the test result code.
        :rtype: None

        :raises ConfigurationError: If the test module is not located within a test root
            directory marked with a ``__testroot__.py`` file.
        :raises SystemExit: Always raised with the test result code (0 for success,
            non-zero for failures).

        Configuration Files:
            The entry point supports loading default options from configuration files.
            Configuration files are searched in the following order (highest precedence first):

            1. Command-line arguments (always override)
            2. Project-level: ``.testbase.yaml`` or ``.testbase.yml`` in current directory
               or any parent directory
            3. User-level: ``~/.ccai/testbase.yaml`` or ``~/.ccai/testbase.yml``
            4. Built-in defaults

            Example configuration file (``.testbase.yaml``)::

                includes:
                  - "test_unit_*"
                  - "test_integration_*"
                excludes:
                  - "test_slow_*"
                console_level: INFO
                logfile_level: DEBUG

        Command Line Arguments:
            -i, --include : Add an include search statement. Can be specified multiple times.
                When no includes are provided, defaults to configuration file values or ``["*"]``.
            -x, --exclude : Add an exclude filter statement. Can be specified multiple times.
            --include-marker : Add a marker-based include filter. Can be specified multiple times.
                Format: (+|-)(group)(operator)(value). Examples: '+categories~=unit', '+priority==1'.
                Operators: == (equals), ~= (contains), != (not equals).
            --exclude-marker : Add a marker-based exclude filter. Can be specified multiple times.
                Format: (-)(group)(operator)(value). Examples: '-categories~=slow', '-priority==3'.
                Note: The leading - is required for exclude markers.
            --console-level : Logging level for console output. Choices: DEBUG, INFO, WARNING,
                ERROR, CRITICAL. Default: INFO (or configuration file value).
            --logfile-level : Logging level for logfile output. Choices: DEBUG, INFO, WARNING,
                ERROR, CRITICAL. Default: DEBUG (or configuration file value).

        Initialization Sequence:
            1. Initialize TestBase runtime environment (application persona, runtime variables)
            2. Activate the TestRun job profile
            3. Initialize the test results recording system
            4. Configure environment context (jobtype, output_directory)
            5. Resolve test module identity (find test root, compute full module name)
            6. Register module in sys.modules under its full name
            7. Remap class and function ``__module__`` attributes from ``__main__``
            8. Rename injection registry resource origins from ``__main__``
            9. Parse command-line arguments
            10. Create and execute the TestJob
            11. Exit with the test result code

        Example:
            Add to the bottom of any test module to enable direct execution::

                # test_example.py
                from ccai.testbase.declaration import testcontainer, test

                @testcontainer()
                class TestExample:

                    @test()
                    def test_something(self):
                        assert True

                # Enable direct execution for debugging
                if __name__ == "__main__":
                    from ccai.testbase.entrypoints import generic_test_entrypoint
                    generic_test_entrypoint()

        Example with custom job type::

            from ccai.testbase.testjob import TestJob

            class CustomTestJob(TestJob):
                name = "Custom Test Suite"
                description = "Tests with custom configuration"

            if __name__ == "__main__":
                from ccai.testbase.entrypoints import generic_test_entrypoint
                generic_test_entrypoint(job_type=CustomTestJob)

        Example with command-line filters::

            # Run only tests matching pattern
            python test_module.py -i "test_feature_*"

            # Run all except slow tests
            python test_module.py -i "*" -x "test_slow_*"

            # Multiple includes with verbose logging
            python test_module.py -i "test_unit_*" -i "test_integration_*" --console-level DEBUG

        .. note::
            The ``generic_test_entrypoint`` is a useful tool to place at the bottom of test files
            to allow them to easily be run for debugging purposes. It provides the same
            initialization as the CLI command but allows running individual test files directly.

        .. seealso::
            :func:`find_testmodule_root` : Discovers the test root directory
            :func:`find_testmodule_fullname` : Computes the full dotted module name
            :func:`initialize_testbase_runtime` : Initializes the runtime environment
            :func:`initialize_testbase_results` : Initializes the results recording system
    """
    # Standalone entry point: no runtime activation. Results record to stdout via the
    # StdoutResultRecorder and artefacts (if any) land under the SimpleOutputContext base dir.
    # The integration entry point (ccai.integrationruntime.entrypoints) performs the
    # this-app activation before delegating here when an IntegratedTestJob is in play.

    # We must exit with a result code, initialize it to 0 here
    result_code = 0

    # =========================================================================
    # CONFIGURATION FILE LOADING
    # =========================================================================
    # Load configuration from user-level and project-level configuration files.
    # Configuration precedence (highest to lowest):
    #   1. Command-line arguments (always override)
    #   2. Project-level configuration (.testbase.yaml in current or parent dirs)
    #   3. User-level configuration (~/.ccai/testbase.yaml)
    #   4. Built-in defaults
    #
    # This allows users to set default options in configuration files to reduce
    # command-line verbosity for common scenarios.
    # =========================================================================
    file_config = load_entrypoint_configuration()

    # Determine default values from configuration files or built-in defaults
    default_console_level = file_config.console_level if file_config.console_level else "INFO"
    default_logfile_level = file_config.logfile_level if file_config.logfile_level else "DEBUG"

    base_parser = argparse.ArgumentParser()

    base_parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
    base_parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
    base_parser.add_argument("--include-marker", dest="include_markers", action="append", default=[], type=validate_marker_expression, metavar="EXPR", help="Add a marker-based include filter. Format: (+)(group)(operator)(value). Examples: '+categories~=unit', '+priority==1'. Operators: == (equals), ~= (contains), != (not equals).")
    base_parser.add_argument("--exclude-marker", dest="exclude_markers", action="append", default=[], type=validate_marker_expression, metavar="EXPR", help="Add a marker-based exclude filter. Format: (-)(group)(operator)(value). Examples: '-categories~=slow', '-priority==3'. Note: The leading - is required for exclude markers.")
    base_parser.add_argument("--console-level", dest="consolelevel", action="store", default=default_console_level, type=validate_log_level, metavar="LEVEL", help="The logging level for console output. Valid options: " + ", ".join(LOG_LEVEL_NAMES) + ". Default: INFO.")
    base_parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default=default_logfile_level, type=validate_log_level, metavar="LEVEL", help="The logging level for logfile output. Valid options: " + ", ".join(LOG_LEVEL_NAMES) + ". Default: DEBUG.")

    test_module = sys.modules["__main__"]

    logger = getEnhancedLogger()

    tpmod = sys.modules["ccai.testbase"]
    tpmod.logger = logger

    # =========================================================================
    # MODULE RESOLUTION ALGORITHM
    # =========================================================================
    # When a test module is run directly (python test_module.py), Python loads
    # it as "__main__" instead of its proper dotted module name. This causes
    # problems because:
    #   1. The test framework identifies tests by their full module path
    #   2. Dependency injection uses module names to track resource origins
    #   3. The module loader may reload the module under its proper name
    #
    # To fix this, we need to:
    #   Step 1: Find the test root directory (marked by __testroot__.py)
    #   Step 2: Compute the full dotted module name from the path
    #   Step 3: Register the module under its proper name in sys.modules
    #
    # Example: If test_module.py is at /project/tests/unit/test_auth.py
    #          and __testroot__.py is at /project/tests/__testroot__.py
    #          then the full module name is "tests.unit.test_auth"
    # =========================================================================
    
    # Step 1: Walk up the directory tree to find the test root
    # The test root is identified by the presence of __testroot__.py marker file
    testroot = find_testmodule_root(test_module)
    
    # Step 2: Compute the full dotted module name
    # This converts the file path relative to testroot into a dotted name
    # e.g., /project/tests/unit/test_auth.py -> tests.unit.test_auth
    module_fullname = find_testmodule_fullname(test_module, testroot=testroot)
    
    # Step 3: Import parent modules before registering the test module
    # Python requires parent packages to be imported before child modules
    # can be properly registered. For "tests.unit.test_auth", we must first
    # import "tests.unit" to ensure the package hierarchy exists.
    module_lastdot = module_fullname.rfind('.')
    if module_lastdot > -1:
        # Extract parent module name (e.g., "tests.unit" from "tests.unit.test_auth")
        parent_module_name = module_fullname[:module_lastdot]
        # Import all parent modules in the hierarchy
        import_by_name(parent_module_name)

    # Step 4: Register the test module under its full name in sys.modules
    # This prevents the module loader from reloading the module when it's
    # imported by name elsewhere. Without this, we'd have two copies of the
    # module: one as "__main__" and one as "tests.unit.test_auth"
    sys.modules[module_fullname] = test_module

    # =========================================================================
    # CLASS AND FUNCTION MODULE ATTRIBUTE REMAPPING
    # =========================================================================
    # When Python loads a module as "__main__", all classes and functions
    # defined in that module have their __module__ attribute set to "__main__".
    # This causes problems because:
    #   1. Test discovery uses __module__ to identify which module a test belongs to
    #   2. Error messages and stack traces show "__main__" instead of the real path
    #   3. Serialization/pickling may fail due to module name mismatches
    #
    # We need to update the __module__ attribute of all classes and functions
    # that were originally defined in "__main__" to use the proper module name.
    #
    # Note: We only update items where __module__ == "__main__" to avoid
    # changing imported classes/functions from other modules.
    # =========================================================================
    
    if test_module.__name__ == "__main__":
        # Update the module's own __name__ attribute to the full module name
        test_module.__name__ = module_fullname

        # -----------------------------------------------------------------
        # CLASS REMAPPING
        # -----------------------------------------------------------------
        # Iterate over all classes defined in the test module and update
        # their __module__ attribute from "__main__" to the full module name.
        #
        # inspect.getmembers with inspect.isclass returns all class objects
        # in the module, including imported classes. We filter to only update
        # classes that were originally defined in this module (__main__).
        # -----------------------------------------------------------------
        test_class_coll = inspect.getmembers(test_module, inspect.isclass)
        for testclass_name, testclass_obj in test_class_coll:
            tcobj_module_name = testclass_obj.__module__
            # Only remap classes originally defined in __main__
            # Imported classes retain their original module attribution
            if tcobj_module_name == "__main__":
                testclass_obj.__module__ = module_fullname
        
        # -----------------------------------------------------------------
        # FUNCTION REMAPPING
        # -----------------------------------------------------------------
        # Iterate over all functions defined in the test module and update
        # their __module__ attribute from "__main__" to the full module name.
        #
        # This is similar to class remapping but for standalone functions.
        # Test functions decorated with @test() need proper module attribution
        # for the test framework to correctly identify and organize them.
        # -----------------------------------------------------------------
        test_func_coll = inspect.getmembers(test_module, inspect.isfunction)
        for testfunc_name, testfunc_obj in test_func_coll:
            tfobj_module_name = testfunc_obj.__module__
            # Only remap functions originally defined in __main__
            # Imported functions retain their original module attribution
            if tfobj_module_name == "__main__":
                testfunc_obj.__module__ = module_fullname

        # -----------------------------------------------------------------
        # INJECTION REGISTRY ORIGIN RENAMING
        # -----------------------------------------------------------------
        # The dependency injection system tracks resource origins using the
        # module name where resources were registered. When decorators like
        # @integration, @resource, or @configuration are executed during
        # module loading, they register resources with origins like:
        #   "__main__#function_name"
        #
        # These origins need to be renamed to use the proper module path:
        #   "tests.unit.test_auth#function_name"
        #
        # This ensures that:
        #   1. Resource lookups work correctly during test execution
        #   2. Scope resolution can properly match resources to their origins
        #   3. Error messages show meaningful module paths
        #
        # The rename operation walks the injection scope tree and updates
        # all resource origins that reference "__main__" to use the full
        # module name instead.
        # -----------------------------------------------------------------
        resource_registry = InjectionRegistry()
        resource_registry.rename_resource_origins_from_main(module_fullname)

    args = base_parser.parse_args()
    
    # =========================================================================
    # MERGE CONFIGURATION FILE VALUES WITH COMMAND-LINE ARGUMENTS
    # =========================================================================
    # Command-line arguments take precedence over configuration file values.
    # If no command-line includes/excludes are provided, use values from
    # configuration files. If no configuration file values exist either,
    # default to including all tests with "*".
    # =========================================================================
    includes = args.includes
    excludes = args.excludes
    
    # If no command-line includes provided, use configuration file values
    if len(includes) == 0:
        if file_config.includes:
            includes = file_config.includes
        else:
            includes.append("*")
    
    # If no command-line excludes provided, use configuration file values
    if len(excludes) == 0 and file_config.excludes:
        excludes = file_config.excludes

    # =========================================================================
    # MARKER EXPRESSION PARSING
    # =========================================================================
    # Parse marker expressions from command-line arguments into MetaFilter objects.
    # Marker expressions allow filtering tests based on metadata such as categories,
    # keywords, or priority. The expressions are parsed using parse_marker_expression
    # which returns MetaFilter objects that can be used by the TestSequencer.
    #
    # Include markers use the + prefix: +categories~=unit
    # Exclude markers use the - prefix: -categories~=slow
    # =========================================================================
    metafilters = []
    
    # Parse include marker expressions
    for marker_expr in args.include_markers:
        metafilter = parse_marker_expression(marker_expr)
        metafilters.append(metafilter)
    
    # Parse exclude marker expressions
    for marker_expr in args.exclude_markers:
        metafilter = parse_marker_expression(marker_expr)
        metafilters.append(metafilter)

    result_code = 0
    with job_type(logger, testroot, includes=includes, excludes=excludes, metafilters=metafilters, test_module=test_module) as tjob:
        result_code = tjob.execute()

    sys.exit(result_code)

    return
