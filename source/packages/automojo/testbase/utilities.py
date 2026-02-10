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
        Finds the root directory that is associated with a given test module.
    """
    mod_dir = os.path.dirname(module.__file__)
    while True:
        pkg_dir_file = os.path.join(mod_dir, "__testroot__.py")
        if not os.path.exists(pkg_dir_file):
            parent_dir = os.path.dirname(mod_dir)
            if parent_dir == mod_dir:
                errmsg = "TestBase test files must exist inside a test root directory marked with a __testroot__.py file."
                raise ConfigurationError(errmsg)
            mod_dir = parent_dir
        else:
            break

    return mod_dir

def find_testmodule_fullname(module, testroot=None) -> str:
    """
        Finds the root directory that is associated with a given test module and
        then uses the leaf path to a module to develop a full module name.
    """

    if testroot is None:
        testroot = find_testmodule_root(module)

    mod_filebase, _ = os.path.splitext(os.path.abspath(module.__file__))
    testroot_parent = os.path.dirname(testroot)
    testmodule_fullname = mod_filebase[len(testroot_parent):].strip("/").replace("/", ".")

    return testmodule_fullname





