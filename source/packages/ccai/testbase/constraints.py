"""
    .. module:: ccai.testbase.constraints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for constraints management with priority-based resolution.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

Constraints System
==================

The Constraints System provides a mechanism for passing configuration parameters
and feature requirements from external sources to test execution. It enables
defining constraint sets as dictionary-like objects, storing constraints from
multiple origins, and looking up constraints with priority-based resolution.

Constraint Hierarchy Patterns
-----------------------------

The constraints system follows a hierarchical pattern with two priority levels:

**Priority Levels (highest to lowest):**

1. **Override Parameters** (``ConstraintsOrigin.OVERRIDE_PARAMETER``):
   Runtime overrides that take precedence over all other constraints.
   Use these for temporary configuration changes during test execution.

2. **Site Parameters** (``ConstraintsOrigin.SITE_PARAMETER``):
   Default constraints from site configuration. These provide baseline
   configuration values that can be overridden at runtime.

**Scope Hierarchy:**

Constraints are organized by scope, following the test execution hierarchy::

    <session> (root)
    ├── package_a
    │   ├── module_1
    │   │   └── test_function_1
    │   └── module_2
    └── package_b
        └── module_3

Each scope can have its own constraints, identified by a unique key in the
format ``{scope}:{identifier}``. For example::

    tests.integration:db_config
    tests.unit#test_login:device_config

**Resolution Order:**

When looking up constraints, the system checks:

1. Override constraints table first (higher priority)
2. Site constraints table second (lower priority)
3. Returns ``None`` if not found in either table

Integration with Dependency Injection
-------------------------------------

The Constraints System integrates with the Dependency Injection System to
pass configuration parameters to resource factories:

**Registration Flow:**

1. Constraints are registered with the :class:`ConstraintsCatalog` using
   :meth:`ConstraintsCatalog.add_constraints`.
2. A constraint key is generated and stored with the ``ResourceOrigin``.
3. During resource instantiation, the injection system looks up constraints
   using the stored key.

**Usage in Source Functions:**

Source functions can receive constraints by declaring a ``constraints``
parameter::

    def create_database_connection(constraints: Constraints = None):
        host = constraints.get("host", "localhost") if constraints else "localhost"
        port = constraints.get("port", 5432) if constraints else 5432
        return DatabaseConnection(host=host, port=port)

**Constraint Passing:**

The injection system automatically:

1. Retrieves the ``constraints_key`` from the ``ResourceOrigin``
2. Looks up constraints via :meth:`ConstraintsCatalog.lookup_constraints`
3. Passes resolved constraints to source functions with a ``constraints`` parameter
4. Allows source functions to use default values when constraints are not provided

Best Practices for Constraint Organization
------------------------------------------

**1. Use Meaningful Identifiers:**

Choose descriptive identifiers that indicate the purpose of the constraints::

    # Good: Clear purpose
    catalog.add_constraints(
        origin=ConstraintsOrigin.SITE_PARAMETER,
        originating_scope="tests.integration",
        identifier="database_config",
        constraints=Constraints(host="localhost", port=5432)
    )

    # Avoid: Vague identifiers
    catalog.add_constraints(
        origin=ConstraintsOrigin.SITE_PARAMETER,
        originating_scope="tests.integration",
        identifier="config1",  # Not descriptive
        constraints=Constraints(host="localhost", port=5432)
    )

**2. Separate Concerns:**

Create separate constraint sets for different configuration aspects::

    # Database constraints
    db_constraints = Constraints(host="localhost", port=5432, timeout=30)

    # Feature constraints
    feature_constraints = FeatureConstraints(
        required_features=[DeviceFeatures.Bluetooth],
        checkout=True
    )

**3. Use Override Constraints Sparingly:**

Reserve override constraints for runtime configuration changes::

    # Site-level defaults (use for most configurations)
    catalog.add_constraints(
        origin=ConstraintsOrigin.SITE_PARAMETER,
        originating_scope="tests.integration",
        identifier="db_config",
        constraints=Constraints(timeout=30)
    )

    # Override only when needed (e.g., debugging, special test runs)
    catalog.add_constraints(
        origin=ConstraintsOrigin.OVERRIDE_PARAMETER,
        originating_scope="tests.integration",
        identifier="db_config",
        constraints=Constraints(timeout=120)  # Extended timeout for debugging
    )

**4. Merge Constraints for Composition:**

Use :func:`merge_constraints` to combine base configurations with
environment-specific or test-specific values::

    base_constraints = Constraints(timeout=30, retries=3)
    env_constraints = Constraints(host="test-server.local")
    test_constraints = Constraints(debug=True)

    combined = merge_constraints(base_constraints, env_constraints, test_constraints)
    # Result: {'timeout': 30, 'retries': 3, 'host': 'test-server.local', 'debug': True}

**5. Prune Constraints for Performance:**

For large test suites, prune constraints to relevant scopes before execution::

    # Keep only constraints needed for current test run
    catalog.prune_constraints([
        "tests.integration:db_config",
        "tests.integration:api_config"
    ])

**6. Use FeatureConstraints for Resource Filtering:**

When filtering resources based on capabilities, use :class:`FeatureConstraints`::

    device_constraints = FeatureConstraints(
        required_features=[DeviceFeatures.Bluetooth, DeviceFeatures.WiFi],
        excluded_features=[DeviceFeatures.Legacy],
        checkout=True  # Reserve the device during test
    )

**7. Document Constraint Dependencies:**

When constraints are required by source functions, document the expected keys::

    def create_api_client(constraints: Constraints = None):
        '''
        Create an API client with configuration from constraints.

        Expected constraint keys:
            - api_url (str): Base URL for the API
            - api_key (str): Authentication key
            - timeout (int, optional): Request timeout in seconds (default: 30)
        '''
        if constraints is None:
            constraints = Constraints()

        return APIClient(
            url=constraints.get("api_url", "http://localhost:8080"),
            key=constraints.get("api_key", ""),
            timeout=constraints.get("timeout", 30)
        )

Module Components
-----------------

- :class:`Constraints`: Dictionary wrapper for key-value constraint pairs
- :class:`ConstraintsOrigin`: Enumeration of constraint origin types
- :class:`ConstraintsCatalog`: Singleton registry for constraint management
- :class:`ConstraintsRef`: Reference object associating constraints with metadata
- :class:`FeatureConstraintKeys`: Standard keys for feature constraints
- :class:`FeatureConstraints`: Feature-based constraint definitions
- :func:`create_constraint_key`: Generate unique constraint keys
- :func:`merge_constraints`: Combine multiple constraint sets
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Union

from enum import Enum

from ccai.testbase.features import FeatureMask, FeatureTag


class ConstraintsOrigin(str, Enum):
    """
        Enumeration of the origins from which constraints may be provided.

        This enumeration inherits from both ``str`` and ``Enum`` to allow
        string comparison with enum values.

        :cvar SITE_PARAMETER: Represents constraints from site configuration
            (lower priority). String value: ``"site-parameter"``.
        :cvar OVERRIDE_PARAMETER: Represents runtime override constraints
            (higher priority). String value: ``"override-parameter"``.

        Example::

            >>> origin = ConstraintsOrigin.SITE_PARAMETER
            >>> origin == "site-parameter"
            True
            >>> origin == ConstraintsOrigin.SITE_PARAMETER
            True
    """

    SITE_PARAMETER = "site-parameter"
    OVERRIDE_PARAMETER = "override-parameter"


class Constraints(dict):
    """
        Dictionary wrapper representing a set of key-value constraint pairs.

        The :class:`Constraints` class inherits from Python's built-in ``dict``
        class and supports all standard dictionary operations. It provides a
        callable interface to create derived constraint sets with updated values.

        Example::

            >>> constraints = Constraints(timeout=30, retries=3)
            >>> constraints["timeout"]
            30
            >>> derived = constraints(timeout=60)
            >>> derived
            {'timeout': 60, 'retries': 3}
            >>> constraints["timeout"]  # Original unchanged
            30
    """

    def __init__(self, **kwargs):
        """
            Initialize a new Constraints object with keyword arguments.

            All keyword arguments are stored as dictionary key-value pairs.

            :param kwargs: Arbitrary keyword arguments to store as constraints.
            :type kwargs: Any

            Example::

                >>> constraints = Constraints(host="localhost", port=5432)
                >>> constraints
                {'host': 'localhost', 'port': 5432}
        """
        for key, value in kwargs.items():
            if not isinstance(value, (int, float, str, bool, list, dict, type(None))):
                raise TypeError(f"Constraint value for '{key}' must be a primitive type, not {type(value).__name__}")
        super().__init__(**kwargs)
        return

    def __call__(self, **kwargs: Any):
        """
            Create a new dictionary with original values updated by provided arguments.

            This method implements a prototype pattern, creating a copy of the
            current constraints with additional or overridden values. The original
            :class:`Constraints` object is not modified.

            :param kwargs: Keyword arguments to add or override in the copy.
            :type kwargs: Any

            :returns: A new dictionary containing merged key-value pairs.
            :rtype: dict

            Example::

                >>> base = Constraints(timeout=30, retries=3)
                >>> derived = base(timeout=60, debug=True)
                >>> derived
                {'timeout': 60, 'retries': 3, 'debug': True}
                >>> base  # Original unchanged
                {'timeout': 30, 'retries': 3}
        """
        for key, value in kwargs.items():
            if not isinstance(value, (int, float, str, bool, list, dict, type(None))):
                raise TypeError(f"Constraint value for '{key}' must be a primitive type, not {type(value).__name__}")
        inst = dict(self)
        inst.update(kwargs)
        return inst


class ConstraintsCatalog:
    """
        Singleton registry that manages all registered constraints and provides
        lookup functionality with priority-based resolution.

        The :class:`ConstraintsCatalog` stores constraints from multiple origins
        (site parameters and override parameters) and provides lookup with
        priority-based resolution where override constraints take precedence
        over site constraints.

        The catalog maintains two separate storage tables:

        - ``_site_constraints``: Lower priority constraints from site configuration
        - ``_override_constraints``: Higher priority runtime override constraints

        Example::

            >>> catalog = ConstraintsCatalog()
            >>> # Register site-level constraints
            >>> key = catalog.add_constraints(
            ...     origin=ConstraintsOrigin.SITE_PARAMETER,
            ...     originating_scope="tests.integration",
            ...     identifier="db_config",
            ...     constraints=Constraints(host="localhost", port=5432)
            ... )
            >>> # Register override constraints (higher priority)
            >>> catalog.add_constraints(
            ...     origin=ConstraintsOrigin.OVERRIDE_PARAMETER,
            ...     originating_scope="tests.integration",
            ...     identifier="db_config",
            ...     constraints=Constraints(port=5433)
            ... )
            >>> # Lookup returns override constraints when both exist
            >>> constraints = catalog.lookup_constraints(key)
            >>> constraints["port"]
            5433

        .. note::
            Multiple calls to ``ConstraintsCatalog()`` return the same instance
            due to the singleton pattern implementation.
    """

    _instance = None
    _initialized = False


    def __new__(cls):
        """
            Create or return the singleton instance of ConstraintsCatalog.

            This method implements the singleton pattern by checking if an
            instance already exists. If not, it creates one; otherwise, it
            returns the existing instance.

            :returns: The singleton ConstraintsCatalog instance.
            :rtype: ConstraintsCatalog

            Example::

                >>> catalog1 = ConstraintsCatalog()
                >>> catalog2 = ConstraintsCatalog()
                >>> catalog1 is catalog2
                True
        """
        if cls._instance is None:
            cls._instance = super(ConstraintsCatalog, cls).__new__(cls)

        return cls._instance


    def __init__(self):
        """
            Initialize the ConstraintsCatalog storage tables.

            This method initializes the internal storage dictionaries only
            on the first instantiation. Subsequent calls to ``__init__``
            (from repeated ``ConstraintsCatalog()`` calls) are no-ops due
            to the ``_initialized`` flag.

            The following storage tables are created:

            - ``_site_constraints``: Dictionary mapping constraint keys to
              :class:`ConstraintsRef` objects for site-level constraints.
            - ``_override_constraints``: Dictionary mapping constraint keys to
              :class:`ConstraintsRef` objects for override constraints.

            Example::

                >>> catalog = ConstraintsCatalog()
                >>> # Storage tables are initialized internally
                >>> # catalog._site_constraints = {}
                >>> # catalog._override_constraints = {}
        """
        thisType = type(self)

        if not thisType._initialized:
            thisType._initialized = True

            self._site_constraints: Dict[str, ConstraintsRef] = {}
            self._override_constraints: Dict[str, ConstraintsRef] = {}

        return


    def add_constraints(self, origin: ConstraintsOrigin, originating_scope: str, identifier: str, constraints: Union[Constraints, "FeatureConstraints", Dict[str, Any]]) -> str:
        """
            Register constraints with the catalog and return the generated key.

            This method stores the provided constraints in the appropriate
            storage table based on the origin parameter. A unique constraint
            key is generated from the scope and identifier.

            :param origin: The origin type for the constraints, determining
                which storage table to use.
            :type origin: ConstraintsOrigin
            :param originating_scope: The scope path to which the constraints
                apply (e.g., ``"tests.integration"``).
            :type originating_scope: str
            :param identifier: A unique identifier for this constraint set
                within the scope (e.g., ``"db_config"``).
            :type identifier: str
            :param constraints: The constraint set to store. Can be a
                :class:`Constraints`, :class:`FeatureConstraints`, or dict.
            :type constraints: Union[Constraints, FeatureConstraints, Dict[str, Any]]

            :returns: The generated constraint key in format
                ``"{originating_scope}:{identifier}"``.
            :rtype: str

            :raises ValueError: If the origin is not a recognized
                :class:`ConstraintsOrigin` value. The error message includes
                the origin, scope, and identifier for debugging.

            Example::

                >>> catalog = ConstraintsCatalog()
                >>> key = catalog.add_constraints(
                ...     origin=ConstraintsOrigin.SITE_PARAMETER,
                ...     originating_scope="tests.integration",
                ...     identifier="db_config",
                ...     constraints=Constraints(host="localhost", port=5432)
                ... )
                >>> key
                'tests.integration:db_config'

            Example with override constraints::

                >>> catalog.add_constraints(
                ...     origin=ConstraintsOrigin.OVERRIDE_PARAMETER,
                ...     originating_scope="tests.integration",
                ...     identifier="db_config",
                ...     constraints=Constraints(timeout=60)
                ... )
                'tests.integration:db_config'
        """
        ckey = create_constraint_key(originating_scope, identifier)

        cref = ConstraintsRef(origin, originating_scope, identifier, constraints)

        if origin == ConstraintsOrigin.SITE_PARAMETER:
            self._site_constraints[ckey] = cref
        elif origin == ConstraintsOrigin.OVERRIDE_PARAMETER:
            self._override_constraints[ckey] = cref
        else:
            raise ValueError(f"Unknown constraint origin='{origin}' scope='{originating_scope}' identifier={identifier}")
        
        return ckey
    

    def lookup_constraints(self, constraints_key: str) -> Union[Constraints, "FeatureConstraints", Dict[str, Any]]:
        """
            Look up constraints by key with priority-based resolution.

            This method implements priority-based constraint resolution:

            1. First checks the override constraints table (higher priority)
            2. Falls back to site constraints table (lower priority)
            3. Returns ``None`` if the key is not found in either table

            :param constraints_key: The constraint key to look up, in format
                ``"{scope}:{identifier}"``.
            :type constraints_key: str

            :returns: The resolved constraints object if found, or ``None``
                if the key does not exist in either storage table.
            :rtype: Union[Constraints, FeatureConstraints, Dict[str, Any], None]

            Example::

                >>> catalog = ConstraintsCatalog()
                >>> # Add site constraints
                >>> catalog.add_constraints(
                ...     origin=ConstraintsOrigin.SITE_PARAMETER,
                ...     originating_scope="tests.unit",
                ...     identifier="config",
                ...     constraints=Constraints(timeout=30)
                ... )
                >>> # Lookup returns site constraints
                >>> constraints = catalog.lookup_constraints("tests.unit:config")
                >>> constraints["timeout"]
                30

            Example with override priority::

                >>> # Add override constraints for same key
                >>> catalog.add_constraints(
                ...     origin=ConstraintsOrigin.OVERRIDE_PARAMETER,
                ...     originating_scope="tests.unit",
                ...     identifier="config",
                ...     constraints=Constraints(timeout=60)
                ... )
                >>> # Lookup now returns override constraints
                >>> constraints = catalog.lookup_constraints("tests.unit:config")
                >>> constraints["timeout"]
                60

            Example with non-existent key::

                >>> result = catalog.lookup_constraints("nonexistent:key")
                >>> result is None
                True
        """

        rtnval = None

        if constraints_key in self._override_constraints:
            cref = self._override_constraints[constraints_key]
            rtnval = cref.constraints
        elif constraints_key in self._site_constraints:
            cref = self._site_constraints[constraints_key]
            rtnval = cref.constraints
        
        return rtnval


    def prune_constraints(self, keep_keys: List[str]):
        """
            Remove constraints not in the specified scopes from both storage tables.

            This method optimizes memory usage and lookup performance by removing
            constraints that are not relevant to the current execution context.
            It modifies the catalog in place, affecting both site and override
            constraint tables.

            :param keep_keys: List of constraint keys to retain. Constraints with
                keys not matching these will be removed.
            :type keep_keys: List[str]

            :returns: None. The catalog is modified in place.
            :rtype: None

            Example::

                >>> catalog = ConstraintsCatalog()
                >>> # Add constraints for multiple scopes
                >>> catalog.add_constraints(
                ...     origin=ConstraintsOrigin.SITE_PARAMETER,
                ...     originating_scope="tests.integration",
                ...     identifier="config",
                ...     constraints=Constraints(timeout=30)
                ... )
                >>> catalog.add_constraints(
                ...     origin=ConstraintsOrigin.SITE_PARAMETER,
                ...     originating_scope="tests.unit",
                ...     identifier="config",
                ...     constraints=Constraints(timeout=10)
                ... )
                >>> # Prune to keep only integration tests
                >>> catalog.prune_constraints(["tests.integration:config"])
                >>> # Unit test constraints are now removed
                >>> catalog.lookup_constraints("tests.unit:config") is None
                True
                >>> # Integration test constraints are retained
                >>> catalog.lookup_constraints("tests.integration:config") is not None
                True

            .. note::
                The ``keep_keys`` parameter should contain full constraint keys
                (``"{scope}:{identifier}"`` format), not just scope names.
        """
        
        pruned_constraints = {}
        for key in keep_keys:
            if key in self._site_constraints:
                pruned_constraints[key] = self._site_constraints[key]

        self._site_constraints = pruned_constraints

        pruned_constraints = {}
        for key in keep_keys:
            if key in self._override_constraints:
                pruned_constraints[key] = self._override_constraints[key]

        self._override_constraints = pruned_constraints

        return


class ConstraintsRef:
    """
        Reference object that associates constraints with their origin metadata.

        The :class:`ConstraintsRef` class stores a reference to a constraints
        object along with metadata about its origin, scope, and identifier.
        This allows tracking where constraints came from and their applicable
        scope during constraint resolution.

        All stored values are exposed via read-only properties.

        :ivar _origin: The origin type of the constraints.
        :ivar _originating_scope: The scope to which constraints apply.
        :ivar _identifier: Unique identifier for the constraint set.
        :ivar _constraints: Reference to the actual constraints object.

        Example::

            >>> constraints = Constraints(timeout=30)
            >>> ref = ConstraintsRef(
            ...     origin=ConstraintsOrigin.SITE_PARAMETER,
            ...     originating_scope="tests.integration",
            ...     identifier="db_config",
            ...     constraints=constraints
            ... )
            >>> ref.origin
            <ConstraintsOrigin.SITE_PARAMETER: 'site-parameter'>
            >>> ref.originating_scope
            'tests.integration'
            >>> ref.identifier
            'db_config'
            >>> ref.constraints["timeout"]
            30
    """

    def __init__(self, origin: ConstraintsOrigin, originating_scope: str, identifier: str, constraints: Constraints):
        """
            Initialize a ConstraintsRef with origin metadata and constraints.

            :param origin: The origin type indicating where the constraints
                came from (site parameter or override parameter).
            :type origin: ConstraintsOrigin
            :param originating_scope: The scope path to which these constraints
                apply (e.g., ``"tests.integration"``).
            :type originating_scope: str
            :param identifier: A unique identifier for this constraint set
                within the scope.
            :type identifier: str
            :param constraints: The actual constraints object to reference.
            :type constraints: Union[Constraints, FeatureConstraints, Dict[str, Any]]

            Example::

                >>> ref = ConstraintsRef(
                ...     origin=ConstraintsOrigin.OVERRIDE_PARAMETER,
                ...     originating_scope="tests.unit",
                ...     identifier="config",
                ...     constraints=Constraints(debug=True)
                ... )
        """
        self._origin = origin
        self._originating_scope = originating_scope
        self._identifier = identifier
        self._constraints = constraints
        return

    @property
    def constraints(self) ->  Union[Constraints, "FeatureConstraints", Dict[str, Any]]:
        """
            The constraint object referenced by this instance.

            :returns: The stored :class:`Constraints`, :class:`FeatureConstraints`,
                or dict object.
            :rtype: Union[Constraints, FeatureConstraints, Dict[str, Any]]

            Example::

                >>> ref = ConstraintsRef(
                ...     ConstraintsOrigin.SITE_PARAMETER,
                ...     "scope", "id",
                ...     Constraints(key="value")
                ... )
                >>> ref.constraints
                {'key': 'value'}
        """
        return self._constraints
    
    @property
    def identifier(self) -> str:
        """
            The identifier for the constraint set.

            :returns: A unique identifier string for this constraint set
                within its scope.
            :rtype: str

            Example::

                >>> ref = ConstraintsRef(
                ...     ConstraintsOrigin.SITE_PARAMETER,
                ...     "tests.unit", "db_config",
                ...     Constraints()
                ... )
                >>> ref.identifier
                'db_config'
        """
        return self._identifier

    @property
    def origin(self) -> ConstraintsOrigin:
        """
            The origin that supplied the constraints.

            :returns: A :class:`ConstraintsOrigin` enumeration value indicating
                whether this is a site parameter or override parameter.
            :rtype: ConstraintsOrigin

            Example::

                >>> ref = ConstraintsRef(
                ...     ConstraintsOrigin.OVERRIDE_PARAMETER,
                ...     "scope", "id",
                ...     Constraints()
                ... )
                >>> ref.origin
                <ConstraintsOrigin.OVERRIDE_PARAMETER: 'override-parameter'>
                >>> ref.origin == "override-parameter"
                True
        """
        return self._origin

    @property
    def originating_scope(self) -> str:
        """
            The scope to which the constraints apply.

            :returns: The scope name string associated with these constraints.
            :rtype: str

            Example::

                >>> ref = ConstraintsRef(
                ...     ConstraintsOrigin.SITE_PARAMETER,
                ...     "tests.integration.api",
                ...     "config",
                ...     Constraints()
                ... )
                >>> ref.originating_scope
                'tests.integration.api'
        """
        return self._originating_scope


class FeatureConstraintKeys(str, Enum):
    """
        Enumeration of standard keys used when defining feature constraints.

        This enumeration inherits from both ``str`` and ``Enum`` to allow
        string comparison with enum values. These keys are used in
        :class:`FeatureConstraints` to specify required and excluded features.

        :cvar REQUIRED_FEATURES: Key for specifying features that must be
            present. String value: ``"required_features"``.
        :cvar EXCLUDED_FEATURES: Key for specifying features that must not
            be present. String value: ``"excluded_features"``.

        Example::

            >>> key = FeatureConstraintKeys.REQUIRED_FEATURES
            >>> key == "required_features"
            True
            >>> constraints = {
            ...     FeatureConstraintKeys.REQUIRED_FEATURES: ["bluetooth"],
            ...     FeatureConstraintKeys.EXCLUDED_FEATURES: ["legacy"]
            ... }
    """

    REQUIRED_FEATURES = "required_features"
    EXCLUDED_FEATURES = "excluded_features"


class FeatureConstraints(FeatureMask):
    """
        Specialized :class:`FeatureMask` subclass for feature-based constraints.

        The :class:`FeatureConstraints` class extends :class:`FeatureMask` to
        provide feature-based constraint definitions with an additional
        ``checkout`` capability. It supports specifying required and excluded
        features for resource filtering.

        Like :class:`Constraints`, this class provides a callable interface
        to create derived constraint sets with updated values.

        :ivar checkout: Whether to checkout/reserve the resource.

        Example::

            >>> from ccai.testbase.features import FeatureTag
            >>> # Define feature constraints
            >>> constraints = FeatureConstraints(
            ...     required_features=[FeatureTag("bluetooth")],
            ...     excluded_features=[FeatureTag("legacy")],
            ...     checkout=True
            ... )
            >>> # Create derived constraints
            >>> derived = constraints(timeout=30)
            >>> derived["checkout"]
            True
            >>> derived["timeout"]
            30
    """

    def __init__(self, *, required_features: List[FeatureTag]=None,
                       excluded_features: List[FeatureTag]=None,
                       checkout: bool=False, **kwargs):
        """
            Initialize a FeatureConstraints object with feature requirements.

            :param required_features: List of feature tags that must be present
                for a resource to match. Defaults to ``None`` (no requirements).
            :type required_features: List[FeatureTag], optional
            :param excluded_features: List of feature tags that must not be
                present for a resource to match. Defaults to ``None`` (no exclusions).
            :type excluded_features: List[FeatureTag], optional
            :param checkout: Whether to checkout/reserve the matching resource.
                Defaults to ``False``.
            :type checkout: bool, optional
            :param kwargs: Additional keyword arguments passed to the parent
                :class:`FeatureMask` class.

            Example::

                >>> constraints = FeatureConstraints(
                ...     required_features=[FeatureTag("wifi")],
                ...     checkout=True
                ... )

            Example with additional kwargs::

                >>> constraints = FeatureConstraints(
                ...     required_features=[FeatureTag("bluetooth")],
                ...     excluded_features=[FeatureTag("legacy")],
                ...     checkout=False,
                ...     custom_param="value"
                ... )
        """
        super().__init__(required_features=required_features,
                         excluded_features=excluded_features,
                         checkout=checkout, **kwargs)
        return

    def __call__(self, **kwargs: Any):
        """
            Create a new dictionary with original values updated by provided arguments.

            This method implements a prototype pattern, creating a copy of the
            current feature constraints with additional or overridden values.
            The original :class:`FeatureConstraints` object is not modified.

            :param kwargs: Keyword arguments to add or override in the copy.
            :type kwargs: Any

            :returns: A new dictionary containing merged key-value pairs.
            :rtype: dict

            Example::

                >>> base = FeatureConstraints(checkout=True)
                >>> derived = base(timeout=60, debug=True)
                >>> derived["checkout"]
                True
                >>> derived["timeout"]
                60
                >>> derived["debug"]
                True
                >>> # Original unchanged
                >>> "timeout" in base
                False
        """
        inst = dict(self)
        inst.update(kwargs)
        return inst


def create_constraint_key(source: str, identifier: str) -> str:
    """
        Generate a unique constraint key from source and identifier.

        This function creates a standardized key format used for both
        registration and lookup operations in the :class:`ConstraintsCatalog`.

        :param source: The originating scope path (e.g., ``"tests.integration"``).
        :type source: str
        :param identifier: A unique identifier for the constraint set within
            the scope (e.g., ``"db_config"``).
        :type identifier: str

        :returns: A constraint key in the format ``"{source}:{identifier}"``.
        :rtype: str

        Example::

            >>> key = create_constraint_key("tests.integration", "db_config")
            >>> key
            'tests.integration:db_config'

        Example with complex scope::

            >>> key = create_constraint_key(
            ...     "tests.integration#test_login",
            ...     "device_config"
            ... )
            >>> key
            'tests.integration#test_login:device_config'
    """
    return f"{source}:{identifier}"


def merge_constraints(*args: Union[Constraints, dict]) -> Constraints:
    """
        Merge multiple constraint sets into a single Constraints object.

        This function takes a variable number of :class:`Constraints` or dict
        objects and combines them into a new :class:`Constraints` object.
        When multiple constraints have the same key, the value from the last
        constraint in the argument list wins (last-wins semantics).

        The input constraint objects are not modified.

        :param args: Variable number of :class:`Constraints` or dict objects
            to merge.
        :type args: Union[Constraints, dict]

        :returns: A new :class:`Constraints` object containing all merged
            key-value pairs.
        :rtype: Constraints

        Example::

            >>> base = Constraints(timeout=30, retries=3)
            >>> override = Constraints(timeout=60)
            >>> merged = merge_constraints(base, override)
            >>> merged
            {'timeout': 60, 'retries': 3}
            >>> # Original unchanged
            >>> base["timeout"]
            30

        Example with multiple constraints::

            >>> env = Constraints(host="localhost", port=5432)
            >>> test = Constraints(port=5433, debug=True)
            >>> runtime = {"timeout": 60}
            >>> merged = merge_constraints(env, test, runtime)
            >>> merged
            {'host': 'localhost', 'port': 5433, 'debug': True, 'timeout': 60}

        Example with no arguments::

            >>> empty = merge_constraints()
            >>> empty
            {}
            >>> isinstance(empty, Constraints)
            True

        .. note::
            In cases where this method is provided with constraints with
            overlapping values, the last constraint with a given key
            overwrites earlier values.
    """

    combined: Constraints = Constraints()

    for av in args:
        combined.update(av)
    
    return combined

