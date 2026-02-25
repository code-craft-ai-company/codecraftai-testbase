# Test Declaration and Registration - Requirements Document

## Introduction

The Test Declaration and Registration system provides the foundational mechanisms for declaring test functions, registering resource factories, and managing the lifecycle of injectable resources within the TestBase framework. This system enables dependency injection and resource management across test execution scopes through Python decorators and a centralized registry.

## Glossary

- **InjectionRegistry**: The singleton registry that manages all registered sources and origins for dependency injection
- **Source**: A wrapper object that encapsulates a factory function and its metadata for resource creation
- **Origin**: An object that describes where a resource parameter originates and its visibility scope
- **ResourceLifespan**: An enumeration defining the lifecycle duration of a resource (Session, Package, Test, Task)
- **IntegrationCoupling**: A base class for declaring automation integration requirements
- **ConfigurationCoupling**: A base class for declaring configuration specifications
- **ValidatorCoupling**: A base class for declaring test validators
- **Factory_Function**: A Python function decorated to produce injectable resources
- **Constraint**: A dictionary of key-value pairs used to conditionally filter resource creation

## Requirements

### Requirement 1: Integration Factory Registration

**User Story:** As a test developer, I want to register integration factory functions, so that I can provide integration coupling resources to tests through dependency injection.

#### Acceptance Criteria

1. WHEN a function is decorated with `@integration_factory`, THE InjectionRegistry SHALL register the function as an integration source
2. WHEN the decorated function lacks a return type annotation, THE System SHALL raise a SemanticError with a descriptive message
3. WHEN the return type annotation is a Generator yielding an IntegrationCoupling subclass, THE System SHALL extract the resource type from the yield type
4. WHEN the return type is an IntegrationCoupling subclass (not yielded), THE System SHALL raise a SemanticError indicating the function should yield instead of return
5. WHEN the return type does not inherit from IntegrationCoupling, THE System SHALL raise a SemanticError
6. WHEN optional constraints are provided, THE System SHALL associate the constraints with the registered source
7. THE System SHALL preserve the original function behavior after decoration

### Requirement 2: Resource Factory Registration

**User Story:** As a test developer, I want to register general resource factory functions, so that I can provide arbitrary resources to tests through dependency injection.

#### Acceptance Criteria

1. WHEN a function is decorated with `@resource_factory`, THE InjectionRegistry SHALL register the function as a resource source
2. WHEN the decorated function lacks a return type annotation, THE System SHALL raise a SemanticError
3. WHEN the return type annotation is a Generator, THE System SHALL extract the resource type from the yield or return type
4. WHEN the return type is a direct class reference, THE System SHALL use that class as the resource type
5. WHEN an optional query_function is provided, THE System SHALL associate it with the resource source
6. WHEN optional constraints are provided, THE System SHALL associate the constraints with the registered source
7. THE System SHALL preserve the original function behavior after decoration

### Requirement 3: Configuration Factory Registration

**User Story:** As a test developer, I want to register configuration factory functions, so that I can provide configuration coupling resources to tests through dependency injection.

#### Acceptance Criteria

1. WHEN a function is decorated with `@configuration_factory`, THE InjectionRegistry SHALL register the function as a configuration source
2. WHEN the decorated function lacks a return type annotation, THE System SHALL raise a SemanticError
3. WHEN the return type annotation is a Generator yielding a ConfigurationCoupling subclass, THE System SHALL extract the resource type from the yield type
4. WHEN the return type does not inherit from ConfigurationCoupling, THE System SHALL raise a SemanticError
5. WHEN an optional query_function is provided, THE System SHALL associate it with the configuration source
6. WHEN optional constraints are provided, THE System SHALL associate the constraints with the registered source
7. THE System SHALL preserve the original function behavior after decoration

### Requirement 4: Validator Factory Registration

**User Story:** As a test developer, I want to register validator factory functions, so that I can provide validator coupling resources to tests through dependency injection.

#### Acceptance Criteria

1. WHEN a function is decorated with `@validator_factory`, THE InjectionRegistry SHALL register the function as a validator source
2. WHEN the decorated function lacks a return type annotation, THE System SHALL raise a SemanticError
3. WHEN the return type does not inherit from ValidatorCoupling, THE System SHALL raise a SemanticError
4. WHEN optional constraints are provided, THE System SHALL associate the constraints with the registered source
5. THE System SHALL preserve the original function behavior after decoration

### Requirement 5: Parameter Attachment to Tests

**User Story:** As a test developer, I want to attach resource parameters to specific test functions, so that I can localize resource injection to individual tests.

#### Acceptance Criteria

1. WHEN a test function is decorated with `@parameter`, THE System SHALL create a ResourceOrigin with Test lifespan
2. WHEN an identifier is provided, THE System SHALL use that identifier for the parameter origin
3. WHEN no identifier is provided, THE System SHALL use the source function name as the identifier
4. WHEN the identifier is the reserved word "constraints", THE System SHALL raise a SemanticError
5. WHEN constraints are provided but the source function has no constraints parameter, THE System SHALL raise a SemanticError
6. THE System SHALL register the parameter origin with the InjectionRegistry
7. THE System SHALL preserve the original test function behavior after decoration

### Requirement 6: Validation Attachment to Tests

**User Story:** As a test developer, I want to attach validators to specific test functions, so that I can perform post-test validation.

#### Acceptance Criteria

1. WHEN a test function is decorated with `@validation`, THE System SHALL create a ValidatorOrigin
2. WHEN an identifier is provided, THE System SHALL use that identifier for the validator origin
3. WHEN no identifier is provided, THE System SHALL use the source function name as the identifier
4. WHEN the identifier is the reserved word "constraints", THE System SHALL raise a SemanticError
5. WHEN a suffix is provided, THE System SHALL associate it with the validator origin
6. THE System SHALL register the validator origin with the InjectionRegistry
7. THE System SHALL preserve the original test function behavior after decoration

### Requirement 7: Global Parameter Origination

**User Story:** As a test developer, I want to create global parameter origins, so that resources can be shared across multiple tests within a package or session scope.

#### Acceptance Criteria

1. WHEN the `parameter()` origination function is called, THE System SHALL create a ResourceOrigin with the specified lifespan
2. WHEN lifespan is ResourceLifespan.Test, THE System SHALL raise a SemanticError
3. WHEN no lifespan is specified and the resource is an IntegrationCoupling, THE System SHALL default to Session lifespan
4. WHEN no lifespan is specified and the resource is not an IntegrationCoupling, THE System SHALL default to Package lifespan
5. WHEN the identifier is the reserved word "constraints", THE System SHALL raise a SemanticError
6. WHEN constraints are provided but the source function has no constraints parameter, THE System SHALL raise a SemanticError
7. WHEN assigned_scope is specified for an IntegrationSource, THE System SHALL raise a SemanticError
8. WHEN the function is mistakenly used as a decorator, THE System SHALL raise a SemanticError with guidance to use `@testbase.attach.parameter()` instead
9. THE System SHALL register the parameter origin with the InjectionRegistry

### Requirement 8: Injection Registry Singleton

**User Story:** As a framework developer, I want a singleton registry for all injection sources and origins, so that there is a single source of truth for dependency injection.

#### Acceptance Criteria

1. THE InjectionRegistry SHALL implement the singleton pattern
2. WHEN multiple instances are requested, THE System SHALL return the same instance
3. THE InjectionRegistry SHALL maintain separate tables for integration, resource, configuration, and validator sources
4. THE InjectionRegistry SHALL maintain a scope tree for managing parameter visibility
5. THE InjectionRegistry SHALL track unknown parameters that cannot be resolved

### Requirement 9: Source Lookup

**User Story:** As a framework component, I want to look up registered sources by their factory function, so that I can resolve parameter origins.

#### Acceptance Criteria

1. WHEN looking up a resource source, THE InjectionRegistry SHALL search integration, configuration, and resource source tables
2. WHEN the source function is found, THE System SHALL return the corresponding source object
3. WHEN the source function is not found, THE System SHALL return None
4. WHEN looking up a validator source, THE InjectionRegistry SHALL search the validator source table
5. WHEN the validator source function is found, THE System SHALL return the corresponding ValidatorSource object

### Requirement 10: Origin Registration and Uniqueness

**User Story:** As a framework developer, I want to ensure parameter origins are unique within their scope, so that there are no identifier conflicts.

#### Acceptance Criteria

1. WHEN registering a resource origin, THE System SHALL add it to the scope tree at the specified scope
2. WHEN a resource origin with the same identifier already exists in the scope, THE System SHALL raise a SemanticError
3. WHEN registering a validator origin, THE System SHALL add it to the scope tree at the specified scope
4. WHEN a validator origin with the same identifier already exists in the scope, THE System SHALL raise a SemanticError

### Requirement 11: Startup Finalization

**User Story:** As a framework developer, I want to finalize the injection registry after test discovery, so that all parameter origins are resolved before execution.

#### Acceptance Criteria

1. WHEN finalize_startup is called, THE System SHALL ensure injection scopes exist for all injection moments
2. THE System SHALL prune unreferenced scopes from the scope tree
3. THE System SHALL resolve resource originations for each injection moment
4. WHEN parameters cannot be resolved, THE System SHALL record them in the unknown_parameters table
5. THE System SHALL collect referenced integrations and configurations for the execution run

### Requirement 12: Resource Lifespan Management

**User Story:** As a test developer, I want to specify resource lifespans, so that resources are created and destroyed at appropriate times.

#### Acceptance Criteria

1. THE System SHALL support Session lifespan for resources that live for the entire test session
2. THE System SHALL support Package lifespan for resources that live within a module hierarchy
3. THE System SHALL support Test lifespan for resources that are created and destroyed per test
4. THE System SHALL support Task lifespan for resources that live within a task scope
5. WHEN a resource origin is created, THE System SHALL assign the appropriate lifespan based on the origination context

