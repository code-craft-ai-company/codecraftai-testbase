# Test Sequence Document Generation - Requirements Document

## Introduction

The Test Sequence Document Generation system is responsible for creating executable Python modules that encode the test execution order, parameter provisioning, and scope management for TestBase test runs. These generated documents serve as the bridge between test discovery and test execution, providing a human-readable and debuggable representation of the test run structure. The system generates Python code that defines hierarchical scope functions mirroring the test tree structure, encodes parameter factory invocations for dependency injection, inserts constraint lookups for parameterized factories, supports debugger breakpoint integration, and produces reproducible and deterministic test execution flows.

## Glossary

- **TestSequencer**: The central state machine that orchestrates test discovery, collection, and execution flow, containing the sequence document generation logic
- **Sequence_Document**: A generated Python module file that defines the test execution sequence as executable code
- **Session_Method**: The entry point function `session(sequencer)` in the generated document that initiates test execution
- **Scope_Method**: A generated function `scope_{name}(sequencer, ...)` that manages execution for a specific test module
- **Test_Scope_Block**: A code block within a scope method that handles execution of an individual test
- **Module_Template**: The base Python code template (TEMPLATE_TESTRUN_SEQUENCE_MODULE) that forms the foundation of every sequence document
- **Factory_Import**: An import statement for a parameter factory function collected during generation
- **Constraint_Import**: An import statement for constraint-related modules collected during generation
- **Insertion_Point**: A marker comment in the template where imports are dynamically inserted
- **TestTree**: The hierarchical structure of discovered tests organized by package and module
- **TestGroup**: A composite node in the test tree representing a collection of tests (module or package)
- **TestRef**: A leaf node in the test tree representing an individual test reference
- **ResourceScope**: The scope object containing parameter originations for a test tree node
- **Parameter_Origination**: Metadata about a parameter's source factory function and constraints
- **Notables_Map**: A dictionary mapping parameter names to their values for parameterized tests
- **Validator_Origination**: Metadata about a validator's source factory function and attachment configuration
- **ConstraintsCatalog**: A registry for looking up constraint objects by key at runtime
- **InjectionRegistry**: The registry containing resource scope information for dependency injection
- **Breadth_First_Traversal**: The traversal pattern used to generate scope methods in order
- **Two_Pass_Generation**: The generation pattern where code is written first, then imports are inserted

## Requirements

### Requirement 1: Sequence Document File Generation

**User Story:** As a framework developer, I want to generate a sequence document file, so that test execution order is defined in an executable Python module.

#### Acceptance Criteria

1. THE TestSequencer SHALL provide a `generate_testrun_sequence_document` method that accepts an output filename parameter
2. THE TestSequencer SHALL provide an optional `indent_space` parameter defaulting to four spaces
3. WHEN `generate_testrun_sequence_document` is called, THE System SHALL create a valid Python module file at the specified path
4. WHEN generation completes, THE System SHALL store the output filename in the `_sequence_document` attribute
5. THE generated document SHALL be importable as a Python module without syntax errors

### Requirement 2: Module Template Structure

**User Story:** As a framework developer, I want a consistent module template, so that all generated documents have the same foundational structure.

#### Acceptance Criteria

1. THE generated document SHALL begin with a docstring indicating it is code-generated and should not be manually edited
2. THE generated document SHALL set `__traceback_format_policy__` to "Brief" for debugging support
3. THE generated document SHALL import the logging module and getEnhancedLogger
4. THE generated document SHALL import ConstraintsCatalog from automojo.testbase.constraints
5. THE generated document SHALL instantiate a module-level logger using getEnhancedLogger()
6. THE generated document SHALL instantiate a module-level constraints_catalog using ConstraintsCatalog()

### Requirement 3: Import Insertion Points

**User Story:** As a framework developer, I want designated insertion points for imports, so that collected imports can be placed at the correct location.

#### Acceptance Criteria

1. THE module template SHALL contain a constraint import insertion point marker: `# ------- INSERT CONSTRAINT IMPORTS HERE -------`
2. THE module template SHALL contain a factory import insertion point marker: `# ------- INSERT FACTORY IMPORTS HERE -------`
3. THE constraint import insertion point SHALL appear before the factory import insertion point
4. WHEN the final document is written, THE System SHALL replace the constraint insertion point with collected constraint imports
5. WHEN the final document is written, THE System SHALL replace the factory insertion point with collected factory imports

### Requirement 4: Two-Pass Generation Pattern

**User Story:** As a framework developer, I want a two-pass generation approach, so that forward-referenced imports can be collected and inserted correctly.

#### Acceptance Criteria

1. THE System SHALL write the initial document to a temporary file with ".tmp" extension
2. DURING the first pass, THE System SHALL collect factory imports and constraint imports into sets
3. DURING the second pass, THE System SHALL read the temporary file and write the final document
4. WHEN reading the temporary file, THE System SHALL insert collected imports at their respective insertion points
5. AFTER the final document is written, THE System SHALL remove the temporary file

### Requirement 5: Session Method Generation

**User Story:** As a framework developer, I want a session method generated as the entry point, so that test execution can be initiated from a single function.

#### Acceptance Criteria

1. THE System SHALL generate a `session(sequencer)` function as the entry point
2. THE session function SHALL include a docstring indicating it is the entry point for the test run sequence document
3. THE session function SHALL contain a `with sequencer.enter_session_scope_context() as ssc:` context manager block
4. THE session function SHALL end with a `return` statement
5. THE `_generate_session_method` SHALL return a list of child scopes to be generated

### Requirement 6: Session-Level Parameter Loops

**User Story:** As a framework developer, I want session-scoped parameters generated as loops, so that tests can be parameterized at the session level.

#### Acceptance Criteria

1. WHEN the session scope has parameter originations, THE System SHALL generate import statements for each factory function
2. WHEN the session scope has parameter originations, THE System SHALL generate `for` loops iterating over factory function calls
3. THE parameter loops SHALL be nested within the session scope context
4. THE parameter variable names SHALL be added to the child scope call arguments
5. WHEN a parameter origination is marked as implied, THE System SHALL skip generating its import and loop

### Requirement 7: Debugger Breakpoint Integration

**User Story:** As a test developer, I want debugger breakpoints inserted in the session method, so that I can debug test execution from the start.

#### Acceptance Criteria

1. WHEN AM_DEBUG_DEBUGGER runtime variable is set, THE System SHALL check for configured breakpoints
2. WHEN AM_DEBUG_BREAKPOINTS includes TESTRUN_START, THE System SHALL insert breakpoint code in the session method
3. THE breakpoint code SHALL be inserted after the docstring and before the scope context
4. THE System SHALL use `debugger_wellknown_breakpoint_code_append` to generate the breakpoint code
5. WHEN debugger is not configured, THE System SHALL not insert any breakpoint code

### Requirement 8: Child Scope Function Calls

**User Story:** As a framework developer, I want child scope function calls generated, so that the test tree hierarchy is traversed during execution.

#### Acceptance Criteria

1. FOR each child of the root node, THE System SHALL generate a function call to the corresponding scope method
2. THE scope function name SHALL follow the pattern `scope_{module_name}` with dots replaced by underscores
3. THE scope function call SHALL pass the sequencer and all session-scoped parameters as arguments
4. THE child nodes SHALL be processed in sorted order by name
5. THE System SHALL add each child scope to the scopes_called list for later generation

### Requirement 9: Scope Method Generation

**User Story:** As a framework developer, I want scope methods generated for each module, so that module-level test groupings are properly managed.

#### Acceptance Criteria

1. THE System SHALL generate a `scope_{name}(sequencer, ...)` function for each TestGroup in the tree
2. THE scope function signature SHALL include all parameters passed from parent scopes
3. THE scope function SHALL include a docstring indicating the scope name
4. THE scope function SHALL contain a `with sequencer.enter_module_scope_context("{module}")` context manager block
5. THE scope function SHALL end with a `return` statement
6. THE `_generate_scope_method` SHALL return a list of child scopes to be generated

### Requirement 10: Module-Level Parameter Loops

**User Story:** As a framework developer, I want module-scoped parameters generated as loops, so that tests can be parameterized at the module level.

#### Acceptance Criteria

1. WHEN the module scope has parameter originations, THE System SHALL add factory imports to the factory_imports set
2. WHEN the module scope has parameter originations, THE System SHALL generate `for` loops iterating over factory function calls
3. THE parameter loops SHALL be nested within the module scope context
4. THE parameter variable names SHALL be added to the child scope call arguments
5. THE factory import format SHALL be `from {module} import {function}`

### Requirement 11: Constraint Lookup Generation

**User Story:** As a framework developer, I want constraint lookups generated for parameterized factories, so that constraints are available at runtime.

#### Acceptance Criteria

1. WHEN a factory function signature includes a `constraints` parameter, THE System SHALL check for a constraints_key
2. WHEN a constraints_key is present, THE System SHALL generate a constraint lookup line
3. THE constraint lookup format SHALL be `constraints=constraints_catalog.lookup_constraints({key})`
4. WHEN the constraint is not found in the catalog, THE System SHALL raise a RuntimeError
5. WHEN no constraints_key is present, THE System SHALL remove 'constraints' from the parameter list

### Requirement 12: Breadth-First Scope Traversal

**User Story:** As a framework developer, I want scopes generated in breadth-first order, so that parent scopes are defined before child scopes.

#### Acceptance Criteria

1. THE System SHALL use a queue (scopes_called list) to track scopes to be generated
2. THE System SHALL pop scopes from the front of the queue (FIFO order)
3. WHEN a scope method is generated, THE System SHALL append its child scopes to the end of the queue
4. THE generation loop SHALL continue until the scopes_called queue is empty
5. EACH scope method SHALL be separated by a blank line in the output

### Requirement 13: Test Scope Code Generation

**User Story:** As a framework developer, I want test scope code generated for each test, so that individual tests are executed within proper scope contexts.

#### Acceptance Criteria

1. WHEN a child node is a TestRef, THE System SHALL generate a test scope code block
2. THE test scope block SHALL begin with a comment header: `# ================ Test Scope: {test_name} ================`
3. THE test scope block SHALL set a `test_scope_name` variable with the test name
4. THE test scope block SHALL contain a `with sequencer.enter_test_scope_context(test_scope_name, ...) as tscope:` context manager
5. THE test scope block SHALL import and call the test function with all required parameters

### Requirement 14: Test-Local Parameter Generation

**User Story:** As a framework developer, I want test-local parameters generated, so that tests can have parameters scoped to individual test execution.

#### Acceptance Criteria

1. WHEN a test has test-local parameter originations, THE System SHALL generate a test setup context
2. THE test setup context format SHALL be `with sequencer.enter_test_setup_context(test_scope_name) as tsetup:`
3. THE System SHALL add factory imports for test-local parameter factories to the factory_imports set
4. THE System SHALL generate `for` loops for each test-local parameter
5. THE test-local parameter loops SHALL be nested within the test setup context

### Requirement 15: Notables Map Generation

**User Story:** As a framework developer, I want notables maps generated for parameterized tests, so that parameter values can be tracked for identification.

#### Acceptance Criteria

1. WHEN a test has test-local parameters, THE System SHALL generate a notables dictionary
2. THE notables format SHALL be `notables = { 'param1': param1, 'param2': param2, }`
3. WHEN there is only one notable, THE System SHALL include a trailing comma for dict syntax
4. THE notables dictionary SHALL be passed to the test scope context as `notables=notables`
5. WHEN there are no test-local parameters, THE System SHALL not generate a notables dictionary

### Requirement 16: Test Function Import and Call

**User Story:** As a framework developer, I want test functions imported and called, so that tests are executed within their scope contexts.

#### Acceptance Criteria

1. THE System SHALL generate an import statement for the test function within the test scope context
2. THE import format SHALL be `from {module_name} import {test_name}`
3. THE System SHALL generate a function call with all required parameters
4. THE function call format SHALL be `{test_name}({param1}, {param2}, ...)`
5. THE parameters SHALL be passed in the order defined by the test function signature

### Requirement 17: Validator Integration

**User Story:** As a framework developer, I want validators integrated into test scope code, so that test validation can be performed.

#### Acceptance Criteria

1. WHEN a test scope has validator originations, THE System SHALL generate validator construction code
2. THE validator code SHALL be wrapped in a try/finally block
3. THE System SHALL add factory imports for validator factories to the factory_imports set
4. THE System SHALL generate validator construction calls with constraint lookups if needed
5. THE System SHALL generate `{validator}.attach_to_test(tscope, '{suffix}')` calls for each validator

### Requirement 18: Validator Finalization

**User Story:** As a framework developer, I want validator finalization code generated, so that validators are properly cleaned up after test execution.

#### Acceptance Criteria

1. WHEN validators are present, THE System SHALL generate a finally block after the test call
2. THE finally block SHALL contain `{validator}.finalize()` calls for each validator
3. THE validators SHALL be finalized in reverse order of construction
4. THE test function call SHALL be within the try block
5. THE validator finalization SHALL execute regardless of test outcome

### Requirement 19: Factory Import Collection

**User Story:** As a framework developer, I want factory imports collected during generation, so that all required imports are included in the document.

#### Acceptance Criteria

1. THE System SHALL maintain a set of factory imports during generation
2. THE System SHALL add imports for session-scoped parameter factories
3. THE System SHALL add imports for module-scoped parameter factories
4. THE System SHALL add imports for test-local parameter factories
5. THE System SHALL add imports for validator factories
6. THE import set SHALL prevent duplicate imports

### Requirement 20: Constraint Import Collection

**User Story:** As a framework developer, I want constraint imports collected during generation, so that constraint-related modules are available.

#### Acceptance Criteria

1. THE System SHALL maintain a set of constraint imports during generation
2. WHEN a constraint lookup is generated, THE System SHALL add the relevant constraint import
3. THE constraint imports SHALL be inserted at the constraint insertion point
4. THE import set SHALL prevent duplicate imports
5. THE constraint imports SHALL appear before factory imports in the final document

### Requirement 21: Code Indentation Management

**User Story:** As a framework developer, I want proper code indentation, so that the generated document is readable and valid Python.

#### Acceptance Criteria

1. THE System SHALL use the configured indent_space for all indentation
2. THE System SHALL track the current indentation level during generation
3. WHEN entering a context manager or loop, THE System SHALL increase indentation
4. WHEN exiting a context manager or loop, THE System SHALL decrease indentation
5. THE default indentation SHALL be four spaces

### Requirement 22: Line Separator Handling

**User Story:** As a framework developer, I want proper line separators, so that the generated document works across platforms.

#### Acceptance Criteria

1. THE System SHALL use `os.linesep` for line separators when joining method lines
2. THE System SHALL write blank lines between scope methods
3. THE System SHALL write blank lines between logical sections within methods
4. THE method content SHALL be joined using `os.linesep.join(method_lines)`
5. THE final document SHALL use consistent line endings

### Requirement 23: Test Tree Node Type Handling

**User Story:** As a framework developer, I want different node types handled correctly, so that both test groups and test references are processed appropriately.

#### Acceptance Criteria

1. WHEN a child node is a TestRef, THE System SHALL generate test scope code
2. WHEN a child node is a TestGroup, THE System SHALL generate a child scope function call
3. THE System SHALL use `isinstance(child_node, TestRef)` to determine node type
4. THE child nodes SHALL be processed in sorted order by name
5. THE System SHALL handle mixed TestRef and TestGroup children within a scope

### Requirement 24: Scope Module Name Construction

**User Story:** As a framework developer, I want scope module names constructed correctly, so that scopes can be identified and located.

#### Acceptance Criteria

1. THE scope module name SHALL include the package prefix if present
2. THE scope module format SHALL be `{package}.{module}` when package exists
3. THE scope module format SHALL be `{module}` when no package exists
4. THE scope function name SHALL replace dots with underscores: `scope_{module_name.replace('.', '_')}`
5. THE scope module name SHALL be passed to `enter_module_scope_context`

### Requirement 25: Parameter Source Function Calls

**User Story:** As a framework developer, I want parameter source function calls generated correctly, so that parameters are created at runtime.

#### Acceptance Criteria

1. THE System SHALL call `porigin.generate_call()` to generate the factory function call
2. WHEN constraints are required, THE System SHALL pass the constraints to `generate_call(constraints=...)`
3. THE generated call SHALL be used in the `for` loop: `for {param} in {call}:`
4. THE System SHALL handle factory functions with and without constraints parameters
5. THE System SHALL use the parameter origination's source_function_name for the call

### Requirement 26: Import Error Recording

**User Story:** As a framework developer, I want import errors recorded, so that module import failures can be diagnosed.

#### Acceptance Criteria

1. THE TestSequencer SHALL provide a `record_import_errors` method that accepts an output filename
2. THE method SHALL write import errors to the specified file
3. EACH import error record SHALL include module name, filename, and traceback
4. THE records SHALL be separated by JSOS CHAR_RECORD_SEPERATOR
5. THE import errors SHALL be formatted as JSON objects

### Requirement 27: Sequence Document Storage

**User Story:** As a framework developer, I want the sequence document path stored, so that it can be accessed for execution.

#### Acceptance Criteria

1. AFTER generation completes, THE System SHALL store the output filename in `_sequence_document`
2. THE `execute_tests` method SHALL verify `_sequence_document` is not None before execution
3. IF `_sequence_document` is None during execution, THE System SHALL raise a SemanticError
4. THE error message SHALL indicate that `generate_testrun_sequence_document` must be called first
5. THE stored path SHALL be used to import the sequence document module

### Requirement 28: Generated Code Executability

**User Story:** As a framework developer, I want the generated code to be executable, so that tests can be run from the sequence document.

#### Acceptance Criteria

1. THE generated document SHALL be importable using `import_file`
2. THE generated document SHALL have a callable `session` function
3. THE `session` function SHALL accept a sequencer parameter
4. WHEN `session(sequencer)` is called, THE System SHALL execute all tests in the defined order
5. THE generated code SHALL not have any syntax errors or undefined references

### Requirement 29: Resource Scope Integration

**User Story:** As a framework developer, I want resource scopes queried during generation, so that parameter originations are correctly identified.

#### Acceptance Criteria

1. THE System SHALL call `scope_node.get_resource_scope()` to obtain the resource scope
2. THE System SHALL iterate over `resource_scope.parameter_originations` for parameter loops
3. THE System SHALL query `injection_registry.lookup_resource_scope(test_scope_name)` for test scopes
4. THE System SHALL access `test_scope.validator_originations` for validator integration
5. THE System SHALL check `porigin.implied` to skip implied parameters

### Requirement 30: Temporary File Cleanup

**User Story:** As a framework developer, I want temporary files cleaned up, so that no artifacts remain after generation.

#### Acceptance Criteria

1. THE System SHALL create a temporary file with ".tmp" extension during generation
2. AFTER the final document is written, THE System SHALL remove the temporary file using `os.remove`
3. THE temporary file path SHALL be `{outputfilename}.tmp`
4. THE cleanup SHALL occur after successful generation
5. IF an error occurs during generation, THE temporary file may remain for debugging

