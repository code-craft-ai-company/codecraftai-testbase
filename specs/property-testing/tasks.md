# Property Testing - Tasks Document

## Overview

This document tracks the implementation tasks for the Property Testing feature. The feature adds a built-in,
stdlib-only property testing engine to TestBase with `@given` decorator, strategies, seed-based reproducibility,
`CheckResult` sub-results, and agent extraction support.

## Implementation Status

### Completed Tasks

**Phase 1:** Core Engine — PropertySettings, Strategy base, 11 built-in strategies, @composite, public API

**Phase 2:** Decorator and Metadata — @given decorator, settings() helper, properties/__init__.py

**Phase 3:** Result Model — ResultType.CHECK, CheckResult class, model __init__ export

**Phase 4:** Property Runner — seed derivation, PropertyRunner class, shrinking engine

**Phase 5 (partial):** Result consolidation for CHECK records in ResultRecorder

**Phase 6:** HTML Report Rendering — testsummary.js CHECK parsing, 3 new web components, syncData() integration, custom element registration

---

### In Progress

**Phase 5 (remaining):** create_check_result() factory, sequence document generation, property metadata on TestResult

---

### Planned Tasks

#### Phase 1: Core Engine

- [x] Implement `PropertySettings` dataclass (`properties/propertysettings.py`)
  - `max_examples` (default: 100), `seed` (Optional[int]), `max_shrink_attempts` (default: 100)
  - _Requirements: 2.1–2.6_

- [x] Implement `Strategy` base class (`properties/strategies.py`)
  - Abstract `generate(rng)`, `shrink(value)`, `describe()` methods
  - _Requirements: 3.2, 3.3, 3.4, 3.5_

- [x] Implement built-in strategies (`properties/strategies.py`)
  - `IntegerStrategy` — `generate`, `shrink` (toward zero), `describe`
  - `FloatStrategy` — `generate`, `shrink` (toward 0.0), `describe`
  - `TextStrategy` — `generate` with alphabet/size, `shrink` (remove chars), `describe`
  - `BooleanStrategy` — `generate`, `shrink` (True→False)
  - `ListStrategy` — `generate` with element strategy/size, `shrink` (remove elements), `describe`
  - `TupleStrategy` — `generate`, `shrink` (element-wise)
  - `DictionaryStrategy` — `generate`, `shrink` (remove keys)
  - `SampledFromStrategy` — `generate` (random.choice), no shrink
  - `OneOfStrategy` — `generate` (pick strategy then generate), `describe`
  - `JustStrategy` — always returns fixed value
  - `CharacterStrategy` — `generate` from categories or explicit set
  - _Requirements: 3.1_

- [x] Implement `@composite` decorator (`properties/strategies.py`)
  - Accept function with `draw` callable as first argument
  - Return `CompositeStrategy` instance when called
  - _Requirements: 4.1–4.5_

- [x] Implement strategy module public API (`properties/strategies.py`)
  - Expose convenience functions: `integers()`, `floats()`, `text()`, `booleans()`, `lists()`, `tuples()`, `dictionaries()`, `sampled_from()`, `one_of()`, `just()`, `characters()`
  - _Requirements: 3.1_

#### Phase 2: Decorator and Metadata

- [x] Implement `@given` decorator (`properties/decorators.py`)
  - Accept keyword args mapping param names to Strategy instances
  - Accept optional `settings` keyword for PropertySettings
  - Store `_property_` attribute on decorated function containing strategies and settings
  - Preserve function name, module, and existing decorators
  - _Requirements: 1.1–1.7_

- [x] Implement `settings()` helper function (`properties/decorators.py`)
  - Return PropertySettings instance with provided overrides
  - _Requirements: 2.1–2.6_

- [x] Create `properties/__init__.py` package init
  - Export `given`, `settings`, `strategies` (as `st` alias)
  - _Requirements: 1.1_

#### Phase 3: Result Model

- [x] Extend `ResultType` enum (`results/model/resulttype.py`)
  - Add `CHECK = 11`
  - _Requirements: 7.3_

- [x] Implement `CheckResult` class (`results/model/checkresult.py`)
  - Extend `ResultNode` with `ResultType.CHECK`
  - Fields: `generated_values` (dict), `example_index` (int), `seed` (int)
  - Implement `as_dict(is_preview)` following `TaskingResult` pattern
  - Include `generated_values`, `example_index`, `seed` in serialized output
  - When failed, include error/failure detail
  - _Requirements: 7.1, 7.2, 7.4–7.9_

- [x] Update `results/model/__init__.py` to export `CheckResult`
  - _Requirements: 7.11_

#### Phase 4: Property Runner

- [x] Implement seed derivation logic (`properties/propertyrunner.py`)
  - `derive_test_seed(job_seed, test_name)` using `hashlib.sha256`
  - Per-test seed isolation using `random.Random(per_test_seed)`
  - Per-test seed override from `PropertySettings.seed`
  - _Requirements: 13.1–13.9_

- [x] Implement `PropertyRunner` class (`properties/propertyrunner.py`)
  - Constructor: accept `settings`, `job_seed`, `test_name`, `recorder`, `parent_inst`
  - `run()` method: generate `max_examples` sets, invoke test function, catch failures
  - Merge injected args with generated args for each invocation
  - Create `CheckResult` for each example
  - Record each `CheckResult` via the recorder
  - On failure: trigger shrinking, record final FAILED test result with counterexample
  - On error (non-AssertionError): record ERRORED test result, skip shrinking
  - On all pass: record PASSED test result
  - _Requirements: 6.1–6.8, 13.1–13.9_

- [x] Implement shrinking engine (`properties/propertyrunner.py`)
  - For each strategy parameter, attempt `strategy.shrink()` candidates
  - Continue while candidates still reproduce the failure
  - Bounded by `max_shrink_attempts` from settings
  - Record the final shrunk counterexample
  - _Requirements: 5.1–5.5_

#### Phase 5: Sequencer Integration

- [x] Add `job_seed` property to `TestSequencer` (after `get_recorder`, ~line 1862)
  - Read from `RuntimeVariables.AM_JOB_SEED` with fallback to `random.randint(0, 2**32-1)`
  - PropertyRunner needs this to derive per-test seeds
  - _Requirements: 13.1_

- [x] Update `_generate_scope_method` to detect `@given` tests (lines 2686-2700)
  - After importing the test function, emit `hasattr(func, '_property_')` runtime check
  - For property tests: generate `PropertyRunner` instantiation and `run()` call
  - Separate strategy params from injected params (`{k: v for k, v in args.items() if k not in strategies}`)
  - For non-property tests: emit the existing direct `test_function(params)` call
  - All detection is runtime since test modules are lazily imported
  - _Requirements: 6.1–6.3_

- [x] Update result consolidation for CHECK records
  - Add `ResultType.CHECK.name` case in `consolidate_results()`
  - Attach check records to parent TestResult's `checks` list
  - Handle preview/final merging for CHECK records
  - _Requirements: 7.11_

- [ ] Add property metadata to TestResult
  - When test has `_property_` attribute, include `property_metadata` in `as_dict()`
  - Fields: `is_property_test`, `examples_run`, `max_examples`, `seed`, `job_seed`, `counterexample`, `strategy_descriptions`
  - _Requirements: 8.4, 8.5_

#### Phase 6: HTML Report Rendering

- [x] Update `testsummary.js` stream parsing for CHECK records
  - Add `rtype=CHECK` case in `load_results_from_stream()` following TASKING pattern
  - Attach CHECK records to parent TEST's `checks` array with pass/fail/error counters
  - Ensure CHECK records are NOT counted in top-level result counters
  - _Requirements: 14.1, 14.2_

- [x] Create `TestSummaryCheckGroup` web component (`testsummary-components.js`)
  - Follow `TestSummaryTaskGroup` pattern with collapsible summary
  - Show passed/failed/errored counters for check results
  - Render individual `TestSummaryCheckResult` entries inside
  - _Requirements: 14.3, 14.6_

- [x] Create `TestSummaryCheckResult` web component (`testsummary-components.js`)
  - Follow `TestSummaryTaskResult` pattern
  - Display generated values as key-value pairs, example index, result status
  - Display start/stop/elapsed time
  - Display error/failure detail when applicable
  - _Requirements: 14.4, 14.5_

- [x] Create `TestSummaryPropertyMetadata` web component (`testsummary-components.js`)
  - Collapsible section showing seed, job_seed, examples_run, max_examples
  - Show strategy descriptions for each parameter
  - Show counterexample values when test failed
  - _Requirements: 14.7_

- [x] Update `TestSummaryResultItem.syncData()` (`testsummary-components.js`)
  - After `tasking_groups` rendering block, add `checks` rendering using `TestSummaryCheckGroup`
  - Add `property_metadata` rendering using `TestSummaryPropertyMetadata`
  - _Requirements: 14.3, 14.7_

- [x] Update `ResultRecorder.consolidate_results()` for CHECK records
  - Add `ResultType.CHECK.name` case to attach CHECK records to parent TEST's `checks` list
  - Handle preview/final merging for CHECK records
  - _Requirements: 14.8_

#### Phase 7: Query Mode Support

- [ ] Update query mode for property test introspection
  - Report property tests as single test entries with strategy descriptions
  - Include `max_examples` configuration
  - Show strategy `describe()` output for each generated parameter
  - _Requirements: 11.1–11.4_

#### Phase 8: Agent Tooling Updates

- [ ] Update JSOS parser to handle CHECK records
  - Recognize `rtype=CHECK` entries
  - Do not include CHECK entries in top-level test counts
  - _Requirements: 10.6_

- [ ] Update `testresult extract` for property tests
  - Include `property` section with `examples_run`, `max_examples`, `seed`, `job_seed`
  - Include `counterexample` on failure
  - Include check result summary (passed/failed counts)
  - _Requirements: 10.1–10.3_

- [ ] Update `testresult failures` for property tests
  - Include counterexample in error summary
  - Include seed and `--job-seed` reproduction hint
  - _Requirements: 10.4_

- [ ] Verify `testresult list` unchanged behavior
  - Property tests appear as single lines, same as regular tests
  - _Requirements: 10.5_

#### Phase 9: Unit Tests

- [ ] Add unit tests for strategies (`test_strategies.py`)
  - Test each built-in strategy: generation within bounds, shrinking correctness, describe() output
  - Test composite strategy with draw callable
  - Test edge cases: empty ranges, single-element lists, boundary values
  - _Requirements: 3.1–3.5, 4.1–4.5_

- [ ] Add unit tests for PropertyRunner (`test_propertyrunner.py`)
  - Test pass path: all examples pass → PASSED result
  - Test fail path: assertion failure → shrinking → FAILED result with counterexample
  - Test error path: unexpected exception → ERRORED result
  - Test seed determinism: same seed + same test name → same generated values
  - Test per-test seed isolation: different test names → different sequences
  - Test max_examples setting honored
  - _Requirements: 6.1–6.8, 5.1–5.5_

- [ ] Add unit tests for CheckResult (`test_checkresult.py`)
  - Test as_dict() serialization format
  - Test ResultType.CHECK in serialized output
  - Test generated_values, example_index, seed in output
  - Test error detail inclusion on failure
  - _Requirements: 7.1–7.11_

- [ ] Add unit tests for @given decorator (`test_decorators.py`)
  - Test _property_ attribute attachment
  - Test composability with @mark_categories, @mark_priority
  - Test settings override
  - Test function name preservation
  - _Requirements: 1.1–1.7_

- [ ] Add unit tests for seed derivation (`test_seed_derivation.py`)
  - Test deterministic: same inputs → same seed
  - Test isolation: different test names → different seeds
  - Test per-test override takes precedence
  - Test no job seed → auto-generated seed → recorded
  - _Requirements: 13.1–13.10_

#### Phase 10: Strategy Combinators, Additional Strategies, and Assume

- [ ] Add `.map(fn)`, `.filter(predicate)`, `.flatmap(fn)` to Strategy base class (`properties/strategies.py`)
  - `MappedStrategy` — wraps source, applies `fn` to generated values, shrinks via source then re-maps
  - `FilteredStrategy` — wraps source, retries up to `max_tries`, shrinks keeping only satisfying values
  - `FlatMappedStrategy` — wraps source, calls `fn(value)` to get second strategy, generates from it
  - _Requirements: 15.1–15.8_

- [ ] Add additional built-in strategies (`properties/strategies.py`)
  - `NoneStrategy` / `none()` — always returns `None`
  - `BinaryStrategy` / `binary(min_size, max_size)` — generates `bytes`, shrinks toward empty
  - `SetStrategy` / `sets(element, min_size, max_size)` — generates `set`, shrinks by removing elements
  - `FrozenSetStrategy` / `frozensets(element, min_size, max_size)` — generates `frozenset`
  - `FixedDictionaryStrategy` / `fixed_dictionaries(mapping)` — fixed keys, per-key strategies, shrinks values
  - `BuildsStrategy` / `builds(target, *args, **kwargs)` — constructs instances from strategies
  - _Requirements: 16.1–16.12_

- [ ] Create `assume()` function and `UnsatisfiedAssumption` (`properties/assumptions.py`)
  - `UnsatisfiedAssumption` sentinel exception
  - `assume(condition)` raises `UnsatisfiedAssumption` when falsy
  - _Requirements: 17.1–17.3_

- [ ] Update `PropertyRunner` to handle `UnsatisfiedAssumption` (`properties/propertyrunner.py`)
  - Catch `UnsatisfiedAssumption` in example loop — skip example, no CheckResult
  - Track `assumptions_rejected` counter in metadata
  - Abort if too many consecutive rejections (50 × max_examples)
  - _Requirements: 17.4–17.7_

- [ ] Update `properties/__init__.py` to export `assume`
  - _Requirements: 17.1_

- [ ] Add unit tests for strategy combinators (`test_strategies.py`)
  - `MappedStrategyTests` — map transforms values, describe output
  - `FilteredStrategyTests` — filter rejects, raises on exhaustion, describe output
  - `FlatMappedStrategyTests` — dependent generation
  - Determinism tests for all combinators
  - _Requirements: 15.1–15.8_

- [ ] Add unit tests for additional strategies (`test_strategies.py`)
  - `NoneStrategyTests`, `BinaryStrategyTests`, `SetStrategyTests`
  - `FrozenSetStrategyTests`, `FixedDictionaryStrategyTests`, `BuildsStrategyTests`
  - Shrinking, describe, determinism for each
  - _Requirements: 16.1–16.12_

- [ ] Add unit tests for assume() integration (`test_propertyrunner.py`)
  - Assumed examples are skipped without failure
  - `assumptions_rejected` appears in metadata
  - Test abort on too many rejections
  - _Requirements: 17.4–17.7_

---

## Requirements Traceability

| Requirement | Status | Implementation Location |
|-------------|--------|------------------------|
| 1.1–1.7 | ⬜ Not Started | `properties/decorators.py` |
| 2.1–2.6 | ⬜ Not Started | `properties/propertysettings.py`, `properties/decorators.py` |
| 3.1–3.5 | ⬜ Not Started | `properties/strategies.py` |
| 4.1–4.5 | ⬜ Not Started | `properties/strategies.py` (@composite) |
| 5.1–5.5 | ⬜ Not Started | `properties/propertyrunner.py` (shrinking) |
| 6.1–6.8 | ⬜ Not Started | `properties/propertyrunner.py` |
| 7.1–7.11 | ⬜ Not Started | `results/model/checkresult.py`, `results/model/resulttype.py` |
| 8.1–8.6 | ⬜ Not Started | TestResult metadata, TestSequencer |
| 9.1–9.4 | ⬜ Not Started | `properties/decorators.py`, TestCollector |
| 10.1–10.6 | ⬜ Not Started | Agent tooling updates |
| 11.1–11.4 | ⬜ Not Started | Query mode updates |
| 12.1–12.4 | ⬜ Not Started | Verified by implementation (stdlib only) |
| 13.1–13.10 | ⬜ Not Started | `properties/propertyrunner.py` (seed logic) |
| 14.1–14.8 | ⬜ Not Started | `testsummary.js`, `testsummary-components.js`, `resultrecorder.py` |

---

## Test Coverage Summary

| Component | Unit Tests | Integration Tests |
|-----------|------------|-------------------|
| Strategy Classes | ⬜ | — |
| @composite | ⬜ | — |
| @given Decorator | ⬜ | — |
| PropertySettings | ⬜ | — |
| PropertyRunner | ⬜ | ⬜ |
| CheckResult | ⬜ | — |
| Seed Derivation | ⬜ | ⬜ |
| Sequencer Integration | — | ⬜ |
| Agent Extraction | ⬜ | — |
| Query Mode | — | ⬜ |
| HTML Report Rendering | — | ⬜ |

**Legend:** ✅ = Complete, ⚠️ = Partial, ⬜ = Not Started

---

## File Structure

```
source/packages/automojo/testbase/
├── properties/                       # [NEW] Property testing package
│   ├── __init__.py                   # Exports: given, settings, strategies
│   ├── decorators.py                 # @given decorator, settings() function
│   ├── strategies.py                 # Strategy base + all built-in strategies + @composite
│   ├── propertyrunner.py             # PropertyRunner + shrinking + seed derivation
│   └── propertysettings.py           # PropertySettings dataclass
│
├── results/model/
│   ├── checkresult.py                # [NEW] CheckResult class
│   └── resulttype.py                 # [MODIFY] Add CHECK = 11
│
├── results/recorders/
│   └── resultrecorder.py             # [MODIFY] Handle CHECK in consolidate_results()
│
├── sequencing/
│   └── testsequencer.py              # [MODIFY] create_check_result(), _property_ detection
│
└── templates/v2/static/javascript/
    ├── testsummary.js                # [MODIFY] Add CHECK record case in load_results_from_stream()
    └── testsummary-components.js     # [MODIFY] Add TestSummaryCheckGroup, TestSummaryCheckResult,
                                     #          TestSummaryPropertyMetadata; update TestSummaryResultItem

source/tests/automojo_tests/testbase/properties/  # [NEW] Test package
├── __init__.py
├── test_strategies.py
├── test_propertyrunner.py
├── test_checkresult.py
├── test_decorators.py
└── test_seed_derivation.py
```
