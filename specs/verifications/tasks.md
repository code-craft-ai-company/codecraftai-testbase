# Test Verification/Assertions - Tasks Document

## Overview

This document tracks the implementation status of the Test Verification/Assertions system and identifies enhancement opportunities for future development. The verification module provides assertion and verification functions for validating test outcomes with detailed, debuggable error messages.

## Implementation Status

### Completed Tasks

#### Equality Assertions (`verification.py`)
- [x] Implement `assert_equal()` function
  - Compares found and expected values for equality
  - Raises AssertionError with formatted message on mismatch
  - Supports optional API context parameter
  - _Requirements: 1.1, 1.2, 1.5, 1.6, 1.7_

- [x] Implement `assert_not_equal()` function
  - Compares found and not_expected values for inequality
  - Raises AssertionError with formatted message on match
  - Supports optional API context parameter
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7_

#### Boolean Assertions (`verification.py`)
- [x] Implement `assert_true()` function
  - Evaluates value for truthiness
  - Raises AssertionError when value evaluates to False
  - Supports optional API context parameter
  - _Requirements: 2.1, 2.2, 2.5, 2.6_

- [x] Implement `assert_false()` function
  - Evaluates value for falsiness
  - Raises AssertionError when value evaluates to True
  - Supports optional API context parameter
  - _Requirements: 2.3, 2.4, 2.5, 2.6_

#### Comparison Assertions (`verification.py`)
- [x] Implement `assert_greater()` function
  - Compares found value against boundary
  - Raises AssertionError when found is not greater than boundary
  - Supports optional API context parameter
  - _Requirements: 3.1, 3.2, 3.5, 3.6_

- [x] Implement `assert_lessthan()` function
  - Compares found value against boundary
  - Raises AssertionError when found is not less than boundary
  - Supports optional API context parameter
  - _Requirements: 3.3, 3.4, 3.5, 3.6_

#### Type Assertions (`verification.py`)
- [x] Implement `assert_type()` function
  - Checks if found value matches expected type
  - Raises AssertionError when types don't match
  - Supports optional API context parameter
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

#### Expression Assertions (`verification.py`)
- [x] Implement `assert_expression()` function
  - Matches found string against regex pattern
  - Supports both string and compiled Pattern objects
  - Raises AssertionError when pattern doesn't match
  - Supports optional API context parameter
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

#### Dictionary Key Verification (`verification.py`)
- [x] Implement `assert_dict_response_has_keys()` function
  - Verifies dictionary contains all expected keys
  - Raises AssertionError listing missing keys
  - Supports optional API context parameter
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] Implement `verify_dict_has_keys()` function
  - Returns list of missing keys without raising exception
  - Supports optional template for formatting missing key messages
  - _Requirements: 6.5, 6.6_

#### List Length Assertions (`verification.py`)
- [x] Implement `assert_list_length()` function
  - Verifies list has exact expected length
  - Raises AssertionError with actual vs expected length
  - Includes list items in error message
  - _Requirements: 8.1, 8.2, 8.7, 8.8_

- [x] Implement `assert_list_length_greater()` function
  - Verifies list length exceeds boundary
  - Raises AssertionError when length doesn't exceed boundary
  - Includes list items in error message
  - _Requirements: 8.3, 8.4, 8.7, 8.8_

- [x] Implement `assert_list_length_less()` function
  - Verifies list length is below boundary
  - Raises AssertionError when length isn't below boundary
  - Includes list items in error message
  - _Requirements: 8.5, 8.6, 8.7, 8.8_

#### Error Message Formatting (`verification.py`)
- [x] Implement consistent error message structure
  - Uses PREFIX_STD and PREFIX_API constants
  - Applies pretty printing with pformat
  - Handles single-line and multi-line value formatting
  - Uses OS-specific line separators
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

#### Traceback Policy (`verification.py`)
- [x] Set `__traceback_format_policy__` to `TracebackFormatPolicy.Hide`
  - Excludes verification module from exception tracebacks
  - _Requirements: 10.1, 10.2, 10.3_

#### API Context Support (`verification.py`)
- [x] Implement API context customization
  - PREFIX_STD constant set to "Result"
  - PREFIX_API template formats as "'{api}' API result"
  - All assertion functions accept optional api parameter
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

#### Unit Tests (`test_verification_module.py`)
- [x] Tests for `assert_dict_response_has_keys()`
  - Tests success when keys present
  - Tests error when keys missing with API context

- [x] Tests for `verify_dict_has_keys()`
  - Tests missing key list with template
  - Tests no missing keys scenario

- [x] Tests for assertion functions
  - Tests `assert_equal()` failure message
  - Tests `assert_expression()` failure
  - Tests `assert_greater()` and `assert_lessthan()` failures
  - Tests list length assertion failures
  - Tests `assert_type()` success and failure

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Bug Fixes
- [ ] Fix `assert_not_equal()` error message formatting bug
  - Current implementation has duplicate "EXPECTED:" line before "NOT EXPECTED:"
  - Remove the erroneous "EXPECTED:" line
  - _Requirements: 1.7_

- [ ] Fix `verify_dict_has_paths()` incomplete implementation
  - Current implementation returns empty list regardless of input
  - Implement path traversal logic using `_verify_dict_has_paths_descend()`
  - Connect leaf_parts to missing_list population
  - _Requirements: 7.1, 7.2, 7.5, 7.6, 7.7_

- [ ] Fix `_verify_dict_has_paths_descend()` helper function
  - Current implementation doesn't properly accumulate path parts
  - Fix `desc_leaf_parts.extend(nxt_key)` to use `append()` instead
  - Ensure return value is used by caller
  - _Requirements: 7.6_

- [ ] Fix `assert_dict_response_has_paths()` to work with fixed verification
  - Depends on `verify_dict_has_paths()` fix
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

#### Test Coverage Enhancements
- [ ] Add unit tests for `assert_true()` and `assert_false()`
  - Test success cases with truthy/falsy values
  - Test failure cases with appropriate error messages
  - Test API context in error messages
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

- [ ] Add unit tests for `assert_not_equal()` (after bug fix)
  - Test success when values differ
  - Test failure when values match
  - Test error message formatting
  - _Requirements: 1.3, 1.4, 1.5, 1.6, 1.7_

- [ ] Add unit tests for `verify_dict_has_paths()` (after bug fix)
  - Test with simple single-level paths
  - Test with nested multi-level paths
  - Test with missing paths at various depths
  - Test path stripping of leading/trailing slashes
  - _Requirements: 7.5, 7.6, 7.7_

- [ ] Add unit tests for `assert_dict_response_has_paths()` (after bug fix)
  - Test success when all paths present
  - Test failure when paths missing
  - Test API context in error messages
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] Add edge case tests for all assertion functions
  - Test with None values
  - Test with empty collections
  - Test with complex nested structures
  - Test with Unicode and special characters
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

- [ ] Add tests for error message formatting
  - Test single-line value formatting
  - Test multi-line value formatting with indentation
  - Test consistent label usage
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6_

#### Documentation Enhancements
- [ ] Add comprehensive docstrings to all functions
  - Include parameter descriptions
  - Include return value descriptions
  - Include exception descriptions
  - Add usage examples

- [ ] Add module-level documentation
  - Document overall verification strategy
  - Document error message formatting conventions
  - Document traceback policy rationale

---

## Enhancement Opportunities

### Short-term Improvements

1. **Bug Fixes (Critical)**
   - Fix `assert_not_equal()` duplicate "EXPECTED:" line
   - Complete `verify_dict_has_paths()` implementation
   - Fix `_verify_dict_has_paths_descend()` path accumulation

2. **Test Coverage Expansion**
   - Add missing unit tests for boolean assertions
   - Add tests for path verification after bug fix
   - Add edge case tests for all functions

3. **Code Quality**
   - Remove duplicate line in `assert_not_equal()` error message
   - Ensure consistent error message formatting across all functions

### Medium-term Improvements

1. **Soft Assertions**
   - Implement assertion collector for multiple failures
   - Allow tests to continue after assertion failure
   - Report all failures at end of test

2. **Custom Comparators**
   - Support custom equality functions for `assert_equal()`
   - Support custom comparison functions for boundary checks
   - Support approximate equality for floating-point values

3. **Detailed Diff Output**
   - Show character-level differences for string comparisons
   - Show structural differences for dictionary comparisons
   - Show element differences for list comparisons

### Long-term Improvements

1. **Assertion Chaining**
   - Implement fluent API for multiple assertions
   - Support assertion grouping with descriptive names
   - Support conditional assertion execution

2. **Integration Enhancements**
   - Better integration with test result recording
   - Support for assertion metadata in reports
   - Support for assertion timing/performance tracking

3. **Extensibility**
   - Plugin architecture for custom assertion types
   - Hook system for assertion lifecycle events
   - Support for domain-specific assertion libraries

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.2 | ✅ Complete | `verification.py::assert_equal` |
| 1.3-1.4 | ⚠️ Bug | `verification.py::assert_not_equal` |
| 1.5-1.7 | ✅ Complete | `verification.py::assert_equal`, `assert_not_equal` |
| 2.1-2.6 | ✅ Complete | `verification.py::assert_true`, `assert_false` |
| 3.1-3.6 | ✅ Complete | `verification.py::assert_greater`, `assert_lessthan` |
| 4.1-4.4 | ✅ Complete | `verification.py::assert_type` |
| 5.1-5.6 | ✅ Complete | `verification.py::assert_expression` |
| 6.1-6.6 | ✅ Complete | `verification.py::assert_dict_response_has_keys`, `verify_dict_has_keys` |
| 7.1-7.7 | ❌ Incomplete | `verification.py::assert_dict_response_has_paths`, `verify_dict_has_paths` |
| 8.1-8.8 | ✅ Complete | `verification.py::assert_list_length*` |
| 9.1-9.6 | ✅ Complete | `verification.py` (error formatting) |
| 10.1-10.3 | ✅ Complete | `verification.py::__traceback_format_policy__` |
| 11.1-11.5 | ✅ Complete | `verification.py::PREFIX_STD`, `PREFIX_API` |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests | Property Tests |
|-----------|------------|-------------------|----------------|
| `assert_equal` | ✅ | ⬜ | ⬜ |
| `assert_not_equal` | ⚠️ Bug test | ⬜ | ⬜ |
| `assert_true` | ⬜ | ⬜ | ⬜ |
| `assert_false` | ⬜ | ⬜ | ⬜ |
| `assert_greater` | ✅ | ⬜ | ⬜ |
| `assert_lessthan` | ✅ | ⬜ | ⬜ |
| `assert_type` | ✅ | ⬜ | ⬜ |
| `assert_expression` | ✅ | ⬜ | ⬜ |
| `assert_dict_response_has_keys` | ✅ | ⬜ | ⬜ |
| `assert_dict_response_has_paths` | ⬜ | ⬜ | ⬜ |
| `verify_dict_has_keys` | ✅ | ⬜ | ⬜ |
| `verify_dict_has_paths` | ⬜ | ⬜ | ⬜ |
| `assert_list_length` | ✅ | ⬜ | ⬜ |
| `assert_list_length_greater` | ✅ | ⬜ | ⬜ |
| `assert_list_length_less` | ✅ | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial/Bug, ⬜ = Not Started, ❌ = Broken

---

## Known Issues

### Issue 1: `assert_not_equal()` Error Message Bug
**Severity:** Low
**Description:** The error message contains a duplicate "EXPECTED:" line before the "NOT EXPECTED:" label.
**Location:** `verification.py`, lines 476-477
**Fix:** Remove the erroneous `"EXPECTED:"` line from `err_msg_lines`.

### Issue 2: `verify_dict_has_paths()` Not Implemented
**Severity:** High
**Description:** The function returns an empty list regardless of input. The path traversal logic is not connected.
**Location:** `verification.py`, lines 530-540
**Fix:** Implement the path traversal using `_verify_dict_has_paths_descend()` and populate `missing_list`.

### Issue 3: `_verify_dict_has_paths_descend()` Path Accumulation Bug
**Severity:** High
**Description:** Uses `extend()` instead of `append()` for adding key to path parts, which would split the key into characters.
**Location:** `verification.py`, line 556
**Fix:** Change `desc_leaf_parts.extend(nxt_key)` to `desc_leaf_parts.append(nxt_key)`.
