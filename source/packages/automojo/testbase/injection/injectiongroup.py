"""
    .. module:: automojo.testbase.injection.injectiongroup
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for injectiongroup.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import Dict, List, Optional, Union

import sys

from automojo.errors.exceptions import SemanticError

from automojo.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from automojo.testbase.injection.injectionregistry import injection_registry
from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.injection.injectionmoment import InjectionMoment

logger = getEnhancedLogger()

class InjectionGroup:
    """
        Represents a hierarchical grouping of injection moments organized by module paths.

        The InjectionGroup class forms a tree structure that mirrors the Python module hierarchy,
        enabling metadata resolution and propagation through the injection system. Each group
        can contain child groups (representing subpackages or modules) and injection moments
        (representing test functions).

        Hierarchy Construction
        ----------------------
        The group hierarchy is built dynamically as injection moments are registered. When an
        injection moment is added via :meth:`add_descendent`, the system:

        1. Parses the module path from the injection moment's scope name
        2. Walks or creates intermediate group nodes along the path
        3. Inserts the injection moment at the appropriate leaf position

        Example hierarchy structure::

                  -------------
                  |  Group A  |
            ---------------------------
            |  Group AA  |  Group AB  |
            -------------------------------
            |         Group AAA/ABA       |
            -------------------------------

        For a test function at ``tests.unit.auth.test_login#test_valid_credentials``:

        - Root group (package=None) contains child "tests"
        - "tests" group contains child "unit"
        - "unit" group contains child "auth"
        - "auth" group contains child "test_login"
        - "test_login" group contains the InjectionMoment for "test_valid_credentials"

        Metadata Propagation
        --------------------
        Metadata flows from parent groups to child groups and injection moments during the
        :meth:`resolve_metadata` phase. The propagation follows these rules:

        1. Each group checks its associated module for a ``_metadata_`` attribute
        2. Parent metadata is merged with the group's own metadata
        3. Child metadata values override parent values for the same keys
        4. The resolved metadata is propagated to all children recursively

        This enables test modules to define metadata that applies to all tests within,
        while allowing individual tests or submodules to override specific values.

        Usage Example::

            # Create root group
            root = InjectionGroup("root")

            # Add injection moment (creates intermediate groups automatically)
            moment = InjectionMoment(test_function)
            root.add_descendent(moment)

            # Resolve metadata from root down
            root.resolve_metadata()

        Context Manager Support
        -----------------------
        InjectionGroup supports the context manager protocol for scoped operations::

            with InjectionGroup("mygroup") as group:
                # Perform operations within group context
                pass
    """

    def __init__(self, name, package=None):
        """
            Initializes an :class:`InjectionGroup` instance.

            Creates a new group node that can serve as part of the injection hierarchy.
            Groups with ``package=None`` are root groups and can use the :meth:`add_descendent`
            API. Groups with a package value are intermediate nodes created during hierarchy
            construction.

            :param name: Name of the group, typically corresponding to a module or package name.
            :param package: Optional dotted package path where the group resides. When ``None``,
                this group is the root of the hierarchy and can accept descendent additions.
                When set, this group is an intermediate node in the hierarchy.

            .. note::
                The combination of ``package`` and ``name`` forms the group's full scope name,
                which is used for resource scope lookup via :meth:`get_resource_scope`.
        """
        self._name = name
        self._package = package
        self._children = {}
        self._finalized = False
        self._metadata = None
        return

    def __enter__(self):
        """
            Enter the context manager.

            :returns: The current :class:`InjectionGroup` instance.
        """
        return self

    def __exit__(self, ex_type, ex_inst, ex_tb):
        """
            Exit the context manager.

            :param ex_type: Exception type if raised.
            :param ex_inst: Exception instance if raised.
            :param ex_tb: Traceback object if raised.

            :returns: ``False`` to propagate exceptions.
        """
        return False

    @property
    def children(self):
        """
            Mapping of child injection groups and moments.

            Returns a dictionary where keys are child names (module names or test base names)
            and values are either :class:`InjectionGroup` instances (for intermediate nodes)
            or :class:`InjectionMoment` instances (for leaf nodes representing test functions).

            The children dictionary is populated during hierarchy construction via
            :meth:`add_descendent` and its internal helper :meth:`_add_descendent`.

            :returns: Dictionary mapping child names to :class:`InjectionGroup` or
                :class:`InjectionMoment` objects.
        """
        return self._children

    @property
    def finalized(self):
        """
            Indicates whether the group has been finalized.

            :returns: ``True`` if finalized.
        """
        return self._finalized

    @property
    def name(self):
        """
            The name of the injection group.

            :returns: Group name string.
        """
        return self._name

    @property
    def package(self):
        """
            Package path for the injection group.

            :returns: Package name or ``None``.
        """
        return self._package

    @property
    def scope_name(self):
        """
            Fully qualified scope name for the group.

            Computes the dotted scope name by combining the package path and group name.
            This scope name is used to look up the associated :class:`InjectionScope` in
            the injection registry via :meth:`get_resource_scope`.

            For a group with ``name="test_auth"`` and ``package="tests.unit"``, the
            scope name would be ``"tests.unit.test_auth"``.

            For a root group with ``name="root"`` and ``package=None``, the scope name
            would simply be ``"root"``.

            :returns: The dotted scope name string used for resource scope lookup.
        """
        sname = self._name
        if self._package is not None and len(self._package) > 0:
            sname = "{}.{}".format(self.package, sname)
        return sname

    def add_descendent(self, child_ref:InjectionMoment, group_type: Optional[type] = None):
        """
            Adds a descendent injection moment under this group, creating intermediate nodes as needed.

            This is the primary API for building the injection group hierarchy. It parses the
            injection moment's scope name to determine the module path, then walks or creates
            intermediate group nodes along that path before inserting the moment at the leaf.

            Hierarchy Construction Process
            -------------------------------
            1. Extract the module path from the injection moment's name (before the ``#`` separator)
            2. Split the module path into components (e.g., ``["tests", "unit", "auth"]``)
            3. Recursively walk the tree, creating intermediate :class:`InjectionGroup` nodes
               for any missing path components
            4. Insert the injection moment at the final position using its base name

            Example::

                # For an injection moment with name "tests.unit.auth#test_login"
                root.add_descendent(moment)

                # This creates the hierarchy:
                # root -> tests -> unit -> auth -> test_login (InjectionMoment)

            :param child_ref: The :class:`InjectionMoment` to add to the hierarchy.
            :param group_type: Optional class to use when creating intermediate group nodes.
                If ``None``, uses the same class as ``self`` (typically :class:`InjectionGroup`).
                This allows subclasses to maintain their type throughout the hierarchy.

            :raises SemanticError: If called on a non-root group (i.e., a group with a
                non-None package). Only the root group should use this API; intermediate
                nodes are populated via the internal :meth:`_add_descendent` method.
        """

        if self._package is not None:
            err_msg = "The 'add_descendent' API can only be called on the root package."
            raise SemanticError(err_msg) from None

        injname = child_ref.name
        module_name, _ = injname.split("#")
        to_walk_list = module_name.split(".")
        path_stack = []

        self._add_descendent(child_ref, to_walk_list, path_stack, group_type=group_type)

        return

    def finalize(self):
        """
            Marks the group as finalized, indicating setup is complete.

            Once finalized, the group's structure should not be modified. This method
            is called after all injection moments have been added and metadata has
            been resolved, signaling that the group is ready for test execution.

            The finalized state can be checked via the :attr:`finalized` property.
        """
        self._finalized = True
        return

    def get_resource_scope(self) -> InjectionScope:
        """
            Retrieves the resource scope associated with this group from the injection registry.

            The resource scope contains parameter and validator originations that are visible
            at this group's level in the hierarchy. This method looks up the scope using the
            group's :attr:`scope_name` property.

            :returns: The :class:`InjectionScope` instance associated with this group's
                scope name, or ``None`` if no scope exists for this group.
        """
        scope_name = self.scope_name
        rscope = injection_registry.lookup_resource_scope(scope_name)
        return rscope

    def resolve_metadata(self, parent_metadata: Optional[Dict[str, str]]=None):
        """
            Resolves metadata for this group and propagates it to all descendents.

            This method implements the metadata propagation algorithm that flows metadata
            from parent groups down to child groups and injection moments. It is typically
            called on the root group after the hierarchy has been fully constructed.

            Metadata Resolution Algorithm
            ------------------------------
            1. Look up this group's reference metadata from its associated module's
               ``_metadata_`` attribute (via :meth:`_reference_metadata`)
            2. Merge parent metadata with reference metadata:

               - If both exist: create new dict, copy parent, then update with reference
                 (child values override parent values for same keys)
               - If only parent exists: use parent metadata directly
               - If only reference exists: use reference metadata directly
               - If neither exists: metadata remains ``None``

            3. Store the resolved metadata in ``self._metadata``
            4. Recursively call :meth:`resolve_metadata` on all children, passing
               the resolved metadata as the new parent metadata

            Metadata Inheritance Example
            ----------------------------
            Given a module hierarchy where:

            - ``tests`` module has ``_metadata_ = {"priority": "high", "team": "core"}``
            - ``tests.unit`` module has ``_metadata_ = {"priority": "low"}``

            After resolution:

            - ``tests`` group has metadata ``{"priority": "high", "team": "core"}``
            - ``tests.unit`` group has metadata ``{"priority": "low", "team": "core"}``
              (priority overridden, team inherited)

            :param parent_metadata: Metadata dictionary inherited from the parent group.
                When ``None``, this group is either the root or has no parent metadata
                to inherit.
        """

        reference_metadata = self._reference_metadata()

        if parent_metadata is not None:
            if reference_metadata is not None:
                self._metadata = {}
                self._metadata.update(parent_metadata)
                self._metadata.update(reference_metadata)
            else:
                self._metadata = parent_metadata
        else:
            self._metadata = reference_metadata

        child: Union[InjectionMoment, InjectionGroup]
        for child in self._children.values():
            child.resolve_metadata(self._metadata)

        return

    def _add_descendent(self, child_ref: InjectionMoment, to_walk_list: List[str], path_stack: List[str], group_type: Optional[type] = None):
        """
            Internal recursive helper that walks the group tree and inserts a child.

            This method implements the recursive tree traversal for hierarchy construction.
            It is called by :meth:`add_descendent` and recursively calls itself to walk
            down the module path until reaching the insertion point.

            Tree Walking Algorithm
            ----------------------
            1. If ``to_walk_list`` is empty, we've reached the insertion point:

               - Insert the injection moment using its ``base_name`` as the key

            2. Otherwise, process the next path component:

               - Extract the first element from ``to_walk_list`` as ``child_leaf``
               - Check if a child group already exists for ``child_leaf``
               - If not, create a new group using ``group_type`` (or ``type(self)``)
               - Push ``child_leaf`` onto ``path_stack`` for package path tracking
               - Recursively call ``_add_descendent`` on the child group
               - Pop ``child_leaf`` from ``path_stack`` after recursion completes

            Path Stack Usage
            ----------------
            The ``path_stack`` accumulates the traversed path components and is used
            to construct the ``package`` attribute for newly created intermediate groups.
            For example, when creating a group at path ``["tests", "unit", "auth"]``:

            - At "tests": path_stack=[], new group has package=""
            - At "unit": path_stack=["tests"], new group has package="tests"
            - At "auth": path_stack=["tests", "unit"], new group has package="tests.unit"

            :param child_ref: The :class:`InjectionMoment` being inserted into the tree.
            :param to_walk_list: Remaining path segments to traverse before insertion.
            :param path_stack: Stack of already-traversed path segments, used to build
                the package path for new intermediate groups.
            :param group_type: Optional class to use when creating new group nodes.
                Defaults to ``type(self)`` if not specified.
        """

        if len(to_walk_list) == 0:
            tbname = child_ref.base_name
            self._children[tbname] = child_ref
        else:
            child_leaf = to_walk_list[0]

            desc_to_walk_list = []
            if len(to_walk_list) > 1:
                desc_to_walk_list = to_walk_list[1:]

            child_leaf_group = None
            if child_leaf in self._children:
                child_leaf_group = self._children[child_leaf]
            else:
                if group_type is None:
                    group_type = type(self)

                tgname = child_leaf
                tgpkg = ".".join(path_stack) 

                child_leaf_group = group_type(tgname, tgpkg)
                self._children[child_leaf] = child_leaf_group

            path_stack.append(child_leaf)
            try:
                child_leaf_group._add_descendent(child_ref, desc_to_walk_list, path_stack)
            finally:
                path_stack.pop()

        return

    def _reference_metadata(self):
        """
            Looks up the metadata defined on the module associated with this group.

            This method checks if the module corresponding to this group's scope name
            has been imported and contains a ``_metadata_`` attribute. The ``_metadata_``
            attribute is a convention for defining metadata that should apply to all
            tests within a module.

            Module Lookup Process
            ---------------------
            1. Construct the full module name from ``package`` and ``name``
            2. Check if the module exists in ``sys.modules``
            3. If found, check for a ``_metadata_`` attribute on the module
            4. Return the metadata dictionary if found, otherwise ``None``

            Example Module with Metadata::

                # In tests/unit/test_auth.py
                _metadata_ = {
                    "priority": "high",
                    "team": "security",
                    "tags": ["authentication", "security"]
                }

                def test_login():
                    pass  # This test inherits the module's metadata

            :returns: The metadata dictionary from the module's ``_metadata_`` attribute,
                or ``None`` if the module is not loaded or has no metadata defined.
        """
        
        modname = self._name
        if self._package is not None and self._package != "":
            modname = "{}.{}".format(self._package, self._name)

        refmd = None
        if modname in sys.modules:
            mod = sys.modules[modname]
            if hasattr(mod, "_metadata_"):
                refmd = mod._metadata_

        return refmd

    def __contains__(self, key):
        """
            Checks whether a child with *key* exists.

            :param key: Name of the child to check.

            :returns: ``True`` if the child exists.
        """
        has_item = key in self._children
        return has_item

    def __getitem__(self, key):
        """
            Retrieves a child by *key*.

            :param key: Name of the child to retrieve.

            :returns: The requested child object.
        """
        item = self._children[key]
        return item

    def __setitem__(self, key, value):
        """
            Inserts or replaces a child in the group.

            :param key: Name of the child.
            :param value: The child object to store.
        """
        self._children[key] = value
        return
