"""
    .. module:: automojo.testbase.utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for utilities.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Dict, Union

import fnmatch
import json
import os

from automojo.errors.exceptions import ConfigurationError, UnSupportedPlatformError
from automojo.xmodules.ximport import import_file

def catalog_tree(rootdir: str, ignore_dirs=[]):
    """
        Adds json catalog files to a file system tree to help provide directory
        services to javascript in html files.
    """
    for dirpath, dirnames, filenames in os.walk(rootdir, topdown=True):
        dir_base_name = os.path.basename(dirpath)
        if dir_base_name not in ignore_dirs:

            for igdir in ignore_dirs:
                if igdir in dirnames:
                    dirnames.remove(igdir)

            catalog = {
                "files": filenames,
                "folders": dirnames
            }

            catalogfile = os.path.join(dirpath, "catalog.json")
            with open(catalogfile, 'w') as cf:
                json.dump(catalog, cf, indent=4)

    return

def create_testpack_key(testpack_cls):
    mtpkey = testpack_cls.__module__ + "@" + testpack_cls.__name__
    return mtpkey

def _build_platforms_module_name(root: str, dirpath: str) -> str:
    root = os.path.abspath(root)
    dirpath = os.path.abspath(dirpath)

    root_pkg = os.path.basename(root)
    rel_dir = os.path.relpath(dirpath, root)

    if rel_dir in (".", ""):
        modname = "{}.{}".format(root_pkg, "__platforms__")
    else:
        rel_mod = rel_dir.replace(os.path.sep, ".")
        modname = "{}.{}.{}".format(root_pkg, rel_mod, "__platforms__")

    return modname

def _is_platform_supported(root: str, dirpath: str, platforms_cache: Dict[str, bool]) -> bool:
    dirpath = os.path.abspath(dirpath)

    if dirpath in platforms_cache:
        return platforms_cache[dirpath]

    platforms_file = os.path.join(dirpath, "__platforms__.py")
    if not os.path.exists(platforms_file):
        platforms_cache[dirpath] = True
        return True

    modname = _build_platforms_module_name(root, dirpath)

    try:
        import_file(modname, platforms_file)
    except UnSupportedPlatformError:
        platforms_cache[dirpath] = False
        return False
    # If the exception is unexpected, just let it bubble

    platforms_cache[dirpath] = True

    return True

def collect_python_modules_for_tests(search_dir: str, root: str, platforms_cache: Dict[str, bool], max_depth=None):
    """
        Walks a directory tree of python modules and collects the names
        of all of the python module files or .py files.  This method allows
        for python namespaces by not forcing the root folder to contain a
        __init__.py file.  The search will skip any directory whose
        __platforms__.py file raises UnSupportedPlatformError.

        :params searchdir: The root directory to search when collecting python modules.
        :params root: The root directory used to calculate module names for __platforms__.py files.
        :params platforms_cache: A cache of directory paths to platform support decisions.
        :params max_depth: The maximum depth to search for python modules.  If this is None
                        then the entire directory tree will be searched.  If this is
                        an integer then the search will be limited to that depth.
        
        :returns: A list of the full paths to the python module files.
    """
    pyfiles = []

    search_dir = os.path.abspath(search_dir)
    root = os.path.abspath(root)
    search_dir_len = len(search_dir)

    if not _is_platform_supported(root, search_dir, platforms_cache):
        return pyfiles

    for root_dir, dirnames, files in os.walk(search_dir, topdown=True):

        if not _is_platform_supported(root, root_dir, platforms_cache):
            dirnames[:] = []
            continue

        if max_depth is not None:
            dir_leaf = root_dir[search_dir_len:].strip(os.path.sep)
            depth = 0
            if dir_leaf != '':
                dir_leaf_parts = dir_leaf.split(os.path.sep)
                depth = len(dir_leaf_parts)
                if depth > max_depth:
                    dirnames[:] = []
                    continue

        if len(dirnames) > 0:
            supported_dirnames = []
            for dname in dirnames:
                dpath = os.path.join(root_dir, dname)
                if _is_platform_supported(root, dpath, platforms_cache):
                    supported_dirnames.append(dname)
            dirnames[:] = supported_dirnames

        for fname in files:
            fbase, fext = os.path.splitext(fname)
            if fext == '.py' and fbase not in ("__init__", "__platforms__"):
                ffull = os.path.join(root_dir, fname)
                pyfiles.append(ffull)

    return pyfiles

def find_included_modules_under_root(root: str, package: Union[str, None], module: str, excluded_path_prefixes: list = []):
    """
        Walks through a directory tree starting at a root directory and finds all of the files that corresponded to
        the package, module expressions specified.

        :param root: The root directory to start from when performing the tree walk to look
                     for included tests.
        :param package: The package name component if there is one.  The package components are the directories
                        with __init__.py files up to the file where the module file itself is found. It could be
                        that there is only a module name.
        :param module: The module name component.  There must be a module because that is the file where the tests
                       are found.
    """

    root_pkg = os.path.basename(root)

    included_file_candidates = set()
    platforms_cache: Dict[str, bool] = {}

    if not _is_platform_supported(root, root, platforms_cache):
        return [], []

    if package is None:
        # If package is None, then we had a single item expression, this means
        # we can look for a single file, or a directory with lots of files.
        filenames = os.listdir(root)
        for fname in filenames:
            pkg_name = "{}.{}".format(root_pkg, fname)
            if pkg_name.startswith(module) or fnmatch.fnmatch(pkg_name, module):
                ffull = os.path.join(root, fname)
                if os.path.isfile(ffull):
                    fbase, fext = os.path.splitext(fname)
                    if fext == ".py" and fbase not in ("__init__", "__platforms__"):
                        included_file_candidates.add(ffull)
                elif os.path.isdir(ffull):
                    module_list = collect_python_modules_for_tests(ffull, root, platforms_cache)
                    for mod in module_list:
                        included_file_candidates.add(mod)
    else:
        pkgpathpfx = package.replace(".", "/")
        fullpathpfx = pkgpathpfx + "/" + module
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            if not _is_platform_supported(root, dirpath, platforms_cache):
                dirnames[:] = []
                continue

            if len(dirnames) > 0:
                supported_dirnames = []
                for dname in dirnames:
                    dpath = os.path.join(dirpath, dname)
                    if _is_platform_supported(root, dpath, platforms_cache):
                        supported_dirnames.append(dname)
                dirnames[:] = supported_dirnames

            dirleaf = root_pkg + "/" + dirpath[len(root):].lstrip(os.sep)
            dirleaf = dirleaf.rstrip("/")

            if dirleaf.startswith(fullpathpfx) or fnmatch.fnmatch(dirleaf, fullpathpfx):
                collected_modules = collect_python_modules_for_tests(dirpath, root, platforms_cache)
                for cm in collected_modules:
                    included_file_candidates.add(cm)
            elif dirleaf.startswith(pkgpathpfx) or fnmatch.fnmatch(dirleaf, pkgpathpfx):
                for fname in filenames:
                    fbase, fext = os.path.splitext(fname)
                    if fext == ".py" and fbase not in ("__init__", "__platforms__") and \
                        (fbase.startswith(module) or fnmatch.fnmatch(fbase, module)):
                        ffull = os.path.join(dirpath, fname)
                        included_file_candidates.add(ffull)

    included_files = []
    excluded_files = []

    while len(included_file_candidates) > 0:
        candidate_file: str = included_file_candidates.pop()

        keep_file = True
        for expfx in excluded_path_prefixes:
            if candidate_file.startswith(expfx):
                keep_file = False
                break

        if keep_file:
            included_files.append(candidate_file)
        else:
            excluded_files.append(candidate_file)

    return included_files, excluded_files

def find_testmodule_root(module) -> str:
    """
        Discovers the test root directory for a given test module.

        This function walks up the directory tree from the module's location until it finds
        a directory containing a ``__testroot__.py`` marker file. The test root directory
        defines the boundary of the test package namespace and is essential for proper
        module name resolution.

        :param module: The test module object (typically ``sys.modules["__main__"]``) for which
            to find the test root directory. The module must have a ``__file__`` attribute
            pointing to its source file location.
        :type module: ModuleType

        :returns: The absolute path to the test root directory containing the
            ``__testroot__.py`` marker file.
        :rtype: str

        :raises ConfigurationError: If no ``__testroot__.py`` marker file is found when
            walking up the directory tree to the filesystem root. The error message indicates
            that test files must exist inside a test root directory marked with a
            ``__testroot__.py`` file.

        Algorithm:
            1. Start from the directory containing the module's source file
            2. Check if ``__testroot__.py`` exists in the current directory
            3. If found, return the current directory path
            4. If not found, move to the parent directory
            5. Repeat until found or filesystem root is reached
            6. If filesystem root is reached without finding the marker, raise ConfigurationError

        Example:
            Given a test file structure::

                tests/
                ├── __testroot__.py    # Marker file
                ├── __init__.py
                └── package/
                    ├── __init__.py
                    └── test_module.py

            When called with the test_module module::

                import sys
                test_module = sys.modules["__main__"]
                root = find_testmodule_root(test_module)
                # Returns: "/path/to/tests"

        .. note::
            The ``__testroot__.py`` marker file can be empty or contain test root configuration.
            Its presence alone is sufficient to mark the test root boundary.

        .. seealso::
            :func:`find_testmodule_fullname` : Uses the test root to compute the full module name
    """
    # =========================================================================
    # TEST ROOT DISCOVERY ALGORITHM
    # =========================================================================
    # The test root is the directory that contains the __testroot__.py marker
    # file. This marker defines the boundary of the test package namespace.
    #
    # Why we need this:
    #   - Python modules are identified by their dotted path from a root
    #   - Without a marker, we wouldn't know where the module namespace begins
    #   - The marker allows test files to be organized in any directory structure
    #
    # Algorithm: Walk up the directory tree until we find __testroot__.py
    #   1. Start at the directory containing the test module file
    #   2. Check if __testroot__.py exists in current directory
    #   3. If found, return this directory as the test root
    #   4. If not found, move to parent directory and repeat
    #   5. If we reach filesystem root without finding marker, raise error
    #
    # Example directory structure:
    #   /project/tests/__testroot__.py  <- Test root marker
    #   /project/tests/unit/test_auth.py <- Test module
    #
    # Walking up from test_auth.py:
    #   /project/tests/unit/ -> no __testroot__.py, continue
    #   /project/tests/ -> found __testroot__.py, return this path
    # =========================================================================
    
    # Get the directory containing the module's source file
    # This is our starting point for the upward directory walk
    mod_dir = os.path.dirname(module.__file__)
    
    while True:
        # Construct the path to the potential marker file in current directory
        pkg_dir_file = os.path.join(mod_dir, "__testroot__.py")
        
        if not os.path.exists(pkg_dir_file):
            # Marker not found in current directory, move to parent
            parent_dir = os.path.dirname(mod_dir)
            
            # Check if we've reached the filesystem root
            # At root, dirname returns the same path (e.g., "/" on Unix)
            if parent_dir == mod_dir:
                # We've walked all the way to root without finding the marker
                # This is a configuration error - test files must be in a test root
                errmsg = "TestBase test files must exist inside a test root directory marked with a __testroot__.py file."
                raise ConfigurationError(errmsg)
            
            # Continue walking up the directory tree
            mod_dir = parent_dir
        else:
            # Found the __testroot__.py marker file
            # This directory is the test root
            break

    return mod_dir

def find_testmodule_fullname(module, testroot=None) -> str:
    """
        Computes the fully qualified dotted module name for a test module.

        This function determines the full module name by computing the relative path from
        the test root's parent directory to the module file, then converting path separators
        to dots. This is essential for proper module registration in ``sys.modules`` and
        for correct identification of test classes and functions.

        :param module: The test module object (typically ``sys.modules["__main__"]``) for which
            to compute the full module name. The module must have a ``__file__`` attribute
            pointing to its source file location.
        :type module: ModuleType

        :param testroot: The path to the test root directory. If not provided, the function
            will call :func:`find_testmodule_root` to discover it automatically.
        :type testroot: Optional[str]

        :returns: The fully qualified dotted module name (e.g., ``"tests.package.test_module"``).
        :rtype: str

        :raises ConfigurationError: If ``testroot`` is not provided and no ``__testroot__.py``
            marker file is found when discovering the test root.

        Algorithm:
            1. If testroot is not provided, discover it using :func:`find_testmodule_root`
            2. Get the absolute path to the module file (without extension)
            3. Get the parent directory of the test root
            4. Compute the relative path from the test root parent to the module file
            5. Convert path separators (``/``) to dots (``.``) to form the dotted module name

        Example:
            Given a test file structure::

                /home/user/project/
                └── tests/
                    ├── __testroot__.py
                    ├── __init__.py
                    └── package/
                        ├── __init__.py
                        └── test_module.py

            When called with the test_module module::

                import sys
                test_module = sys.modules["__main__"]
                fullname = find_testmodule_fullname(test_module)
                # Returns: "tests.package.test_module"

            With explicit testroot::

                fullname = find_testmodule_fullname(test_module, testroot="/home/user/project/tests")
                # Returns: "tests.package.test_module"

        .. note::
            The full module name is computed relative to the test root's parent directory,
            which means the test root directory name itself becomes the first component
            of the module name.

        .. seealso::
            :func:`find_testmodule_root` : Discovers the test root directory
            :func:`generic_test_entrypoint` : Uses this function for module registration
    """
    # =========================================================================
    # MODULE FULL NAME COMPUTATION ALGORITHM
    # =========================================================================
    # This function converts a file system path to a Python dotted module name.
    # The module name is computed relative to the test root's PARENT directory,
    # so the test root directory name becomes the first component of the module name.
    #
    # Why relative to parent?
    #   - The test root directory (e.g., "tests") is itself a Python package
    #   - We want module names like "tests.unit.test_auth", not "unit.test_auth"
    #   - This matches how Python would import the module if it were on sys.path
    #
    # Algorithm:
    #   1. Get absolute path to module file without .py extension
    #   2. Get the parent directory of the test root
    #   3. Strip the parent path from the module path to get relative path
    #   4. Convert path separators to dots for dotted module name
    #
    # Example:
    #   Module file: /project/tests/unit/test_auth.py
    #   Test root:   /project/tests/
    #   Parent:      /project/
    #
    #   Relative path: tests/unit/test_auth
    #   Module name:   tests.unit.test_auth
    # =========================================================================

    # If testroot not provided, discover it by walking up the directory tree
    if testroot is None:
        testroot = find_testmodule_root(module)

    # Get the absolute path to the module file without the .py extension
    # Example: /project/tests/unit/test_auth.py -> /project/tests/unit/test_auth
    mod_filebase, _ = os.path.splitext(os.path.abspath(module.__file__))
    
    # Get the parent directory of the test root
    # This is the directory from which we compute the relative module path
    # Example: /project/tests/ -> /project/
    testroot_parent = os.path.dirname(testroot)
    
    # Compute the relative path from testroot_parent to the module file
    # Then convert path separators to dots for the dotted module name
    #
    # Steps:
    #   1. Strip testroot_parent prefix from mod_filebase
    #      /project/tests/unit/test_auth -> tests/unit/test_auth
    #   2. Strip leading slashes (in case of edge cases)
    #   3. Replace "/" with "." to get dotted module name
    #      tests/unit/test_auth -> tests.unit.test_auth
    testmodule_fullname = mod_filebase[len(testroot_parent):].strip("/").replace("/", ".")

    return testmodule_fullname





