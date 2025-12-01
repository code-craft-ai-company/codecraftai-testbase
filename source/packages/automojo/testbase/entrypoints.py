"""
    .. module:: automojo.testbase.entrypoints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for entrypoints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional, Type

import argparse
import inspect
import os
import sys

from automojo.xmodules.xlogging.levels import LOG_LEVEL_NAMES
from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger
from automojo.xmodules.ximport import import_by_name

from automojo.thisapp.wellknown import ThisApplicationSingleton

from automojo.runtime.paths import get_path_for_testresults

from automojo.testbase.injection.injectionregistry import InjectionRegistry

from automojo.testbase.utilities import find_testmodule_root, find_testmodule_fullname
from automojo.testbase.testjob import TestJob, DefaultTestJob


def generic_test_entrypoint(job_type: Optional[Type[TestJob]] = DefaultTestJob):
    """
        This is the generic test entry point for test modules.  It provides a standardized set of
        commanline parameters that can be used to run test files as scripts.

        .. note::
            The ``generic_test_entrypoint`` is a useful tool to place at the bottom of test files to
            allow them to easily be run for debugging purposes.
    """
    from automojo.testbase.initialize import initialize_testbase_runtime, initialize_testbase_results
    initialize_testbase_runtime()

    from automojo.runtime.activation import activate_profile_job, JobType

    activate_profile_job(job_type=JobType.TestRun)

    initialize_testbase_results()

    # We must exit with a result code, initialize it to 0 here
    result_code = 0

    base_parser = argparse.ArgumentParser()

    base_parser.add_argument("-i", "--include", dest="includes", action="append", default=[], help="Add an include search statement.")
    base_parser.add_argument("-x", "--exclude", dest="excludes", action="append", default=[], help="Add an exclude filter statement.")
    base_parser.add_argument("--console-level", dest="consolelevel", action="store", default="INFO", choices=LOG_LEVEL_NAMES, help="The logging level for console output.")
    base_parser.add_argument("--logfile-level", dest="logfilelevel", action="store", default="DEBUG", choices=LOG_LEVEL_NAMES, help="The logging level for logfile output.")

    test_module = sys.modules["__main__"]

    ctx = ContextSingleton()
    env = ctx.lookup("/environment")

    # Set the jobtype
    env["jobtype"] = "testrun"

    test_results_dir = get_path_for_testresults()
    if not os.path.exists(test_results_dir):
        os.makedirs(test_results_dir)
    env["output_directory"] = test_results_dir

    logger = getEnhancedLogger()

    tpmod = sys.modules["automojo.testbase"]
    tpmod.logger = logger

    testroot = find_testmodule_root(test_module)
    module_fullname = find_testmodule_fullname(test_module, testroot=testroot)
    
    module_lastdot = module_fullname.rfind('.')
    if module_lastdot > -1:
        # We need to import every module up to the test module
        parent_module_name = module_fullname[:module_lastdot]
        import_by_name(parent_module_name)

    # Copy the test module to the name of the module_fullname name so the loader won't reload it
    sys.modules[module_fullname] = test_module

    if test_module.__name__ == "__main__":
        test_module.__name__ = module_fullname

        # Re-map the object classes from the module over to the module name we just registered the test
        # module under.
        test_class_coll = inspect.getmembers(test_module, inspect.isclass)
        for testclass_name, testclass_obj in test_class_coll:
            tcobj_module_name = testclass_obj.__module__
            if tcobj_module_name == "__main__":
                testclass_obj.__module__ = module_fullname
        
        # Re-map the object function objects from the module over to the module name we just registered
        # the test module under.
        test_func_coll = inspect.getmembers(test_module, inspect.isfunction)
        for testfunc_name, testfunc_obj in test_func_coll:
            tfobj_module_name = testfunc_obj.__module__
            if tfobj_module_name == "__main__":
                testfunc_obj.__module__ = module_fullname

        resource_registry = InjectionRegistry()
        resource_registry.rename_resource_origins_from_main(module_fullname)

    args = base_parser.parse_args()
    
    includes = args.includes
    excludes = args.excludes
    if len(includes) == 0:
        includes.append("*")

    result_code = 0
    with job_type(logger, testroot, includes=includes, excludes=excludes, test_module=test_module) as tjob:
        result_code = tjob.execute()

    sys.exit(result_code)

    return
