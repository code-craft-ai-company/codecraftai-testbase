# Agent Tooling - Tasks Document

## Overview

This document tracks the implementation tasks for the Agent Tooling feature. The feature adds a `testbase agents`
command group with commands for extracting, listing, comparing, and analyzing test result data in compact
formats optimized for AI agent consumption.

## Implementation Status

### Completed Tasks

_No tasks completed yet._

---

### In Progress

_No tasks currently in progress._

---

### Planned Tasks

#### Shared Utilities

- [ ] Implement CompactFormatter utility (`agents/formatting.py`)
  - Implement `format_kv(key, value)` for key-value line output
  - Implement `format_section(name)` for section headers
  - Implement `format_error(message)` for stderr error output
  - Implement `omit_unset(value)` to filter `(not-set)`, `(unknown)`, and `None` values
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] Implement JSOS Parser utility (`agents/jsosparser.py`)
  - Implement `parse_file(filepath)` to read and parse JSOS (blank-line-delimited JSON objects)
  - Implement `filter_tests(entries)` to filter entries with `rtype=TEST`
  - Implement `get_final_results(entries)` to deduplicate and keep last entry per test name
  - _Requirements: 3.3, 3.8, 5.2, 5.5_

- [ ] Implement Path Resolver utility (`agents/pathresolver.py`)
  - Implement `resolve_file_path(filepath)` with expandvars, expanduser, abspath
  - Validate file existence and raise `FileNotFoundError` with resolved path in message
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

#### Agents Command Group Structure

- [ ] Create agents command group (`cmdtree/agents/__init__.py`)
  - Define `@arcli.group("agents")` decorator
  - Register on root `testbase` command
  - Ensure no runtime initialization is triggered
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [ ] Create summary subgroup (`cmdtree/agents/summary/__init__.py`)
  - Define `@arcli.group("summary")` decorator
  - Register on agents group
  - _Requirements: 1.2_

- [ ] Create testresult subgroup (`cmdtree/agents/testresult/__init__.py`)
  - Define `@arcli.group("testresult")` decorator
  - Register on agents group
  - _Requirements: 1.2_

- [ ] Create config subgroup (`cmdtree/agents/config/__init__.py`)
  - Define `@arcli.group("config")` decorator
  - Register on agents group
  - _Requirements: 1.2_

#### Summary Commands

- [ ] Implement summary extract command (`agents/summary/extract.py`)
  - Accept `--summary-file` option for `testrun_summary.json` path
  - Resolve and validate file path
  - Parse summary JSON
  - Extract: result, start, stop, detail counters (passed, failed, errors, skipped, total)
  - Extract: job.id, job.name, job.type (when not placeholder)
  - Extract: build.branch, build.build (when not placeholder)
  - Output via CompactFormatter
  - Handle file-not-found and invalid-JSON errors
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9_

- [ ] Implement summary compare command (`agents/summary/compare.py`)
  - Accept `--baseline` and `--current` options for summary file paths
  - Resolve and validate both file paths
  - Parse both summary JSON files
  - Compare overall result (e.g., `PASSED->FAILED`)
  - Compute counter deltas for passed, failed, errors, skipped, total
  - Classify as regression, improvement, or stable
  - Output via CompactFormatter
  - Handle file-not-found and invalid-JSON errors for both files
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

#### Test Result Commands

- [ ] Implement testresult extract command (`agents/testresult/extract.py`)
  - Accept `--results-file` option for `testrun_results_stream.jsos` path
  - Accept `--testname` option for fully qualified test name
  - Resolve and validate file path
  - Parse JSOS file via JSOSParser
  - Get final results and locate specified test
  - Extract: name, result, start, stop, error details
  - Output via CompactFormatter
  - Handle file-not-found and test-not-found errors
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8_

- [ ] Implement testresult list command (`agents/testresult/list.py`)
  - Accept `--results-file` option for JSOS file path
  - Accept optional `--result-filter` option to filter by result code
  - Resolve and validate file path
  - Parse JSOS file and get final results for TEST entries only
  - Output each test name and result code, one per line
  - Maintain stream order
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ] Implement testresult failures command (`agents/testresult/failures.py`)
  - Accept `--results-file` option for JSOS file path
  - Resolve and validate file path
  - Parse JSOS file and collect tests with final result FAILED or ERRORED
  - Include brief error summary when available in detail
  - Print "All tests passed" message when no failures found
  - Maintain stream order
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

#### Configuration Commands

- [ ] Implement config extract command (`agents/config/extract.py`)
  - Accept `--config-file` option for `startup-configuration.json` path
  - Resolve and validate file path
  - Parse configuration JSON
  - Extract: test root path, console log level, file log level
  - Extract: active debug settings (debugger, breakpoints) when present
  - Output via CompactFormatter
  - Handle file-not-found error
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_

#### Error Handling

- [ ] Implement consistent error output across all agent commands
  - Print errors to stderr in `ERROR: <description>` format
  - Exit with non-zero code on error
  - Include resolved file path in file-not-found errors
  - Suppress stack traces unless `--verbose` is specified
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

#### Unit Tests

- [ ] Add unit tests for CompactFormatter (`test_compact_formatter.py`)
  - Test key-value formatting
  - Test section header formatting
  - Test nested indentation
  - Test omission of unset/placeholder values
  - Test deterministic output
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] Add unit tests for JSOS Parser (`test_jsosparser.py`)
  - Test parsing multi-object JSOS files
  - Test filtering by rtype TEST
  - Test deduplication of UNSET→final result pairs
  - Test handling of empty files
  - Test handling of malformed JSOS
  - _Requirements: 3.3, 3.8, 5.2, 5.5_

- [ ] Add unit tests for summary extract command (`test_summary_extract.py`)
  - Test extraction of all key fields from valid summary
  - Test omission of unset metadata fields
  - Test file-not-found error
  - Test invalid-JSON error
  - _Requirements: 2.1–2.9_

- [ ] Add unit tests for summary compare command (`test_summary_compare.py`)
  - Test regression detection (more failures)
  - Test improvement detection (fewer failures)
  - Test stable detection (no change)
  - Test counter delta computation
  - Test error handling for missing/invalid files
  - _Requirements: 6.1–6.6_

- [ ] Add unit tests for testresult extract command (`test_testresult_extract.py`)
  - Test extraction of a specific test by name
  - Test UNSET deduplication returns final result
  - Test inclusion of error details
  - Test test-not-found error
  - Test file-not-found error
  - _Requirements: 3.1–3.8_

- [ ] Add unit tests for testresult list command (`test_testresult_list.py`)
  - Test full listing of all tests
  - Test result-filter option (PASSED, FAILED, SKIPPED)
  - Test exclusion of TEST_CONTAINER and JOB entries
  - Test stream order preservation
  - _Requirements: 5.1–5.6_

- [ ] Add unit tests for testresult failures command (`test_testresult_failures.py`)
  - Test listing of FAILED and ERRORED tests
  - Test inclusion of error summaries
  - Test "All tests passed" message when no failures
  - Test stream order preservation
  - _Requirements: 4.1–4.6_

- [ ] Add unit tests for config extract command (`test_config_extract.py`)
  - Test extraction of key configuration fields
  - Test omission of unset values
  - Test file-not-found error
  - _Requirements: 7.1–7.6_

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1–1.4 | ⬜ Not Started | `cmdtree/agents/__init__.py` |
| 2.1–2.9 | ⬜ Not Started | `cmdtree/agents/summary/extract.py` |
| 3.1–3.8 | ⬜ Not Started | `cmdtree/agents/testresult/extract.py` |
| 4.1–4.6 | ⬜ Not Started | `cmdtree/agents/testresult/failures.py` |
| 5.1–5.6 | ⬜ Not Started | `cmdtree/agents/testresult/list.py` |
| 6.1–6.6 | ⬜ Not Started | `cmdtree/agents/summary/compare.py` |
| 7.1–7.6 | ⬜ Not Started | `cmdtree/agents/config/extract.py` |
| 8.1–8.6 | ⬜ Not Started | `cmdtree/agents/formatting.py` |
| 9.1–9.5 | ⬜ Not Started | `cmdtree/agents/pathresolver.py` |
| 10.1–10.5 | ⬜ Not Started | All agent commands (cross-cutting) |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| CompactFormatter | ⬜ | — |
| JSOS Parser | ⬜ | — |
| Path Resolver | ⬜ | — |
| Summary Extract | ⬜ | ⬜ |
| Summary Compare | ⬜ | ⬜ |
| Test Result Extract | ⬜ | ⬜ |
| Test Result List | ⬜ | ⬜ |
| Test Result Failures | ⬜ | ⬜ |
| Config Extract | ⬜ | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## File Structure

```
source/packages/automojo/testbase/cli/
└── cmdtree/
    └── agents/
        ├── __init__.py              # Agents group definition
        ├── formatting.py            # CompactFormatter utility
        ├── jsosparser.py            # JSOS file parser
        ├── pathresolver.py          # File path resolution utility
        ├── summary/
        │   ├── __init__.py          # Summary subgroup definition
        │   ├── extract.py           # Summary extract command
        │   └── compare.py           # Summary compare command
        ├── testresult/
        │   ├── __init__.py          # Test result subgroup definition
        │   ├── extract.py           # Test result extract command
        │   ├── list.py              # Test result list command
        │   └── failures.py          # Test result failures command
        └── config/
            ├── __init__.py          # Config subgroup definition
            └── extract.py           # Config extract command

source/tests/automojo_tests/testbase/cli/agents/
├── __init__.py
├── test_jsosparser.py
├── test_compact_formatter.py
├── test_summary_extract.py
├── test_summary_compare.py
├── test_testresult_extract.py
├── test_testresult_list.py
├── test_testresult_failures.py
└── test_config_extract.py
```
