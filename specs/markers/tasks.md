# Test Markers and Metadata - Tasks Document

## Overview

This document tracks the implementation status of the Test Markers and Metadata system and identifies enhancement opportunities for future development. The markers module provides mechanisms for annotating tests and test modules with metadata that can be used for filtering, categorization, and prioritization during test execution.

## Implementation Status

### Completed Tasks

#### Function-Level Marker Decorators (`markers.py`)
- [x] Implement `mark_categories()` decorator
  - Creates `_metadata_` dictionary on function if not present
  - Stores categories list under `categories` key
  - Accepts categories as keyword-only argument
  - Preserves original function behavior
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] Implement `mark_keywords()` decorator
  - Creates `_metadata_` dictionary on function if not present
  - Stores keywords list under `keywords` key
  - Accepts keywords as keyword-only argument
  - Preserves original function behavior
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] Implement `mark_priority()` decorator
  - Creates `_metadata_` dictionary on function if not present
  - Stores priority as string under `priority` key
  - Converts integer priority to string before storing
  - Accepts priority as keyword-only argument
  - Preserves original function behavior
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

#### Module-Level Descendent Markers (`markers.py`)
- [x] Implement `mark_descendent_categories()` function
  - Inspects call stack to identify calling module
  - Creates `_metadata_` dictionary on module if not present
  - Stores categories list under `categories` key
  - Accepts categories as keyword-only argument
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] Implement `mark_descendent_keywords()` function
  - Inspects call stack to identify calling module
  - Creates `_metadata_` dictionary on module if not present
  - Stores keywords list under `keywords` key
  - Accepts keywords as keyword-only argument
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] Implement `mark_descendent_priority()` function
  - Inspects call stack to identify calling module
  - Creates `_metadata_` dictionary on module if not present
  - Stores priority as string under `priority` key
  - Converts integer priority to string before storing
  - Accepts priority as keyword-only argument
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

#### MetaFilter Base Class (`markers.py`)
- [x] Implement `MetaFilter` base class
  - Stores include flag for inclusion/exclusion mode
  - Stores group string for metadata key identification
  - Exposes `include` property (read-only)
  - Exposes `group` property (read-only)
  - Defines abstract `should_include()` method
  - Raises NotImplementedError when base method called
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

#### Filter Implementations (`markers.py`)
- [x] Implement `MetaFilterContains` class
  - Extends MetaFilter base class
  - Checks if metadata value contains filter value
  - Handles string values (substring match)
  - Handles list/tuple values (membership check)
  - Returns False for None metadata in include mode
  - Returns False when group key missing in include mode
  - Inverts result for exclude mode
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [x] Implement `MetaFilterEquals` class
  - Extends MetaFilter base class
  - Checks if metadata value exactly equals filter value
  - Returns True when values match in include mode
  - Returns False when values don't match in include mode
  - Returns False for None metadata in include mode
  - Returns False when group key missing in include mode
  - Inverts result for exclude mode
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

- [x] Implement `MetaFilterNotEquals` class
  - Extends MetaFilterEquals class
  - Inverts result of parent equals evaluation
  - Returns False when values match in include mode
  - Returns True when values don't match in include mode
  - Applies exclude inversion after not-equals inversion
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

#### Expression Parser (`markers.py`)
- [x] Implement `parse_marker_expression()` function
  - Parses string expressions into MetaFilter objects
  - Recognizes `+` for include mode
  - Recognizes `-` for exclude mode
  - Recognizes `==` operator (creates MetaFilterEquals)
  - Recognizes `~=` operator (creates MetaFilterContains)
  - Recognizes `!=` operator (creates MetaFilterNotEquals)
  - Strips leading/trailing whitespace from expressions
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9_

- [x] Implement expression syntax validation
  - Raises SemanticError for missing include/exclude symbol
  - Raises SemanticError for missing valid operator
  - Raises SemanticError for missing value component
  - Includes original expression in error messages
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

#### Unit Tests (`test_markers.py`)
- [x] Tests for decorator metadata attachment
  - Tests `mark_categories()` creates `_metadata_` and stores categories
  - Tests `mark_keywords()` creates `_metadata_` and stores keywords
  - Tests `mark_priority()` stores priority as string

- [x] Tests for descendent marker module modification
  - Tests `mark_descendent_categories()` modifies calling module
  - Tests `mark_descendent_keywords()` modifies calling module
  - Tests `mark_descendent_priority()` modifies calling module

- [x] Tests for MetaFilter matching
  - Tests `MetaFilterContains` include mode with list values
  - Tests `MetaFilterContains` exclude mode
  - Tests `MetaFilterEquals` exact matching
  - Tests `MetaFilterNotEquals` inverse matching

- [x] Tests for expression parsing
  - Tests parsing equals expressions
  - Tests parsing contains expressions
  - Tests parsing not-equals expressions
  - Tests error on missing include/exclude symbol
  - Tests error on invalid operator

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Bug Fixes
- [x] Fix `mark_categories()` metadata assignment bug
  - Current implementation only assigns categories when `_metadata_` doesn't exist
  - Categories assignment is inside the `if not hasattr` block
  - Move `func._metadata_["categories"] = categories` outside the if block
  - _Requirements: 1.2_

- [x] Fix `mark_keywords()` metadata assignment bug
  - Current implementation only assigns keywords when `_metadata_` doesn't exist
  - Keywords assignment is inside the `if not hasattr` block
  - Move `func._metadata_["keywords"] = keywords` outside the if block
  - _Requirements: 2.2_

- [x] Fix `mark_priority()` metadata assignment bug
  - Current implementation only assigns priority when `_metadata_` doesn't exist
  - Priority assignment is inside the `if not hasattr` block
  - Move `func._metadata_["priority"] = str(priority)` outside the if block
  - _Requirements: 3.2_

#### Test Coverage Enhancements
- [x] Add unit tests for decorator behavior with existing metadata
  - Test applying multiple decorators to same function
  - Test that existing metadata keys are preserved
  - Test that new metadata keys are added correctly
  - _Requirements: 1.1, 1.2, 2.1, 2.2, 3.1, 3.2_

- [x] Add unit tests for MetaFilterContains with string values
  - Test substring matching in string metadata values
  - Test case sensitivity behavior
  - _Requirements: 8.2_

- [x] Add unit tests for MetaFilter with None metadata
  - Test all filter types with None metadata input
  - Test all filter types with missing group key
  - _Requirements: 8.4, 8.5, 9.4, 9.5_

- [x] Add unit tests for expression parsing edge cases
  - Test expressions with extra whitespace
  - Test expressions with empty value component
  - Test expressions with special characters in values
  - _Requirements: 12.5_

- [x] Add unit tests for exclude mode behavior
  - Test MetaFilterEquals in exclude mode
  - Test MetaFilterNotEquals in exclude mode
  - Test combined include/exclude scenarios
  - _Requirements: 8.6, 9.6, 10.5_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to MetaFilter classes
  - Document constructor parameters
  - Document `should_include()` behavior
  - Add usage examples

- [x] Add module-level documentation
  - Document marker expression syntax
  - Document metadata propagation behavior
  - Document integration with test execution

---

## Enhancement Opportunities

### Short-term Improvements

1. **Bug Fixes (Critical)**
   - Fix metadata assignment in all three decorator functions
   - Ensure decorators work correctly when applied to functions with existing `_metadata_`

2. **Test Coverage Expansion**
   - Add tests for multiple decorator application
   - Add tests for edge cases in filter matching
   - Add tests for expression parsing edge cases

3. **Code Quality**
   - Ensure consistent indentation in decorator implementations
   - Add type hints to all function parameters and return values

### Medium-term Improvements

1. **Compound Expressions**
   - Support AND/OR combinations of filter expressions
   - Implement expression grouping with parentheses
   - Support negation operator for complex filters

2. **Regex Matching Filter**
   - Add `MetaFilterRegex` class for pattern matching
   - Support `=~` operator in expression parser
   - Allow regex flags in expressions

3. **Custom Metadata Keys**
   - Support user-defined metadata keys beyond categories/keywords/priority
   - Implement generic `mark_metadata()` decorator
   - Implement generic `mark_descendent_metadata()` function

### Long-term Improvements

1. **Metadata Inheritance Control**
   - Explicit control over metadata inheritance from parent modules
   - Support for metadata override vs merge behavior
   - Support for metadata exclusion at function level

2. **Priority as Integer**
   - Store priority as integer for proper numeric comparison
   - Support numeric comparison operators in expressions
   - Maintain backward compatibility with string storage

3. **Validation Framework**
   - Add validation for metadata values
   - Support valid priority ranges
   - Support valid category/keyword formats

4. **Performance Optimization**
   - Cache descendent marker lookups
   - Optimize `inspect.stack()` usage in descendent markers
   - Implement lazy metadata resolution

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.5 | ⚠️ Bug | `markers.py::mark_categories` |
| 2.1-2.5 | ⚠️ Bug | `markers.py::mark_keywords` |
| 3.1-3.5 | ⚠️ Bug | `markers.py::mark_priority` |
| 4.1-4.5 | ✅ Complete | `markers.py::mark_descendent_categories` |
| 5.1-5.5 | ✅ Complete | `markers.py::mark_descendent_keywords` |
| 6.1-6.6 | ✅ Complete | `markers.py::mark_descendent_priority` |
| 7.1-7.6 | ✅ Complete | `markers.py::MetaFilter` |
| 8.1-8.6 | ✅ Complete | `markers.py::MetaFilterContains` |
| 9.1-9.6 | ✅ Complete | `markers.py::MetaFilterEquals` |
| 10.1-10.5 | ✅ Complete | `markers.py::MetaFilterNotEquals` |
| 11.1-11.9 | ✅ Complete | `markers.py::parse_marker_expression` |
| 12.1-12.5 | ✅ Complete | `markers.py::parse_marker_expression` |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | Property Tests |
|-----------|------------|-------------------|----------------|
| `mark_categories` | ✅ | ⬜ | ⬜ |
| `mark_keywords` | ✅ | ⬜ | ⬜ |
| `mark_priority` | ✅ | ⬜ | ⬜ |
| `mark_descendent_categories` | ✅ | ⬜ | ⬜ |
| `mark_descendent_keywords` | ✅ | ⬜ | ⬜ |
| `mark_descendent_priority` | ✅ | ⬜ | ⬜ |
| `MetaFilter` | ⬜ | ⬜ | ⬜ |
| `MetaFilterContains` | ✅ | ⬜ | ⬜ |
| `MetaFilterEquals` | ✅ | ⬜ | ⬜ |
| `MetaFilterNotEquals` | ✅ | ⬜ | ⬜ |
| `parse_marker_expression` | ✅ | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial/Bug, ⬜ = Not Started, ❌ = Broken

---

## Known Issues

### Issue 1: Decorator Metadata Assignment Bug
**Severity:** High
**Description:** All three decorator functions (`mark_categories`, `mark_keywords`, `mark_priority`) have a bug where the metadata assignment is inside the `if not hasattr` block. This means if a function already has `_metadata_` from a previous decorator, the new metadata key will not be added.
**Location:** `markers.py`, lines 29-35, 46-52, 63-69
**Fix:** Move the metadata key assignment outside the `if not hasattr` block:
```python
def mark_categories(*, categories: List[str]):
    def decorator(func: Callable) -> Callable:
        if not hasattr(func, "_metadata_"):
            func._metadata_ = {}
        func._metadata_["categories"] = categories  # Move outside if block
        return func
    return decorator
```

### Issue 2: Priority Stored as String
**Severity:** Low
**Description:** The `mark_priority` decorator converts integer priority to string, which may cause unexpected behavior when comparing priorities numerically.
**Location:** `markers.py`, line 68
**Impact:** Numeric comparisons like `priority > 5` won't work as expected with string values.
**Workaround:** Use string comparison or convert back to integer when needed.

### Issue 3: Descendent Marker Performance
**Severity:** Low
**Description:** Descendent markers use `inspect.stack()` which may have performance implications in deeply nested call stacks.
**Location:** `markers.py`, lines 75, 90, 105
**Impact:** Potential slowdown during test collection in large test suites.
**Mitigation:** Consider caching or lazy evaluation for performance-critical scenarios.
