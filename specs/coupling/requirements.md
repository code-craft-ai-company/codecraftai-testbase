# Coupling System - Requirements Document

## Introduction

The Coupling System provides a mechanism for integrating external resources, configurations, and validators into the TestBase test execution framework. It enables defining integration points with external systems (devices, services, databases), managing configuration resources that provide test environment setup, creating validators that verify test outcomes, establishing lifecycle hooks for resource management, and supporting hierarchical resource organization with precedence ordering. The system works in conjunction with the Dependency Injection System to provide injectable resources and with the Test Execution Engine to manage resource lifecycles during test runs.

## Glossary

- **BaseCoupling**: The foundational abstract base class for all coupling-based resources, providing common infrastructure including logging capabilities
- **IntegrationCoupling**: A coupling type for integrating external automation resources into the test environment with a structured lifecycle for resource discovery, connectivity, and diagnostics
- **ConfigurationCoupling**: A coupling type for declaring configuration specifications that must be satisfied for a test environment to function
- **ValidatorCoupling**: A coupling type for validator objects that verify test outcomes and attach to test scopes
- **Integration_Key**: A hierarchical identifier string in the format `{root}:{section}:{leaf}:{class}` used to uniquely identify integration couplings
- **Precedence**: An integer value declared by integration couplings that determines the order in which couplings are initialized (lower values initialize first)
- **IntegrationSource**: A wrapper object that associates an integration factory function with its resource type and constraints
- **ConfigurationSource**: A wrapper object that associates a configuration factory function with its resource type and constraints
- **ValidatorSource**: A wrapper object that associates a validator factory function with its resource type and constraints
- **Lifecycle_Phase**: A stage in the coupling initialization process (attach_to_framework, attach_to_environment, collect_resources, establish_connectivity, establish_presence)
- **Diagnostic_Point**: A checkpoint during test execution where couplings generate diagnostic information (pre-run, post-run)

## Requirements

### Requirement 1: Base Coupling Foundation

**User Story:** As a framework developer, I want a common base class for all coupling types, so that shared infrastructure like logging is consistently available across all coupling implementations.

#### Acceptance Criteria

1. THE BaseCoupling class SHALL provide a shared logger instance accessible to all derived classes
2. THE BaseCoupling class SHALL serve as the base type for detecting coupling-based resources
3. WHEN a class inherits from BaseCoupling, THE System SHALL provide access to the logger property without additional initialization
4. THE logger property SHALL be an EnhancedLogger instance

### Requirement 2: Integration Coupling Type

**User Story:** As a test developer, I want to define integration couplings for external resources, so that I can integrate devices, services, and other automation resources into my test environment.

#### Acceptance Criteria

1. THE IntegrationCoupling class SHALL inherit from BaseCoupling
2. THE IntegrationCoupling class SHALL define class attributes for integration_root, integration_section, integration_leaf, and integration_class
3. THE IntegrationCoupling class SHALL define a class attribute integration_activated defaulting to False
4. WHEN an IntegrationCoupling is instantiated, THE System SHALL initialize connectivity_establish and presence_establish properties to False
5. THE IntegrationCoupling class SHALL expose connectivity_establish and presence_establish as read-only properties

### Requirement 3: Integration Key Generation

**User Story:** As a framework developer, I want integration couplings to have unique hierarchical identifiers, so that they can be organized and looked up consistently.

#### Acceptance Criteria

1. THE get_integration_key method SHALL return a string in the format `{integration_root}:{integration_section}:{integration_leaf}:{integration_class}`
2. THE get_integration_key_parts method SHALL return a tuple containing (integration_root, integration_section, integration_leaf, integration_class)
3. WHEN any integration key component is None, THE System SHALL include the None value in the key string
4. THE integration key SHALL uniquely identify an integration coupling type

### Requirement 4: Integration Coupling Lifecycle Methods

**User Story:** As a test developer, I want integration couplings to have a defined lifecycle, so that resources are properly initialized, connected, and cleaned up during test execution.

#### Acceptance Criteria

1. THE attach_to_framework method SHALL be a classmethod that registers the coupling with the test framework
2. THE attach_to_environment method SHALL be a classmethod that processes configuration information and validates the environment
3. THE collect_resources method SHALL be a classmethod that connects with resource management systems to acquire required resources
4. THE establish_connectivity method SHALL be a classmethod that establishes connections to compute or storage resources
5. THE establish_connectivity method SHALL accept an allow_missing_devices boolean parameter defaulting to False
6. THE establish_connectivity method SHALL return a tuple containing (errors_list, reports_dict)
7. THE establish_presence method SHALL be a classmethod that verifies resource availability and readiness
8. THE establish_presence method SHALL return a tuple containing (errors_list, reports_dict)
9. WHEN a lifecycle method is called on the base IntegrationCoupling class without being overloaded, THE System SHALL raise an AbstractMethodError

### Requirement 5: Integration Coupling Diagnostics

**User Story:** As a test developer, I want integration couplings to generate diagnostic information at checkpoints, so that I can troubleshoot issues during test execution.

#### Acceptance Criteria

1. THE diagnostic method SHALL be a classmethod that generates diagnostic information
2. THE diagnostic method SHALL accept a label parameter identifying the diagnostic point
3. THE diagnostic method SHALL accept a level parameter specifying the maximum diagnostic level
4. THE diagnostic method SHALL accept a diag_folder parameter specifying the output folder path
5. WHEN the diagnostic method is called on the base IntegrationCoupling class without being overloaded, THE System SHALL raise an AbstractMethodError

### Requirement 6: Integration Coupling Precedence

**User Story:** As a framework developer, I want integration couplings to declare precedence values, so that they can be initialized in the correct order based on dependencies.

#### Acceptance Criteria

1. THE declare_precedence method SHALL be a classmethod that returns an integer precedence value
2. WHEN the declare_precedence method is called on the base IntegrationCoupling class without being overloaded, THE System SHALL raise an AbstractMethodError
3. THE sort_integration_couplings_by_precedence function SHALL accept a list of IntegrationCoupling classes
4. THE sort_integration_couplings_by_precedence function SHALL return a list ordered by precedence values from lowest to highest
5. WHEN multiple couplings have the same precedence value, THE System SHALL group them together in the returned list

### Requirement 7: Integration Coupling Configuration Validation

**User Story:** As a test developer, I want integration couplings to validate item configurations, so that configuration errors are detected before test execution.

#### Acceptance Criteria

1. THE validate_item_configuration method SHALL be a classmethod that validates configuration items
2. THE validate_item_configuration method SHALL accept an item_info dictionary parameter
3. THE validate_item_configuration method SHALL return a tuple containing (errors_list, warnings_list)
4. WHEN the validate_item_configuration method is called on the base IntegrationCoupling class without being overloaded, THE System SHALL raise an AbstractMethodError

### Requirement 8: Integration Coupling Type Detection

**User Story:** As a framework developer, I want to detect whether a class is an IntegrationCoupling subclass, so that I can filter and process integration couplings correctly.

#### Acceptance Criteria

1. THE is_integration_coupling function SHALL accept a class as input
2. THE is_integration_coupling function SHALL return True if the class is a subclass of IntegrationCoupling but not IntegrationCoupling itself
3. THE is_integration_coupling function SHALL return False if the class is the IntegrationCoupling base class
4. THE is_integration_coupling function SHALL return False if the input is not a class
5. THE is_integration_coupling function SHALL return False if the class is not a subclass of IntegrationCoupling

### Requirement 9: Configuration Coupling Type

**User Story:** As a test developer, I want to define configuration couplings, so that I can declare configuration specifications that must be satisfied for the test environment.

#### Acceptance Criteria

1. THE ConfigurationCoupling class SHALL inherit from BaseCoupling
2. THE ConfigurationCoupling class SHALL have a default constructor that requires no arguments
3. THE attach_to_environment method SHALL be a classmethod that processes configuration information
4. THE attach_to_environment method SHALL accept an optional constraints dictionary parameter
5. WHEN attach_to_environment is called on the base ConfigurationCoupling class, THE System SHALL return without raising an error (default implementation)

### Requirement 10: Validator Coupling Type

**User Story:** As a test developer, I want to define validator couplings, so that I can create validators that verify test outcomes and attach to test scopes.

#### Acceptance Criteria

1. THE ValidatorCoupling class SHALL serve as the base type for validator objects
2. THE attach_to_test method SHALL accept a testscope parameter for the test scope to attach to
3. THE attach_to_test method SHALL accept a suffix string parameter
4. WHEN the attach_to_test method is called on the base ValidatorCoupling class without being overloaded, THE System SHALL raise an AbstractMethodError

### Requirement 11: Integration Factory Registration

**User Story:** As a test developer, I want to register integration coupling factories using a decorator, so that integration resources are automatically available for dependency injection.

#### Acceptance Criteria

1. THE integration_factory decorator SHALL accept an optional constraints dictionary parameter
2. WHEN the integration_factory decorator is applied to a function, THE System SHALL validate that the function has an annotated return type
3. WHEN the return type annotation is not a Generator yielding an IntegrationCoupling subclass, THE System SHALL raise a SemanticError
4. WHEN the return type annotation indicates returning instead of yielding an IntegrationCoupling, THE System SHALL raise a SemanticError with a descriptive message
5. WHEN the decorated function has a valid return type, THE System SHALL create an IntegrationSource and register it with the injection registry
6. THE integration_factory decorator SHALL return the original function unchanged

### Requirement 12: Configuration Factory Registration

**User Story:** As a test developer, I want to register configuration coupling factories using a decorator, so that configuration resources are automatically available for dependency injection.

#### Acceptance Criteria

1. THE configuration_factory decorator SHALL accept an optional query_function parameter
2. THE configuration_factory decorator SHALL accept an optional constraints dictionary parameter
3. WHEN the configuration_factory decorator is applied to a function, THE System SHALL validate that the function has an annotated return type
4. WHEN the return type annotation is not a Generator yielding a ConfigurationCoupling subclass, THE System SHALL raise a SemanticError
5. WHEN the decorated function has a valid return type, THE System SHALL create a ConfigurationSource and register it with the injection registry
6. THE configuration_factory decorator SHALL return the original function unchanged

### Requirement 13: Validator Factory Registration

**User Story:** As a test developer, I want to register validator coupling factories using a decorator, so that validators are automatically available for dependency injection.

#### Acceptance Criteria

1. THE validator_factory decorator SHALL accept an optional constraints dictionary parameter
2. WHEN the validator_factory decorator is applied to a function, THE System SHALL validate that the function has an annotated return type
3. WHEN the return type annotation is not a ValidatorCoupling subclass, THE System SHALL raise a SemanticError
4. WHEN the decorated function has a valid return type, THE System SHALL create a ValidatorSource and register it with the injection registry
5. THE validator_factory decorator SHALL return the original function unchanged

### Requirement 14: Coupling Collection for Injection

**User Story:** As a framework developer, I want to collect all couplings referenced by tests, so that only necessary couplings are initialized during test execution.

#### Acceptance Criteria

1. THE collect_integrations_and_configurations_for_injection_moment method SHALL walk the scope tree path for injectable references
2. THE method SHALL identify parameters whose resource types are IntegrationCoupling subclasses and add them to the integration_table
3. THE method SHALL identify parameters whose resource types are ConfigurationCoupling subclasses and add them to the configuration_table
4. WHEN a parameter has generic type arguments, THE System SHALL check each type argument for coupling types
5. THE method SHALL populate the provided integration_table and configuration_table dictionaries with source_function to coupling_type mappings

### Requirement 15: Integration with Dependency Injection System

**User Story:** As a framework developer, I want couplings to integrate with the dependency injection system, so that coupling instances can be injected into tests and other resources.

#### Acceptance Criteria

1. THE InjectionRegistry SHALL maintain tables for referenced integrations and configurations
2. WHEN a coupling factory is registered, THE System SHALL create appropriate source objects (IntegrationSource, ConfigurationSource, ValidatorSource)
3. THE System SHALL support looking up registered coupling sources by their factory functions
4. WHEN finalize_startup is called, THE System SHALL collect all integrations and configurations referenced by injection moments

