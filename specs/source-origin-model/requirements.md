# Source and Origin Model - Requirements Document

## Introduction

The Source and Origin Model defines the data types that represent injectable resource providers and their placement in the dependency injection scope tree. Sources describe factory functions that create resources, while Origins describe where those resources are placed in the scope hierarchy. This model is consumed by the Dependency Injection system (InjectionRegistry) and the Sequence Document Generator. The model also includes the ResourceLifespan enumeration that controls how long injected resources live.

## Glossary

- **SourceBase**: Base class for all source types, wrapping a factory function with its metadata
- **IntegrationSource**: A source for IntegrationCoupling factories
- **ResourceSource**: A source for general resource factories
- **ConfigurationSource**: A source for ConfigurationCoupling factories
- **ValidatorSource**: A source for Validator factories
- **ResourceOrigin**: Describes the placement of a resource in the scope tree (scope path, identifier, lifespan, source reference)
- **ValidatorOrigin**: Describes the placement of a validator in the scope tree
- **ResourceLifespan**: Enumeration of resource lifetimes (Session, Package, Test, Task)

## Requirements

### Requirement 1: SourceBase Properties

**User Story:** As a framework developer, I want a base source type that captures factory function metadata, so that the injection system can resolve dependencies.

#### Acceptance Criteria

1. THE SourceBase SHALL store: `source_func` (the factory callable), `query_func` (optional query callable), `resource_type` (the type produced), and `constraints` (optional constraint dictionary).
2. THE SourceBase SHALL expose `module_name` derived from `source_func.__module__`.
3. THE SourceBase SHALL expose `source_signature` via `inspect.signature(source_func)`.
4. THE SourceBase SHALL expose `source_id` as `"{module}#{function_name}"`.
5. THE SourceBase SHALL support optional `subscriptions` for event-based resource updates.

### Requirement 2: Source Type Variants

**User Story:** As a framework developer, I want distinct source types for integrations, resources, configurations, and validators, so that the registry can categorize them.

#### Acceptance Criteria

1. `IntegrationSource` SHALL extend SourceBase for IntegrationCoupling factories.
2. `ResourceSource` SHALL extend SourceBase for general resource factories.
3. `ConfigurationSource` SHALL extend SourceBase for ConfigurationCoupling factories.
4. `ValidatorSource` SHALL extend SourceBase for Validator factories.
5. EACH source type SHALL be stored in a separate table in the InjectionRegistry.

### Requirement 3: ResourceOrigin Properties

**User Story:** As a framework developer, I want resource origins to describe where a resource lives in the scope tree, so that the injection system can resolve parameters at the correct scope.

#### Acceptance Criteria

1. THE ResourceOrigin SHALL store: `originating_scope` (scope path string), `identifier` (parameter name), `life_span` (ResourceLifespan), `source` (optional SourceBase reference), and `implied` (boolean flag).
2. WHEN `constraints` are provided, THE ResourceOrigin SHALL register them with the ConstraintsCatalog and store the resulting `constraints_key`.
3. THE ResourceOrigin SHALL expose `source_function`, `source_function_name`, `source_signature`, `source_id`, `source_module_name`, and `source_resource_type` via delegation to the source.
4. THE ResourceOrigin SHALL provide a `generate_call(constraints?)` method that produces the factory function call string for code generation.
5. THE `generate_call` method SHALL include all parameters from the source signature, removing `constraints` if no constraints are provided.
6. THE ResourceOrigin SHALL provide a `describe_source()` method returning a human-readable description including constraints key if present.

### Requirement 4: ResourceLifespan Enumeration

**User Story:** As a framework developer, I want defined resource lifespans, so that resources are created and destroyed at the appropriate scope boundaries.

#### Acceptance Criteria

1. THE ResourceLifespan enum SHALL define: `Session` (lives for the entire test run), `Package` (lives for a package scope), `Test` (lives for a single test), `Task` (lives for a single task within a test).
2. THE ResourceLifespan SHALL be a string enum for serialization compatibility.
3. THE lifespan SHALL determine at which scope level the resource factory is invoked in the generated sequence document.

### Requirement 5: Implied Origins

**User Story:** As a framework developer, I want to mark certain origins as implied (built-in), so that they are available without explicit registration and skipped during code generation.

#### Acceptance Criteria

1. WHEN `implied=True`, THE ResourceOrigin SHALL have no associated source function.
2. IMPLIED origins SHALL be skipped during sequence document generation (no import or factory call generated).
3. IMPLIED origins SHALL be added to the root session scope.
4. THE "sequencer" parameter SHALL be an implied session resource added during collection finalization.
