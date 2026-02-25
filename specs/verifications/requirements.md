# Test Verification/Assertions - Requirements Document

## Introduction

The Test Verification/Assertions system provides a comprehensive set of assertion and verification functions for validating test outcomes in the TestBase framework. Unlike traditional assertion libraries that simply raise exceptions on failure, this system is designed with debuggability as a primary concern, providing detailed, well-formatted error messages that clearly communicate what was expected versus what was found. The verification module serves as the primary mechanism for test authors to validate API responses, data structures, and computed values during test execution.

## Glossary

- **Assertion_Function**: A function that validates a condition and raises an AssertionError with a detailed message on failure
- **Verification_Function**: A function that performs checks without raising exceptions, returning results for further processing
- **API_Context**: An optional string parameter that identifies the API or operation being verified, used to customize error message prefixes
- **Error_Message_Prefix**: A string prefix used in error messages to identify the context of the verification (standard or API-specific)
- **TracebackFormatPolicy**: An enumeration that controls how the verification module appears in exception tracebacks
- **Expected_Value**: The value that the test expects to find
- **Found_Value**: The actual value discovered during test execution
- **Boundary_Value**: A threshold value used in comparison assertions (greater than, less than)
- **Path_Expression**: A slash-separated string representing a path through nested dictionary keys

## Requirements

### Requirement 1: Equality Verification

**User Story:** As a test developer, I want to verify that values are equal or not equal, so that I can validate API responses and computed results match expected values.

#### Acceptance Criteria

1. WHEN assert_equal is called with matching found and expected values, THE System SHALL return None without raising an exception
2. WHEN assert_equal is called with non-matching values, THE System SHALL raise an AssertionError with a descriptive message
3. WHEN assert_not_equal is called with different found and not_expected values, THE System SHALL return None without raising an exception
4. WHEN assert_not_equal is called with matching values, THE System SHALL raise an AssertionError with a descriptive message
5. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
6. WHEN no api parameter is provided, THE System SHALL use the standard "Result" prefix in error messages
7. THE error message SHALL include both the expected and found values formatted for readability

### Requirement 2: Boolean Verification

**User Story:** As a test developer, I want to verify that values evaluate to true or false, so that I can validate boolean conditions and truthiness of results.

#### Acceptance Criteria

1. WHEN assert_true is called with a value that evaluates to True, THE System SHALL return None without raising an exception
2. WHEN assert_true is called with a value that evaluates to False, THE System SHALL raise an AssertionError
3. WHEN assert_false is called with a value that evaluates to False, THE System SHALL return None without raising an exception
4. WHEN assert_false is called with a value that evaluates to True, THE System SHALL raise an AssertionError
5. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
6. THE error message SHALL include the found value formatted for readability

### Requirement 3: Comparison Verification

**User Story:** As a test developer, I want to verify that values are greater than or less than boundary values, so that I can validate numeric ranges and ordering constraints.

#### Acceptance Criteria

1. WHEN assert_greater is called with a found value greater than the boundary, THE System SHALL return None without raising an exception
2. WHEN assert_greater is called with a found value not greater than the boundary, THE System SHALL raise an AssertionError
3. WHEN assert_lessthan is called with a found value less than the boundary, THE System SHALL return None without raising an exception
4. WHEN assert_lessthan is called with a found value not less than the boundary, THE System SHALL raise an AssertionError
5. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
6. THE error message SHALL include both the boundary and found values formatted for readability

### Requirement 4: Type Verification

**User Story:** As a test developer, I want to verify that values have the expected type, so that I can validate API responses return the correct data types.

#### Acceptance Criteria

1. WHEN assert_type is called with a value matching the expected type, THE System SHALL return None without raising an exception
2. WHEN assert_type is called with a value not matching the expected type, THE System SHALL raise an AssertionError
3. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
4. THE error message SHALL include both the expected type and the found type

### Requirement 5: Expression Pattern Verification

**User Story:** As a test developer, I want to verify that string values match regular expression patterns, so that I can validate formatted strings and structured text responses.

#### Acceptance Criteria

1. WHEN assert_expression is called with a string matching the pattern, THE System SHALL return None without raising an exception
2. WHEN assert_expression is called with a string not matching the pattern, THE System SHALL raise an AssertionError
3. WHEN the expr parameter is a string, THE System SHALL compile it as a regular expression pattern
4. WHEN the expr parameter is a compiled Pattern object, THE System SHALL use it directly for matching
5. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
6. THE error message SHALL include both the found string and the expression pattern

### Requirement 6: Dictionary Key Verification

**User Story:** As a test developer, I want to verify that dictionaries contain expected keys, so that I can validate API response structures have required fields.

#### Acceptance Criteria

1. WHEN assert_dict_response_has_keys is called with a dictionary containing all expected keys, THE System SHALL return None without raising an exception
2. WHEN assert_dict_response_has_keys is called with a dictionary missing one or more expected keys, THE System SHALL raise an AssertionError
3. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
4. THE error message SHALL list each missing key individually
5. WHEN verify_dict_has_keys is called, THE System SHALL return a list of missing keys without raising an exception
6. WHEN a template parameter is provided to verify_dict_has_keys, THE System SHALL format each missing key using the template

### Requirement 7: Dictionary Path Verification

**User Story:** As a test developer, I want to verify that nested dictionaries contain expected paths, so that I can validate deeply nested API response structures.

#### Acceptance Criteria

1. WHEN assert_dict_response_has_paths is called with a dictionary containing all expected paths, THE System SHALL return None without raising an exception
2. WHEN assert_dict_response_has_paths is called with a dictionary missing one or more expected paths, THE System SHALL raise an AssertionError
3. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
4. THE error message SHALL list each missing path individually
5. WHEN verify_dict_has_paths is called, THE System SHALL return a list of missing paths without raising an exception
6. THE System SHALL support slash-separated path expressions for nested dictionary traversal
7. THE System SHALL strip leading and trailing slashes from path expressions before processing

### Requirement 8: List Length Verification

**User Story:** As a test developer, I want to verify that lists have expected lengths or meet length constraints, so that I can validate collection sizes in API responses.

#### Acceptance Criteria

1. WHEN assert_list_length is called with a list matching the expected length, THE System SHALL return None without raising an exception
2. WHEN assert_list_length is called with a list not matching the expected length, THE System SHALL raise an AssertionError
3. WHEN assert_list_length_greater is called with a list length exceeding the boundary, THE System SHALL return None without raising an exception
4. WHEN assert_list_length_greater is called with a list length not exceeding the boundary, THE System SHALL raise an AssertionError
5. WHEN assert_list_length_less is called with a list length below the boundary, THE System SHALL return None without raising an exception
6. WHEN assert_list_length_less is called with a list length not below the boundary, THE System SHALL raise an AssertionError
7. WHEN an api parameter is provided, THE System SHALL include the API name in the error message prefix
8. THE error message SHALL include the actual length, expected/boundary length, and list items

### Requirement 9: Error Message Formatting

**User Story:** As a test developer, I want assertion error messages to be well-formatted and readable, so that I can quickly understand what went wrong during test failures.

#### Acceptance Criteria

1. THE System SHALL format single-line values inline with their labels
2. THE System SHALL format multi-line values on subsequent lines with proper indentation
3. THE System SHALL use consistent label names (EXPECTED, FOUND, BOUNDARY, ITEMS, etc.)
4. THE System SHALL use pretty printing (pformat) for complex data structures
5. THE System SHALL join error message lines using the operating system's line separator
6. THE System SHALL apply consistent indentation to nested content

### Requirement 10: Traceback Policy Integration

**User Story:** As a framework developer, I want the verification module to be hidden from exception tracebacks, so that test failure stack traces focus on the test code rather than framework internals.

#### Acceptance Criteria

1. THE verification module SHALL set __traceback_format_policy__ to TracebackFormatPolicy.Hide
2. WHEN an AssertionError is raised, THE System SHALL exclude verification module frames from the traceback display
3. THE traceback policy SHALL improve readability by showing only relevant test code in stack traces

### Requirement 11: API Context Customization

**User Story:** As a test developer, I want to provide API context to assertions, so that error messages clearly identify which API call produced the failing result.

#### Acceptance Criteria

1. WHEN an api parameter is provided, THE System SHALL use the PREFIX_API template with the API name
2. WHEN no api parameter is provided, THE System SHALL use the PREFIX_STD constant
3. THE PREFIX_STD constant SHALL be "Result"
4. THE PREFIX_API template SHALL format as "'{api}' API result" where {api} is replaced with the provided API name
5. THE api parameter SHALL be optional for all assertion functions

