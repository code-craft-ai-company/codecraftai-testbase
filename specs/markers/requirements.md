# Test Markers and Metadata - Requirements Document

## Introduction

The Test Markers and Metadata system provides mechanisms for annotating tests and test modules with metadata that can be used for filtering, categorization, and prioritization during test execution. The system supports both function-level markers (applied via decorators) and module-level markers (applied via descendent functions) that propagate to all tests within a module hierarchy. This enables test authors to categorize tests by functional area, tag tests with searchable keywords, assign priority levels, and filter test execution based on metadata expressions.

## Glossary

- **Marker_Decorator**: A Python decorator function that attaches metadata to a test function via the `_metadata_` attribute
- **Descendent_Marker**: A function that applies metadata to a module, propagating to all tests within that module's hierarchy
- **Metadata_Dictionary**: A dictionary stored as `_metadata_` attribute on functions or modules containing marker key-value pairs
- **MetaFilter**: A base class for metadata-based test filtering that determines whether a test should be included or excluded
- **Marker_Expression**: A string expression in the format `(+ | -) <group> (== | ~= | !=) <value>` used to specify filter criteria
- **Include_Mode**: A filter mode (indicated by `+`) where tests matching the filter are included in execution
- **Exclude_Mode**: A filter mode (indicated by `-`) where tests matching the filter are excluded from execution
- **Category**: A string label used to classify tests by functional area or test type
- **Keyword**: A searchable string tag associated with a test for discovery and filtering
- **Priority**: A numeric value (stored as string) indicating test execution priority
- **SemanticError**: An exception raised when marker expressions contain invalid syntax or semantics

## Requirements

### Requirement 1: Category Marker Application

**User Story:** As a test developer, I want to assign category labels to individual tests, so that I can classify tests by functional area and filter execution by category.

#### Acceptance Criteria

1. WHEN a function is decorated with `@mark_categories`, THE System SHALL create a `_metadata_` dictionary on the function if one does not exist
2. WHEN a function is decorated with `@mark_categories`, THE System SHALL store the categories list under the key `categories` in the `_metadata_` dictionary
3. WHEN the categories parameter is provided as a list of strings, THE System SHALL store the exact list without modification
4. THE System SHALL preserve the original function behavior after decoration
5. THE decorator SHALL accept the categories parameter as a keyword-only argument

### Requirement 2: Keyword Marker Application

**User Story:** As a test developer, I want to assign searchable keywords to individual tests, so that I can tag tests for discovery and filter execution by keyword.

#### Acceptance Criteria

1. WHEN a function is decorated with `@mark_keywords`, THE System SHALL create a `_metadata_` dictionary on the function if one does not exist
2. WHEN a function is decorated with `@mark_keywords`, THE System SHALL store the keywords list under the key `keywords` in the `_metadata_` dictionary
3. WHEN the keywords parameter is provided as a list of strings, THE System SHALL store the exact list without modification
4. THE System SHALL preserve the original function behavior after decoration
5. THE decorator SHALL accept the keywords parameter as a keyword-only argument

### Requirement 3: Priority Marker Application

**User Story:** As a test developer, I want to assign priority levels to individual tests, so that I can control execution ordering and filter tests by priority.

#### Acceptance Criteria

1. WHEN a function is decorated with `@mark_priority`, THE System SHALL create a `_metadata_` dictionary on the function if one does not exist
2. WHEN a function is decorated with `@mark_priority`, THE System SHALL store the priority value under the key `priority` in the `_metadata_` dictionary
3. WHEN the priority parameter is provided as an integer, THE System SHALL convert it to a string before storing
4. THE System SHALL preserve the original function behavior after decoration
5. THE decorator SHALL accept the priority parameter as a keyword-only argument

### Requirement 4: Descendent Category Marker Application

**User Story:** As a test developer, I want to apply category labels to all tests within a module hierarchy, so that I can classify entire test suites without decorating each test individually.

#### Acceptance Criteria

1. WHEN `mark_descendent_categories` is called, THE System SHALL inspect the call stack to identify the calling module
2. WHEN the calling module is identified, THE System SHALL create a `_metadata_` dictionary on the module if one does not exist
3. WHEN the calling module is identified, THE System SHALL store the categories list under the key `categories` in the module's `_metadata_` dictionary
4. THE categories SHALL propagate to all tests that reside under the module in scope
5. THE function SHALL accept the categories parameter as a keyword-only argument

### Requirement 5: Descendent Keyword Marker Application

**User Story:** As a test developer, I want to apply keywords to all tests within a module hierarchy, so that I can tag entire test suites without decorating each test individually.

#### Acceptance Criteria

1. WHEN `mark_descendent_keywords` is called, THE System SHALL inspect the call stack to identify the calling module
2. WHEN the calling module is identified, THE System SHALL create a `_metadata_` dictionary on the module if one does not exist
3. WHEN the calling module is identified, THE System SHALL store the keywords list under the key `keywords` in the module's `_metadata_` dictionary
4. THE keywords SHALL propagate to all tests that reside under the module in scope
5. THE function SHALL accept the keywords parameter as a keyword-only argument

### Requirement 6: Descendent Priority Marker Application

**User Story:** As a test developer, I want to apply priority levels to all tests within a module hierarchy, so that I can set default priorities for entire test suites.

#### Acceptance Criteria

1. WHEN `mark_descendent_priority` is called, THE System SHALL inspect the call stack to identify the calling module
2. WHEN the calling module is identified, THE System SHALL create a `_metadata_` dictionary on the module if one does not exist
3. WHEN the calling module is identified, THE System SHALL store the priority value under the key `priority` in the module's `_metadata_` dictionary
4. WHEN the priority parameter is provided as an integer, THE System SHALL convert it to a string before storing
5. THE priority SHALL propagate to all tests that reside under the module in scope
6. THE function SHALL accept the priority parameter as a keyword-only argument

### Requirement 7: MetaFilter Base Class

**User Story:** As a framework developer, I want a base class for metadata filters, so that different filter types can share common include/exclude logic.

#### Acceptance Criteria

1. THE MetaFilter class SHALL store an include flag indicating whether the filter is for inclusion or exclusion
2. THE MetaFilter class SHALL store a group string identifying the metadata key to filter on
3. THE MetaFilter class SHALL expose the include flag via a read-only `include` property
4. THE MetaFilter class SHALL expose the group string via a read-only `group` property
5. THE MetaFilter class SHALL define an abstract `should_include` method that derived classes must implement
6. WHEN `should_include` is called on the base class, THE System SHALL raise a NotImplementedError

### Requirement 8: Contains Filter Matching

**User Story:** As a test developer, I want to filter tests where a metadata value contains a substring or list member, so that I can select tests with partial matches.

#### Acceptance Criteria

1. WHEN `should_include` is called on MetaFilterContains with metadata containing the group key, THE System SHALL check if the value contains the filter value
2. WHEN the metadata value is a string, THE System SHALL return True if the filter value is a substring of the metadata value
3. WHEN the metadata value is a list or tuple, THE System SHALL return True if the filter value is a member of the collection
4. WHEN the metadata is None, THE System SHALL return False for include mode
5. WHEN the metadata does not contain the group key, THE System SHALL return False for include mode
6. WHEN the filter is in exclude mode, THE System SHALL invert the match result

### Requirement 9: Equals Filter Matching

**User Story:** As a test developer, I want to filter tests where a metadata value exactly equals a target value, so that I can select tests with precise matches.

#### Acceptance Criteria

1. WHEN `should_include` is called on MetaFilterEquals with metadata containing the group key, THE System SHALL check if the value exactly equals the filter value
2. WHEN the metadata value equals the filter value, THE System SHALL return True for include mode
3. WHEN the metadata value does not equal the filter value, THE System SHALL return False for include mode
4. WHEN the metadata is None, THE System SHALL return False for include mode
5. WHEN the metadata does not contain the group key, THE System SHALL return False for include mode
6. WHEN the filter is in exclude mode, THE System SHALL invert the match result

### Requirement 10: Not Equals Filter Matching

**User Story:** As a test developer, I want to filter tests where a metadata value does not equal a target value, so that I can exclude tests with specific metadata.

#### Acceptance Criteria

1. WHEN `should_include` is called on MetaFilterNotEquals, THE System SHALL first evaluate the equals condition using the parent class logic
2. THE System SHALL then invert the result of the equals evaluation
3. WHEN the metadata value equals the filter value, THE System SHALL return False for include mode
4. WHEN the metadata value does not equal the filter value, THE System SHALL return True for include mode
5. WHEN the filter is in exclude mode, THE System SHALL apply the exclude inversion after the not-equals inversion

### Requirement 11: Marker Expression Parsing

**User Story:** As a test developer, I want to specify filter criteria using string expressions, so that I can configure test filtering via command-line arguments or configuration files.

#### Acceptance Criteria

1. WHEN `parse_marker_expression` is called with a valid expression, THE System SHALL return the appropriate MetaFilter subclass instance
2. WHEN the expression starts with `+`, THE System SHALL create a filter in include mode
3. WHEN the expression starts with `-`, THE System SHALL create a filter in exclude mode
4. WHEN the expression does not start with `+` or `-`, THE System SHALL raise a SemanticError
5. WHEN the expression contains `==`, THE System SHALL create a MetaFilterEquals instance
6. WHEN the expression contains `~=`, THE System SHALL create a MetaFilterContains instance
7. WHEN the expression contains `!=`, THE System SHALL create a MetaFilterNotEquals instance
8. WHEN the expression does not contain a valid operator, THE System SHALL raise a SemanticError
9. WHEN the expression uses `==`, `~=`, or `!=` without a value component, THE System SHALL raise a SemanticError

### Requirement 12: Expression Syntax Validation

**User Story:** As a framework developer, I want marker expressions to be validated for correct syntax, so that users receive clear error messages for malformed expressions.

#### Acceptance Criteria

1. WHEN a marker expression is missing the include/exclude symbol, THE System SHALL raise a SemanticError with a message indicating the expression must begin with `+` or `-`
2. WHEN a marker expression is missing a valid operator, THE System SHALL raise a SemanticError with a message describing the expected format
3. WHEN a marker expression using `==`, `~=`, or `!=` is missing the value component, THE System SHALL raise a SemanticError indicating a value is required
4. THE error messages SHALL include the original expression for debugging purposes
5. THE System SHALL strip leading and trailing whitespace from expressions before parsing

