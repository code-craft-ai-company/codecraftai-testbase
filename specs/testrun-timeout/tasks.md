# Test Run Timeout - Tasks Document

## Overview

This document tracks the implementation status of the Test Run Timeout feature.

## Implementation Tasks

### Runtime Infrastructure (automojo-runtime)
- [ ] Add `AM_TESTRUN_TIMEOUT` to `RuntimeVariablesDesc` in `runtimevariables.py`
  - _Requirements: 2.1, 2.4_
- [ ] Add `AM_TESTRUN_TIMEOUT` accessor to `RuntimeVariables` in `runtimevariables.py`
  - _Requirements: 2.2_
- [ ] Add `override_testrun_timeout()` to `AM_RUNTIME_OPTION_OVERRIDES` in `optionoverrides.py`
  - _Requirements: 2.3_

### Error Definition (automojo-testbase)
- [ ] Create `TestRunTimeoutError` exception in `errors/testruntimeouterror.py`
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

### CLI Integration (automojo-testbase)
- [ ] Add `HELP_TIMEOUT` help text and `TimeoutOptionGroup` to `cli/options.py`
  - _Requirements: 1.4_
- [ ] Wire `--timeout` in `cli/cmdtree/testing/run.py`
  - _Requirements: 1.1, 1.2, 1.3, 2.5_
- [ ] Wire `--timeout` in `cli/cmdtree/testing/jobs.py`
  - _Requirements: 1.5_

### Timeout Enforcement (automojo-testbase)
- [ ] Read `AM_TESTRUN_TIMEOUT` in `TestJob.__init__()` in `testjob.py`
  - _Requirements: 3.1, 6.1_
- [ ] Implement timeout guard in `TestJob.execute()` in `testjob.py`
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 5.1, 5.2, 5.3, 6.2, 6.3_

### Unit Tests (automojo-testbase)
- [ ] Add `TestRunTimeoutError` tests in `tests/automojo_tests/testbase/test_testruntimeouterror.py`
  - _Requirements: 4.1, 4.2, 4.3, 4.4_
- [ ] Add timeout-related tests to `tests/automojo_tests/testbase/test_testjob.py`
  - _Requirements: 3.1, 3.2, 3.6, 6.1, 6.2, 6.3_

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1-1.5 | ⬜ Planned | `cli/options.py`, `cli/cmdtree/testing/run.py`, `cli/cmdtree/testing/jobs.py` |
| 2.1-2.5 | ⬜ Planned | `automojo-runtime: runtimevariables.py, optionoverrides.py` |
| 3.1-3.7 | ⬜ Planned | `testjob.py` |
| 4.1-4.4 | ⬜ Planned | `errors/testruntimeouterror.py` |
| 5.1-5.3 | ⬜ Planned | `testjob.py` |
| 6.1-6.3 | ⬜ Planned | `testjob.py` |
