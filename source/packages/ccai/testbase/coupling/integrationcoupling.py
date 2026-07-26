"""
.. module:: ccai.testbase.coupling.integrationcoupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the :class:`IntegrationCoupling` class and associated reflection
        methods for integrating external automation resources into the test environment.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The IntegrationCoupling module provides the primary mechanism for integrating external automation
resources into the TestBase test execution framework. It defines a structured lifecycle for
resource discovery, connectivity establishment, and diagnostic collection.

The module includes:

* :class:`IntegrationCoupling` - Base class for external resource integration
* :func:`is_integration_coupling` - Helper to detect IntegrationCoupling subclasses
* :func:`sort_integration_couplings_by_precedence` - Orders couplings by precedence value

Example usage::

    from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling

    class DeviceIntegration(IntegrationCoupling):
        '''
            Integration coupling for device automation.
        '''

        integration_root = "devices"
        integration_section = "network"
        integration_leaf = "router"
        integration_class = "DeviceIntegration"

        @classmethod
        def declare_precedence(cls) -> int:
            return 100

        # ... implement other abstract methods

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, Tuple, TypeVar

import inspect

from ccai.testbase.coupling.basecoupling import BaseCoupling
from ccai.errors.exceptions import AbstractMethodError


class IntegrationCoupling(BaseCoupling):
    """
        The :class:`IntegrationCoupling` class serves as the base class for declaring automation
        integration requirements. It provides a structured lifecycle for integrating external
        resources such as devices, services, and databases into the test environment.

        The test sequencer queries the class hierarchies of tests included in an automation run
        to identify required integration couplings. Each coupling type is uniquely identified by
        its integration key, which follows a hierarchical naming scheme.

        Integration Key Format::

            {integration_root}:{integration_section}:{integration_leaf}:{integration_class}

        Lifecycle Methods (in order of execution):

        1. :meth:`attach_to_framework` - Register with test framework
        2. :meth:`attach_to_environment` - Process configuration and validate environment
        3. :meth:`collect_resources` - Acquire resources from resource management system
        4. :meth:`establish_connectivity` - Establish connections to compute/storage resources
        5. :meth:`establish_presence` - Verify resource availability and readiness
        6. :meth:`diagnostic` - Generate diagnostic information at checkpoints

        :cvar integration_root: Top-level category for the integration (e.g., "devices")
        :cvar integration_section: Subcategory for the integration (e.g., "network")
        :cvar integration_leaf: Specific type within the section (e.g., "router")
        :cvar integration_class: Implementation class name (e.g., "CiscoRouter")
        :cvar integration_activated: Class-level flag indicating if the integration is activated

        :ivar _connectivity_establish: Internal flag tracking connectivity establishment status
        :ivar _presence_establish: Internal flag tracking presence establishment status

        Example usage::

            from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling

            class DatabaseIntegration(IntegrationCoupling):
                '''
                    Integration coupling for database resources.
                '''

                integration_root = "services"
                integration_section = "database"
                integration_leaf = "postgresql"
                integration_class = "DatabaseIntegration"

                @classmethod
                def attach_to_framework(cls, **kwargs):
                    # Register with framework
                    return

                @classmethod
                def attach_to_environment(cls, **kwargs):
                    # Validate database configuration
                    return

                @classmethod
                def collect_resources(cls):
                    # Acquire database connection pool
                    return

                @classmethod
                def declare_precedence(cls) -> int:
                    return 50  # Lower values initialize first

                @classmethod
                def establish_connectivity(cls, allow_missing_devices=False):
                    errors = []
                    reports = {}
                    # Establish database connections
                    return (errors, reports)

                @classmethod
                def establish_presence(cls):
                    errors = []
                    reports = {}
                    # Verify database is accessible
                    return (errors, reports)

                @classmethod
                def diagnostic(cls, label, level, diag_folder):
                    # Generate database diagnostic information
                    return

                @classmethod
                def validate_item_configuration(cls, item_info):
                    errors = []
                    warnings = []
                    # Validate configuration items
                    return (errors, warnings)

        .. seealso::
            :class:`BaseCoupling` for the base coupling type
            :class:`ConfigurationCoupling` for environment configuration
            :func:`is_integration_coupling` for type detection
            :func:`sort_integration_couplings_by_precedence` for ordering couplings
    """

    integration_root: str = None
    integration_section: str = None
    integration_leaf: str = None
    integration_class: str = None

    integration_activated: bool = False

    def __init__(self, *args, **kwargs): # pylint: disable=unused-argument
        """
            Initializes a new :class:`IntegrationCoupling` instance.

            The constructor initializes the internal state tracking flags for connectivity
            and presence establishment to False. These flags are updated during the
            lifecycle method execution.

            :param args: Variable positional arguments (unused, for compatibility).
            :param kwargs: Variable keyword arguments (unused, for compatibility).

            Example usage::

                integration = MyIntegrationCoupling()
                print(integration.connectivity_establish)  # False
                print(integration.presence_establish)  # False
        """
        super().__init__()

        self._connectivity_establish = False
        self._presence_establish = False

        return

    @property
    def connectivity_establish(self) -> bool:
        """
            Read-only property indicating whether connectivity has been established.

            This property returns the current state of the connectivity establishment
            flag. The flag is set to True after the :meth:`establish_connectivity`
            method successfully completes.

            :returns: True if connectivity has been established, False otherwise.

            Example usage::

                integration = MyIntegrationCoupling()
                if not integration.connectivity_establish:
                    # Connectivity not yet established
                    pass
        """
        return self._connectivity_establish

    @property
    def presence_establish(self) -> bool:
        """
            Read-only property indicating whether presence has been established.

            This property returns the current state of the presence establishment
            flag. The flag is set to True after the :meth:`establish_presence`
            method successfully completes.

            :returns: True if presence has been established, False otherwise.

            Example usage::

                integration = MyIntegrationCoupling()
                if not integration.presence_establish:
                    # Presence not yet established
                    pass
        """
        return self._presence_establish

    @classmethod
    def attach_to_framework(cls, **kwargs):
        """
            Registers the integration coupling with the test framework for participation.

            This is the first lifecycle method called during integration initialization.
            It allows the coupling to register with the test framework and participate
            in registration processes. This enables the framework to ignore couplings
            that are not being included by any test.

            The DEFAULT implementation is a no-op. Framework attachment is an
            OPTIONAL phase: most couplings do their real work in
            ``attach_to_environment``, and the near-standalone testbase framework
            has no framework-level state a coupling must attach to. Integration
            tiers that do (e.g. the landscape-backed coupling hierarchy) override
            this hook in their own coupling base classes.

            :param kwargs: Variable keyword arguments for framework-specific
                registration parameters, forwarded by the sequencer.

            :returns: None. This method does not return a value.
        """
        return

    @classmethod
    def attach_to_environment(cls, **kwargs):
        """
            Processes configuration information and validates the test environment.

            This lifecycle method is called after :meth:`attach_to_framework` to allow
            the coupling to process configuration information and verify that it has
            a valid environment and configuration to run in.

            :param kwargs: Variable keyword arguments for environment-specific configuration
                parameters. The specific parameters accepted depend on the derived class
                implementation.

            :returns: None. This method does not return a value.

            :raises ccai.errors.exceptions.AKitMissingConfigError: When required
                configuration is missing.
            :raises ccai.errors.exceptions.ConfigurationError: When configuration
                validation fails.
            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def attach_to_environment(cls, **kwargs):
                        config = kwargs.get('config')
                        if config is None:
                            raise AKitMissingConfigError("Configuration required")
                        # Validate configuration
                        return

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        errmsg = "The 'attach_to_environment' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def collect_resources(cls):
        """
            Connects with a resource management system to acquire required resources.

            This lifecycle method is called after :meth:`attach_to_environment` to allow
            the coupling to connect with a resource management system and gain access
            to the resources required for the automation run.

            :returns: None. This method does not return a value.

            :raises ccai.errors.exceptions.AKitResourceError: When resource acquisition
                fails.
            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def collect_resources(cls):
                        # Acquire resources from resource manager
                        resource_manager = get_resource_manager()
                        cls._resources = resource_manager.acquire('my_resources')
                        return

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        errmsg = "The 'collect_resources' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def declare_precedence(cls) -> int:
        """
            Declares the ordinal precedence value for integration initialization order.

            This method returns an integer precedence value that determines the order
            in which integration couplings are initialized. Lower values are initialized
            first, allowing couplings with dependencies to be initialized after their
            dependencies.

            :returns: An integer precedence value. Lower values indicate higher priority
                (initialized first).

            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class DatabaseIntegration(IntegrationCoupling):
                    '''
                        Database integration with low precedence (initialized early).
                    '''

                    @classmethod
                    def declare_precedence(cls) -> int:
                        return 10  # Initialize early

                class ServiceIntegration(IntegrationCoupling):
                    '''
                        Service integration that depends on database.
                    '''

                    @classmethod
                    def declare_precedence(cls) -> int:
                        return 100  # Initialize after database

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.

            .. seealso::
                :func:`sort_integration_couplings_by_precedence` for ordering couplings
        """
        errmsg = "The 'declare_precedence' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def diagnostic(cls, label: str, level: int, diag_folder: str): # pylint: disable=unused-argument
        """
            Generates diagnostic information at specified checkpoints during test execution.

            This method is called by the sequencer when building a diagnostic package at
            diagnostic points in the automation sequence. Each diagnostic package has its
            own storage location, so derived classes can write diagnostic information to
            their specified output folder.

            Common diagnostic points include:

            * ``pre-run`` - Before test execution begins
            * ``post-run`` - After test execution completes

            :param label: A string identifying the diagnostic point (e.g., "pre-run", "post-run").
            :param level: An integer specifying the maximum diagnostic level to run diagnostics
                for. Higher levels may include more detailed diagnostic information.
            :param diag_folder: The output folder path where diagnostic information should be
                written. Each coupling should write its diagnostics to this folder.

            :returns: None. This method does not return a value.

            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def diagnostic(cls, label, level, diag_folder):
                        import os
                        import json

                        # Collect diagnostic data
                        diag_data = {
                            'label': label,
                            'level': level,
                            'status': cls.get_status()
                        }

                        # Write to diagnostic folder
                        diag_file = os.path.join(diag_folder, 'my_integration_diag.json')
                        with open(diag_file, 'w') as f:
                            json.dump(diag_data, f, indent=2)
                        return

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        # ============================================================================
        # DIAGNOSTIC FOLDER STRUCTURE - INTEGRATION IMPLEMENTATION GUIDE
        # ============================================================================
        # When implementing this method in a derived class, follow these guidelines
        # for creating the diagnostic folder structure:
        #
        # 1. CREATE INTEGRATION-SPECIFIC SUBFOLDER:
        #    Each integration should create its own subfolder within diag_folder:
        #
        #        integration_diag_folder = os.path.join(diag_folder, "my_integration")
        #        os.makedirs(integration_diag_folder, exist_ok=True)
        #
        # 2. RESPECT DIAGNOSTIC LEVEL:
        #    Use the level parameter to control verbosity:
        #    - Level 1-3: Basic diagnostics (quick status, minimal files)
        #    - Level 4-6: Standard diagnostics (logs, configuration)
        #    - Level 7-9: Detailed diagnostics (full dumps, traces)
        #
        # 3. HANDLE ERRORS INTERNALLY:
        #    Catch and handle errors within the diagnostic method to prevent
        #    propagation to the test framework. Log errors but don't raise.
        #
        # 4. RESULTING FOLDER STRUCTURE:
        #    <test_results_dir>/diagnostics/<label>/
        #    └── <integration_name>/           <- Created by this method
        #        ├── status.json               <- Basic diagnostic file
        #        ├── logs.txt                  <- Standard diagnostic file
        #        └── full_dump.json            <- Detailed diagnostic file
        #
        # Example implementation:
        #
        #     @classmethod
        #     def diagnostic(cls, label, level, diag_folder):
        #         import os
        #         import json
        #
        #         # Create integration-specific subfolder
        #         my_diag_folder = os.path.join(diag_folder, "myservice")
        #         os.makedirs(my_diag_folder, exist_ok=True)
        #
        #         # Level 1+: Basic status
        #         if level >= 1:
        #             status = cls._get_status()
        #             with open(os.path.join(my_diag_folder, "status.json"), 'w') as f:
        #                 json.dump(status, f, indent=2)
        #
        #         # Level 5+: Logs
        #         if level >= 5:
        #             logs = cls._get_logs()
        #             with open(os.path.join(my_diag_folder, "logs.txt"), 'w') as f:
        #                 f.write(logs)
        #
        #         # Level 9: Full dump
        #         if level >= 9:
        #             dump = cls._get_full_dump()
        #             with open(os.path.join(my_diag_folder, "full_dump.json"), 'w') as f:
        #                 json.dump(dump, f, indent=2)
        # ============================================================================
        errmsg = "The 'diagnostic' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def establish_connectivity(cls, allow_missing_devices: bool=False) -> Tuple[List[str], Dict]:
        """
            Establishes connections to compute or storage resources.

            This lifecycle method is called after :meth:`collect_resources` to establish
            actual connections to the resources. It handles connection setup and reports
            any errors or connectivity status.

            :param allow_missing_devices: A boolean indicating whether missing devices should
                be allowed without raising errors. When True, missing devices are reported
                but do not cause failures. When False (default), missing devices result in
                error messages.

            :returns: A tuple containing:

                * ``errors`` (List[str]): A list of error messages for failed connections.
                  Empty list if all connections succeeded.
                * ``reports`` (Dict): A dictionary of connectivity reports for devices,
                  keyed by device identifier. The structure of reports depends on the
                  derived class implementation.

            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def establish_connectivity(cls, allow_missing_devices=False):
                        errors = []
                        reports = {}

                        for device in cls._devices:
                            try:
                                connection = device.connect()
                                reports[device.id] = {'status': 'connected'}
                            except ConnectionError as err:
                                if not allow_missing_devices:
                                    errors.append(f"Failed to connect to {device.id}: {err}")
                                reports[device.id] = {'status': 'failed', 'error': str(err)}

                        return (errors, reports)

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        errmsg = "The 'establish_connectivity' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def establish_presence(cls) -> Tuple[List[str], Dict]:
        """
            Verifies resource availability and readiness after connectivity is established.

            This lifecycle method is called after :meth:`establish_connectivity` to verify
            that resources are not only connected but also available and ready for use.
            This may involve health checks, capability verification, or other readiness
            assessments.

            :returns: A tuple containing:

                * ``errors`` (List[str]): A list of error messages for resources that
                  failed presence verification. Empty list if all resources are ready.
                * ``reports`` (Dict): A dictionary of presence reports for resources,
                  keyed by resource identifier. The structure of reports depends on the
                  derived class implementation.

            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def establish_presence(cls):
                        errors = []
                        reports = {}

                        for device in cls._devices:
                            try:
                                health = device.health_check()
                                reports[device.id] = {'status': 'ready', 'health': health}
                            except Exception as err:
                                errors.append(f"Device {device.id} not ready: {err}")
                                reports[device.id] = {'status': 'not_ready', 'error': str(err)}

                        return (errors, reports)

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        errmsg = "The 'establish_presence' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)

    @classmethod
    def get_integration_key(cls) -> str:
        """
            Returns the unique hierarchical identifier string for this integration coupling.

            The integration key uniquely identifies an integration coupling type using a
            hierarchical naming scheme with four components separated by colons.

            Key Format::

                {integration_root}:{integration_section}:{integration_leaf}:{integration_class}

            :returns: A string containing the integration key in the format
                ``root:section:leaf:class``. If any component is None, the string "None"
                is included in that position.

            Example usage::

                class DeviceIntegration(IntegrationCoupling):
                    integration_root = "devices"
                    integration_section = "network"
                    integration_leaf = "router"
                    integration_class = "DeviceIntegration"

                key = DeviceIntegration.get_integration_key()
                # Returns: "devices:network:router:DeviceIntegration"

            .. seealso::
                :meth:`get_integration_key_parts` for getting key components as a tuple
        """
        rtnval = f"{cls.integration_root}:{cls.integration_section}:{cls.integration_leaf}:{cls.integration_class}"
        return rtnval
    
    @classmethod
    def get_integration_key_parts(cls) -> Tuple[str, str, str, str]:
        """
            Returns the integration key components as a tuple.

            This method provides access to the individual components of the integration
            key without string parsing. Useful when you need to work with specific
            parts of the key hierarchy.

            :returns: A tuple containing four elements:

                * ``integration_root`` (str): Top-level category
                * ``integration_section`` (str): Subcategory
                * ``integration_leaf`` (str): Specific type
                * ``integration_class`` (str): Implementation class name

            Example usage::

                class DeviceIntegration(IntegrationCoupling):
                    integration_root = "devices"
                    integration_section = "network"
                    integration_leaf = "router"
                    integration_class = "DeviceIntegration"

                root, section, leaf, cls_name = DeviceIntegration.get_integration_key_parts()
                # root = "devices"
                # section = "network"
                # leaf = "router"
                # cls_name = "DeviceIntegration"

            .. seealso::
                :meth:`get_integration_key` for getting the key as a formatted string
        """
        rtnval = (cls.integration_root, cls.integration_section, cls.integration_leaf, cls.integration_class)
        return rtnval

    @classmethod
    def validate_item_configuration(cls, item_info: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """
            Validates configuration items for this integration coupling.

            This method is called to validate configuration items before test execution.
            It checks the provided configuration dictionary for errors and warnings,
            allowing early detection of configuration problems.

            :param item_info: A dictionary containing configuration item information to
                validate. The expected structure and keys depend on the derived class
                implementation.

            :returns: A tuple containing:

                * ``errors`` (List[str]): A list of critical configuration error messages.
                  These indicate problems that will prevent the integration from functioning.
                * ``warnings`` (List[str]): A list of non-critical warning messages.
                  These indicate potential issues that may not prevent operation but
                  should be addressed.

            :raises ccai.errors.exceptions.AbstractMethodError: When called on the base
                :class:`IntegrationCoupling` class without being overloaded by a derived class.

            Example usage::

                class MyIntegration(IntegrationCoupling):
                    '''
                        Custom integration implementation.
                    '''

                    @classmethod
                    def validate_item_configuration(cls, item_info):
                        errors = []
                        warnings = []

                        # Check required fields
                        if 'host' not in item_info:
                            errors.append("Missing required 'host' configuration")

                        # Check optional fields
                        if 'timeout' not in item_info:
                            warnings.append("No 'timeout' specified, using default")

                        # Validate values
                        if 'port' in item_info:
                            port = item_info['port']
                            if not isinstance(port, int) or port < 1 or port > 65535:
                                errors.append(f"Invalid port value: {port}")

                        return (errors, warnings)

            .. note::
                This method must be overloaded by derived classes. Calling this method on
                the base :class:`IntegrationCoupling` class will raise an
                :class:`AbstractMethodError`.
        """
        errmsg = "The 'validate_item_configuration' method must be overloaded by derived integration coupling types."
        raise AbstractMethodError(errmsg)


IntegrationCouplingType = TypeVar('IntegrationCouplingType', bound=IntegrationCoupling)


def is_integration_coupling(cls) -> bool:
    """
        Determines if a type is an :class:`IntegrationCoupling` subclass.

        This helper function is used to detect whether a given class is a valid
        :class:`IntegrationCoupling` subclass (but not the base class itself).
        It is useful for filtering and processing integration couplings during
        dependency injection and test execution.

        :param cls: The class to check. Can be any type.

        :returns: True if the class is a subclass of :class:`IntegrationCoupling` but not
            the :class:`IntegrationCoupling` base class itself. False otherwise.

        Example usage::

            from ccai.testbase.coupling.integrationcoupling import (
                IntegrationCoupling,
                is_integration_coupling
            )

            class MyIntegration(IntegrationCoupling):
                pass

            # Check various types
            is_integration_coupling(MyIntegration)      # True - valid subclass
            is_integration_coupling(IntegrationCoupling)  # False - base class
            is_integration_coupling(str)                # False - not a coupling
            is_integration_coupling("not a class")      # False - not a class

        .. note::
            This function returns False for the :class:`IntegrationCoupling` base class
            itself, as the base class should not be used directly for integration.
    """
    is_integmi = False
    if inspect.isclass(cls) and cls is not IntegrationCoupling and issubclass(cls, IntegrationCoupling):
        is_integmi = True
    return is_integmi


def sort_integration_couplings_by_precedence(coupling_list: List[IntegrationCoupling]) -> List[IntegrationCoupling]:
    """
        Orders integration couplings by their declared precedence values.

        This function takes a list of :class:`IntegrationCoupling` classes and returns
        a new list ordered by the precedence values declared by each coupling. Couplings
        with lower precedence values appear first in the returned list.

        Couplings with the same precedence value are grouped together in the output,
        maintaining their relative order within the group.

        :param coupling_list: A list of :class:`IntegrationCoupling` classes to sort.
            Each class must implement the :meth:`declare_precedence` method.

        :returns: A new list containing the same couplings ordered by precedence value
            from lowest (first) to highest (last).

        Example usage::

            from ccai.testbase.coupling.integrationcoupling import (
                IntegrationCoupling,
                sort_integration_couplings_by_precedence
            )

            class DatabaseIntegration(IntegrationCoupling):
                @classmethod
                def declare_precedence(cls) -> int:
                    return 10

            class ServiceIntegration(IntegrationCoupling):
                @classmethod
                def declare_precedence(cls) -> int:
                    return 50

            class UIIntegration(IntegrationCoupling):
                @classmethod
                def declare_precedence(cls) -> int:
                    return 100

            couplings = [UIIntegration, DatabaseIntegration, ServiceIntegration]
            ordered = sort_integration_couplings_by_precedence(None, couplings)
            # ordered = [DatabaseIntegration, ServiceIntegration, UIIntegration]

        .. note::
            This function has an incorrect signature with an unused ``self`` parameter.
            When calling this function, pass ``None`` as the first argument.

        .. seealso::
            :meth:`IntegrationCoupling.declare_precedence` for declaring precedence values
    """
    precedence_table = {}

    for coupling in coupling_list:
        precedence = coupling.declare_precedence()
        precedence_level_list = None
        if precedence in precedence_table:
            precedence_level_list = precedence_table[precedence]
        else:
            precedence_level_list = []
            precedence_table[precedence] = precedence_level_list
        precedence_level_list.append(coupling)

    precedence_keys_sorted = sorted(precedence_table.keys())

    ordered_couplings = []
    for precedence in precedence_keys_sorted:
        ordered_couplings.extend(precedence_table[precedence])

    return ordered_couplings