"""
    .. module:: automojo.testbase.injection.injectionscope
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the InjectionScope class for managing hierarchical
               dependency injection scopes in the TestBase framework.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

    This module provides the :class:`InjectionScope` class which represents a node in the
    hierarchical scope tree used for dependency injection. The scope tree mirrors Python's
    module hierarchy and enables parameter visibility inheritance from parent to child scopes.

    Tree Structure Overview
    -----------------------
    The scope tree is organized as follows::

        <session> (root)
        ├── package_a
        │   ├── module_1
        │   │   ├── test_function_1 (injection moment)
        │   │   └── test_function_2 (injection moment)
        │   └── module_2
        │       └── test_function_3 (injection moment)
        └── package_b
            └── module_3
                └── test_function_4 (injection moment)

    Key Concepts
    ------------
    - **Scope Path**: A dot-separated string representing location in the tree
      (e.g., "package.module#test_function")
    - **Parameter Origination**: A mapping of parameter identifiers to ResourceOrigin objects
    - **Validator Origination**: A mapping of validator identifiers to ValidatorOrigin objects
    - **Relevance**: A flag indicating whether a scope is referenced by an injection moment

    Tree Traversal Algorithms
    -------------------------
    The module implements several tree traversal patterns:

    1. **Descendent Insertion** (``add_descendent_*_origination``):
       Walks from root to target scope, creating intermediate nodes as needed.

    2. **Scope Lookup** (``lookup_scope``):
       Parses scope path and traverses tree to find matching node.

    3. **Scope Pruning** (``prune_unreference_scopes``):
       Post-order traversal removing non-relevant leaf nodes.

    4. **Parameter Resolution** (``resolve_resource_originations_for_injection_moment``):
       Pre-order traversal accumulating visible parameters.

    Usage Example
    -------------
    ::

        from automojo.testbase.injection.injectionscope import InjectionScope
        from automojo.testbase.origins.resourceorigin import ResourceOrigin

        # Create root scope
        root = InjectionScope(name=None, package=None)

        # Register a resource origin at a specific scope
        origin = ResourceOrigin(...)
        root.add_descendent_resource_origination("package.module#test_func", origin)

        # Lookup a scope by path
        scope = root.lookup_scope("package.module#test_func")

        # Check if a parameter exists at a scope
        exists = root.has_descendent_resource("package.module#test_func", "my_param")

"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import (
    Any, Callable, Dict, List, Optional, Set, get_args as typing_get_args
)

import collections
import json
import warnings

from automojo.errors.exceptions import SemanticError

from automojo.testbase.coupling.integrationcoupling import IntegrationCoupling
from automojo.testbase.coupling.configurationcoupling import ConfigurationCoupling

from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.origins.validatororigin import ValidatorOrigin

from automojo.testbase.injection.injectionmoment import InjectionMoment

RESOURCE_KEY_FORMAT = "{}@{}:{}"

RESERVED_PARAMETER_NAMES = ["constraints"]


def _get_source_dependencies(param_origin) -> List[str]:
    """
    Extract the parameter names that a source function depends on.
    
    Parameters
    ----------
    param_origin : ResourceOrigin
        The parameter origin to analyze.
    
    Returns
    -------
    List[str]
        List of parameter names required by the source function.
    """
    if param_origin.implied or param_origin._source is None:
        return []
    
    try:
        source_params = param_origin.source_signature.parameters
        return [
            name for name in source_params.keys()
            if name not in RESERVED_PARAMETER_NAMES
        ]
    except (AttributeError, TypeError):
        return []

class InjectionScope:
    """
    A node in the hierarchical injection scope tree used to resolve resources and validators.

    The ``InjectionScope`` class represents a single node in the scope tree that mirrors
    Python's module hierarchy. Each scope can contain:

    - **Child scopes**: Other ``InjectionScope`` instances forming a tree structure
    - **Parameter originations**: ``ResourceOrigin`` objects defining injectable parameters
    - **Validator originations**: ``ValidatorOrigin`` objects defining post-test validators

    The scope tree enables hierarchical parameter visibility where parameters defined at
    higher scopes (closer to root) are visible to all descendant scopes. This follows
    Python's module hierarchy pattern.

    Attributes
    ----------
    children : Dict[str, InjectionScope]
        Dictionary of child scope nodes keyed by scope name.
    is_relevant : bool
        Flag indicating if this scope is referenced by an injection moment.
        Used during pruning to remove unreferenced scopes.
    name : str
        The local name of this scope (e.g., "module_name" or "test_function").
    package : str
        The full package path to this scope (e.g., "package.subpackage.module").
    parameter_originations : Dict[str, ResourceOrigin]
        Ordered dictionary of parameter origins available at this scope.
    validator_originations : Dict[str, ValidatorOrigin]
        Ordered dictionary of validator origins available at this scope.

    Parameters
    ----------
    name : str, optional
        The local name for this scope node. None for root scope.
    package : str, optional
        The full package path. None for root scope.
    is_inj_scope : bool, optional
        Whether this scope represents an injection moment (test function).
        Default is False.

    Examples
    --------
    Creating a root scope and adding child scopes::

        # Create root scope (represents <session>)
        root = InjectionScope(name=None, package=None)

        # Add a resource origin at package.module#test_func scope
        from automojo.testbase.origins.resourceorigin import ResourceOrigin
        origin = ResourceOrigin(
            originating_scope="package.module#test_func",
            identifier="my_resource",
            life_span=ResourceLifespan.Test,
            source=my_source
        )
        root.add_descendent_resource_origination("package.module#test_func", origin)

        # The tree now looks like:
        # root (<session>)
        # └── package
        #     └── module
        #         └── test_func (contains my_resource)

    Checking parameter visibility::

        # Parameters at parent scopes are visible to children
        root.add_descendent_resource_origination("<session>", session_origin)

        # This session-level parameter is visible to all descendant scopes
        # when resolving parameters for any injection moment

    Notes
    -----
    - The root scope has ``name=None`` and ``package=None``
    - Scope paths use "#" to separate module path from function name
    - The ``add_descendent_*`` methods can only be called on the root scope
    - Insertion order of parameter originations is preserved using OrderedDict

    See Also
    --------
    InjectionRegistry : The singleton registry that manages the scope tree
    ResourceOrigin : Describes where an injectable parameter comes from
    ValidatorOrigin : Describes where a validator comes from
    InjectionMoment : Represents a point where injection occurs
    """

    def __init__(self, name=None, package=None, is_inj_scope=False):
        self._name = name
        self._package = package
        self._children: Dict[str, InjectionScope] = {}
        self._parameter_originations = collections.OrderedDict()
        self._validator_originations = collections.OrderedDict()
        self._is_inj_scope = is_inj_scope
        self._is_relevant = False
        return

    @property
    def children(self) -> Dict[str, "InjectionScope"]:
        return self._children

    @property
    def is_relevant(self) -> bool:
        return self._is_relevant

    @property
    def name(self) -> str:
        return self._name

    @property
    def package(self) -> str:
        return self._package

    @property
    def parameter_originations(self) -> Dict[str, ResourceOrigin]:
        return self._parameter_originations

    @property
    def validator_originations(self) -> Dict[str, ValidatorOrigin]:
        return self._validator_originations

    def add_descendent_resource_origination(self, assigned_scope: str, parameter_origin: ResourceOrigin):
        """
        Add a resource origin to the scope tree at the specified scope path.

        This method walks (or creates) the scope tree from the root to the target
        scope and inserts the parameter origin into that scope's parameter originations
        dictionary.

        Tree Traversal Algorithm
        ------------------------
        1. Parse the ``assigned_scope`` path into components
        2. Replace "#" with "." for uniform traversal
        3. Walk the tree, creating intermediate nodes as needed
        4. Insert the origin at the final scope node

        The algorithm uses a recursive descent pattern where each call processes
        one path component and delegates to the child scope for remaining components.

        Parameters
        ----------
        assigned_scope : str
            The full scope path where the origin should be registered.
            Format: "package.module#function" or "<session>" for root.
            The "#" character separates module path from injection moment name.
        parameter_origin : ResourceOrigin
            The origin object describing the injectable parameter.
            Contains identifier, lifespan, source function, and constraints.

        Raises
        ------
        SemanticError
            If called on a non-root scope (where ``package`` is not None).
            This API is designed to be called only from the root scope.

        Examples
        --------
        Register a session-scoped resource (available everywhere)::

            root = InjectionScope(name=None, package=None)
            root.add_descendent_resource_origination("<session>", session_origin)

        Register a test-scoped resource::

            root.add_descendent_resource_origination(
                "tests.unit.test_auth#test_login",
                login_resource_origin
            )

        Register a module-scoped resource (available to all tests in module)::

            root.add_descendent_resource_origination(
                "tests.unit.test_auth",
                auth_module_origin
            )

        Notes
        -----
        - The "#" character in scope paths is converted to "." for tree traversal
        - Intermediate scope nodes are created automatically if they don't exist
        - Origins are stored in insertion order using OrderedDict
        - Duplicate identifiers at the same scope will overwrite previous entries

        See Also
        --------
        add_descendent_validator_origination : Similar method for validator origins
        has_descendent_resource : Check if a resource exists at a scope
        lookup_scope : Find a scope node by path
        """

        if self._package is not None:
            err_msg = "The 'add_descendent' API can only be called on the root package."
            raise SemanticError(err_msg) from None

        if self._package is None and assigned_scope == "<session>":
            if parameter_origin is not None:
                identifier = parameter_origin.identifier
                self._parameter_originations[identifier] =  parameter_origin
                self._parameter_originations.move_to_end(identifier, last=True)
        else:
            is_inj_scope = False
            if assigned_scope.find("#") > -1:
                is_inj_scope = True
                assigned_scope = assigned_scope.replace("#", ".")
            to_walk_list = assigned_scope.split(".")
            path_stack = []

            self._add_descendent_resource_origination(parameter_origin, to_walk_list, path_stack, is_inj_scope)

        return
    
    def add_descendent_validator_origination(self, assigned_scope: str, validator_origin: ValidatorOrigin):
        """
        Add a validator origin to the scope tree at the specified scope path.

        This method walks (or creates) the scope tree from the root to the target
        scope and inserts the validator origin into that scope's validator originations
        dictionary. Validators are used for post-test validation.

        Tree Traversal Algorithm
        ------------------------
        1. Parse the ``assigned_scope`` path into components
        2. Replace "#" with "." for uniform traversal
        3. Walk the tree, creating intermediate nodes as needed
        4. Insert the origin at the final scope node

        The algorithm mirrors ``add_descendent_resource_origination`` but operates
        on the validator originations dictionary instead.

        Parameters
        ----------
        assigned_scope : str
            The full scope path where the validator should be registered.
            Format: "package.module#function" or "<session>" for root.
            The "#" character separates module path from injection moment name.
        validator_origin : ValidatorOrigin
            The origin object describing the validator.
            Contains identifier, suffix, lifespan, and source function.

        Raises
        ------
        SemanticError
            If called on a non-root scope (where ``package`` is not None).
            This API is designed to be called only from the root scope.

        Examples
        --------
        Register a session-scoped validator::

            root = InjectionScope(name=None, package=None)
            root.add_descendent_validator_origination("<session>", cleanup_validator)

        Register a test-scoped validator::

            root.add_descendent_validator_origination(
                "tests.unit.test_auth#test_login",
                login_validator_origin
            )

        Notes
        -----
        - Validators are executed after test completion for post-test validation
        - The "#" character in scope paths is converted to "." for tree traversal
        - Intermediate scope nodes are created automatically if they don't exist
        - Origins are stored in insertion order using OrderedDict

        See Also
        --------
        add_descendent_resource_origination : Similar method for resource origins
        has_descendent_validator : Check if a validator exists at a scope
        """

        if self._package is not None:
            err_msg = "The 'add_descendent' API can only be called on the root package."
            raise SemanticError(err_msg) from None

        if self._package is None and assigned_scope == "<session>":
            if validator_origin is not None:
                identifier = validator_origin.identifier
                self._validator_originations[identifier] =  validator_origin
                self._validator_originations.move_to_end(identifier, last=True)
        else:
            is_inj_scope = False
            if assigned_scope.find("#") > -1:
                is_inj_scope = True
                assigned_scope = assigned_scope.replace("#", ".")
            to_walk_list = assigned_scope.split(".")
            path_stack = []

            self._add_descendent_validator_origination(validator_origin, to_walk_list, path_stack, is_inj_scope)

        return

    def collect_integrations_and_configurations_for_injection_moment(self, integration_table: Dict[Callable, IntegrationCoupling],
        configuration_table: Dict[Callable, ConfigurationCoupling]):
        """
        Collect all integration and configuration couplings from the scope tree.

        This method performs a depth-first traversal of the entire scope tree,
        examining each parameter origination to identify ``IntegrationCoupling``
        and ``ConfigurationCoupling`` types. These couplings represent external
        dependencies that must be established before test execution.

        Tree Traversal Algorithm
        ------------------------
        1. Iterate through all parameter originations at current scope
        2. For each non-implied origin, examine the resource type
        3. Handle generic types by extracting type arguments
        4. Classify as integration or configuration coupling
        5. Recursively process all child scopes

        The traversal is a standard depth-first search that visits every node
        in the tree to build complete coupling tables.

        Parameters
        ----------
        integration_table : Dict[Callable, IntegrationCoupling]
            Dictionary to populate with discovered integration couplings.
            Keyed by source function, value is the coupling type.
            Modified in-place during traversal.
        configuration_table : Dict[Callable, ConfigurationCoupling]
            Dictionary to populate with discovered configuration couplings.
            Keyed by source function, value is the coupling type.
            Modified in-place during traversal.

        Examples
        --------
        Collect all couplings from the scope tree::

            integration_table = {}
            configuration_table = {}

            root_scope.collect_integrations_and_configurations_for_injection_moment(
                integration_table,
                configuration_table
            )

            # integration_table now contains all IntegrationCoupling types
            # configuration_table now contains all ConfigurationCoupling types

        Notes
        -----
        - Implied parameter originations are skipped (built-in framework resources)
        - Generic types (e.g., ``List[IntegrationCoupling]``) are unwrapped
        - Each source function appears at most once in each table
        - The tables are used by the execution engine to prepare couplings

        See Also
        --------
        IntegrationCoupling : Base class for integration couplings
        ConfigurationCoupling : Base class for configuration couplings
        """

        # =====================================================================
        # INTEGRATION/CONFIGURATION TYPE EXTRACTION ALGORITHM
        # =====================================================================
        # This algorithm performs a depth-first traversal of the scope tree to
        # identify all IntegrationCoupling and ConfigurationCoupling types that
        # are referenced by parameter originations.
        #
        # Purpose:
        # - The execution engine needs to know what external couplings are required
        # - Integrations represent connections to external systems (databases, APIs)
        # - Configurations represent environment/runtime settings
        # - This information is used to prepare couplings before test execution
        #
        # Type extraction handles two cases:
        # 1. Direct coupling types: resource_type IS an IntegrationCoupling subclass
        # 2. Generic types: resource_type is List[IntegrationCoupling] or similar
        #
        # The algorithm uses Python's typing module to unwrap generic types and
        # extract the actual coupling type from type arguments.
        # =====================================================================

        param_orig: ResourceOrigin

        # Step 1: Process all parameter originations at this scope level
        for param_orig in self._parameter_originations.values():

            # Step 2: Skip implied parameters (built-in framework resources)
            # Implied parameters are inherent to the framework and don't represent
            # external couplings that need to be established
            if not param_orig.implied:

                source_function = param_orig.source_function
                param_resource_type = param_orig.source_resource_type

                # Step 3: Check if the resource type is a generic type
                # Generic types like List[IntegrationCoupling] or Optional[ConfigurationCoupling]
                # need to be unwrapped to extract the actual coupling type
                if len(typing_get_args(param_resource_type)) > 0:
                    # Step 3a: Iterate through type arguments to find coupling types
                    # For example, List[MyIntegration] has type args (MyIntegration,)
                    for type_arg in typing_get_args(param_resource_type):
                        if issubclass(type_arg, IntegrationCoupling):
                            # Found an integration coupling - add to integration table
                            # The table is keyed by source function to prevent duplicates
                            # There should never be more than one fixture with the same
                            # well-known or declared name in the same collection
                            integration_table[source_function] = type_arg
                            break  # Only one coupling type per parameter
                        elif issubclass(type_arg, ConfigurationCoupling):
                            # Found a configuration coupling - add to configuration table
                            configuration_table[source_function] = type_arg
                            break  # Only one coupling type per parameter
                else:
                    # Step 3b: Handle direct (non-generic) coupling types
                    # The resource type itself is the coupling type
                    if issubclass(param_resource_type, IntegrationCoupling):
                        # Direct integration coupling type
                        # There should never be more than one fixture with the same well-known or
                        # declared name in the same collection of injection moments.
                        integration_table[source_function] = param_resource_type
                    elif issubclass(param_resource_type, ConfigurationCoupling):
                        # Direct configuration coupling type
                        configuration_table[source_function] = param_resource_type

        # Step 4: Recursively process all child scopes (depth-first traversal)
        # This ensures we collect couplings from the entire scope tree
        for child_scope in self._children.values():

            # Call each child and collect descendant integrations and scopes.
            child_scope.collect_integrations_and_configurations_for_injection_moment(integration_table, configuration_table)

        return

    def ensure_injection_scopes_for_injection_moment(self, inj_mom: InjectionMoment):
        """
        Ensure scope nodes exist for all components of an injection moment's path.

        This method walks through the scope tree using the injection moment's
        full scope name and creates any missing intermediate scope nodes. It also
        marks each scope along the path as "relevant" to prevent pruning.

        Tree Traversal Algorithm
        ------------------------
        1. Parse the injection moment's scope name into components
        2. Split module path and function name at "#" character
        3. For each path component:
           a. Check if child scope exists
           b. Create new scope node if missing
           c. Mark scope as relevant
           d. Recurse into child scope
        4. Final component becomes an injection scope node

        This is a pre-order traversal that ensures the path exists before
        any parameter resolution occurs.

        Parameters
        ----------
        inj_mom : InjectionMoment
            The injection moment object whose scope path should be ensured.
            The scope name is extracted from the moment's module and function name.

        Examples
        --------
        Ensure scopes exist for a test function::

            from automojo.testbase.injection.injectionmoment import InjectionMoment

            # Create an injection moment for tests.unit.test_auth#test_login
            inj_mom = InjectionMoment(test_login_function)

            # Ensure all scope nodes exist
            root.ensure_injection_scopes_for_injection_moment(inj_mom)

            # Tree now contains:
            # root (<session>) [relevant=True]
            # └── tests [relevant=True]
            #     └── unit [relevant=True]
            #         └── test_auth [relevant=True]
            #             └── test_login [relevant=True, is_inj_scope=True]

        Notes
        -----
        - The root scope is automatically marked as relevant
        - Scope names use "#" to separate module from function name
        - Created scopes have ``is_inj_scope=True`` only for the final component
        - This method should be called for all injection moments before pruning

        See Also
        --------
        prune_unreference_scopes : Remove non-relevant scopes after this step
        resolve_resource_originations_for_injection_moment : Resolve parameters after ensuring scopes
        """

        inj_scope_name = inj_mom.scope_name

        module_name, inj_name = inj_scope_name.split("#")

        inj_scope_parts = module_name.split(".")
        inj_scope_parts.append(inj_name)

        path_stack = []

        self._is_relevant = True
        self._ensure_injection_scopes_for_injection_moment(inj_mom, inj_scope_parts, path_stack)

        return

    def has_descendent_resource(self, scope_name: str, identifier: str) -> bool:
        """
        Check if a parameter with the given identifier exists at the specified scope.

        This method traverses the scope tree to the target scope and checks
        if a parameter origination with the given identifier is registered there.
        It does NOT check parent scopes - only the exact scope specified.

        Tree Traversal Algorithm
        ------------------------
        1. Handle special case of "<session>" (root scope)
        2. Parse scope path by replacing "#" with "." and splitting
        3. Recursively traverse to target scope
        4. Check if identifier exists in parameter_originations

        Parameters
        ----------
        scope_name : str
            The full scope path to check.
            Format: "package.module#function" or "<session>" for root.
        identifier : str
            The parameter identifier to search for.

        Returns
        -------
        bool
            True if the parameter exists at the specified scope, False otherwise.

        Examples
        --------
        Check if a parameter exists at session scope::

            exists = root.has_descendent_resource("<session>", "session_config")

        Check if a parameter exists at a test scope::

            exists = root.has_descendent_resource(
                "tests.unit.test_auth#test_login",
                "auth_token"
            )

        Notes
        -----
        - This checks only the exact scope, not parent scopes
        - Returns False if the scope path doesn't exist
        - Used to prevent duplicate registration of the same identifier

        See Also
        --------
        has_descendent_validator : Similar method for validators
        add_descendent_resource_origination : Register a resource at a scope
        """

        rtnval = False

        if self._package is None and scope_name == "<session>":
            if identifier in self._parameter_originations:
                rtnval = True
        else:
            scope_name = scope_name.replace("#", ".")
            to_walk_list = scope_name.split(".")

            rtnval = self._has_descendent_resource(to_walk_list, identifier)

        return rtnval
    
    def has_descendent_validator(self, scope_name: str, identifier: str) -> bool:
        """
        Check if a validator with the given identifier exists at the specified scope.

        This method traverses the scope tree to the target scope and checks
        if a validator origination with the given identifier is registered there.
        It does NOT check parent scopes - only the exact scope specified.

        Tree Traversal Algorithm
        ------------------------
        1. Handle special case of "<session>" (root scope)
        2. Parse scope path by replacing "#" with "." and splitting
        3. Recursively traverse to target scope
        4. Check if identifier exists in validator_originations

        Parameters
        ----------
        scope_name : str
            The full scope path to check.
            Format: "package.module#function" or "<session>" for root.
        identifier : str
            The validator identifier to search for.

        Returns
        -------
        bool
            True if the validator exists at the specified scope, False otherwise.

        Examples
        --------
        Check if a validator exists at session scope::

            exists = root.has_descendent_validator("<session>", "cleanup_validator")

        Check if a validator exists at a test scope::

            exists = root.has_descendent_validator(
                "tests.unit.test_auth#test_login",
                "auth_cleanup"
            )

        Notes
        -----
        - This checks only the exact scope, not parent scopes
        - Returns False if the scope path doesn't exist
        - Used to prevent duplicate registration of the same identifier

        See Also
        --------
        has_descendent_resource : Similar method for resources
        add_descendent_validator_origination : Register a validator at a scope
        """

        rtnval = False

        if self._package is None and scope_name == "<session>":
            if identifier in self._validator_originations:
                rtnval = True
        else:
            scope_name = scope_name.replace("#", ".")
            to_walk_list = scope_name.split(".")

            rtnval = self._has_descendent_validator(to_walk_list, identifier)

        return rtnval

    def lookup_scope(self, scope_name: str) -> "InjectionScope":
        """
        Find and return a scope node by its full path name.

        This method parses the scope path and traverses the tree to find
        the matching scope node. It handles the special "<session>" path
        for the root scope and converts "#" to "." for uniform traversal.

        Tree Traversal Algorithm
        ------------------------
        1. Handle special case: "<session>" returns self (root)
        2. Replace "#" with "." in scope path
        3. Split path into components
        4. Recursively traverse tree following path components
        5. Return matching scope or None if not found

        Parameters
        ----------
        scope_name : str
            The full scope path to look up.
            Format: "package.module#function" or "<session>" for root.

        Returns
        -------
        InjectionScope or None
            The scope node if found, None if the path doesn't exist.

        Examples
        --------
        Look up the root session scope::

            root_scope = root.lookup_scope("<session>")
            assert root_scope is root

        Look up a module scope::

            module_scope = root.lookup_scope("tests.unit.test_auth")
            if module_scope:
                print(f"Found scope: {module_scope.package}")

        Look up an injection moment scope::

            test_scope = root.lookup_scope("tests.unit.test_auth#test_login")
            if test_scope:
                # Access parameter originations at this scope
                for name, origin in test_scope.parameter_originations.items():
                    print(f"Parameter: {name}")

        Notes
        -----
        - Returns None if any component of the path doesn't exist
        - The "#" character is converted to "." for traversal
        - This is a read-only operation that doesn't modify the tree

        See Also
        --------
        has_descendent_resource : Check if a resource exists at a scope
        ensure_injection_scopes_for_injection_moment : Create scopes if missing
        """

        scope_found = None
        if self._package is None and scope_name == "<session>":
            scope_found = self
        else:
            scope_name = scope_name.replace("#", ".")
            to_walk_list = scope_name.split(".")

            if len(to_walk_list) > 0:
                scope_found = self._lookup_scope(to_walk_list)

        return scope_found

    def prune_unreference_scopes(self):
        """
        Remove non-relevant scope nodes from the tree.

        This method performs a post-order traversal of the scope tree,
        removing any scope nodes that are not marked as relevant. A scope
        is relevant if it lies on the path to an injection moment.

        Tree Traversal Algorithm (Post-Order Pruning)
        ----------------------------------------------
        1. Create a copy of child keys to allow safe deletion during iteration
        2. For each child scope:
           a. Recursively prune the child's descendants first (post-order)
           b. After child is pruned, check if child is relevant
           c. If not relevant, remove child from this scope's children
        3. Work backwards from leaves toward root

        The post-order traversal ensures that leaf nodes are processed before
        their parents, allowing proper bottom-up pruning.

        Examples
        --------
        Prune unreferenced scopes after ensuring injection moments::

            # First, ensure scopes for all injection moments
            for inj_mom in injection_moments:
                root.ensure_injection_scopes_for_injection_moment(inj_mom)

            # Now prune any scopes not on a path to an injection moment
            root.prune_unreference_scopes()

            # Tree now contains only relevant scopes

        Before and after pruning::

            # Before (some scopes not relevant):
            # root [relevant=True]
            # ├── tests [relevant=True]
            # │   ├── unit [relevant=True]
            # │   │   └── test_auth [relevant=True]
            # │   └── integration [relevant=False]  <- will be pruned
            # │       └── test_api [relevant=False] <- will be pruned
            # └── utils [relevant=False]            <- will be pruned

            # After pruning:
            # root [relevant=True]
            # └── tests [relevant=True]
            #     └── unit [relevant=True]
            #         └── test_auth [relevant=True]

        Notes
        -----
        - Must be called after ``ensure_injection_scopes_for_injection_moment``
        - Scopes are marked relevant during the ensure phase
        - Pruning optimizes memory and traversal performance
        - The root scope is never pruned (always relevant)

        See Also
        --------
        ensure_injection_scopes_for_injection_moment : Mark scopes as relevant
        is_relevant : Property indicating if scope should be kept
        """

        # =====================================================================
        # SCOPE PRUNING ALGORITHM (Post-Order Tree Traversal)
        # =====================================================================
        # This algorithm removes non-relevant scope nodes from the tree using
        # a post-order traversal pattern. Post-order ensures we process children
        # before parents, which is essential for bottom-up pruning.
        #
        # Why post-order?
        # - We must prune leaf nodes first before we can determine if their
        #   parent should be pruned
        # - A parent might become a leaf after its children are pruned
        # - Working backwards from leaves ensures correct pruning decisions
        #
        # Relevance marking:
        # - Scopes are marked relevant during ensure_injection_scopes_for_injection_moment()
        # - A scope is relevant if it lies on the path to an injection moment
        # - Non-relevant scopes are intermediate nodes with no injection moments
        #
        # Memory optimization:
        # - Pruning reduces memory footprint for large test suites
        # - Fewer nodes means faster traversal during parameter resolution
        # =====================================================================

        # Step 1: Create a snapshot of child keys to allow safe deletion during iteration
        # We cannot modify a dictionary while iterating over it, so we copy the keys first
        temp_child_key_list = [csk for csk in self._children.keys()]

        # Step 2: Process each child in reverse order (pop from end)
        # The order doesn't affect correctness, but processing in reverse
        # matches the typical depth-first post-order pattern
        while len(temp_child_key_list) > 0:
            nxt_child_key = temp_child_key_list.pop()
            nxt_child = self._children[nxt_child_key]

            # Step 3: Recursively prune grandchildren first (post-order descent)
            # This ensures all descendants are processed before we decide
            # whether to prune this child. A child might become prunable
            # only after its own children are removed.
            if len(nxt_child._children) > 0:
                nxt_child.prune_unreference_scopes()

            # Step 4: After descendants are pruned, check if this child is relevant
            # A scope is kept if:
            # - It was marked relevant during ensure_injection_scopes_for_injection_moment()
            # - OR it still has children (even if not directly relevant)
            # Note: We only check _is_relevant here because if a scope has
            # remaining children after pruning, those children are relevant
            # and this scope is implicitly relevant as their ancestor.
            if not nxt_child._is_relevant:
                del self._children[nxt_child_key]

        return

    def rename_resource_origins_from_main(self, new_origin: str):
        """
        Rename resource origins that were registered from __main__ module.

        When tests are run from a debug script (executed as __main__), the
        scope names contain "__main__" instead of the actual module name.
        This method renames those scopes to use the correct module path.

        Algorithm
        ---------
        1. Check if "__main__" exists as a child scope
        2. Remove "__main__" from children and add with new name
        3. For each injection scope under the renamed scope:
           a. Update the originating_scope of all parameter originations
           b. Re-register the origins with the corrected scope path

        Parameters
        ----------
        new_origin : str
            The correct module path to replace "__main__" with.
            Example: "tests.unit.test_auth"

        Examples
        --------
        Rename __main__ scopes after loading from debug script::

            # If tests were loaded from a script run as __main__:
            # root
            # └── __main__
            #     └── test_login

            root.rename_resource_origins_from_main("tests.unit.test_auth")

            # After renaming:
            # root
            # └── tests.unit.test_auth
            #     └── test_login

        Notes
        -----
        - Only affects scopes under the "__main__" child
        - Updates originating_scope in all affected ResourceOrigin objects
        - Re-registers origins to ensure proper scope tree structure
        - No-op if "__main__" child doesn't exist

        See Also
        --------
        add_descendent_resource_origination : Re-registers origins after rename
        """

        if "__main__" in self._children:
            last_dot = new_origin.rfind(".")

            cobj = self._children["__main__"]
            del self._children["__main__"]

            self._children[new_origin] = cobj

            # All of the children of cobj will be injection moments, go through all of
            # the child objects and fix the package name
            for inj_scope in cobj._children.values():
                inj_scope_origin = "{}#{}".format(new_origin, inj_scope._name)
                for _, poval in inj_scope.parameter_originations.items():
                    poval._originating_scope = inj_scope_origin
                    self.add_descendent_resource_origination(inj_scope_origin, poval)

        return

    def collect_used_sources(self, used_sources: Set[Callable]):
        """
        Collect all source functions that are used by parameter originations in the scope tree.
        
        This method performs a depth-first traversal of the scope tree, collecting
        all source functions that are referenced by parameter originations. This is
        used to identify unused registered sources.
        
        Parameters
        ----------
        used_sources : Set[Callable]
            A set to populate with source functions that are used.
            Modified in-place during traversal.
        
        Examples
        --------
        Collect all used sources from the scope tree::
        
            used_sources = set()
            root_scope.collect_used_sources(used_sources)
            
            # used_sources now contains all source functions referenced
            # by parameter originations in the tree
        
        Notes
        -----
        - Implied parameter originations (with no source) are skipped
        - Validator originations are also checked for source usage
        - The traversal visits every node in the tree
        """
        # Collect sources from parameter originations at this scope
        for param_origin in self._parameter_originations.values():
            if not param_origin.implied and param_origin.source_function is not None:
                used_sources.add(param_origin.source_function)
        
        # Collect sources from validator originations at this scope
        for validator_origin in self._validator_originations.values():
            if hasattr(validator_origin, 'source_function') and validator_origin.source_function is not None:
                used_sources.add(validator_origin.source_function)
        
        # Recursively collect from child scopes
        for child_scope in self._children.values():
            child_scope.collect_used_sources(used_sources)
        
        return

    def warn_shadowed_parameters(self, parent_params: Dict[str, Any] = None):
        """
        Warn about parameters that shadow parameters in parent scopes.
        
        This method performs a pre-order traversal of the scope tree, tracking
        visible parameters at each level. When a parameter at a child scope has
        the same identifier as a parameter in a parent scope, a warning is issued.
        
        Parameter shadowing can be intentional (to override a parent parameter)
        but may also indicate a configuration error where a developer accidentally
        reused an identifier.
        
        Parameters
        ----------
        parent_params : Dict[str, Any], optional
            Dictionary of parameter identifiers visible from parent scopes.
            Maps identifier to (scope_path, ResourceOrigin) tuple.
            If None, starts with an empty dictionary (root scope).
        
        Examples
        --------
        Check for shadowed parameters in the scope tree::
        
            root_scope.warn_shadowed_parameters()
            
            # Warnings will be issued for any parameters that shadow
            # parameters defined in parent scopes
        
        Notes
        -----
        - Shadowing is detected by comparing parameter identifiers
        - The warning includes both the shadowing and shadowed scope paths
        - This is a warning, not an error - shadowing may be intentional
        
        See Also
        --------
        resolve_resource_originations_for_injection_moment : Uses similar visibility logic
        """
        # Import here to avoid circular import
        from automojo.testbase.injection.injectionregistry import InjectionRegistry
        
        if parent_params is None:
            parent_params = {}
        
        # Build the current scope path for warning messages
        if self._package is None:
            current_scope_path = "<session>"
        else:
            current_scope_path = self._package
        
        # Check each parameter at this scope for shadowing
        for param_name, param_origin in self._parameter_originations.items():
            if param_name in parent_params:
                parent_scope_path, _ = parent_params[param_name]
                warnings.warn(
                    f"Parameter '{param_name}' at scope '{current_scope_path}' "
                    f"shadows parameter with same identifier at parent scope '{parent_scope_path}'. "
                    f"This may be intentional to override the parent parameter, "
                    f"or may indicate a configuration error.",
                    InjectionRegistry.ShadowedParameterWarning,
                    stacklevel=2
                )
        
        # Build the parameter visibility table for child scopes
        # Include both parent parameters and parameters at this scope
        child_params = parent_params.copy()
        for param_name, param_origin in self._parameter_originations.items():
            child_params[param_name] = (current_scope_path, param_origin)
        
        # Recursively check child scopes
        for child_scope in self._children.values():
            child_scope.warn_shadowed_parameters(child_params)
        
        return

    def to_tree_diagram(self, indent: str = "", is_last: bool = True, include_details: bool = True) -> str:
        """
        Generate a text-based tree diagram of the scope tree for debugging.

        This method produces an ASCII tree representation of the scope hierarchy,
        showing scope names, parameter originations, and validator originations
        at each level. The output is suitable for console display and debugging.

        Tree Diagram Format
        -------------------
        The diagram uses box-drawing characters to show the tree structure::

            <session> [relevant]
            ├── package_a
            │   ├── module_1
            │   │   │   Parameters: [param1, param2]
            │   │   │   Validators: [validator1]
            │   │   ├── test_function_1 [inj_scope]
            │   │   └── test_function_2 [inj_scope]
            │   └── module_2
            │       └── test_function_3 [inj_scope]
            └── package_b
                └── module_3
                    └── test_function_4 [inj_scope]

        Parameters
        ----------
        indent : str, optional
            The current indentation prefix for this node. Used internally
            during recursive calls. Default is empty string.
        is_last : bool, optional
            Whether this node is the last child of its parent. Used internally
            to determine the correct box-drawing character. Default is True.
        include_details : bool, optional
            Whether to include parameter and validator details in the output.
            Set to False for a more compact tree view. Default is True.

        Returns
        -------
        str
            A multi-line string containing the ASCII tree diagram.

        Examples
        --------
        Generate a tree diagram for debugging::

            root = InjectionScope()
            # ... populate the scope tree ...
            
            print(root.to_tree_diagram())
            
            # Output:
            # <session> [relevant]
            # ├── tests
            # │   └── unit
            # │       │   Parameters: [auth_token]
            # │       └── test_auth [inj_scope]
            # └── utils

        Generate a compact tree without details::

            print(root.to_tree_diagram(include_details=False))
            
            # Output:
            # <session> [relevant]
            # ├── tests
            # │   └── unit
            # │       └── test_auth [inj_scope]
            # └── utils

        Notes
        -----
        - The root scope is displayed as "<session>"
        - Injection moment scopes are marked with "[inj_scope]"
        - Relevant scopes are marked with "[relevant]"
        - Parameters and validators are listed if include_details is True
        - This method is intended for debugging and development use

        See Also
        --------
        to_json : Export the scope tree to JSON format
        to_dict : Convert the scope tree to a dictionary
        """
        lines = []
        
        # Build the node label
        if self._name is None:
            label = "<session>"
        else:
            label = self._name
        
        # Add status indicators
        indicators = []
        if self._is_relevant:
            indicators.append("relevant")
        if self._is_inj_scope:
            indicators.append("inj_scope")
        
        if indicators:
            label = f"{label} [{', '.join(indicators)}]"
        
        # Add the current node
        if indent == "":
            # Root node
            lines.append(label)
        else:
            # Child node with tree connector
            connector = "└── " if is_last else "├── "
            lines.append(f"{indent}{connector}{label}")
        
        # Calculate the new indent for children and details
        if indent == "":
            child_indent = ""
        else:
            child_indent = indent + ("    " if is_last else "│   ")
        
        # Add parameter and validator details if requested
        if include_details:
            detail_prefix = child_indent + ("    " if self._children else "")
            
            if self._parameter_originations:
                param_names = list(self._parameter_originations.keys())
                lines.append(f"{detail_prefix}│   Parameters: {param_names}")
            
            if self._validator_originations:
                validator_names = list(self._validator_originations.keys())
                lines.append(f"{detail_prefix}│   Validators: {validator_names}")
        
        # Recursively add children
        child_keys = list(self._children.keys())
        for i, child_key in enumerate(child_keys):
            child_scope = self._children[child_key]
            is_last_child = (i == len(child_keys) - 1)
            
            # Calculate indent for child
            if indent == "":
                next_indent = ""
            else:
                next_indent = child_indent
            
            child_diagram = child_scope.to_tree_diagram(
                indent=next_indent if indent != "" else "",
                is_last=is_last_child,
                include_details=include_details
            )
            lines.append(child_diagram)
        
        return "\n".join(lines)

    def to_dict(self, include_origins: bool = True) -> Dict[str, Any]:
        """
        Convert the scope tree to a dictionary representation.

        This method creates a dictionary structure that represents the scope
        tree, suitable for serialization to JSON or other formats. The output
        includes scope metadata, parameter originations, validator originations,
        and child scopes.

        Dictionary Structure
        --------------------
        The returned dictionary has the following structure::

            {
                "name": "<session>" or scope_name,
                "package": null or package_path,
                "is_injection_scope": bool,
                "is_relevant": bool,
                "parameters": {
                    "param_name": {
                        "identifier": str,
                        "originating_scope": str,
                        "lifespan": str,
                        "source_id": str or null,
                        "implied": bool
                    },
                    ...
                },
                "validators": {
                    "validator_name": {
                        "identifier": str,
                        "originating_scope": str,
                        "suffix": str,
                        "source_id": str or null
                    },
                    ...
                },
                "children": {
                    "child_name": { ... recursive structure ... },
                    ...
                }
            }

        Parameters
        ----------
        include_origins : bool, optional
            Whether to include detailed origin information for parameters
            and validators. Set to False for a more compact representation
            that only includes identifiers. Default is True.

        Returns
        -------
        Dict[str, Any]
            A dictionary representation of the scope tree.

        Examples
        --------
        Convert scope tree to dictionary::

            root = InjectionScope()
            # ... populate the scope tree ...
            
            tree_dict = root.to_dict()
            print(tree_dict["name"])  # "<session>"
            print(tree_dict["children"].keys())  # dict_keys(['tests', 'utils'])

        Convert to compact dictionary without origin details::

            compact_dict = root.to_dict(include_origins=False)

        Notes
        -----
        - The root scope name is represented as "<session>"
        - Origin details include lifespan, source_id, and implied status
        - Child scopes are recursively converted
        - This method is useful for debugging and serialization

        See Also
        --------
        to_json : Export the scope tree to JSON string
        to_tree_diagram : Generate ASCII tree diagram
        """
        result = {
            "name": self._name if self._name is not None else "<session>",
            "package": self._package,
            "is_injection_scope": self._is_inj_scope,
            "is_relevant": self._is_relevant,
        }
        
        # Add parameter originations
        if include_origins:
            parameters = {}
            for param_name, param_origin in self._parameter_originations.items():
                param_info = {
                    "identifier": param_origin.identifier,
                    "originating_scope": param_origin.originating_scope,
                    "lifespan": param_origin.life_span.name if param_origin.life_span else None,
                    "source_id": param_origin.source_id if hasattr(param_origin, 'source_id') else None,
                    "implied": param_origin.implied if hasattr(param_origin, 'implied') else False,
                }
                parameters[param_name] = param_info
            result["parameters"] = parameters
            
            validators = {}
            for val_name, val_origin in self._validator_originations.items():
                val_info = {
                    "identifier": val_origin.identifier,
                    "originating_scope": val_origin.originating_scope,
                    "suffix": val_origin.suffix if hasattr(val_origin, 'suffix') else None,
                    "source_id": val_origin.source_id if hasattr(val_origin, 'source_id') else None,
                }
                validators[val_name] = val_info
            result["validators"] = validators
        else:
            result["parameters"] = list(self._parameter_originations.keys())
            result["validators"] = list(self._validator_originations.keys())
        
        # Add children recursively
        children = {}
        for child_name, child_scope in self._children.items():
            children[child_name] = child_scope.to_dict(include_origins=include_origins)
        result["children"] = children
        
        return result

    def to_json(self, include_origins: bool = True, indent: int = 2) -> str:
        """
        Export the scope tree to JSON format.

        This method serializes the scope tree to a JSON string, suitable for
        saving to a file, sending over a network, or loading into other tools
        for analysis. The JSON structure mirrors the dictionary representation
        from ``to_dict()``.

        JSON Structure
        --------------
        The JSON output has the following structure::

            {
                "name": "<session>",
                "package": null,
                "is_injection_scope": false,
                "is_relevant": true,
                "parameters": { ... },
                "validators": { ... },
                "children": {
                    "package_name": { ... recursive structure ... }
                }
            }

        Parameters
        ----------
        include_origins : bool, optional
            Whether to include detailed origin information for parameters
            and validators. Set to False for a more compact JSON output.
            Default is True.
        indent : int, optional
            The number of spaces to use for indentation in the JSON output.
            Set to None for compact (single-line) output. Default is 2.

        Returns
        -------
        str
            A JSON string representation of the scope tree.

        Examples
        --------
        Export scope tree to JSON::

            root = InjectionScope()
            # ... populate the scope tree ...
            
            json_str = root.to_json()
            print(json_str)
            
            # Save to file
            with open("scope_tree.json", "w") as f:
                f.write(json_str)

        Export compact JSON without origin details::

            compact_json = root.to_json(include_origins=False, indent=None)

        Load JSON back for analysis::

            import json
            tree_data = json.loads(root.to_json())
            print(tree_data["children"].keys())

        Notes
        -----
        - The JSON output is valid and can be parsed by any JSON parser
        - Large scope trees may produce significant JSON output
        - Use ``include_origins=False`` for smaller output size
        - Use ``indent=None`` for compact single-line output

        See Also
        --------
        to_dict : Convert to dictionary (used internally)
        to_tree_diagram : Generate ASCII tree diagram for console
        """
        tree_dict = self.to_dict(include_origins=include_origins)
        return json.dumps(tree_dict, indent=indent, default=str)

    def collect_all_parameters(self, scope_path: str = None) -> Dict[str, Any]:
        """
        Collect all parameter originations from the scope tree.
        
        This method performs a depth-first traversal of the scope tree,
        collecting all parameter originations into a dictionary keyed by
        "scope:identifier".
        
        Parameters
        ----------
        scope_path : str, optional
            The current scope path (used internally during recursion).
            If None, starts from the root scope.
        
        Returns
        -------
        Dict[str, Any]
            A dictionary mapping "scope:identifier" to parameter information
            including the ResourceOrigin object and scope path.
        
        Examples
        --------
        Collect all parameters from the scope tree::
        
            root = InjectionScope()
            # ... populate the scope tree ...
            
            all_params = root.collect_all_parameters()
            for key, info in all_params.items():
                print(f"{key}: {info['origin'].source_function_name}")
        """
        if scope_path is None:
            scope_path = "<session>" if self._package is None else self._package
        
        result = {}
        
        # Collect parameters at this scope
        for param_name, param_origin in self._parameter_originations.items():
            key = f"{scope_path}:{param_name}"
            result[key] = {
                "identifier": param_name,
                "scope": scope_path,
                "origin": param_origin
            }
        
        # Recursively collect from children
        for child_name, child_scope in self._children.items():
            if self._package is None:
                child_path = child_name
            else:
                child_path = f"{self._package}.{child_name}"
            
            # Handle injection moment scopes (marked with #)
            if child_scope._is_inj_scope:
                if self._package is None:
                    child_path = f"{child_name}"
                else:
                    # Replace the last . with # for injection moment scopes
                    parent_path = self._package
                    child_path = f"{parent_path}#{child_name}"
            
            child_params = child_scope.collect_all_parameters(child_path)
            result.update(child_params)
        
        return result

    def build_dependency_graph(self):
        """
        Build a dependency graph from the scope tree.
        
        This method analyzes all parameter originations in the scope tree
        and builds a graph showing the dependency relationships between
        parameters.
        
        Returns
        -------
        DependencyGraph
            A dependency graph object containing nodes and edges.
        
        Examples
        --------
        Build and visualize a dependency graph::
        
            root = InjectionScope()
            # ... populate the scope tree ...
            
            graph = root.build_dependency_graph()
            print(graph.to_mermaid())
        
        Notes
        -----
        - The graph includes all parameters in the scope tree
        - Edges represent "depends on" relationships
        - Root parameters have no incoming edges
        - Leaf parameters have no outgoing edges
        """
        from automojo.testbase.injection.introspection import (
            DependencyGraph,
            DependencyGraphNode,
            DependencyGraphEdge
        )
        
        graph = DependencyGraph()
        
        # First, collect all parameters
        all_params = self.collect_all_parameters()
        
        # Build a lookup table for parameter identifiers to their scopes
        # This helps resolve dependencies that might be defined at different scopes
        param_by_identifier: Dict[str, List[str]] = {}
        for key, info in all_params.items():
            identifier = info["identifier"]
            if identifier not in param_by_identifier:
                param_by_identifier[identifier] = []
            param_by_identifier[identifier].append(info["scope"])
        
        # Create nodes for all parameters
        for key, info in all_params.items():
            origin = info["origin"]
            
            source_func_name = None
            lifespan = None
            is_implied = False
            
            if hasattr(origin, 'implied'):
                is_implied = origin.implied
            
            if not is_implied and origin._source is not None:
                try:
                    source_func_name = origin.source_function_name
                except (AttributeError, TypeError):
                    pass
            
            if hasattr(origin, 'life_span') and origin.life_span is not None:
                lifespan = origin.life_span.name
            
            node = DependencyGraphNode(
                identifier=info["identifier"],
                scope=info["scope"],
                source_function_name=source_func_name,
                lifespan=lifespan,
                is_implied=is_implied
            )
            graph.nodes[key] = node
        
        # Create edges based on source function dependencies
        has_incoming: Set[str] = set()
        has_outgoing: Set[str] = set()
        
        for key, info in all_params.items():
            origin = info["origin"]
            from_scope = info["scope"]
            from_param = info["identifier"]
            
            # Get dependencies from source function signature
            dependencies = _get_source_dependencies(origin)
            
            for dep_name in dependencies:
                # Find the scope where this dependency is defined
                # Look for the dependency in the visibility chain
                dep_scope = self._find_dependency_scope(
                    from_scope, dep_name, param_by_identifier
                )
                
                if dep_scope is not None:
                    edge = DependencyGraphEdge(
                        from_param=from_param,
                        to_param=dep_name,
                        from_scope=from_scope,
                        to_scope=dep_scope
                    )
                    graph.edges.append(edge)
                    has_outgoing.add(key)
                    has_incoming.add(f"{dep_scope}:{dep_name}")
        
        # Identify root and leaf parameters
        for key in graph.nodes.keys():
            if key not in has_outgoing:
                graph.root_parameters.append(key)
            if key not in has_incoming:
                graph.leaf_parameters.append(key)
        
        return graph

    def _find_dependency_scope(self, from_scope: str, dep_name: str, 
                                param_by_identifier: Dict[str, List[str]]) -> Optional[str]:
        """
        Find the scope where a dependency is defined, following visibility rules.
        
        This method searches for a parameter by name, starting from the given
        scope and walking up the scope hierarchy (following visibility rules).
        
        Parameters
        ----------
        from_scope : str
            The scope where the dependent parameter is defined.
        dep_name : str
            The name of the dependency to find.
        param_by_identifier : Dict[str, List[str]]
            A lookup table mapping parameter names to their scopes.
        
        Returns
        -------
        str or None
            The scope where the dependency is defined, or None if not found.
        """
        if dep_name not in param_by_identifier:
            return None
        
        available_scopes = param_by_identifier[dep_name]
        
        # If only one scope has this parameter, return it
        if len(available_scopes) == 1:
            return available_scopes[0]
        
        # Otherwise, find the most specific scope that is visible from from_scope
        # A scope is visible if it's an ancestor of from_scope or the same scope
        
        # Parse from_scope into components
        if "#" in from_scope:
            module_part, func_part = from_scope.split("#")
            from_parts = module_part.split(".") + [func_part]
        else:
            from_parts = from_scope.split(".") if from_scope != "<session>" else []
        
        best_scope = None
        best_depth = -1
        
        for scope in available_scopes:
            # Check if this scope is visible from from_scope
            if scope == "<session>":
                # Session scope is always visible
                if best_depth < 0:
                    best_scope = scope
                    best_depth = 0
            else:
                # Parse the candidate scope
                if "#" in scope:
                    scope_module, scope_func = scope.split("#")
                    scope_parts = scope_module.split(".") + [scope_func]
                else:
                    scope_parts = scope.split(".")
                
                # Check if scope is an ancestor of from_scope
                if len(scope_parts) <= len(from_parts):
                    is_ancestor = True
                    for i, part in enumerate(scope_parts):
                        if i >= len(from_parts) or from_parts[i] != part:
                            is_ancestor = False
                            break
                    
                    if is_ancestor and len(scope_parts) > best_depth:
                        best_scope = scope
                        best_depth = len(scope_parts)
        
        return best_scope

    def get_parameter_dependencies(self, identifier: str, scope: Optional[str] = None):
        """
        Get detailed dependency information for a specific parameter.
        
        This method analyzes a parameter's dependencies, including both
        direct dependencies (parameters required by its source function)
        and transitive dependencies (dependencies of dependencies).
        
        Parameters
        ----------
        identifier : str
            The parameter identifier to analyze.
        scope : str, optional
            The scope where the parameter is defined. If None, searches
            all scopes for the parameter.
        
        Returns
        -------
        DependencyAnalysisResult or None
            A result object containing dependency information, or None
            if the parameter is not found.
        
        Examples
        --------
        Analyze dependencies for a parameter::
        
            root = InjectionScope()
            # ... populate the scope tree ...
            
            result = root.get_parameter_dependencies("auth_token", "tests.unit#test_login")
            if result:
                print(f"Direct dependencies: {[d.identifier for d in result.direct_dependencies]}")
                print(f"Transitive dependencies: {[d.identifier for d in result.transitive_dependencies]}")
                if result.has_circular_dependency:
                    print(f"Circular dependency detected: {result.circular_path}")
        
        Notes
        -----
        - Circular dependencies are detected and reported
        - The dependency chain shows the order of resolution
        - Implied parameters have no dependencies
        """
        from automojo.testbase.injection.introspection import (
            ParameterDependency,
            DependencyAnalysisResult
        )
        
        # Collect all parameters
        all_params = self.collect_all_parameters()
        
        # Find the parameter
        target_key = None
        target_info = None
        
        if scope is not None:
            target_key = f"{scope}:{identifier}"
            if target_key in all_params:
                target_info = all_params[target_key]
        else:
            # Search all scopes for the parameter
            for key, info in all_params.items():
                if info["identifier"] == identifier:
                    target_key = key
                    target_info = info
                    break
        
        if target_info is None:
            return None
        
        # Build the parameter dependency object
        origin = target_info["origin"]
        
        source_func_name = None
        source_module = None
        lifespan = None
        is_implied = False
        
        if hasattr(origin, 'implied'):
            is_implied = origin.implied
        
        if not is_implied and origin._source is not None:
            try:
                source_func_name = origin.source_function_name
                source_module = origin.source_module_name
            except (AttributeError, TypeError):
                pass
        
        if hasattr(origin, 'life_span') and origin.life_span is not None:
            lifespan = origin.life_span.name
        
        direct_deps = _get_source_dependencies(origin)
        
        param_dep = ParameterDependency(
            identifier=identifier,
            scope=target_info["scope"],
            source_function_name=source_func_name,
            source_module=source_module,
            lifespan=lifespan,
            direct_dependencies=direct_deps,
            is_implied=is_implied
        )
        
        result = DependencyAnalysisResult(parameter=param_dep)
        
        # Build a lookup table for finding dependencies
        param_by_identifier: Dict[str, List[str]] = {}
        for key, info in all_params.items():
            ident = info["identifier"]
            if ident not in param_by_identifier:
                param_by_identifier[ident] = []
            param_by_identifier[ident].append(info["scope"])
        
        # Resolve direct dependencies
        for dep_name in direct_deps:
            dep_scope = self._find_dependency_scope(
                target_info["scope"], dep_name, param_by_identifier
            )
            if dep_scope is not None:
                dep_key = f"{dep_scope}:{dep_name}"
                if dep_key in all_params:
                    dep_info = all_params[dep_key]
                    dep_origin = dep_info["origin"]
                    
                    dep_source_func = None
                    dep_source_module = None
                    dep_lifespan = None
                    dep_implied = False
                    
                    if hasattr(dep_origin, 'implied'):
                        dep_implied = dep_origin.implied
                    
                    if not dep_implied and dep_origin._source is not None:
                        try:
                            dep_source_func = dep_origin.source_function_name
                            dep_source_module = dep_origin.source_module_name
                        except (AttributeError, TypeError):
                            pass
                    
                    if hasattr(dep_origin, 'life_span') and dep_origin.life_span is not None:
                        dep_lifespan = dep_origin.life_span.name
                    
                    dep_direct_deps = _get_source_dependencies(dep_origin)
                    
                    dep_param = ParameterDependency(
                        identifier=dep_name,
                        scope=dep_scope,
                        source_function_name=dep_source_func,
                        source_module=dep_source_module,
                        lifespan=dep_lifespan,
                        direct_dependencies=dep_direct_deps,
                        is_implied=dep_implied
                    )
                    result.direct_dependencies.append(dep_param)
        
        # Resolve transitive dependencies (with circular detection)
        visited: Set[str] = set()
        path: List[str] = []
        
        def resolve_transitive(param_key: str, param_info: dict):
            if param_key in visited:
                # Check for circular dependency
                if param_key in path:
                    result.has_circular_dependency = True
                    cycle_start = path.index(param_key)
                    result.circular_path = path[cycle_start:] + [param_key]
                return
            
            visited.add(param_key)
            path.append(param_key)
            
            origin = param_info["origin"]
            deps = _get_source_dependencies(origin)
            
            for dep_name in deps:
                dep_scope = self._find_dependency_scope(
                    param_info["scope"], dep_name, param_by_identifier
                )
                if dep_scope is not None:
                    dep_key = f"{dep_scope}:{dep_name}"
                    if dep_key in all_params and dep_key != target_key:
                        dep_info = all_params[dep_key]
                        
                        # Add to transitive dependencies if not already there
                        if not any(d.identifier == dep_name and d.scope == dep_scope 
                                   for d in result.transitive_dependencies):
                            dep_origin = dep_info["origin"]
                            
                            dep_source_func = None
                            dep_source_module = None
                            dep_lifespan = None
                            dep_implied = False
                            
                            if hasattr(dep_origin, 'implied'):
                                dep_implied = dep_origin.implied
                            
                            if not dep_implied and dep_origin._source is not None:
                                try:
                                    dep_source_func = dep_origin.source_function_name
                                    dep_source_module = dep_origin.source_module_name
                                except (AttributeError, TypeError):
                                    pass
                            
                            if hasattr(dep_origin, 'life_span') and dep_origin.life_span is not None:
                                dep_lifespan = dep_origin.life_span.name
                            
                            dep_direct_deps = _get_source_dependencies(dep_origin)
                            
                            trans_dep = ParameterDependency(
                                identifier=dep_name,
                                scope=dep_scope,
                                source_function_name=dep_source_func,
                                source_module=dep_source_module,
                                lifespan=dep_lifespan,
                                direct_dependencies=dep_direct_deps,
                                is_implied=dep_implied
                            )
                            result.transitive_dependencies.append(trans_dep)
                        
                        # Recurse
                        resolve_transitive(dep_key, dep_info)
            
            path.pop()
        
        # Start transitive resolution from direct dependencies
        for dep in result.direct_dependencies:
            dep_key = f"{dep.scope}:{dep.identifier}"
            if dep_key in all_params:
                resolve_transitive(dep_key, all_params[dep_key])
        
        # Build dependency chain
        result.dependency_chain = [target_key] + [
            f"{d.scope}:{d.identifier}" for d in result.transitive_dependencies
        ]
        
        return result

    def resolve_resource_originations_for_injection_moment(self, inj_mom: InjectionMoment, missing_params: List[Any]):
        """
        Resolve and validate parameter dependencies for an injection moment.

        This method walks the scope tree from root to the injection moment,
        building a parameter visibility table as it descends. At each scope,
        it validates that all source function dependencies can be satisfied
        by parameters visible at that scope level.

        Parameter Resolution Algorithm
        ------------------------------
        1. Parse injection moment scope name into path components
        2. Initialize parameter table with root scope's parameter originations
        3. For each scope along the path (pre-order descent):
           a. Copy parent's parameter table (inheritance)
           b. For each parameter origination at current scope:
              - Check if source function's dependencies are in param table
              - Record any missing dependencies
              - Add this parameter to the table for child scopes
           c. Recurse into next scope component
        4. Collect all missing parameters in the provided list

        Parameter Visibility Rules
        --------------------------
        - Parameters at parent scopes are visible to all descendant scopes
        - Local parameters shadow parent parameters with the same identifier
        - Reserved parameter names (e.g., "constraints") are skipped
        - Parameters are visible in declaration order within each scope

        Parameters
        ----------
        inj_mom : InjectionMoment
            The injection moment whose parameter dependencies should be resolved.
        missing_params : List[Any]
            A list to populate with any unresolved parameter dependencies.
            Each entry is [param_name, param_info] for missing parameters.
            Modified in-place during traversal.

        Examples
        --------
        Resolve parameters for a test function::

            missing = []
            root.resolve_resource_originations_for_injection_moment(
                test_login_moment,
                missing
            )

            if missing:
                for param_name, param_info in missing:
                    print(f"Missing parameter: {param_name}")

        Understanding parameter visibility::

            # Given this scope tree:
            # root (<session>)
            #   - session_config (visible everywhere)
            # └── tests
            #     └── unit
            #         - unit_fixture (visible to unit tests)
            #         └── test_auth
            #             - auth_token (visible to test_auth tests)
            #             └── test_login
            #                 - login_data (visible only here)

            # When resolving test_login, visible parameters are:
            # - session_config (from root)
            # - unit_fixture (from tests.unit)
            # - auth_token (from tests.unit.test_auth)
            # - login_data (from tests.unit.test_auth#test_login)

        Notes
        -----
        - This is called during finalize_startup after scope pruning
        - Missing parameters indicate configuration errors
        - The "constraints" parameter is reserved and always skipped
        - Source functions may depend on parameters from parent scopes

        See Also
        --------
        ensure_injection_scopes_for_injection_moment : Must be called first
        prune_unreference_scopes : Should be called before resolution
        """

        # =====================================================================
        # PARAMETER VISIBILITY CHAIN ALGORITHM (Pre-Order Tree Traversal)
        # =====================================================================
        # This algorithm resolves parameter dependencies by walking the scope
        # tree from root to the injection moment, building a visibility table
        # that accumulates parameters as we descend.
        #
        # Key concept: Parameter Inheritance
        # - Parameters defined at parent scopes are visible to all descendants
        # - This mirrors Python's module hierarchy and import visibility
        # - Local parameters can shadow parent parameters with the same name
        #
        # The visibility chain works like a scope chain in programming languages:
        # - Session scope (root) -> Package scope -> Module scope -> Test scope
        # - Each level inherits all parameters from its ancestors
        # - Each level can add new parameters visible to its descendants
        #
        # Example visibility chain for "tests.unit.test_auth#test_login":
        #   root (<session>)     -> {session_config}
        #   tests                -> {session_config}
        #   tests.unit           -> {session_config, unit_fixture}
        #   tests.unit.test_auth -> {session_config, unit_fixture, auth_token}
        #   test_login           -> {session_config, unit_fixture, auth_token, login_data}
        # =====================================================================

        # Step 1: Parse the injection moment's scope name into traversable components
        # Format: "package.module#function" -> ["package", "module", "function"]
        inj_scope_name = inj_mom.scope_name

        # Split at "#" to separate module path from function name
        # The "#" character is a convention to distinguish injection moment scopes
        module_name, inj_name = inj_scope_name.split("#")

        # Build the complete path as a list of components to traverse
        inj_scope_parts = module_name.split(".")
        inj_scope_parts.append(inj_name)

        # Step 2: Initialize the parameter visibility table with root scope parameters
        # The root scope (<session>) contains session-level parameters that are
        # visible to ALL injection moments in the test session
        param_table = {}
        for pname, pinfo in self._parameter_originations.items():
            param_table[pname] = pinfo

        # Step 3: Begin the recursive descent, passing the visibility table
        # The table will be copied and extended at each scope level
        # Missing parameters are accumulated in the missing_params list
        self._resolve_resource_originations_for_injection_moment_descend(inj_mom, inj_scope_parts, param_table, missing_params)

        return

    def _add_descendent_resource_origination(self, parameter_origin: ResourceOrigin, to_walk_list: List[str], path_stack: List[str], is_inj_scope):
        """
        Private recursive helper for add_descendent_resource_origination.

        This method implements the recursive descent through the scope tree,
        creating intermediate nodes as needed and inserting the origin at
        the final destination.

        Algorithm Steps
        ---------------
        1. Pop the next path component from to_walk_list
        2. Look up or create the child scope for this component
        3. If more path components remain:
           a. Push current component to path_stack
           b. Recurse into child scope
           c. Pop from path_stack on return
        4. If at final destination:
           a. Insert parameter_origin into child's parameter_originations
           b. Move to end to maintain insertion order

        Parameters
        ----------
        parameter_origin : ResourceOrigin
            The origin to insert at the final scope.
        to_walk_list : List[str]
            Remaining path components to traverse. Modified during recursion.
        path_stack : List[str]
            Accumulated path for building full package names.
        is_inj_scope : bool
            Whether the final scope is an injection moment scope.
        """

        curr_leaf = to_walk_list.pop(0)
        curr_scope = None

        if curr_leaf in self._children:
            curr_scope = self._children[curr_leaf]
        else:
            curr_package = curr_leaf
            if len(path_stack) > 0:
                curr_package = "{}.{}".format(".".join(path_stack), curr_package)

            set_inj_scope = False
            if len(to_walk_list) == 0:
                set_inj_scope = is_inj_scope

            curr_scope = InjectionScope(curr_leaf, curr_package, set_inj_scope)
            self._children[curr_leaf] = curr_scope

        if len(to_walk_list) > 0:
            path_stack.append(curr_leaf)
            curr_scope._add_descendent_resource_origination(parameter_origin, to_walk_list, path_stack, is_inj_scope)
            path_stack.pop()
        else:
            if parameter_origin is not None:
                identifier = parameter_origin.identifier
                curr_scope._parameter_originations[identifier] = parameter_origin
                curr_scope._parameter_originations.move_to_end(identifier, last=True)

        return
    
    def _add_descendent_validator_origination(self, validator_origin: ValidatorOrigin, to_walk_list: List[str], path_stack: List[str], is_inj_scope):
        """
        Private recursive helper for add_descendent_validator_origination.

        This method implements the recursive descent through the scope tree,
        creating intermediate nodes as needed and inserting the validator
        origin at the final destination.

        Algorithm Steps
        ---------------
        1. Pop the next path component from to_walk_list
        2. Look up or create the child scope for this component
        3. If more path components remain:
           a. Push current component to path_stack
           b. Recurse into child scope
           c. Pop from path_stack on return
        4. If at final destination:
           a. Insert validator_origin into child's validator_originations
           b. Move to end to maintain insertion order

        Parameters
        ----------
        validator_origin : ValidatorOrigin
            The validator origin to insert at the final scope.
        to_walk_list : List[str]
            Remaining path components to traverse. Modified during recursion.
        path_stack : List[str]
            Accumulated path for building full package names.
        is_inj_scope : bool
            Whether the final scope is an injection moment scope.
        """

        curr_leaf = to_walk_list.pop(0)
        curr_scope = None

        if curr_leaf in self._children:
            curr_scope = self._children[curr_leaf]
        else:
            curr_package = curr_leaf
            if len(path_stack) > 0:
                curr_package = "{}.{}".format(".".join(path_stack), curr_package)

            set_inj_scope = False
            if len(to_walk_list) == 0:
                set_inj_scope = is_inj_scope

            curr_scope = InjectionScope(curr_leaf, curr_package, set_inj_scope)
            self._children[curr_leaf] = curr_scope

        if len(to_walk_list) > 0:
            path_stack.append(curr_leaf)
            curr_scope._add_descendent_validator_origination(validator_origin, to_walk_list, path_stack, is_inj_scope)
            path_stack.pop()
        else:
            if validator_origin is not None:
                identifier = validator_origin.identifier
                curr_scope._validator_originations[identifier] = validator_origin
                curr_scope._validator_originations.move_to_end(identifier, last=True)

        return

    def _ensure_injection_scopes_for_injection_moment(self, inj_mom: InjectionMoment, inj_scope_parts: List[str], path_stack: List[str]):
        """
        Private recursive helper for ensure_injection_scopes_for_injection_moment.

        This method implements the recursive descent that creates scope nodes
        along the path to an injection moment and marks them as relevant.

        Algorithm Steps
        ---------------
        1. If path components remain:
           a. Pop next component from inj_scope_parts
           b. If child doesn't exist:
              - Create new InjectionScope with appropriate package path
              - Set is_inj_scope=True if this is the final component
              - Mark as relevant
              - Add to children dictionary
           c. If child exists:
              - Mark existing child as relevant
           d. Push component to path_stack
           e. Recurse into child scope
        2. Base case: no more components (recursion terminates)

        Parameters
        ----------
        inj_mom : InjectionMoment
            The injection moment being processed.
        inj_scope_parts : List[str]
            Remaining path components. Modified during recursion.
        path_stack : List[str]
            Accumulated path for building full package names.
        """

        if len(inj_scope_parts) > 0:
            curr_leaf = inj_scope_parts.pop(0)

            if curr_leaf not in self._children:
                curr_package = curr_leaf
                if len(path_stack) > 0:
                    curr_package = "{}.{}".format(".".join(path_stack), curr_package)
                
                set_inj_scope = False
                if len(inj_scope_parts) == 0:
                    set_inj_scope = True
                curr_scope = InjectionScope(curr_leaf, curr_package, set_inj_scope)
                curr_scope._is_relevant = True
                self._children[curr_leaf] = curr_scope

                path_stack.append(curr_leaf)
                curr_scope = self._children[curr_leaf]
                curr_scope._ensure_injection_scopes_for_injection_moment(inj_mom, inj_scope_parts, path_stack)

            else:
                path_stack.append(curr_leaf)
                curr_scope = self._children[curr_leaf]
                curr_scope._is_relevant = True
                curr_scope._ensure_injection_scopes_for_injection_moment(inj_mom, inj_scope_parts, path_stack)

        return

    def _has_descendent_resource(self, to_walk_list: List[str], identifier: str):
        """
        Private recursive helper for has_descendent_resource.

        Traverses the scope tree following the path in to_walk_list and
        checks if the identifier exists at the final scope.

        Parameters
        ----------
        to_walk_list : List[str]
            Remaining path components to traverse.
        identifier : str
            The parameter identifier to search for.

        Returns
        -------
        bool
            True if identifier found at target scope, False otherwise.
        """

        rtnval = False

        if len(to_walk_list) == 0:
            if identifier in self._parameter_originations:
                rtnval = True
        else:
            child_name = to_walk_list[0]
            if child_name in self._children:
                scope = self._children[child_name]
                desc_to_walk_list = to_walk_list[1:]
                rtnval = scope._has_descendent_resource(desc_to_walk_list, identifier)

        return rtnval
    
    def _has_descendent_validator(self, to_walk_list: List[str], identifier: str):
        """
        Private recursive helper for has_descendent_validator.

        Traverses the scope tree following the path in to_walk_list and
        checks if the validator identifier exists at the final scope.

        Parameters
        ----------
        to_walk_list : List[str]
            Remaining path components to traverse.
        identifier : str
            The validator identifier to search for.

        Returns
        -------
        bool
            True if identifier found at target scope, False otherwise.
        """

        rtnval = False

        if len(to_walk_list) == 0:
            if identifier in self._validator_originations:
                rtnval = True
        else:
            child_name = to_walk_list[0]
            if child_name in self._children:
                scope = self._children[child_name]
                desc_to_walk_list = to_walk_list[1:]
                rtnval = scope._has_descendent_validator(desc_to_walk_list, identifier)

        return rtnval

    def _lookup_scope(self, to_walk_list: List[str]) -> "InjectionScope":
        """
            The private recursive method for lookup_scope that is used to find a scope by path
            in the scope tree.

            :param to_walk_list: A list of scope names to walk down to find the desired scope.
        """

        scope_found = None

        child_name = to_walk_list.pop(0)
        if child_name in self._children:
            child_scope = self._children[child_name]
            if len(to_walk_list) > 0:
                scope_found = child_scope._lookup_scope(to_walk_list)
            else:
                scope_found = child_scope

        return scope_found

    def _resolve_resource_originations_for_injection_moment_descend(self, inj_mom: InjectionMoment, inj_scope_parts: List[str],
        param_table: dict, missing_params: List[Any]):
        """
        Private recursive helper for resolve_resource_originations_for_injection_moment.

        This method implements the pre-order descent through the scope tree,
        building the parameter visibility table and checking for missing
        dependencies at each scope level.

        Algorithm Steps
        ---------------
        1. If path components remain:
           a. Pop next scope name from inj_scope_parts
           b. Look up child scope by name
           c. If child exists:
              - Copy param_table for this scope level (inheritance)
              - For each parameter origination in child scope:
                * Call lateral check to validate source dependencies
                * Add parameter to nxt_param_table for descendants
              - Recurse into child with updated param_table
           d. If child not found: log warning (shouldn't happen after ensure)

        Parameters
        ----------
        inj_mom : InjectionMoment
            The injection moment being resolved.
        inj_scope_parts : List[str]
            Remaining path components. Modified during recursion.
        param_table : dict
            Current parameter visibility table. Copied at each level.
        missing_params : List[Any]
            Accumulator for missing parameter dependencies.
        """

        # =====================================================================
        # PARAMETER VISIBILITY DESCENT (Recursive Pre-Order Traversal)
        # =====================================================================
        # This helper implements the recursive descent through the scope tree,
        # building the parameter visibility table at each level and checking
        # for missing dependencies.
        #
        # At each scope level, we:
        # 1. Copy the parent's parameter table (inheritance)
        # 2. Validate each local parameter's source dependencies
        # 3. Add local parameters to the table for descendants
        # 4. Recurse into the next scope level
        #
        # The copy-on-descent pattern ensures that:
        # - Each scope level has its own view of visible parameters
        # - Sibling scopes don't interfere with each other's visibility
        # - Parameter shadowing works correctly (local overrides parent)
        # =====================================================================

        if len(inj_scope_parts) > 0:
            # Step 1: Get the next scope name from the path
            nxt_scope_name = inj_scope_parts.pop(0)

            if nxt_scope_name in self._children:
                nxt_scope = self._children[nxt_scope_name]

                # Step 2: Create a copy of the parameter table for this scope level
                # This implements parameter inheritance - all parent parameters
                # are visible at this level, plus any new parameters defined here
                # Using copy() ensures modifications don't affect parent scope's table
                nxt_param_table = param_table.copy()

                # Step 3: Process all parameter originations at this scope level
                # We iterate over a snapshot to allow safe modification during iteration
                origination_items = [(spn, spo) for spn, spo in nxt_scope.parameter_originations.items()]

                for scope_param_name, scope_param_origin in origination_items:
                    
                    if isinstance(scope_param_origin, ResourceOrigin):
                        # Step 3a: LATERAL CHECK - Validate source function dependencies
                        # Before adding this parameter to the visibility table, we must
                        # verify that its source function's dependencies are already
                        # visible at this scope level. This catches configuration errors
                        # where a parameter depends on something not yet defined.
                        self._resolve_resource_originations_for_injection_moment_lateral(inj_mom, scope_param_origin,
                            inj_scope_parts, nxt_param_table, missing_params)

                        # Step 3b: Add this parameter to the visibility table
                        # After validation, the parameter becomes visible to all
                        # subsequent parameters at this scope and all descendant scopes
                        # Note: This implements parameter shadowing - if a parent scope
                        # has a parameter with the same name, this one takes precedence
                        nxt_param_table[scope_param_name] = scope_param_origin
                    else:
                        # Debug output for unexpected origin types
                        # This shouldn't happen in normal operation
                        print("{}:{}".format(nxt_scope.package, scope_param_name))

                # Step 4: Recurse into the next scope level with the updated table
                nxt_scope._resolve_resource_originations_for_injection_moment_descend(inj_mom, inj_scope_parts, nxt_param_table, missing_params)
            else:
                # This shouldn't happen if ensure_injection_scopes_for_injection_moment
                # was called first - log a warning for debugging
                print("child not found '{}'".format(nxt_scope_name))
        return

    def _resolve_resource_originations_for_injection_moment_lateral(self, inj_mom: InjectionMoment, lateral_param_origin: ResourceOrigin,
        inj_scope_parts: List[str], scope_param_table: dict, missing_params: List[Any]):
        """
        Check if a parameter origin's source function dependencies are satisfied.

        This method performs a "lateral" check at the current scope level to
        verify that all parameters required by a source function are available
        in the current parameter visibility table.

        Algorithm
        ---------
        1. Get the source function's parameter signature
        2. For each parameter in the signature:
           a. Skip reserved parameter names (e.g., "constraints")
           b. Check if parameter exists in scope_param_table
           c. If not found, add to missing_params list

        Parameters
        ----------
        inj_mom : InjectionMoment
            The injection moment context (for error reporting).
        lateral_param_origin : ResourceOrigin
            The parameter origin whose source dependencies are being checked.
        inj_scope_parts : List[str]
            Remaining path components (for context).
        scope_param_table : dict
            Current parameter visibility table at this scope level.
        missing_params : List[Any]
            Accumulator for missing parameter dependencies.

        Notes
        -----
        - Reserved parameters like "constraints" are handled specially by the
          framework and don't need to be in the parameter table.
        - Missing parameters indicate configuration errors that should be
          reported to the user before test execution.
        """

        # =====================================================================
        # LATERAL DEPENDENCY CHECK
        # =====================================================================
        # This method performs a "lateral" check at the current scope level to
        # verify that all parameters required by a source function are already
        # available in the parameter visibility table.
        #
        # Why "lateral"?
        # - We're checking dependencies at the same scope level, not up/down
        # - A source function may depend on parameters defined earlier in the
        #   same scope or in ancestor scopes
        # - This ensures proper dependency ordering within a scope
        #
        # Example:
        #   @resource
        #   def auth_token(session_config):  # depends on session_config
        #       return create_token(session_config)
        #
        #   If auth_token is defined at tests.unit.test_auth scope, we check
        #   that session_config is visible (either from this scope or ancestors)
        # =====================================================================

        # Step 1: Get the source function's parameter signature
        # This tells us what parameters the source function needs to be called
        source_params = lateral_param_origin.source_signature.parameters

        if len(source_params) > 0:
            # Step 2: Check each required parameter against the visibility table
            for sparam_name, sparam_origin in source_params.items():
                # Step 3: Skip reserved parameter names
                # Reserved parameters like "constraints" are handled specially
                # by the framework and don't need to be in the parameter table
                # They are injected by the execution engine, not resolved from
                # the scope tree
                if sparam_name not in scope_param_table and sparam_name not in RESERVED_PARAMETER_NAMES:
                    # Step 4: Record missing parameter for error reporting
                    # The missing_params list accumulates all unresolved dependencies
                    # across the entire resolution process. These are reported to
                    # the user before test execution begins.
                    missing_params.append([sparam_name, sparam_origin])
        return

