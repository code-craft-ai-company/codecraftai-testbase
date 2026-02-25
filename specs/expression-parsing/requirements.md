# Expression Parsing - Requirements Document

## Introduction

The Expression Parsing system provides a mechanism for parsing test include expressions that specify which tests to run in the TestBase framework. These expressions follow a structured format that identifies test packages, modules, test classes, and individual test methods. The parser supports two primary workflows: command-line test execution where full expressions are parsed, and single-module debugging/scripting where simplified expressions are used with an associated test module object. The system enables flexible test selection through a grammar that supports wildcards, partial specifications, and hierarchical test targeting.

## Glossary

- **Expression_Parser**: The `parse_test_include_expression` function that parses test include expressions into component parts
- **Test_Include_Expression**: A string expression in the format `(package).(module)@(testclass)#(testname)` that specifies which tests to include
- **Package_Expression**: The package component of an expression, representing the Python package path (e.g., `pkg.subpkg`)
- **Module_Expression**: The module component of an expression, representing the Python module name
- **TestClass_Expression**: The test class component of an expression, representing a TestContainer-derived class name
- **TestName_Expression**: The test name component of an expression, representing an individual test method name
- **Method_Prefix**: The string prefix that identifies test methods (default: "test")
- **CLI_Workflow**: The command-line workflow where `testmodule` is None and full expressions are parsed
- **Module_Workflow**: The debug/script workflow where `testmodule` is provided and simplified expressions are used
- **Wildcard_Expression**: The `*` character used to match all tests in a module during module workflow
- **TestModule**: A Python module object containing tests, passed during debug/script workflows
- **TestCollector**: The component that uses parsed expressions to discover and filter tests
- **Delimiter**: Special characters (`#`, `@`, `.`) used to separate expression components

## Requirements

### Requirement 1: Expression Parser Function Interface

**User Story:** As a framework developer, I want a function to parse test include expressions, so that I can extract the package, module, test class, and test name components for test discovery.

#### Acceptance Criteria

1. THE Expression_Parser SHALL provide a `parse_test_include_expression` function
2. THE function SHALL accept an `expression` parameter of type string
3. THE function SHALL accept a `testmodule` parameter of type Optional[ModuleType]
4. THE function SHALL accept a `method_prefix` parameter of type string with default value "test"
5. THE function SHALL return a tuple of four Optional[str] values: (expr_package, expr_module, expr_testclass, expr_testname)

### Requirement 2: CLI Workflow Full Expression Parsing

**User Story:** As a test developer, I want to specify full test include expressions on the command line, so that I can target specific tests at any level of the test hierarchy.

#### Acceptance Criteria

1. WHEN testmodule is None, THE Expression_Parser SHALL parse the expression as a CLI workflow expression
2. WHEN the expression contains `#`, THE Expression_Parser SHALL split on `#` to extract the testname component
3. WHEN the expression contains `@`, THE Expression_Parser SHALL split on `@` to extract the testclass component
4. WHEN the expression contains `.`, THE Expression_Parser SHALL split on `.` to extract package and module components
5. THE Expression_Parser SHALL parse the expression from right to left using delimiter precedence: `#` then `@` then `.`

### Requirement 3: CLI Workflow Package and Module Extraction

**User Story:** As a test developer, I want to specify package and module paths in expressions, so that I can target tests within specific packages or modules.

#### Acceptance Criteria

1. WHEN the expression contains multiple `.` delimiters, THE Expression_Parser SHALL treat all components except the last as the package
2. WHEN the expression contains multiple `.` delimiters, THE Expression_Parser SHALL treat the last component as the module
3. WHEN the expression contains a single identifier with no `.`, THE Expression_Parser SHALL set package to None and module to the identifier
4. THE Expression_Parser SHALL support nested package paths (e.g., `pkg.subpkg.mod` yields package=`pkg.subpkg`, module=`mod`)

### Requirement 4: CLI Workflow TestClass Extraction

**User Story:** As a test developer, I want to specify test classes in expressions, so that I can target all tests within a specific test class.

#### Acceptance Criteria

1. WHEN the expression contains `@`, THE Expression_Parser SHALL extract the testclass component after the `@` delimiter
2. WHEN the testclass component is an empty string (e.g., `pkg.mod@#test_demo`), THE Expression_Parser SHALL set testclass to None
3. WHEN the expression does not contain `@`, THE Expression_Parser SHALL set testclass to None

### Requirement 5: CLI Workflow TestName Extraction

**User Story:** As a test developer, I want to specify individual test names in expressions, so that I can run a single specific test.

#### Acceptance Criteria

1. WHEN the expression contains `#`, THE Expression_Parser SHALL extract the testname component after the `#` delimiter
2. WHEN the expression does not contain `#`, THE Expression_Parser SHALL set testname to None
3. THE testname component SHALL be extracted before processing other delimiters

### Requirement 6: Method Prefix Validation

**User Story:** As a framework developer, I want test names validated against the method prefix, so that invalid test names are rejected early.

#### Acceptance Criteria

1. WHEN a testname is extracted, THE Expression_Parser SHALL verify it starts with the method_prefix
2. IF the testname does not start with the method_prefix, THEN THE Expression_Parser SHALL raise a ValueError
3. THE error message SHALL include the method_prefix value and the expression for debugging
4. THE default method_prefix SHALL be "test"
5. THE Expression_Parser SHALL support custom method prefixes (e.g., "check", "verify")

### Requirement 7: Module Workflow Expression Parsing

**User Story:** As a test developer, I want to use simplified expressions when debugging a test module, so that I can quickly run specific tests without specifying the full path.

#### Acceptance Criteria

1. WHEN testmodule is not None, THE Expression_Parser SHALL parse the expression as a module workflow expression
2. WHEN testmodule is provided, THE Expression_Parser SHALL extract package and module from the testmodule object
3. THE Expression_Parser SHALL use `testmodule.__name__` to determine the module's full path
4. WHEN the module name contains `.`, THE Expression_Parser SHALL split to extract package and module components

### Requirement 8: Module Workflow Expression Restrictions

**User Story:** As a framework developer, I want module workflow expressions restricted to simple formats, so that ambiguous expressions are rejected.

#### Acceptance Criteria

1. WHEN testmodule is provided AND the expression contains `.`, THEN THE Expression_Parser SHALL raise a ValueError
2. WHEN testmodule is provided AND the expression contains `@`, THEN THE Expression_Parser SHALL raise a ValueError
3. WHEN testmodule is provided AND the expression contains `:`, THEN THE Expression_Parser SHALL raise a ValueError
4. THE error message SHALL indicate that module workflow expressions should only have test class and test method

### Requirement 9: Module Workflow Wildcard Support

**User Story:** As a test developer, I want to use wildcards in module workflow, so that I can run all tests in the current module.

#### Acceptance Criteria

1. WHEN testmodule is provided AND the expression is `*`, THE Expression_Parser SHALL set testclass to None
2. WHEN the expression is `*`, THE Expression_Parser SHALL match all tests in the module
3. THE wildcard expression SHALL be valid only in module workflow (when testmodule is provided)

### Requirement 10: Module Workflow __main__ Handling

**User Story:** As a test developer, I want to run tests from a module executed as __main__, so that I can debug tests by running the module directly.

#### Acceptance Criteria

1. WHEN testmodule.__name__ is "__main__", THE Expression_Parser SHALL set expr_package to "*"
2. WHEN testmodule.__name__ is "__main__", THE Expression_Parser SHALL set expr_module to "*"
3. THE wildcard values SHALL enable test discovery to scan for tests without exact path matching

### Requirement 11: Module Workflow TestClass and TestName Extraction

**User Story:** As a test developer, I want to specify test class and test name in module workflow, so that I can target specific tests within the current module.

#### Acceptance Criteria

1. WHEN testmodule is provided AND the expression contains `#`, THE Expression_Parser SHALL extract the testname component
2. WHEN testmodule is provided AND the expression is not `*`, THE Expression_Parser SHALL treat the expression as the testclass
3. THE testname extraction SHALL occur before testclass determination
4. THE method_prefix validation SHALL apply to testnames in module workflow

### Requirement 12: Expression Format Support

**User Story:** As a test developer, I want various expression formats supported, so that I can flexibly specify tests at different granularities.

#### Acceptance Criteria

1. THE Expression_Parser SHALL support `pkg.mod` format (package and module only)
2. THE Expression_Parser SHALL support `pkg.mod@TestClass` format (with test class)
3. THE Expression_Parser SHALL support `pkg.mod@TestClass#test_demo` format (full specification)
4. THE Expression_Parser SHALL support `pkg.mod@#test_demo` format (test name without class)
5. THE Expression_Parser SHALL support `pkg.subpkg.mod` format (nested packages)
6. THE Expression_Parser SHALL support `mod` format (module only, no package)

### Requirement 13: Error Message Quality

**User Story:** As a test developer, I want descriptive error messages, so that I can quickly identify and fix invalid expressions.

#### Acceptance Criteria

1. THE error messages SHALL include the function name for context (`parse_test_include_expression:`)
2. THE error messages SHALL describe the constraint that was violated
3. THE error messages SHALL include relevant parameter values for debugging
4. WHEN method_prefix validation fails, THE error message SHALL include both the method_prefix and expression values

### Requirement 14: Return Value Consistency

**User Story:** As a framework developer, I want consistent return values, so that consumers can reliably process parsed expressions.

#### Acceptance Criteria

1. THE Expression_Parser SHALL always return a tuple of exactly four elements
2. EACH element in the tuple SHALL be either a string or None
3. WHEN a component is not specified in the expression, THE corresponding tuple element SHALL be None
4. THE tuple order SHALL be: (expr_package, expr_module, expr_testclass, expr_testname)

### Requirement 15: Integration with TestCollector

**User Story:** As a framework developer, I want the parser to integrate with TestCollector, so that parsed expressions can be used for test discovery.

#### Acceptance Criteria

1. THE Expression_Parser output SHALL be compatible with TestCollector's test filtering logic
2. THE expr_package value SHALL be usable for package-level filtering in find_included_modules_under_root
3. THE expr_module value SHALL be usable for module-level filtering
4. THE expr_testclass value SHALL be usable for test class filtering in collect_test_references
5. THE expr_testname value SHALL be usable for individual test filtering

