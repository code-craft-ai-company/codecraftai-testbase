# Coupling System - Tasks Document

## Overview

This document tracks the implementation status of the Coupling System and identifies enhancement opportunities for future development. The coupling module provides a mechanism for integrating external resources, configurations, and validators into the TestBase test execution framework, enabling lifecycle management for external automation resources, configuration specifications, and test validators.

## Implementation Status

### Completed Tasks

#### BaseCoupling (`basecoupling.py`)
- [x] Implement `BaseCoupling` class
  - Provides shared logger instance via `getEnhancedLogger()`
  - Serves as base type for detecting coupling-based resources
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

#### IntegrationCoupling (`integrationcoupling.py`)
- [x] Implement `IntegrationCoupling` class inheriting from BaseCoupling
  - Defines class attributes: integration_root, integration_section, integration_leaf, integration_class
  - Defines integration_activated class attribute defaulting to False
  - _Requirements: 2.1, 2.2, 2.3_

- [x] Implement instance state tracking
  - Initializes `_connectivity_establish` and `_presence_establish` to False
  - Exposes `connectivity_establish` and `presence_establish` as read-only properties
  - _Requirements: 2.4, 2.5_

- [x] Implement `get_integration_key` classmethod
  - Returns string in format `{integration_root}:{integration_section}:{integration_leaf}:{integration_class}`
  - _Requirements: 3.1, 3.3, 3.4_

- [x] Implement `get_integration_key_parts` classmethod
  - Returns tuple containing (integration_root, integration_section, integration_leaf, integration_class)
  - _Requirements: 3.2_

- [x] Implement lifecycle methods as abstract methods
  - `attach_to_framework` raises AbstractMethodError when not overloaded
  - `attach_to_environment` raises AbstractMethodError when not overloaded
  - `collect_resources` raises AbstractMethodError when not overloaded
  - `establish_connectivity` raises AbstractMethodError when not overloaded
  - `establish_presence` raises AbstractMethodError when not overloaded
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9_

- [x] Implement `diagnostic` classmethod
  - Accepts label, level, and diag_folder parameters
  - Raises AbstractMethodError when not overloaded
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] Implement `declare_precedence` classmethod
  - Returns integer precedence value
  - Raises AbstractMethodError when not overloaded
  - _Requirements: 6.1, 6.2_

- [x] Implement `validate_item_configuration` classmethod
  - Accepts item_info dictionary parameter
  - Returns tuple containing (errors_list, warnings_list)
  - Raises AbstractMethodError when not overloaded
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

#### Helper Functions (`integrationcoupling.py`)
- [x] Implement `is_integration_coupling` function
  - Returns True for IntegrationCoupling subclasses (not base class)
  - Returns False for IntegrationCoupling base class itself
  - Returns False for non-class inputs
  - Returns False for non-IntegrationCoupling classes
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] Implement `sort_integration_couplings_by_precedence` function
  - Accepts list of IntegrationCoupling classes
  - Returns list ordered by precedence values (lowest to highest)
  - Groups couplings with same precedence value together
  - _Requirements: 6.3, 6.4, 6.5_

#### ConfigurationCoupling (`configurationcoupling.py`)
- [x] Implement `ConfigurationCoupling` class inheriting from BaseCoupling
  - Default constructor requires no arguments
  - _Requirements: 9.1, 9.2_

- [x] Implement `attach_to_environment` classmethod
  - Accepts optional constraints dictionary parameter
  - Returns without raising error (default implementation)
  - _Requirements: 9.3, 9.4, 9.5_

#### ValidatorCoupling (`validatorcoupling.py`)
- [x] Implement `ValidatorCoupling` class
  - Serves as base type for validator objects
  - _Requirements: 10.1_

- [x] Implement `attach_to_test` method
  - Accepts testscope and suffix parameters
  - Raises AbstractMethodError when not overloaded
  - _Requirements: 10.2, 10.3, 10.4_

#### Unit Tests (`test_integrationcoupling.py`)
- [x] Tests for `IntegrationCoupling` properties
  - Tests connectivity_establish and presence_establish default to False

- [x] Tests for `get_integration_key`
  - Tests expected format generation

- [x] Tests for `get_integration_key_parts`
  - Tests tuple contains correct components

- [x] Tests for abstract method enforcement
  - Tests all abstract methods raise AbstractMethodError

- [x] Tests for `is_integration_coupling`
  - Tests returns True for valid subclasses
  - Tests returns False for base class and non-coupling types

- [x] Tests for `sort_integration_couplings_by_precedence`
  - Tests ordering by precedence value

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage Enhancements
- [x] Add unit tests for `BaseCoupling`
  - Test logger property is accessible
  - Test logger is EnhancedLogger instance
  - _Requirements: 1.1, 1.3, 1.4_

- [x] Add unit tests for `ConfigurationCoupling`
  - Test default constructor
  - Test attach_to_environment with no constraints
  - Test attach_to_environment with constraints dictionary
  - _Requirements: 9.2, 9.3, 9.4, 9.5_

- [x] Add unit tests for `ValidatorCoupling`
  - Test attach_to_test raises AbstractMethodError
  - Test with derived class implementing attach_to_test
  - _Requirements: 10.2, 10.3, 10.4_

- [x] Add unit tests for integration key with None components
  - Test get_integration_key when components are None
  - Test get_integration_key_parts when components are None
  - _Requirements: 3.3_

- [x] Add unit tests for `establish_connectivity` parameter
  - Test allow_missing_devices parameter handling
  - _Requirements: 4.5_

- [x] Add unit tests for same precedence grouping
  - Test multiple couplings with identical precedence values
  - Verify they are grouped together in output
  - _Requirements: 6.5_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to all public methods
  - Document parameter types and return values
  - Add usage examples in docstrings
  - Document exception conditions

- [x] Add module-level documentation
  - Document coupling lifecycle patterns
  - Document integration with dependency injection
  - Document best practices for coupling organization

---

## Enhancement Opportunities

### Short-term Improvements

1. **Test Coverage Expansion**
   - Add tests for BaseCoupling logger initialization
   - Add tests for ConfigurationCoupling constraint handling
   - Add tests for ValidatorCoupling abstract method enforcement
   - Add tests for edge cases in integration key generation

2. **Code Quality**
   - Add type hints to all method signatures (partially complete)
   - Ensure consistent docstring format across all methods
   - Fix typo in establish_presence error message (says "diagnostic" instead of "establish_presence")

3. **Error Message Improvement**
   - Fix typo in `establish_presence` method error message
   - Current: `"The 'diagnostic' method must be overloaded..."`
   - Should be: `"The 'establish_presence' method must be overloaded..."`

4. **Function Signature Fix**
   - Fix `sort_integration_couplings_by_precedence` function signature
   - Current: `def sort_integration_couplings_by_precedence(self, coupling_list: ...)`
   - Should be: `def sort_integration_couplings_by_precedence(coupling_list: ...)` (remove `self` parameter)

### Medium-term Improvements

1. **Coupling Dependencies**
   - Add explicit dependency declarations between couplings
   - Support for dependency graph resolution
   - Automatic ordering based on dependencies

2. **Lifecycle Events**
   - Callbacks for lifecycle phase transitions
   - Support for lifecycle event listeners
   - Integration with event system

3. **Health Monitoring**
   - Periodic health checks during test execution
   - Automatic reconnection on connection loss
   - Health status reporting

### Long-term Improvements

1. **Dynamic Discovery**
   - Runtime coupling registration and discovery
   - Plugin-based coupling loading
   - Hot-reload support for development

2. **Coupling Groups**
   - Logical grouping of related couplings
   - Group-level lifecycle management
   - Shared configuration across groups

3. **Async Lifecycle**
   - Asynchronous lifecycle method support
   - Parallel coupling initialization
   - Async diagnostic collection

4. **Coupling Profiles**
   - Named coupling configurations for different environments
   - Profile inheritance and composition
   - Runtime profile switching

5. **Resource Pooling**
   - Shared resource pools across couplings
   - Connection pooling for external resources
   - Resource reuse optimization

6. **Coupling Metrics**
   - Performance metrics collection
   - Usage statistics tracking
   - Diagnostic data aggregation

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.4 | ✅ Complete | `basecoupling.py::BaseCoupling` |
| 2.1-2.5 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling` |
| 3.1-3.4 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling.get_integration_key*` |
| 4.1-4.9 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling` lifecycle methods |
| 5.1-5.5 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling.diagnostic` |
| 6.1-6.5 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling.declare_precedence`, `sort_integration_couplings_by_precedence` |
| 7.1-7.4 | ✅ Complete | `integrationcoupling.py::IntegrationCoupling.validate_item_configuration` |
| 8.1-8.5 | ✅ Complete | `integrationcoupling.py::is_integration_coupling` |
| 9.1-9.5 | ✅ Complete | `configurationcoupling.py::ConfigurationCoupling` |
| 10.1-10.4 | ✅ Complete | `validatorcoupling.py::ValidatorCoupling` |
| 11.1-11.6 | ⬜ Not Verified | Integration factory registration (in declaration module) |
| 12.1-12.6 | ⬜ Not Verified | Configuration factory registration (in declaration module) |
| 13.1-13.5 | ⬜ Not Verified | Validator factory registration (in declaration module) |
| 14.1-14.5 | ⬜ Not Verified | Coupling collection for injection (in injection module) |
| 15.1-15.4 | ⬜ Not Verified | Integration with dependency injection system |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | Property Tests |
|-----------|------------|-------------------|----------------|
| `BaseCoupling.logger` | ⬜ | ⬜ | ⬜ |
| `IntegrationCoupling.__init__` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.connectivity_establish` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.presence_establish` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.get_integration_key` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.get_integration_key_parts` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.attach_to_framework` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.attach_to_environment` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.collect_resources` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.declare_precedence` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.diagnostic` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.establish_connectivity` | ⬜ | ⬜ | ⬜ |
| `IntegrationCoupling.establish_presence` | ✅ | ⬜ | ⬜ |
| `IntegrationCoupling.validate_item_configuration` | ✅ | ⬜ | ⬜ |
| `is_integration_coupling` | ✅ | ⬜ | ⬜ |
| `sort_integration_couplings_by_precedence` | ✅ | ⬜ | ⬜ |
| `ConfigurationCoupling.__init__` | ⬜ | ⬜ | ⬜ |
| `ConfigurationCoupling.attach_to_environment` | ⬜ | ⬜ | ⬜ |
| `ValidatorCoupling.attach_to_test` | ⬜ | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial/Bug, ⬜ = Not Started, ❌ = Broken

---

## Known Issues

### Issue 1: Typo in Error Message
**Severity:** Low
**Description:** The `establish_presence` method raises an AbstractMethodError with an incorrect method name in the message.
**Location:** `integrationcoupling.py`, `establish_presence` method
**Fix:** Change the error message from:
```python
errmsg = "The 'diagnostic' method must be overloaded by derived integration coupling types."
```
to:
```python
errmsg = "The 'establish_presence' method must be overloaded by derived integration coupling types."
```

### Issue 2: Incorrect Function Signature
**Severity:** Medium
**Description:** The `sort_integration_couplings_by_precedence` function has an unnecessary `self` parameter, suggesting it was intended to be a method but is defined as a module-level function.
**Location:** `integrationcoupling.py`, `sort_integration_couplings_by_precedence` function
**Fix:** Remove the `self` parameter from the function signature:
```python
# Current (incorrect)
def sort_integration_couplings_by_precedence(self, coupling_list: List[IntegrationCoupling]) -> List[IntegrationCoupling]:

# Should be
def sort_integration_couplings_by_precedence(coupling_list: List[IntegrationCoupling]) -> List[IntegrationCoupling]:
```
**Note:** The existing test passes `None` as the first argument to work around this issue.

### Issue 3: ValidatorCoupling Missing BaseCoupling Inheritance
**Severity:** Low
**Description:** The `ValidatorCoupling` class does not inherit from `BaseCoupling`, which means it doesn't have access to the shared logger. This may be intentional if validators don't need logging, but it's inconsistent with the other coupling types.
**Location:** `validatorcoupling.py`, `ValidatorCoupling` class
**Impact:** Validators cannot use the shared logger infrastructure.
**Workaround:** Validators can create their own logger instances if needed.

### Issue 4: Missing establish_connectivity Test
**Severity:** Low
**Description:** The `establish_connectivity` abstract method is not tested in the existing test suite, unlike other abstract methods.
**Location:** `test_integrationcoupling.py`
**Impact:** No verification that `establish_connectivity` raises `AbstractMethodError` when called on base class.

---

## Integration Points

### Dependency Injection System
- `IntegrationSource`, `ConfigurationSource`, and `ValidatorSource` wrap coupling factory functions
- `ResourceOrigin` and `ValidatorOrigin` track coupling instances in the scope tree
- `InjectionRegistry` maintains tables of referenced integrations and configurations
- The `collect_integrations_and_configurations_for_injection_moment` method identifies all couplings needed for execution

### Test Declaration System
- The `@integration_factory` decorator registers integration coupling factories
- The `@configuration_factory` decorator registers configuration coupling factories
- The `@validator_factory` decorator registers validator coupling factories
- Type checking ensures correct coupling base classes are used

### Test Execution Engine
- The execution engine uses `referenced_integrations` to determine which integrations to activate
- The execution engine uses `referenced_configurations` to determine which configurations to load
- Couplings are initialized in precedence order before test execution
- Diagnostic methods are called at pre-run and post-run checkpoints

### Constraints System
- `ConfigurationCoupling.attach_to_environment` accepts optional constraints
- Constraints can be used to parameterize configuration behavior
- Integration couplings can validate item configurations against constraints

