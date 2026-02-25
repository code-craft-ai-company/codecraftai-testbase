# Test Declaration and Registration - Tasks Document

## Overview

This document tracks the implementation status of the Test Declaration and Registration system and identifies enhancement opportunities for future development.

## Implementation Status

### Completed Tasks

#### Registration Decorators (`registrations.py`)
- [x] Implement `@integration_factory` decorator for IntegrationCoupling resources
  - Validates return type annotations
  - Extracts resource type from Generator yield type
  - Registers IntegrationSource with InjectionRegistry
  - Supports optional constraints parameter
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7_

- [x] Implement `@resource_factory` decorator for general resources
  - Validates return type annotations
  - Supports Generator and direct return types
  - Registers ResourceSource with InjectionRegistry
  - Supports optional query_function and constraints parameters
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

- [x] Implement `@configuration_factory` decorator for ConfigurationCoupling resources
  - Validates return type annotations
  - Extracts resource type from Generator yield type
  - Registers ConfigurationSource with InjectionRegistry
  - Supports optional query_function and constraints parameters
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

- [x] Implement `@validator_factory` decorator for ValidatorCoupling resources
  - Validates return type annotations
  - Validates ValidatorCoupling inheritance
  - Registers ValidatorSource with InjectionRegistry
  - Supports optional constraints parameter
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

#### Attachment Decorators (`attachments.py`)
- [x] Implement `@parameter` attachment decorator
  - Creates ResourceOrigin with Test lifespan
  - Supports custom identifier or defaults to source function name
  - Validates reserved identifier "constraints"
  - Validates constraints parameter compatibility
  - Registers origin with InjectionRegistry
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_

- [x] Implement `@validation` attachment decorator
  - Creates ValidatorOrigin with suffix support
  - Supports custom identifier or defaults to source function name
  - Validates reserved identifier "constraints"
  - Registers origin with InjectionRegistry
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

#### Origination Functions (`originiations.py`)
- [x] Implement `parameter()` origination function
  - Creates ResourceOrigin with specified lifespan
  - Validates lifespan is not ResourceLifespan.Test
  - Defaults lifespan based on resource type (Session for IntegrationCoupling, Package otherwise)
  - Validates reserved identifier "constraints"
  - Validates constraints parameter compatibility
  - Validates assigned_scope not used with IntegrationSource
  - Provides helpful error when misused as decorator
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

#### Unit Tests (`test_declaration_functions.py`)
- [x] Registration decorator tests
  - Integration factory registration and validation
  - Resource factory registration and validation
  - Configuration factory registration and validation
  - Validator factory registration and validation

- [x] Attachment decorator tests
  - Parameter attachment registration
  - Reserved identifier validation
  - Constraints compatibility validation
  - Validation attachment registration

- [x] Origination function tests
  - Parameter origination registration
  - Source None error handling
  - Lifespan Test error handling
  - Reserved identifier error handling
  - Assigned scope with integration error handling

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage Enhancements
- [x] Add property-based tests for decorator registration
  - Test that arbitrary valid factory functions are correctly registered
  - Test that constraints are properly associated with sources
  - _Requirements: 1.6, 2.6, 3.6, 4.4_

- [x] Add integration tests for end-to-end registration flow
  - Test complete flow from decorator to registry lookup
  - Test scope tree construction with multiple registrations
  - _Requirements: 8.3, 8.4, 9.1, 9.2, 9.3, 9.4, 9.5_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to all public functions
  - Document parameters, return types, and exceptions
  - Include usage examples in docstrings

- [x] Add inline code comments for complex logic
  - Document type extraction logic in decorators
  - Document scope resolution logic in originations

#### Error Handling Improvements
- [x] Verify error handling
  - Verify source function name in error messages
  - Verify expected vs actual type information
  - Added `ErrorHandlingVerificationTests` test class in `test_declaration_functions.py`
  - Tests verify error messages contain appropriate context for debugging
  - Note: Some edge cases (non-Generator types without `_name` attribute) raise AttributeError instead of SemanticError
  - _Requirements: 1.2, 2.2, 3.2, 4.2_

- [x] Add validation for duplicate identifier registration
  - Detect and report duplicate identifiers in same scope
  - _Requirements: 10.2, 10.4_

#### Feature Enhancements
- [x] Support for async factory functions
  - Allow async generators in integration_factory
  - Allow async generators in resource_factory
  - Allow async generators in configuration_factory

- [x] Support for parameterized constraints
  - Verify dynamic constraint evaluation is supported
  - Verify that constraints can be passed to generator in any scope via the commandline and contraint dictionary
  - Added comprehensive test suite in `test_parameterized_constraints.py` with 21 tests covering:
    - Dynamic constraint evaluation (runtime addition, override precedence, callable interface)
    - Constraints passed to generators (resource, integration, configuration factories)
    - Constraints at different scopes (session, package, test)
    - Constraint validation and ResourceOrigin integration

- [x] Add factory function introspection utilities
  - Provide API to list all registered factories
  - Provide API to query factory metadata
  - Added `introspection.py` module with `FactoryType`, `FactoryMetadata`, and `FactoryListResult` classes
  - Added introspection methods to `InjectionRegistry`:
    - `list_factories()` - Lists all registered factories, optionally filtered by type
    - `get_factory_metadata()` - Retrieves metadata for a specific factory function
    - `find_factories_by_resource_type()` - Finds factories producing a specific type
    - `find_factories_by_module()` - Finds factories defined in a specific module
    - `find_factories_with_constraints()` - Finds factories with constraints
  - Added comprehensive test suite in `test_factory_introspection.py` with 23 tests

---

## Enhancement Opportunities

### Short-term Improvements

1. **Type Hint Completeness**
   - Add complete type hints to all function signatures
   - Use TypeVar for generic factory return types
   - Add Protocol definitions for factory function signatures

2. **Validation Robustness**
   - Add validation for circular dependencies in resource origins
   - Add validation for conflicting constraint definitions
   - Add warnings for unused registered factories

3. **Developer Experience**
   - Add debug logging for registration events
   - Add registration summary output for test discovery
   - Improve error messages with suggested fixes

### Medium-term Improvements

1. **Performance Optimization**
   - Cache type extraction results for repeated lookups
   - Optimize scope tree traversal for large test suites
   - Lazy initialization of source metadata

2. **Extensibility**
   - Plugin architecture for custom source types
   - Hook system for registration lifecycle events
   - Custom validator for factory function signatures

### Long-term Improvements

1. **Static Analysis Integration**
   - Provide mypy plugin for decorator type checking
   - Provide pylint plugin for registration validation
   - IDE integration for factory function navigation

2. **Advanced Features**
   - Support for conditional factory registration
   - Support for factory function versioning
   - Support for factory function deprecation warnings

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.7 | ✅ Complete | `registrations.py::integration_factory` |
| 2.1-2.7 | ✅ Complete | `registrations.py::resource_factory` |
| 3.1-3.7 | ✅ Complete | `registrations.py::configuration_factory` |
| 4.1-4.5 | ✅ Complete | `registrations.py::validator_factory` |
| 5.1-5.7 | ✅ Complete | `attachments.py::parameter` |
| 6.1-6.7 | ✅ Complete | `attachments.py::validation` |
| 7.1-7.9 | ✅ Complete | `originiations.py::parameter` |
| 8.1-8.5 | ✅ Complete | `injection/injectionregistry.py` |
| 9.1-9.5 | ✅ Complete | `injection/injectionregistry.py` |
| 10.1-10.4 | ⚠️ Partial | Uniqueness validation needs enhancement |
| 11.1-11.5 | ✅ Complete | `injection/injectionregistry.py::finalize_startup` |
| 12.1-12.5 | ✅ Complete | `resourcelifespan.py` |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | Property Tests |
|-----------|------------|-------------------|----------------|
| `integration_factory` | ✅ | ⬜ | ⬜ |
| `resource_factory` | ✅ | ⬜ | ⬜ |
| `configuration_factory` | ✅ | ⬜ | ⬜ |
| `validator_factory` | ✅ | ⬜ | ⬜ |
| `@parameter` attachment | ✅ | ⬜ | ⬜ |
| `@validation` attachment | ✅ | ⬜ | ⬜ |
| `parameter()` origination | ✅ | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started
