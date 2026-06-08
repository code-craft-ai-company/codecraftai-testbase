"""
    .. module:: ccai.testbase.queries
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for queries.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


import inspect
import os
import fnmatch
import sys
import traceback

from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger
from ccai.xmodules.ximport import import_by_name

from ccai.testbase.testref import TestRef

logger = getEnhancedLogger()

def collect_test_references(root, included_files, filter_package, filter_module, filter_testname, test_prefix):
    """
        Collects references to test functions based on the filters provided.

        :param str root: Path to the root package containing tests.
        :param list included_files: Paths to files that may contain test functions.
        :param str filter_package: Optional filter expression for packages.
        :param str filter_module: Optional filter expression for modules.
        :param str filter_testname: Optional glob expression for test function names.
        :param str test_prefix: Prefix indicating test functions.

        :returns: A tuple ``(test_references, import_errors)`` describing collected tests and import errors.
        :rtype: Tuple[dict, dict]
    """

    test_references = {}

    import_errors = {}

    root_pkgname = os.path.basename(root)

    # Go through the files and import them, then go through the classes and find the TestPack and
    # TestContainer objects that match the specified include expression criteria
    rootlen = len(root)
    for ifile in included_files:
        modname = None
        try:
            ifilebase, _ = os.path.splitext(ifile)
            ifileleaf = ifilebase[rootlen:].strip("/")
            modname = "{}.{}".format(root_pkgname, ifileleaf.replace("/", "."))

            # Import the module for the file being processed
            mod = None
            if modname in sys.modules:
                mod = sys.modules[modname]
            else:
                mod = import_by_name(modname)

            # Go through all of the members of the
            candidate_function_coll = inspect.getmembers(mod, inspect.isfunction)
            for function_name, function_obj in candidate_function_coll:
                cand_module_name = function_obj.__module__
                # We only want to include the classes that are from the target module
                if cand_module_name != modname:
                    continue

                if function_name.startswith(test_prefix):
                    if filter_testname is not None:
                        # If we have a testname expression only add a reference to the test function
                        # if the function_name matches the filter expression
                        if fnmatch.fnmatch(function_name, filter_testname):
                            tref = TestRef(function_obj, is_async=inspect.iscoroutinefunction(function_obj))
                            test_references[tref.name] = tref
                    else:
                        tref = TestRef(function_obj, is_async=inspect.iscoroutinefunction(function_obj))
                        test_references[tref.name] = tref

        except ImportError:
            errmsg = traceback.format_exc()
            print(errmsg)
            import_errors[ifile] = (modname, ifile, errmsg)

    for modname, ifile, errmsg in import_errors.values():
        logger.error("TestCase: Import error filename=%r" % ifile)

    return test_references, import_errors

