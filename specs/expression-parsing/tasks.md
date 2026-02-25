# Expression Parsing - Tasks Document

## Overview

This document tracks the implementation status of the Expression Parsing system and identifies enhancement opportunities for future development. The expression parsing system provides a mechanism for parsing test include expressions that specify which tests to run in the TestBase framework. These expressions follow a structured format that identifies test packages, modules, test classes, and individual test methods.

## Implementation Status

### Completed Tasks

#### Expression Parser Function (`expressions.py`)
- [x] Implement `parse_test_include_expression` function
  - Accept `expression` parameter of type string
  - Accept `testmodule` parameter of type Optional[ModuleType]
  - Accept `method_prefix` parameter with default value "test"
  - Return tuple of four Optional[str] values: (expr_package, expr_module, expr_testclass, expr_testname)
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

#### CLI Workflow Full Expression Parsing
- [x] Implement CLI workflow parsing (when testmodule is None)
  - Split on `#` to extract testname component
  - Split on `@` to extract testclass component
  - Split on `.` to extract package and module components
  - Parse expression from right to left using delimiter precedence: `#` then `@` then `.`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

#### CLI Workflow Package and Module Extraction
- [x] Implement package and module extraction
  - Treat all components except the last as the package when multiple `.` delimiters present
  - Treat the last component as the module
  - Set package to None and module to identifier when single identifier with no `.`
  - Support nested package paths (e.g., `pkg.subpkg.mod`)
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

#### CLI Workflow TestClass Extraction
- [x] Implement testclass extraction
  - Extract testclass component after `@` delimiter
  - Set testclass to None when testclass component is empty string
  - Set testclass to None when expression does not contain `@`
  - _Requirements: 4.1, 4.2, 4.3_

#### CLI Workflow TestName Extraction
- [x] Implement testname extraction
  - Extract testname component after `#` delimiter
  - Set testname to None when expression does not contain `#`
  - Extract testname before processing other delimiters
  - _Requirements: 5.1, 5.2, 5.3_

#### Method Prefix Validation
- [x] Implement method prefix validation
  - Verify testname starts with method_prefix
  - Raise ValueError when testname does not start with method_prefix
  - Include method_prefix value and expression in error message
  - Default method_prefix is "test"
  - Support custom method prefixes
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

#### Module Workflow Expression Parsing
- [x] Implement module workflow parsing (when testmodule is not None)
  - Extract package and module from testmodule object
  - Use `testmodule.__name__` to determine module's full path
  - Split module name to extract package and module components
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

#### Module Workflow Expression Restrictions
- [x] Implement module workflow expression restrictions
  - Raise ValueError when expression contains `.`
  - Raise ValueError when expression contains `@`
  - Raise ValueError when expression contains `:`
  - Include descriptive error message
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

#### Module Workflow Wildcard Support
- [x] Implement wildcard support in module workflow
  - Set testclass to None when expression is `*`
  - Match all tests in module with wildcard expression
  - _Requirements: 9.1, 9.2, 9.3_

#### Module Workflow __main__ Handling
- [x] Implement __main__ module name handling
  - Set expr_package to "*" when testmodule.__name__ is "__main__"
  - Set expr_module to "*" when testmodule.__name__ is "__main__"
  - _Requirements: 10.1, 10.2, 10.3_

#### Module Workflow TestClass and TestName Extraction
- [x] Implement testclass and testname extraction in module workflow
  - Extract testname component when expression contains `#`
  - Treat expression as testclass when not `*`
  - Apply method_prefix validation to testnames
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

#### Expression Format Support
- [x] Support various expression formats
  - `pkg.mod` format (package and module only)
  - `pkg.mod@TestClass` format (with test class)
  - `pkg.mod@TestClass#test_demo` format (full specification)
  - `pkg.mod@#test_demo` format (test name without class)
  - `pkg.subpkg.mod` format (nested packages)
  - `mod` format (module only, no package)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

#### Error Message Quality
- [x] Implement descriptive error messages
  - Include function name for context (`parse_test_include_expression:`)
  - Describe constraint that was violated
  - Include relevant parameter values for debugging
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

#### Return Value Consistency
- [x] Implement consistent return values
  - Always return tuple of exactly four elements
  - Each element is either string or None
  - Set corresponding tuple element to None when component not specified
  - Maintain tuple order: (expr_package, expr_module, expr_testclass, expr_testname)
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

#### Integration with TestCollector
- [x] Integrate with TestCollector
  - Output compatible with TestCollector's test filtering logic
  - expr_package usable for package-level filtering
  - expr_module usable for module-level filtering
  - expr_testclass usable for test class filtering
  - expr_testname usable for individual test filtering
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Test Coverage
- [x] Add unit tests for module workflow invalid expression rejection
  - Test expression with `.` raises ValueError
  - Test expression with `@` raises ValueError
  - Test expression with `:` raises ValueError
  - Verify error message content
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] Add unit tests for module workflow package/module extraction
  - Test extraction from simple module name (e.g., `pkg.mod`)
  - Test extraction from nested package (e.g., `pkg.subpkg.mod`)
  - Test extraction from single-component module name
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] Add unit tests for module workflow wildcard expression
  - Test `*` expression sets testclass to None
  - Test `*` expression preserves package and module from testmodule
  - _Requirements: 9.1, 9.2, 9.3_

- [x] Add unit tests for module workflow __main__ handling
  - Test __main__ module sets package to "*"
  - Test __main__ module sets module to "*"
  - _Requirements: 10.1, 10.2, 10.3_

- [x] Add unit tests for module workflow testclass/testname extraction
  - Test `TestClass#test_method` expression
  - Test `TestClass` expression (no testname)
  - Test `#test_method` expression (no testclass)
  - _Requirements: 11.1, 11.2, 11.3, 11.4_

- [x] Add unit tests for CLI workflow full expression parsing
  - Test `pkg.mod@TestClass#test_demo` format
  - Test `pkg.subpkg.mod@TestClass#test_demo` format
  - Verify all four components extracted correctly
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] Add unit tests for CLI workflow partial expressions
  - Test `pkg.mod` format (package and module only)
  - Test `pkg.mod@TestClass` format (no testname)
  - Test `pkg.mod@#test_demo` format (no testclass)
  - Test `mod` format (module only)
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] Add unit tests for method prefix validation
  - Test default "test" prefix validation
  - Test custom prefix validation (e.g., "check", "verify")
  - Test invalid prefix raises ValueError
  - Verify error message includes prefix and expression
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] Add unit tests for return value consistency
  - Verify tuple always has four elements
  - Verify None returned for unspecified components
  - Verify tuple order is consistent
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

#### Integration Testing
- [x] Add integration tests for TestCollector expression parsing
  - Test expression parsing in collect_references flow
  - Verify parsed components used for test filtering
  - Test various expression formats with actual test discovery
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5_

- [x] Add integration tests for CLI expression parsing
  - Test expression parsing from command-line arguments
  - Verify end-to-end test selection with expressions
  - Test error handling for invalid expressions
  - _Requirements: 2.1-2.5, 12.1-12.6_

- [x] Add integration tests for debug/script workflow
  - Test expression parsing with actual module objects
  - Verify test selection in debug workflow
  - Test __main__ module handling
  - _Requirements: 7.1-7.4, 10.1-10.3_

#### Documentation Enhancements
- [x] Add comprehensive docstrings to parse_test_include_expression
  - Document all parameters with types and descriptions
  - Document return value format
  - Include usage examples for both workflows
  - Document error conditions and messages

- [x] Add inline code comments for complex logic
  - Document delimiter precedence parsing
  - Document module workflow restrictions
  - Document __main__ handling rationale

- [x] Create usage examples in `source/examples/`
  - CLI expression parsing examples
  - Debug/script workflow examples
  - Custom method prefix examples
  - Error handling examples

#### Feature Enhancements
- [ ] Support for expression validation without parsing
  - Add `validate_test_include_expression` function
  - Return boolean indicating validity
  - Provide detailed validation error messages

- [ ] Support for expression building
  - Add `build_test_include_expression` function
  - Accept package, module, testclass, testname parameters
  - Return properly formatted expression string

- [ ] Support for expression normalization
  - Add `normalize_test_include_expression` function
  - Standardize expression format
  - Handle equivalent expressions consistently

- [ ] Support for expression pattern matching
  - Add wildcard support in CLI workflow
  - Support glob patterns for package/module matching
  - Support regex patterns for test name matching

- [ ] Support for expression completion
  - Add `complete_test_include_expression` function
  - Provide suggestions for partial expressions
  - Support IDE integration for expression completion

---

## Enhancement Opportunities

### Short-term Improvements

1. **Expression Validation Function**
   - Add standalone validation without full parsing
   - Return structured validation results
   - Support batch validation of multiple expressions

2. **Expression Builder Function**
   - Programmatically construct expressions
   - Ensure proper formatting and escaping
   - Support incremental expression building

3. **Improved Error Messages**
   - Add suggestions for fixing invalid expressions
   - Include valid expression format examples
   - Support localized error messages

### Medium-term Improvements

1. **Wildcard Support in CLI Workflow**
   - Support `*` for package matching
   - Support `*` for module matching
   - Support `*` for testclass matching

2. **Expression Caching**
   - Cache parsed expressions for repeated use
   - Invalidate cache on expression change
   - Support configurable cache size

3. **Expression Serialization**
   - Serialize parsed expressions to JSON
   - Deserialize expressions from JSON
   - Support expression persistence

### Long-term Improvements

1. **Expression Query Language**
   - Support complex expression queries
   - Enable boolean operators (AND, OR, NOT)
   - Support expression grouping

2. **Expression Analysis Tools**
   - Analyze expression coverage
   - Identify overlapping expressions
   - Optimize expression sets

3. **Expression Migration Tools**
   - Convert expressions between formats
   - Support legacy expression formats
   - Provide migration guidance

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.5 | ✅ Complete | `expressions.py::parse_test_include_expression` |
| 2.1-2.5 | ✅ Complete | CLI workflow parsing logic |
| 3.1-3.4 | ✅ Complete | Package/module extraction logic |
| 4.1-4.3 | ✅ Complete | TestClass extraction logic |
| 5.1-5.3 | ✅ Complete | TestName extraction logic |
| 6.1-6.5 | ✅ Complete | Method prefix validation |
| 7.1-7.4 | ✅ Complete | Module workflow parsing logic |
| 8.1-8.4 | ✅ Complete | Module workflow restrictions |
| 9.1-9.3 | ✅ Complete | Wildcard support |
| 10.1-10.3 | ✅ Complete | __main__ handling |
| 11.1-11.4 | ✅ Complete | Module workflow testclass/testname extraction |
| 12.1-12.6 | ✅ Complete | Expression format support |
| 13.1-13.4 | ✅ Complete | Error message quality |
| 14.1-14.4 | ✅ Complete | Return value consistency |
| 15.1-15.5 | ✅ Complete | TestCollector integration |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| Module workflow invalid expression | ✅ | N/A |
| Module workflow package/module extraction | ✅ | ⬜ |
| Module workflow wildcard | ✅ | ⬜ |
| Module workflow __main__ handling | ⬜ | ⬜ |
| Module workflow testclass/testname | ⬜ | ⬜ |
| CLI workflow full expression | ✅ | ⬜ |
| CLI workflow partial expressions | ✅ | ⬜ |
| Method prefix validation | ✅ | ⬜ |
| Return value consistency | ⬜ | ⬜ |
| TestCollector integration | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## Known Limitations

1. **No Wildcard Support in CLI Workflow**: CLI expressions do not support wildcards for package/module matching
2. **No Expression Validation Function**: No standalone validation without full parsing
3. **No Expression Builder Function**: No programmatic expression construction
4. **No Expression Caching**: Expressions are parsed on every call
5. **No Complex Query Support**: No boolean operators or expression grouping
6. **Limited Test Coverage**: Some edge cases and integration scenarios not yet tested
7. **No Expression Completion**: No IDE integration for expression suggestions

---

## File Structure

```
source/packages/automojo/testbase/
├── expressions.py              # parse_test_include_expression function
└── testcollector.py            # TestCollector using expression parser

source/tests/automojo_tests/testbase/
└── test_expressions.py         # Unit tests for expression parsing

source/examples/
└── debug_expressions.py        # Example usage of expressions (planned)
```
