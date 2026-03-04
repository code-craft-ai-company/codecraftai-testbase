# Property Testing - Requirements Document

## Introduction

The Property Testing feature adds first-class support for property-based testing to the TestBase framework.
Property-based tests verify invariants against randomly generated inputs rather than hand-crafted examples,
enabling broader coverage and automated edge-case discovery. The implementation uses only Python standard
library modules (no third-party dependencies such as Hypothesis) and integrates with the existing TestBase
lifecycle: test discovery, injection, scoping, result recording, and agent tooling.

Property tests produce a single test result per `test_` function (1-to-1 model), preserving test count
stability for CI/CD monitoring. Individual generated examples are recorded as `CheckResult` sub-results
attached to the parent test result, following the same structural pattern used by `TaskingResult` entries
for tasking-based tests.

## Glossary

- **Property**: An invariant or law that should hold true for all valid inputs to a function under test
- **Strategy**: A composable generator that produces random values of a specific type for property-based testing
- **Shrinking**: The process of reducing a failing input to a minimal counterexample that still demonstrates the failure
- **Check_Result**: A sub-result attached to a test result representing the outcome of a single generated example within a property test
- **Counterexample**: A specific set of generated inputs that cause a property test to fail
- **Seed**: An integer value that initializes the random number generator, enabling reproducible property test executions
- **Generated_Parameter**: A test function parameter whose value is produced by a strategy rather than resolved through dependency injection
- **Injected_Parameter**: A test function parameter whose value is resolved through the TestBase injection system (scope tree, resource origins)

## Requirements

### Requirement 1: Given Decorator

**User Story:** As a test author, I want to annotate test functions with input generation strategies, so that TestBase automatically runs the function with randomly generated inputs to verify properties.

#### Acceptance Criteria

1. THE framework SHALL provide a `@given` decorator in the `automojo.testbase.properties` module
2. THE `@given` decorator SHALL accept keyword arguments mapping parameter names to `Strategy` instances
3. WHEN a test function is decorated with `@given`, THE parameters listed in the decorator SHALL receive randomly generated values during execution
4. WHEN a test function has parameters NOT listed in `@given`, THOSE parameters SHALL be resolved through the normal TestBase injection system
5. THE `@given` decorator SHALL be composable with existing TestBase decorators (`@mark_categories`, `@mark_priority`, `@mark_keywords`)
6. THE `@given` decorator SHALL store property metadata on the function's `_property_` attribute for discovery by the test sequencer
7. WHEN a `settings` keyword is passed to `@given`, THE framework SHALL use the provided `PropertySettings` to configure execution behavior

### Requirement 2: Property Settings

**User Story:** As a test author, I want to configure property test execution parameters, so that I can control how many examples are generated and ensure reproducibility.

#### Acceptance Criteria

1. THE framework SHALL provide a `settings()` function that returns a `PropertySettings` instance
2. THE `PropertySettings` SHALL support a `max_examples` parameter controlling the number of generated examples per test (default: 100)
3. THE `PropertySettings` SHALL support a `seed` parameter for overriding the seed at the individual test level
4. WHEN a per-test `seed` is not specified in settings, THE framework SHALL derive the seed from the job-level seed (see Requirement 13)
5. THE seed used for each property test execution SHALL be included in the test result metadata
6. THE `PropertySettings` SHALL support a `max_shrink_attempts` parameter controlling the maximum number of shrinking iterations (default: 100)

### Requirement 3: Built-in Strategies

**User Story:** As a test author, I want a set of built-in strategies for common Python types, so that I can generate test inputs without writing custom generators.

#### Acceptance Criteria

1. THE `automojo.testbase.properties.strategies` module SHALL provide the following built-in strategy functions:
   - `integers(min_value, max_value)` — generates random integers within a range
   - `floats(min_value, max_value)` — generates random floating-point numbers within a range
   - `text(alphabet, min_size, max_size)` — generates random strings
   - `booleans()` — generates random boolean values
   - `lists(element_strategy, min_size, max_size)` — generates random lists of elements
   - `tuples(*strategies)` — generates random tuples with elements from the given strategies
   - `dictionaries(keys, values, min_size, max_size)` — generates random dictionaries
   - `sampled_from(elements)` — randomly selects from a fixed sequence of values
   - `one_of(*strategies)` — randomly selects a strategy and generates a value from it
   - `just(value)` — always returns the same fixed value
   - `characters(categories, characters)` — generates characters matching unicode category or explicit set
2. ALL strategy functions SHALL return instances of a `Strategy` base class
3. ALL strategies SHALL accept a `random.Random` instance for deterministic generation
4. THE `Strategy` base class SHALL define `generate(rng)` and `shrink(value)` methods
5. ALL strategies SHALL provide a `describe()` method returning a human-readable string representation of the strategy configuration

### Requirement 4: Composite Strategies

**User Story:** As a test author, I want to compose custom strategies from built-in ones, so that I can generate domain-specific test data.

#### Acceptance Criteria

1. THE `strategies` module SHALL provide a `@composite` decorator for defining custom strategies
2. THE `@composite` decorated function SHALL receive a `draw` callable as its first argument
3. THE `draw` callable SHALL accept a `Strategy` instance and return a generated value
4. WHEN a composite strategy is used in `@given`, THE framework SHALL correctly generate and shrink composite values
5. THE `@composite` decorated function SHALL return a `Strategy` instance when called

### Requirement 5: Shrinking

**User Story:** As a test author, I want failing property test inputs to be automatically simplified, so that counterexamples are minimal and easier to understand.

#### Acceptance Criteria

1. WHEN a property test fails, THE framework SHALL attempt to shrink the failing inputs to a simpler counterexample
2. EACH built-in strategy SHALL implement a `shrink(value)` method that yields progressively simpler values
3. THE shrinking process SHALL preserve the failure — only values that still cause the assertion to fail SHALL be kept
4. THE shrinking process SHALL terminate after a bounded number of attempts to avoid infinite loops
5. THE final shrunk counterexample SHALL be recorded in the test result detail

### Requirement 6: Property Test Execution

**User Story:** As a test author, I want property tests to execute within the standard TestBase lifecycle, so that they benefit from injection, scoping, and result recording.

#### Acceptance Criteria

1. THE test sequencer SHALL detect the `_property_` attribute on discovered test functions
2. WHEN a property test function is detected, THE sequence document generator SHALL produce code that invokes it through a `PropertyRunner`
3. THE `PropertyRunner` SHALL generate `max_examples` sets of random inputs using the declared strategies
4. THE `PropertyRunner` SHALL call the test function once per generated example set
5. WHEN all examples pass, THE test result SHALL be recorded as PASSED with a single `TestResult` entry
6. WHEN any example fails, THE `PropertyRunner` SHALL trigger shrinking, then record the test result as FAILED
7. THE `PropertyRunner` SHALL merge injected parameters (from the scope tree) with generated parameters for each invocation
8. WHEN an unexpected exception (not `AssertionError`) occurs during a property check, THE test result SHALL be recorded as ERRORED

### Requirement 7: Check Results

**User Story:** As a test author, I want to see the individual results of each generated example within a property test, so that I can understand the distribution of checks and identify which inputs caused failures.

#### Acceptance Criteria

1. THE framework SHALL introduce a `CheckResult` class following the pattern of `TaskingResult`
2. THE `CheckResult` class SHALL extend `ResultNode` with the `ResultType.CHECK` result type
3. THE `ResultType` enum SHALL be extended with a `CHECK` value
4. EACH generated example execution SHALL produce a `CheckResult` instance attached to the parent test result
5. THE `CheckResult` SHALL record the generated input values for that example
6. THE `CheckResult` SHALL record the result code (PASSED, FAILED, or ERRORED) for that individual example
7. THE `CheckResult` SHALL record start and stop timestamps for that individual example
8. WHEN the check fails, THE `CheckResult` SHALL include the assertion error detail
9. THE `CheckResult.as_dict()` method SHALL serialize the check result in the same structural format as `TaskingResult.as_dict()`
10. A test function SHALL support having multiple `CheckResult` entries, following the same collection pattern used for `TaskingResult` entries
11. THE check results SHALL be written to the JSOS result stream alongside other result entries

### Requirement 8: Test Result Count Stability

**User Story:** As a CI/CD engineer, I want property tests to produce a predictable test count, so that I can monitor test suite health through stable test count metrics.

#### Acceptance Criteria

1. EACH property test function SHALL produce exactly one `TestResult` entry in the result tree
2. THE overall test count reported in the summary SHALL include each property test function as one test, regardless of the number of generated examples
3. THE `CheckResult` entries SHALL NOT be counted in the top-level test count
4. THE `TestResult` for a property test SHALL include metadata indicating it is a property test
5. THE `TestResult` metadata SHALL include `examples_run`, `max_examples`, and `seed` fields
6. WHEN comparing test run summaries, THE test count delta SHALL reflect only changes in the number of test functions, not in the number of generated examples

### Requirement 9: Test Discovery Compatibility

**User Story:** As a test author, I want property tests to be discovered using the existing `test_` prefix convention, so that I do not need to learn a new naming pattern.

#### Acceptance Criteria

1. THE `TestCollector` SHALL discover property test functions using the existing `test_` prefix convention
2. THE `@given` decorator SHALL NOT change the function name or module location
3. WHEN a property test has metadata markers (`@mark_categories`, etc.), THE markers SHALL be used for filtering identically to regular tests
4. WHEN running in query mode, THE system SHALL report property tests as single test entries with strategy descriptions

### Requirement 10: Agent Extraction Support

**User Story:** As an AI agent, I want to extract property test results including check results from the result stream, so that I can analyze property test outcomes and counterexamples programmatically.

#### Acceptance Criteria

1. THE `agents testresult extract` command SHALL include `CheckResult` entries when extracting a property test result
2. THE compact output for a property test result SHALL include the `examples_run`, `max_examples`, and `seed` fields
3. WHEN a property test fails, THE compact output SHALL include the shrunk counterexample values
4. THE `agents testresult failures` command SHALL report failed property tests with a summary indicating the counterexample
5. THE `agents testresult list` command SHALL display property tests identically to regular tests (single line per test function)
6. THE JSOS result stream parser SHALL correctly handle `CheckResult` entries (rtype CHECK) alongside existing result types

### Requirement 11: Query Mode Support

**User Story:** As a test author, I want property tests to participate in query mode, so that I can preview which property tests would run and what kinds of inputs they would receive.

#### Acceptance Criteria

1. WHEN running in query mode, THE system SHALL display property test functions as single test entries
2. THE query mode output SHALL include strategy descriptions for each generated parameter (e.g., `integers(min_value=0, max_value=100)`)
3. THE query mode output SHALL indicate the configured `max_examples` for each property test
4. WHEN a test failure occurs and the system reports "what would have run," property tests SHALL show their strategy descriptions

### Requirement 12: No Third-Party Dependencies

**User Story:** As a framework maintainer, I want the property testing feature to use only Python standard library modules, so that no additional third-party packages are required.

#### Acceptance Criteria

1. THE property testing implementation SHALL NOT import or depend on Hypothesis or any other third-party property testing library
2. ALL random value generation SHALL use the `random` module from the Python standard library
3. ALL string generation SHALL use the `string` module from the Python standard library
4. THE property testing module SHALL be self-contained within `automojo.testbase.properties`

### Requirement 13: Seed-Based Reproducibility

**User Story:** As a test author, I want to reproduce an exact property test failure by passing the same job seed to a subsequent test run, so that all randomly generated data is identical and the failure is deterministic.

#### Acceptance Criteria

1. THE `PropertyRunner` SHALL consume the job-level seed from `RuntimeVariables.AM_JOB_SEED` (set via the `--job-seed` CLI option) as the base seed for all property tests in a run
2. WHEN a job seed is provided, THE framework SHALL derive a unique per-test seed for each property test function by combining the job seed with the fully qualified test name
3. THE per-test seed derivation SHALL be deterministic — the same job seed and test name SHALL always produce the same per-test seed
4. WHEN the same job seed is passed to a subsequent run via `--job-seed`, ALL strategies SHALL produce the identical sequence of generated values for every property test
5. WHEN no job seed is provided via `--job-seed` or `AM_JOB_SEED`, THE framework SHALL generate a random job-level seed and record it in the job metadata
6. THE job seed and per-test seed SHALL both be recorded in the `TestResult` metadata for each property test
7. THE job seed and per-test seed SHALL both be recorded in each `CheckResult` for traceability
8. WHEN a property test has a per-test `seed` override specified in its `@given(settings=settings(seed=N))`, THAT override SHALL take precedence over the derived per-test seed
9. THE `PropertyRunner` SHALL initialize a `random.Random` instance with the resolved seed before generating any values, ensuring that the random state is isolated per test function
10. THE agent extraction output for failed property tests SHALL include the seed value, enabling agents to recommend a `--job-seed` value for reproduction

### Requirement 14: Test Result Rendering

**User Story:** As a test author reviewing results in the HTML report, I want to see the property test check results displayed in the test result detail view, so that I can visually inspect which generated examples passed or failed and view counterexample data.

#### Acceptance Criteria

1. THE `testsummary.js` stream parser SHALL recognize `rtype=CHECK` records and attach them to their parent TEST record's `checks` array
2. THE `testsummary.js` stream parser SHALL NOT include CHECK records in the top-level result counters (passed, failed, errored, skipped)
3. THE `TestSummaryResultItem` web component SHALL render a collapsible check results section when the parent test item has `checks` entries
4. THE framework SHALL provide a `TestSummaryCheckResult` web component that displays each individual check result with its generated values, result status, start/stop timestamps, and elapsed time
5. WHEN a check result has a FAILED status, THE `TestSummaryCheckResult` component SHALL display the assertion error detail and the generated input values as a counterexample
6. THE check results section SHALL display summary counters (passed, failed, errored) following the same visual pattern used by `TestSummaryTaskGroup`
7. WHEN a property test result includes `property_metadata`, THE `TestSummaryResultItem` component SHALL display seed, examples_run, max_examples, and strategy descriptions in the test detail area
8. THE `ResultRecorder.consolidate_results()` method SHALL handle `ResultType.CHECK` records by attaching them to their parent TEST node's `checks` list

### Requirement 15: Strategy Combinators

**User Story:** As a test author, I want to transform, filter, and chain strategies, so that I can adapt built-in strategies to my domain without writing full composite strategies for simple cases.

#### Acceptance Criteria

1. THE `Strategy` base class SHALL provide a `.map(fn)` method that returns a new strategy which applies the function `fn` to each generated value
2. THE mapped strategy SHALL preserve deterministic generation — the same seed SHALL produce the same mapped output
3. THE `Strategy` base class SHALL provide a `.filter(predicate)` method that returns a new strategy which only yields values satisfying the predicate
4. THE filtered strategy SHALL retry generation up to a configurable maximum number of attempts (default: 100) before raising an error
5. WHEN the filter exhausts its maximum retries without finding a satisfying value, THE strategy SHALL raise an `UnsatisfiedAssumption` exception
6. THE `Strategy` base class SHALL provide a `.flatmap(fn)` method that returns a new strategy which generates a value, passes it to `fn` to obtain a second strategy, and then generates from that second strategy
7. ALL combinator methods SHALL return `Strategy` instances that support `generate()`, `shrink()`, and `describe()`
8. THE `describe()` output for combinator strategies SHALL include the source strategy description (e.g., `integers().filter(...)`)

### Requirement 16: Additional Built-in Strategies

**User Story:** As a test author, I want strategies for commonly used Python types beyond the initial set, so that I can generate bytes, sets, frozensets, fixed-schema dictionaries, and object instances without custom boilerplate.

#### Acceptance Criteria

1. THE `strategies` module SHALL provide a `none()` function that returns a strategy always generating `None`
2. THE `strategies` module SHALL provide a `binary(min_size, max_size)` function that returns a strategy generating `bytes` objects with lengths in the specified range
3. THE `binary` strategy SHALL support shrinking toward empty bytes, then shorter byte sequences
4. THE `strategies` module SHALL provide a `sets(element, min_size, max_size)` function that returns a strategy generating `set` objects with elements from the given element strategy
5. THE `sets` strategy SHALL support shrinking by removing elements
6. THE `strategies` module SHALL provide a `frozensets(element, min_size, max_size)` function that returns a strategy generating `frozenset` objects
7. THE `strategies` module SHALL provide a `fixed_dictionaries(mapping)` function that accepts a dictionary mapping string keys to `Strategy` instances and generates dictionaries with exactly those keys, each value drawn from its corresponding strategy
8. THE `fixed_dictionaries` strategy SHALL shrink by shrinking individual values
9. THE `strategies` module SHALL provide a `builds(target, *args, **kwargs)` function that accepts a callable and strategies for its arguments, and generates instances by calling the target with generated values
10. ALL new strategies SHALL use only Python standard library modules
11. ALL new strategies SHALL provide `describe()` methods returning human-readable descriptions
12. ALL new strategies SHALL support deterministic generation via `random.Random` instances

### Requirement 17: Assume Function

**User Story:** As a test author, I want to discard invalid generated examples mid-test without counting them as failures, so that I can express preconditions on generated data that are difficult to encode purely in strategy filters.

#### Acceptance Criteria

1. THE `automojo.testbase.properties` module SHALL provide an `assume(condition)` function
2. WHEN `assume()` is called with a falsy condition, THE function SHALL raise an `UnsatisfiedAssumption` exception
3. WHEN `assume()` is called with a truthy condition, THE function SHALL return without side effects
4. THE `PropertyRunner` SHALL catch `UnsatisfiedAssumption` exceptions during example execution and skip that example without recording a failure
5. WHEN an example is skipped due to `assume()`, THE `PropertyRunner` SHALL NOT count it toward `examples_run` and SHALL NOT create a `CheckResult` for it
6. THE `PropertyRunner` SHALL track the number of rejected assumptions in the property test metadata as `assumptions_rejected`
7. WHEN the number of consecutive rejected assumptions exceeds a threshold (default: 50 × `max_examples`), THE `PropertyRunner` SHALL abort the test with an error indicating too many rejected examples
