# Tandem Validators - Requirements Document

## Introduction

The Tandem Validators system provides a mechanism for performing validation work in parallel with test execution. Validators are attached to test scopes and run concurrently, collecting results that are recorded alongside the primary test results. The system supports one-shot validators (validate after test completes), looping validators (continuous work in a background thread), and time-interval validators (periodic work at fixed intervals). Validators integrate with the test result recording system and the sequencer's scope management.

## Glossary

- **Validator**: Base class for all validator implementations, extending ValidatorCoupling
- **LoopingValidator**: A validator that runs a work loop in a background daemon thread
- **TimeIntervalValidator**: A LoopingValidator that performs work at fixed time intervals
- **LoopingValidatorState**: Enumeration of validator states (Initial, Running, Shutdown, Finished)
- **Tandem_Test**: A test that has one or more validators attached, running validation in parallel with the test

## Requirements

### Requirement 1: Validator Base Class

**User Story:** As a test developer, I want a base validator class that integrates with the test scope and result recording system, so that I can create custom validators.

#### Acceptance Criteria

1. THE Validator class SHALL extend ValidatorCoupling.
2. THE Validator SHALL generate a unique instance ID (UUID) on construction.
3. THE Validator SHALL provide an `attach_to_test(testscope, suffix)` method that binds the validator to a test scope.
4. WHEN attached, THE Validator SHALL create a TestResult with the validator's name (test_name + "_" + suffix) and preview it with the recorder.
5. THE Validator SHALL provide an `initialize(*args, **kwargs)` method for setup (default: no-op with warning).
6. THE Validator SHALL provide an abstract `validate()` method that derived types must implement.
7. THE Validator SHALL provide a `finalize()` method that calls `validate()`, marks the result as passed/failed/errored, and records it.
8. WHEN `validate()` raises an AssertionError, THE `finalize()` method SHALL mark the result as failed with traceback detail.
9. WHEN `validate()` raises any other Exception, THE `finalize()` method SHALL mark the result as errored with traceback detail.
10. THE `finalize()` method SHALL always call `result.finalize()` and `recorder.record(result)` in a finally block.

### Requirement 2: Looping Validator

**User Story:** As a test developer, I want a validator that runs continuous work in a background thread, so that I can perform ongoing validation during test execution.

#### Acceptance Criteria

1. THE LoopingValidator SHALL extend Validator.
2. THE LoopingValidator SHALL accept `loop_delay`, `shutdown_timeout`, and `shutdown_interval` parameters.
3. WHEN `initialize()` is called, THE LoopingValidator SHALL start a daemon thread running the work loop.
4. THE LoopingValidator SHALL use a gate Event to synchronize thread startup (initialize returns only after thread is running).
5. THE work loop SHALL call `do_work()` repeatedly while state is Running.
6. IF `do_work()` returns False, THE work loop SHALL exit.
7. BETWEEN work iterations, THE loop SHALL sleep for `loop_delay` seconds (if > 0).
8. WHEN `finalize()` is called, THE LoopingValidator SHALL set state to Shutdown, wait for the thread to finish, then call super().finalize().
9. THE wait SHALL use `wait_for_it` with the configured `shutdown_timeout` and `shutdown_interval`.
10. IF the thread does not finish within the timeout, THE wait SHALL raise a TimeoutError.

### Requirement 3: Time Interval Validator

**User Story:** As a test developer, I want a validator that performs work at fixed time intervals, so that I can sample or check conditions periodically during test execution.

#### Acceptance Criteria

1. THE TimeIntervalValidator SHALL extend LoopingValidator with `loop_delay` set to the specified interval.
2. THE `do_work()` method SHALL call `tick()` and return True (always continue).
3. THE `tick()` method SHALL be overridden by derived classes to perform interval-based work.

### Requirement 4: Validator State Machine

**User Story:** As a framework developer, I want validators to follow a defined state machine, so that lifecycle transitions are predictable.

#### Acceptance Criteria

1. THE LoopingValidatorState SHALL define four states: Initial, Running, Shutdown, Finished.
2. THE validator SHALL start in Initial state.
3. WHEN `initialize()` is called, THE state SHALL transition to Running.
4. WHEN `finalize()` is called, THE state SHALL transition to Shutdown.
5. WHEN the work loop exits, THE state SHALL transition to Finished.
6. IF `initialize()` is called when state is not Initial, THE validator SHALL raise a SemanticError.
