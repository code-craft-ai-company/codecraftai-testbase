# Test Discovery and Collection - Requirements Document

## Introduction

The Test Discovery and Collection system is responsible for finding, importing, filtering, and organizing test functions into a hierarchical test tree for execution. It bridges the gap between test include/exclude expressions (parsed by the Expression Parsing system) and the test execution engine (TestJob/TestSequencer). The system handles filesystem scanning, module importing, test function identification, metadata-based filtering, exclusion processing, and test tree construction. It works in conjunction with the Dependency Injection system to finalize parameter resolution and collect required integrations and configurations.

## Glossary

- **TestCollector**: The central class that orchestrates test discovery, collection, filtering, and tree construction
- **TestRef**: A lightweight reference to a test function that delays instantiation of test runtime state until execution time
- **TestGroup**: A hierarchical grouping node in the test tree, extending InjectionGroup for dependency injection support
- **Test_Tree**: A hierarchical structure of TestGroup and TestRef nodes representing the discovered test organization
- **Test_Root**: A directory marked with a `__testroot__.py` file that defines the boundary of the test package namespace
- **Include_Expression**: A string expression specifying which tests to include (parsed by Expression Parsing system)
- **Exclude_Expression**: A string expression specifying which tests to exclude
- **File_Exclusion**: An exclusion expression without `@` that targets entire files/directories by path prefix
- **Specific_Exclusion**: An exclusion expression with `@` that targets specific test classes or methods within a module
- **MetaFilter**: A metadata filter object used to include/exclude tests based on marker metadata (categories, keywords, priority)
- **Platform_Support**: A mechanism using `__platforms__.py` files to skip directories on unsupported platforms
- **Import_Error**: An error encountered when importing a test module, recorded for diagnostic reporting

## Requirements

### Requirement 1: TestCollector Initialization

**User Story:** As a framework developer, I want to initialize a test collector with root directory, exclusions, and metadata filters, so that test discovery is properly scoped.

#### Acceptance Criteria

1. THE TestCollector SHALL accept a `root` parameter specifying the root directory to scan for tests.
2. THE TestCollector SHALL accept an `excludes` parameter as a sequence of exclusion expressions.
3. THE TestCollector SHALL accept a `metafilters` parameter as a sequence of MetaFilter objects for metadata-based filtering.
4. THE TestCollector SHALL accept an optional `method_prefix` parameter (default: `"test"`) specifying the prefix that identifies test functions.
5. THE TestCollector SHALL accept an optional `test_module` parameter for the debug workflow where a single module is run directly.
6. WHEN initialized, THE TestCollector SHALL categorize exclusion expressions into file exclusions (no `@`) and specific exclusions (with `@`).
7. THE TestCollector SHALL maintain an internal dictionary of collected test references keyed by test name.
8. THE TestCollector SHALL maintain an internal dictionary of import errors keyed by file path.

### Requirement 2: Test Reference Collection

**User Story:** As a framework developer, I want to collect test references based on include expressions, so that the correct tests are discovered for execution.

#### Acceptance Criteria

1. WHEN `collect_references(expression)` is called, THE TestCollector SHALL parse the expression using `parse_test_include_expression`.
2. IF the parsed expression contains a test class component, THE TestCollector SHALL raise a SemanticError (TestBase-style tests do not support tests inside classes).
3. THE TestCollector SHALL find included files by calling `find_included_modules_under_root` with the parsed package and module expressions.
4. THE TestCollector SHALL collect test references by calling `collect_test_references` with the included files and filter expressions.
5. THE TestCollector SHALL merge newly collected references into its internal reference dictionary (extending, not replacing).
6. THE TestCollector SHALL merge newly encountered import errors into its internal import errors dictionary.
7. THE `collect_references` method SHALL be callable multiple times with different include expressions, accumulating results.

### Requirement 3: Test Function Discovery (collect_test_references)

**User Story:** As a framework developer, I want to discover test functions within Python modules, so that all matching test functions are identified for execution.

#### Acceptance Criteria

1. THE `collect_test_references` function SHALL accept: root path, included file list, filter package, filter module, filter test name, and test prefix.
2. FOR each included file, THE function SHALL compute the module name from the file path relative to the root.
3. THE function SHALL import each module (reusing `sys.modules` if already imported, otherwise using `import_by_name`).
4. THE function SHALL inspect all function members of the imported module using `inspect.getmembers(mod, inspect.isfunction)`.
5. THE function SHALL include only functions whose `__module__` matches the target module name (excluding re-exported functions).
6. THE function SHALL include only functions whose name starts with the test prefix.
7. WHEN a `filter_testname` is provided, THE function SHALL further filter using `fnmatch` glob matching against the function name.
8. FOR each matching function, THE function SHALL create a `TestRef` with the function and its async status.
9. WHEN a module import fails with `ImportError`, THE function SHALL record the error (module name, file path, traceback) and continue processing remaining files.
10. THE function SHALL return a tuple of `(test_references, import_errors)`.

### Requirement 4: File System Scanning (find_included_modules_under_root)

**User Story:** As a framework developer, I want to scan directory trees for Python test modules matching include expressions, so that the correct files are identified for import.

#### Acceptance Criteria

1. THE `find_included_modules_under_root` function SHALL accept: root directory, package expression, module expression, and excluded path prefixes.
2. WHEN package is None (single-item expression), THE function SHALL search the root directory for files or directories matching the module expression.
3. WHEN package is provided, THE function SHALL walk the directory tree matching the package path prefix, then find modules matching the module expression within matching directories.
4. THE function SHALL support glob/fnmatch patterns in both package and module expressions.
5. THE function SHALL exclude files whose paths start with any of the excluded path prefixes.
6. THE function SHALL skip `__init__.py` and `__platforms__.py` files.
7. THE function SHALL only include `.py` files.
8. THE function SHALL return a tuple of `(included_files, excluded_files)`.

### Requirement 5: Platform Support Filtering

**User Story:** As a framework developer, I want directories with `__platforms__.py` files to be skipped on unsupported platforms, so that platform-specific tests are not discovered on incompatible systems.

#### Acceptance Criteria

1. WHEN a directory contains a `__platforms__.py` file, THE function SHALL import and execute it.
2. IF the `__platforms__.py` file raises `UnSupportedPlatformError`, THE function SHALL skip the entire directory and its subdirectories.
3. IF the `__platforms__.py` file executes without error, THE function SHALL include the directory in scanning.
4. THE function SHALL cache platform support decisions per directory path to avoid redundant imports.
5. THE function SHALL check platform support for each directory level during tree walking.

### Requirement 6: Test Root Discovery

**User Story:** As a framework developer, I want to discover the test root directory by walking up from a module's location, so that module names can be correctly computed.

#### Acceptance Criteria

1. THE `find_testmodule_root` function SHALL walk up the directory tree from the module's file location.
2. THE function SHALL look for a `__testroot__.py` marker file in each directory.
3. WHEN `__testroot__.py` is found, THE function SHALL return that directory as the test root.
4. IF the filesystem root is reached without finding `__testroot__.py`, THE function SHALL raise a `ConfigurationError`.
5. THE error message SHALL indicate that test files must exist inside a test root directory marked with `__testroot__.py`.

### Requirement 7: Module Full Name Computation

**User Story:** As a framework developer, I want to compute the fully qualified module name for a test module, so that modules are correctly registered in sys.modules.

#### Acceptance Criteria

1. THE `find_testmodule_fullname` function SHALL compute the dotted module name relative to the test root's parent directory.
2. THE function SHALL accept an optional `testroot` parameter; if not provided, it SHALL discover the test root automatically.
3. THE module name SHALL include the test root directory name as the first component (e.g., `tests.package.test_module`).
4. THE function SHALL strip the `.py` extension and convert path separators to dots.

### Requirement 8: Collection Finalization

**User Story:** As a framework developer, I want to finalize the test collection by applying metadata filters and building the test tree, so that the final set of tests is ready for execution.

#### Acceptance Criteria

1. WHEN `finalize_collection()` is called, THE TestCollector SHALL build a temporary test tree from all collected references.
2. THE TestCollector SHALL call `resolve_metadata()` on the temporary tree to resolve metadata reference chains through the hierarchy.
3. WHEN metadata filters are provided, THE TestCollector SHALL filter test references by calling `is_member_of_metaset` on each TestRef against the filter collection.
4. AFTER filtering, THE TestCollector SHALL rebuild the final test tree from the filtered references.
5. THE final test tree SHALL be accessible via the `test_tree` property.

### Requirement 9: Integration and Configuration Collection

**User Story:** As a framework developer, I want to collect all referenced integrations and configurations from the test tree, so that the execution engine knows what couplings are required.

#### Acceptance Criteria

1. WHEN `collect_integrations_and_configurations()` is called, THE TestCollector SHALL add implied session resources (e.g., "sequencer") to the injection registry.
2. THE TestCollector SHALL call `injection_registry.finalize_startup` with the collected test references.
3. IF unknown parameters remain after finalization, THE TestCollector SHALL raise an `UnknownParameterError` with a detailed message listing all unresolved parameters grouped by subscriber.
4. THE TestCollector SHALL return the referenced integrations and configurations from the injection registry.

### Requirement 10: Exclusion Categorization

**User Story:** As a framework developer, I want exclusion expressions categorized into file-based and specific exclusions, so that they can be applied at the appropriate stage of discovery.

#### Acceptance Criteria

1. THE `catagorize_exclusions` function SHALL split exclusion expressions into two lists: file exclusions and specific exclusions.
2. Exclusion expressions WITHOUT an `@` character SHALL be treated as file exclusions (path prefix matching).
3. Exclusion expressions WITH an `@` character SHALL be treated as specific exclusions (targeting types/methods within modules).
4. File exclusion expressions SHALL have dots replaced with path separators for filesystem matching.

### Requirement 11: TestRef Properties

**User Story:** As a framework developer, I want test references to carry all information needed for deferred test execution, so that test runtime state is only created when needed.

#### Acceptance Criteria

1. THE TestRef SHALL extend InjectionMoment, inheriting scope name computation, parameter signature access, and metadata support.
2. THE TestRef SHALL store a reference to the test function.
3. THE TestRef SHALL store optional monikers for test variations.
4. THE TestRef SHALL store optional pivots for parameterized execution.
5. THE TestRef SHALL detect and store whether the test function is async (via `inspect.iscoroutinefunction`).
6. THE TestRef SHALL expose an `is_async` property.

### Requirement 12: TestGroup Hierarchy

**User Story:** As a framework developer, I want test groups to organize tests hierarchically by package and module, so that the test tree mirrors the source code structure.

#### Acceptance Criteria

1. THE TestGroup SHALL extend InjectionGroup, inheriting hierarchical child management and metadata resolution.
2. THE TestGroup SHALL accept a `name` and optional `package` parameter.
3. THE TestGroup SHALL support adding TestRef descendants via `add_descendent`.
4. THE `add_descendent` method SHALL create intermediate group nodes as needed based on the test's module path.
5. THE test tree root SHALL be a TestGroup named `"<session>"`.

### Requirement 13: Import Error Tracking

**User Story:** As a framework developer, I want import errors tracked and reported, so that module import failures are visible without blocking the entire test run.

#### Acceptance Criteria

1. THE TestCollector SHALL maintain a dictionary of import errors keyed by file path.
2. EACH import error record SHALL contain: module name, file path, and formatted traceback string.
3. THE TestCollector SHALL log each import error at the ERROR level.
4. Import errors SHALL NOT prevent collection of tests from other modules.
5. THE import errors SHALL be accessible via the `import_errors` property for diagnostic reporting.
