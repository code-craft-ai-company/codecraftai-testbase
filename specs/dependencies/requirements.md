# Dependency Injection System - Requirements Document

## Introduction

The Dependency Injection (DI) System is a core component of the TestBase framework that manages the resolution, instantiation, and lifecycle of injectable resources during test execution. It provides a hierarchical scope tree for parameter visibility, supports multiple resource lifespans, and enables automatic dependency resolution for test functions and resource factories. The system works in conjunction with the Test Declaration and Registration system to transform registered sources and origins into a runtime dependency graph that can be traversed during test execution.

## Glossary

- **InjectionRegistry**: The singleton registry that manages all registered sources, origins, and the scope tree for dependency injection
- **InjectionScope**: A node in the hierarchical scope tree that contains parameter and validator originations for a specific scope level
- **InjectionGroup**: A hierarchical grouping of injection moments organized by module paths for metadata resolution
- **InjectionMoment**: A point in the execution flow where injection occurs, capturing the injectable function reference and its dependencies
- **Scope_Tree**: A hierarchical tree structure where each node represents a scope level and contains parameter originations visible at that level
- **Parameter_Origination**: A mapping of parameter identifiers to their ResourceOrigin objects within a scope
- **Validator_Origination**: A mapping of validator identifiers to their ValidatorOrigin objects within a scope
- **ResourceLifespan**: An enumeration defining the lifecycle duration of a resource (Session, Package, Test, Task)
- **Scope_Path**: A dot-separated string representing the hierarchical location of a scope (e.g., "package.module#test_function")
- **Parameter_Resolution**: The process of walking the scope tree to find the origin of a requested parameter
- **Scope_Pruning**: The process of removing non-relevant scope nodes from the tree after injection moment discovery

## Requirements

### Requirement 1: Injection Registry Singleton

**User Story:** As a framework developer, I want a singleton registry for all injection sources and scope management, so that there is a single source of truth for dependency injection across the test session.

#### Acceptance Criteria

1. THE InjectionRegistry SHALL implement the singleton pattern ensuring only one instance exists
2. WHEN multiple instances of InjectionRegistry are requested, THE System SHALL return the same instance
3. THE InjectionRegistry SHALL maintain separate source tables for integration, resource, configuration, and validator sources
4. THE InjectionRegistry SHALL maintain a scope tree root for managing parameter visibility hierarchies
5. THE InjectionRegistry SHALL track unknown parameters that cannot be resolved during finalization
6. THE InjectionRegistry SHALL track referenced integrations discovered during finalization
7. THE InjectionRegistry SHALL track referenced configurations discovered during finalization

### Requirement 2: Source Registration

**User Story:** As a framework component, I want to register different types of sources with the registry, so that factory functions are available for dependency resolution.

#### Acceptance Criteria

1. WHEN an IntegrationSource is registered, THE InjectionRegistry SHALL store it in the integration source table keyed by source function
2. WHEN a ResourceSource is registered, THE InjectionRegistry SHALL store it in the resource source table keyed by source function
3. WHEN a ConfigurationSource is registered, THE InjectionRegistry SHALL store it in the configuration source table keyed by source function
4. WHEN a ValidatorSource is registered, THE InjectionRegistry SHALL store it in the validator source table keyed by source function
5. WHEN a source with the same source function is registered multiple times, THE InjectionRegistry SHALL retain only the first registration

### Requirement 3: Source Lookup

**User Story:** As a framework component, I want to look up registered sources by their factory function, so that I can resolve parameter origins during dependency injection.

#### Acceptance Criteria

1. WHEN looking up a resource source, THE InjectionRegistry SHALL search integration, configuration, and resource source tables in that order
2. WHEN the source function is found in any table, THE System SHALL return the corresponding source object
3. WHEN the source function is not found in any table, THE System SHALL return None
4. WHEN looking up a validator source, THE InjectionRegistry SHALL search only the validator source table
5. WHEN the validator source function is found, THE System SHALL return the corresponding ValidatorSource object
6. WHEN the validator source function is not found, THE System SHALL return None

### Requirement 4: Resource Origin Registration

**User Story:** As a framework developer, I want to register resource origins in the scope tree, so that parameters are available for injection at the appropriate scope levels.

#### Acceptance Criteria

1. WHEN registering a resource origin, THE System SHALL add it to the scope tree at the specified originating scope
2. WHEN a resource origin with the same identifier already exists in the target scope, THE System SHALL raise a SemanticError
3. WHEN the originating scope is "<session>", THE System SHALL add the origin to the root scope node
4. WHEN the originating scope contains a "#" character, THE System SHALL treat the portion after "#" as an injection moment scope
5. THE System SHALL create intermediate scope nodes as needed when registering origins at nested scope paths

### Requirement 5: Validator Origin Registration

**User Story:** As a framework developer, I want to register validator origins in the scope tree, so that validators are available for post-test validation at the appropriate scope levels.

#### Acceptance Criteria

1. WHEN registering a validator origin, THE System SHALL add it to the scope tree at the specified originating scope
2. WHEN a validator origin with the same identifier already exists in the target scope, THE System SHALL raise a SemanticError
3. WHEN the originating scope is "<session>", THE System SHALL add the origin to the root scope node
4. WHEN the originating scope contains a "#" character, THE System SHALL treat the portion after "#" as an injection moment scope
5. THE System SHALL create intermediate scope nodes as needed when registering origins at nested scope paths

### Requirement 6: Scope Tree Construction

**User Story:** As a framework developer, I want the scope tree to be constructed hierarchically based on module paths, so that parameter visibility follows Python's module hierarchy.

#### Acceptance Criteria

1. THE InjectionScope SHALL maintain a dictionary of child scopes keyed by scope name
2. THE InjectionScope SHALL maintain an ordered dictionary of parameter originations keyed by identifier
3. THE InjectionScope SHALL maintain an ordered dictionary of validator originations keyed by identifier
4. WHEN adding a descendent origination, THE System SHALL walk or create scope nodes along the path
5. WHEN the add_descendent API is called on a non-root scope, THE System SHALL raise a SemanticError
6. THE System SHALL preserve the insertion order of parameter originations within each scope

### Requirement 7: Injection Scope Finalization

**User Story:** As a framework developer, I want to finalize the injection registry after test discovery, so that all parameter origins are resolved and the scope tree is optimized before execution.

#### Acceptance Criteria

1. WHEN finalize_startup is called, THE System SHALL ensure injection scopes exist for all injection moments
2. WHEN ensuring injection scopes, THE System SHALL mark each scope along the path as relevant
3. AFTER ensuring all injection scopes, THE System SHALL prune unreferenced scopes from the scope tree
4. WHEN pruning scopes, THE System SHALL remove non-relevant leaf nodes working backwards toward the root
5. AFTER pruning, THE System SHALL resolve resource originations for each injection moment
6. WHEN parameters cannot be resolved, THE System SHALL record them in the unknown_parameters table
7. AFTER resolution, THE System SHALL collect referenced integrations and configurations for the execution run

### Requirement 8: Parameter Resolution

**User Story:** As a framework developer, I want parameters to be resolved by walking up the scope tree, so that parameters defined at higher scopes are visible to lower scopes.

#### Acceptance Criteria

1. WHEN resolving parameters for an injection moment, THE System SHALL walk the scope path from root to the injection moment
2. THE System SHALL maintain a parameter visibility table that accumulates parameters as it descends the scope tree
3. WHEN a parameter origination is encountered, THE System SHALL add it to the visibility table for descendant scopes
4. WHEN a source function requires parameters not in the visibility table, THE System SHALL record them as missing
5. THE System SHALL skip reserved parameter names (e.g., "constraints") when checking for missing parameters
6. WHEN parameters shadow parent scope parameters with the same identifier, THE System SHALL use the more local parameter

### Requirement 9: Integration and Configuration Collection

**User Story:** As a framework developer, I want to collect all referenced integrations and configurations, so that the execution engine knows what couplings are required for the test run.

#### Acceptance Criteria

1. WHEN collecting integrations and configurations, THE System SHALL walk the entire scope tree
2. WHEN a parameter origination's resource type is an IntegrationCoupling subclass, THE System SHALL add it to the integration table
3. WHEN a parameter origination's resource type is a ConfigurationCoupling subclass, THE System SHALL add it to the configuration table
4. WHEN the resource type is a generic type containing IntegrationCoupling, THE System SHALL extract and add the coupling type
5. WHEN the resource type is a generic type containing ConfigurationCoupling, THE System SHALL extract and add the coupling type
6. THE System SHALL skip implied parameter originations when collecting couplings

### Requirement 10: Scope Lookup

**User Story:** As a framework component, I want to look up scopes by their full path name, so that I can access scope-specific parameter originations.

#### Acceptance Criteria

1. WHEN looking up a scope by name, THE System SHALL parse the scope path into components
2. WHEN the scope name is "<session>", THE System SHALL return the root scope node
3. WHEN the scope path contains a "#" character, THE System SHALL replace it with "." for traversal
4. WHEN the scope exists in the tree, THE System SHALL return the corresponding InjectionScope object
5. WHEN the scope does not exist in the tree, THE System SHALL return None

### Requirement 11: Injection Group Hierarchy

**User Story:** As a framework developer, I want injection moments organized into a hierarchical group structure, so that metadata can be resolved and propagated through the hierarchy.

#### Acceptance Criteria

1. THE InjectionGroup SHALL maintain a dictionary of child groups and injection moments
2. WHEN adding a descendent injection moment, THE System SHALL create intermediate group nodes as needed
3. WHEN the add_descendent API is called on a non-root group, THE System SHALL raise a SemanticError
4. THE InjectionGroup SHALL provide access to its associated resource scope from the injection registry
5. THE InjectionGroup SHALL support context manager protocol for scoped operations

### Requirement 12: Metadata Resolution

**User Story:** As a framework developer, I want metadata to be resolved and propagated through the injection hierarchy, so that tests inherit metadata from their parent modules.

#### Acceptance Criteria

1. WHEN resolving metadata for an injection group, THE System SHALL check the associated module for _metadata_ attribute
2. WHEN parent metadata exists, THE System SHALL merge it with the group's reference metadata
3. WHEN merging metadata, THE System SHALL allow child metadata to override parent metadata
4. THE System SHALL propagate resolved metadata to all child groups and injection moments
5. WHEN resolving metadata for an injection moment, THE System SHALL check the function for _metadata_ attribute

### Requirement 13: Injection Moment Management

**User Story:** As a framework developer, I want injection moments to capture all information needed for dependency injection, so that resources can be resolved and injected at execution time.

#### Acceptance Criteria

1. THE InjectionMoment SHALL store a reference to the injectable function
2. THE InjectionMoment SHALL store optional monikers for test variations
3. THE InjectionMoment SHALL store optional pivots for parameterized execution
4. THE InjectionMoment SHALL provide access to the function's parameter signature
5. THE InjectionMoment SHALL compute its scope name from the function's module and name
6. THE InjectionMoment SHALL support finalization to mark completion of setup
7. THE InjectionMoment SHALL support membership testing against MetaFilter collections

### Requirement 14: Implied Session Resources

**User Story:** As a framework developer, I want to add implied session resources that are inherent to the framework, so that built-in resources are available without explicit registration.

#### Acceptance Criteria

1. WHEN adding an implied session resource, THE System SHALL create a ResourceOrigin with Session lifespan
2. THE implied ResourceOrigin SHALL have no associated source function
3. THE implied ResourceOrigin SHALL be marked as implied
4. THE System SHALL add the implied origin to the root session scope

### Requirement 15: Scope Origin Renaming

**User Story:** As a framework developer, I want to rename resource origins from __main__, so that resources loaded from debug scripts have correct scope names.

#### Acceptance Criteria

1. WHEN renaming origins from __main__, THE System SHALL find the __main__ child scope if it exists
2. THE System SHALL rename the __main__ scope to the new origin name
3. THE System SHALL update the originating_scope of all parameter originations in child injection scopes
4. THE System SHALL re-register the updated origins with the scope tree

