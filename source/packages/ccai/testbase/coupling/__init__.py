"""
.. module:: ccai.testbase.coupling
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Package containing coupling classes for integrating external resources,
        configurations, and validators into the TestBase test execution framework.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>

The coupling package provides a mechanism for integrating external resources, configurations,
and validators into the TestBase test execution framework. It enables:

* Defining integration points with external systems (devices, services, databases)
* Managing configuration resources that provide test environment setup
* Creating validators that verify test outcomes
* Establishing lifecycle hooks for resource management
* Supporting hierarchical resource organization with precedence ordering

The package includes the following modules:

* :mod:`basecoupling` - Contains :class:`BaseCoupling`, the foundational base class
* :mod:`integrationcoupling` - Contains :class:`IntegrationCoupling` for external resources
* :mod:`configurationcoupling` - Contains :class:`ConfigurationCoupling` for configurations
* :mod:`validatorcoupling` - Contains :class:`ValidatorCoupling` for test validators

Coupling Hierarchy::

    BaseCoupling
    ├── IntegrationCoupling  (external resource integration)
    └── ConfigurationCoupling  (environment configuration)

    ValidatorCoupling  (test validation, separate hierarchy)


Coupling Lifecycle Patterns
===========================

The coupling system follows a well-defined lifecycle pattern that ensures resources are
properly initialized, connected, and cleaned up during test execution. Understanding
these patterns is essential for implementing robust coupling classes.

IntegrationCoupling Lifecycle
-----------------------------

Integration couplings follow a five-phase lifecycle executed in strict order:

1. **Registration Phase** (``attach_to_framework``)
   
   The first phase registers the coupling with the test framework. This allows the
   framework to track which couplings are required by the tests being executed and
   ignore couplings that are not needed.

   ::

       @classmethod
       def attach_to_framework(cls, **kwargs):
           # Register with framework for participation
           framework = kwargs.get('framework')
           framework.register_integration(cls)
           return

2. **Configuration Phase** (``attach_to_environment``)
   
   The second phase processes configuration information and validates that the
   coupling has a valid environment to operate in. This is where configuration
   files are loaded and validated.

   ::

       @classmethod
       def attach_to_environment(cls, **kwargs):
           config = kwargs.get('config')
           if config is None:
               raise AKitMissingConfigError("Configuration required")
           cls._config = config
           return

3. **Resource Acquisition Phase** (``collect_resources``)
   
   The third phase connects with resource management systems to acquire the
   resources needed for the automation run. This may involve reserving devices,
   allocating connections, or acquiring other shared resources.

   ::

       @classmethod
       def collect_resources(cls):
           resource_manager = get_resource_manager()
           cls._resources = resource_manager.acquire('my_resources')
           return

4. **Connectivity Phase** (``establish_connectivity``)
   
   The fourth phase establishes actual connections to compute or storage resources.
   This phase returns error information and connectivity reports.

   ::

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
                       errors.append(f"Failed to connect: {err}")
                   reports[device.id] = {'status': 'failed'}
           return (errors, reports)

5. **Presence Phase** (``establish_presence``)
   
   The fifth phase verifies that resources are not only connected but also
   available and ready for use. This may involve health checks or capability
   verification.

   ::

       @classmethod
       def establish_presence(cls):
           errors = []
           reports = {}
           for device in cls._devices:
               health = device.health_check()
               reports[device.id] = {'status': 'ready', 'health': health}
           return (errors, reports)

Diagnostic Collection
---------------------

Throughout test execution, the ``diagnostic`` method is called at checkpoints
(pre-run, post-run) to collect diagnostic information:

::

    @classmethod
    def diagnostic(cls, label, level, diag_folder):
        import json
        diag_data = {'label': label, 'status': cls.get_status()}
        diag_file = os.path.join(diag_folder, 'my_diag.json')
        with open(diag_file, 'w') as f:
            json.dump(diag_data, f)
        return

ConfigurationCoupling Lifecycle
-------------------------------

Configuration couplings have a simpler lifecycle with only the ``attach_to_environment``
method for customization. The base class provides a default implementation that does
nothing, allowing derived classes to override only when needed:

::

    class DatabaseConfig(ConfigurationCoupling):
        @classmethod
        def attach_to_environment(cls, constraints=None):
            # Load configuration
            config = load_database_config()
            # Apply constraints if provided
            if constraints is not None:
                config.update(constraints)
            # Validate and store
            cls._config = config
            return

ValidatorCoupling Lifecycle
---------------------------

Validator couplings have the simplest lifecycle, focused on test-level attachment
rather than framework-level resource management:

::

    class ResponseValidator(ValidatorCoupling):
        def attach_to_test(self, testscope, suffix):
            self._testscope = testscope
            self._suffix = suffix
            return


Integration with Dependency Injection
=====================================

The coupling system integrates tightly with the TestBase dependency injection system
to provide injectable resources to tests and other components.

Factory Registration
--------------------

Couplings are registered with the injection system using factory decorators from
the ``ccai.testbase.declaration.registrations`` module:

* ``@integration_factory()`` - Registers integration coupling factories
* ``@configuration_factory()`` - Registers configuration coupling factories
* ``@validator_factory()`` - Registers validator coupling factories

Integration Factory Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Integration factories must yield (not return) their coupling instances to support
cleanup operations:

::

    from typing import Generator
    import testbase

    @testbase.register.integration_factory()
    def create_device_integration() -> Generator[DeviceIntegration, None, None]:
        integration = DeviceIntegration()
        yield integration
        # Cleanup code runs when generator is closed
        integration.cleanup()

Configuration Factory Example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Configuration factories also use generators for lifecycle management:

::

    @testbase.register.configuration_factory()
    def create_database_config() -> Generator[DatabaseConfig, None, None]:
        config = DatabaseConfig()
        yield config
        # Cleanup on generator close

Validator Factory Example
^^^^^^^^^^^^^^^^^^^^^^^^^

Validator factories return instances directly (no generator required):

::

    @testbase.register.validator_factory()
    def create_response_validator() -> ResponseValidator:
        return ResponseValidator()

Source Objects
--------------

When a factory is registered, the injection system creates source objects that
wrap the factory function:

* ``IntegrationSource`` - Wraps integration factory functions
* ``ConfigurationSource`` - Wraps configuration factory functions
* ``ValidatorSource`` - Wraps validator factory functions

These source objects are stored in the ``InjectionRegistry`` and used to track
which couplings are referenced by tests.

Coupling Collection
-------------------

During test framework startup, the injection system walks the scope tree to
identify all couplings referenced by tests. This is done by the
``collect_integrations_and_configurations_for_injection_moment`` method:

::

    # The injection system identifies:
    # - Parameters whose resource types are IntegrationCoupling subclasses
    # - Parameters whose resource types are ConfigurationCoupling subclasses
    # These are added to referenced_integrations and referenced_configurations

This collection process ensures that only necessary couplings are initialized
during test execution, improving startup time and resource efficiency.

Injection into Tests
--------------------

Once registered, couplings can be injected into test functions by declaring
parameters with the coupling type:

::

    def test_device_operation(device: DeviceIntegration):
        # The DeviceIntegration instance is automatically injected
        device.perform_operation()
        return


Best Practices for Coupling Organization
========================================

Following these best practices ensures maintainable, scalable, and debuggable
coupling implementations.

Hierarchical Organization
-------------------------

Use the integration key hierarchy to organize couplings logically:

::

    # Good: Clear hierarchical organization
    class CiscoRouter(IntegrationCoupling):
        integration_root = "devices"      # Top-level category
        integration_section = "network"   # Subcategory
        integration_leaf = "router"       # Specific type
        integration_class = "CiscoRouter" # Implementation

    class JuniperSwitch(IntegrationCoupling):
        integration_root = "devices"
        integration_section = "network"
        integration_leaf = "switch"
        integration_class = "JuniperSwitch"

Precedence Management
---------------------

Use precedence values to control initialization order. Lower values initialize
first, so couplings that others depend on should have lower precedence:

::

    class DatabaseIntegration(IntegrationCoupling):
        @classmethod
        def declare_precedence(cls) -> int:
            return 10  # Initialize early (low value)

    class ServiceIntegration(IntegrationCoupling):
        @classmethod
        def declare_precedence(cls) -> int:
            return 50  # Initialize after database

    class UIIntegration(IntegrationCoupling):
        @classmethod
        def declare_precedence(cls) -> int:
            return 100  # Initialize last

Recommended precedence ranges:

* 1-25: Core infrastructure (databases, message queues)
* 26-50: Services and APIs
* 51-75: Devices and hardware
* 76-100: UI and presentation layer

Error Handling
--------------

Return detailed error information from lifecycle methods rather than raising
exceptions immediately. This allows the framework to collect all errors and
present them together:

::

    @classmethod
    def establish_connectivity(cls, allow_missing_devices=False):
        errors = []
        reports = {}
        
        for device in cls._devices:
            try:
                connection = device.connect()
                reports[device.id] = {'status': 'connected'}
            except ConnectionError as err:
                # Collect error instead of raising
                if not allow_missing_devices:
                    errors.append(f"Device {device.id}: {err}")
                reports[device.id] = {'status': 'failed', 'error': str(err)}
        
        return (errors, reports)

Configuration Validation
------------------------

Use ``validate_item_configuration`` to detect configuration problems early:

::

    @classmethod
    def validate_item_configuration(cls, item_info):
        errors = []
        warnings = []
        
        # Check required fields
        if 'host' not in item_info:
            errors.append("Missing required 'host' configuration")
        
        # Check optional fields with warnings
        if 'timeout' not in item_info:
            warnings.append("No 'timeout' specified, using default of 30s")
        
        # Validate field values
        if 'port' in item_info:
            port = item_info['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append(f"Invalid port value: {port}")
        
        return (errors, warnings)

Diagnostic Collection
---------------------

Implement comprehensive diagnostics to aid troubleshooting:

::

    @classmethod
    def diagnostic(cls, label, level, diag_folder):
        import json
        import os
        
        # Collect diagnostic data based on level
        diag_data = {
            'label': label,
            'level': level,
            'integration_key': cls.get_integration_key(),
            'activated': cls.integration_activated
        }
        
        # Add more detail at higher levels
        if level >= 2:
            diag_data['config'] = cls._config
        if level >= 3:
            diag_data['connection_details'] = cls._get_connection_details()
        
        # Write to diagnostic folder
        filename = f"{cls.integration_class}_diag.json"
        diag_file = os.path.join(diag_folder, filename)
        with open(diag_file, 'w') as f:
            json.dump(diag_data, f, indent=2)
        return

State Tracking
--------------

Use the built-in state tracking properties to manage coupling state:

::

    class MyIntegration(IntegrationCoupling):
        
        @classmethod
        def establish_connectivity(cls, allow_missing_devices=False):
            errors, reports = super().establish_connectivity(allow_missing_devices)
            
            # Check state before proceeding
            instance = cls()
            if not instance.connectivity_establish:
                # Handle connectivity not established
                pass
            
            return (errors, reports)

Logging
-------

Use the inherited logger for consistent logging across all couplings:

::

    class MyIntegration(IntegrationCoupling):
        
        @classmethod
        def attach_to_framework(cls, **kwargs):
            cls.logger.info(f"Registering {cls.integration_class} with framework")
            # Registration logic
            return
        
        @classmethod
        def establish_connectivity(cls, allow_missing_devices=False):
            cls.logger.debug(f"Establishing connectivity for {cls.integration_class}")
            errors = []
            reports = {}
            # Connection logic
            if errors:
                cls.logger.warning(f"Connectivity errors: {errors}")
            return (errors, reports)


Example Usage
=============

Complete Integration Coupling Example
-------------------------------------

::

    from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling

    class DeviceIntegration(IntegrationCoupling):
        integration_root = "devices"
        integration_section = "network"
        integration_leaf = "router"
        integration_class = "DeviceIntegration"

        @classmethod
        def declare_precedence(cls) -> int:
            return 100

        @classmethod
        def attach_to_framework(cls, **kwargs):
            cls.logger.info("Attaching DeviceIntegration to framework")
            return

        @classmethod
        def attach_to_environment(cls, **kwargs):
            cls._config = kwargs.get('config', {})
            return

        @classmethod
        def collect_resources(cls):
            cls._devices = []  # Acquire from resource manager
            return

        @classmethod
        def establish_connectivity(cls, allow_missing_devices=False):
            return ([], {})

        @classmethod
        def establish_presence(cls):
            return ([], {})

        @classmethod
        def diagnostic(cls, label, level, diag_folder):
            return

        @classmethod
        def validate_item_configuration(cls, item_info):
            return ([], [])

Complete Configuration Coupling Example
---------------------------------------

::

    from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling

    class TestConfig(ConfigurationCoupling):
        @classmethod
        def attach_to_environment(cls, constraints=None):
            # Load and validate configuration
            cls._config = {}
            if constraints is not None:
                cls._config.update(constraints)
            return

Complete Validator Coupling Example
-----------------------------------

::

    from ccai.testbase.coupling.validatorcoupling import ValidatorCoupling

    class ResponseValidator(ValidatorCoupling):
        def __init__(self):
            self._testscope = None
            self._suffix = None
            return

        def attach_to_test(self, testscope, suffix):
            self._testscope = testscope
            self._suffix = suffix
            return

        def validate_status(self, expected_status):
            # Validation logic
            return

"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


