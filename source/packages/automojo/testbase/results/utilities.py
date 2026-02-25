"""
    .. module:: automojo.testbase.results.utilities
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for utilities.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import List

import os
import json

DEFAULT_DO_NOT_CATALOG_DIRS = [
    "__pycache__"
]

DEFAULT_DO_NOT_DESCEND_DIRS = [
    "diagnostics"
]

def catalog_tree(rootdir: str, dont_catalog_dirs: List[str] = DEFAULT_DO_NOT_CATALOG_DIRS,
                 dont_descend_dirs: List[str] = DEFAULT_DO_NOT_DESCEND_DIRS):
    """
        Adds json catalog files to a file system tree to help provide directory
        services to javascript in html files.

        CATALOG TREE TRAVERSAL ALGORITHM:
        =================================
        This function implements a depth-first recursive traversal of a directory tree,
        creating catalog.json files at each level to enable HTML report navigation.

        Algorithm Overview:
            1. List all entries in the current directory
            2. Classify each entry as file or directory
            3. For directories: optionally include in catalog and optionally recurse
            4. Write catalog.json with files and folders arrays
            5. Recurse into child directories (depth-first)

        Filtering Rules:
            - dont_catalog_dirs: Directories to exclude from the "folders" array
              (e.g., __pycache__) but still descend into for recursive processing
            - dont_descend_dirs: Directories to not recurse into (e.g., diagnostics)
              These may still appear in the catalog if not in dont_catalog_dirs

        Output Format:
            Each catalog.json contains:
            {
                "files": ["file1.txt", "file2.json", ...],
                "folders": ["subdir1", "subdir2", ...]
            }

        :param rootdir: The root directory to start cataloging from.
        :param dont_catalog_dirs: List of directory names to exclude from folder listings.
        :param dont_descend_dirs: List of directory names to not recurse into.

        :returns: None
    """

    # STEP 1: LIST AND SORT DIRECTORY CONTENTS
    # ----------------------------------------
    # Get all entries in the current directory and sort them alphabetically.
    # Sorting ensures consistent catalog output across runs, which is important
    # for reproducibility and makes diffs easier to read.
    directory_items = [item for item in os.listdir(rootdir)]
    directory_items.sort()

    # STEP 2: INITIALIZE CLASSIFICATION LISTS
    # ---------------------------------------
    # Separate lists for files and directories. These will be written to catalog.json.
    dirnames = []
    filenames = []

    # STEP 3: CLASSIFY EACH DIRECTORY ENTRY
    # -------------------------------------
    # Iterate through all entries and classify them as files or directories.
    # Apply filtering rules for directories.
    for dentry in directory_items:

        # Skip special directory entries (current and parent directory references)
        if dentry == "." or dentry == "..":
            continue

        dentry_full = os.path.join(rootdir, dentry)

        if os.path.isfile(dentry_full):
            # CASE: Regular file - add to files list unconditionally
            filenames.append(dentry)
        elif os.path.isdir(dentry_full):
            # CASE: Directory - apply filtering rules

            # CATALOG INCLUSION CHECK:
            # Only add to dirnames if not in the exclusion list.
            # This controls what appears in the "folders" array of catalog.json.
            # Example: __pycache__ is excluded from listings but may still be traversed.
            if dentry not in dont_catalog_dirs:
                dirnames.append(dentry)
        
            # RECURSION CHECK:
            # Only recurse into directories that are:
            # 1. Not in the dont_descend_dirs list (e.g., diagnostics)
            # 2. Not symbolic links (to prevent infinite loops and unexpected behavior)
            # This is a depth-first traversal - we recurse before writing the catalog.
            if dentry not in dont_descend_dirs:
                if not os.path.islink(dentry_full):
                    catalog_tree(dentry_full, dont_catalog_dirs, dont_descend_dirs)

    # STEP 4: WRITE CATALOG FILE
    # --------------------------
    # Write the catalog.json file AFTER recursing into subdirectories.
    # This ensures child catalogs exist before the parent catalog is written,
    # though the order doesn't affect functionality since each catalog is independent.
    catalog = {
        "files": filenames,
        "folders": dirnames
    }

    catalogfile = os.path.join(rootdir, "catalog.json")

    with open(catalogfile, 'w') as cf:
        json.dump(catalog, cf, indent=4)

    return

