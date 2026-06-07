# Package Dependencies - Tasks Document

## Overview

This document tracks the implementation status of the `automojo-testbase` PACKAGE-LEVEL
(inter-package) dependency posture and identifies the remaining work required to reach the
target dependency set. It records the decoupling that has already been delivered (the
dependency-free test-execution core, the four seam modules, the dependency-free environment
accessor, the standalone default recorder, the relocation of the runtime foundation into
`automojo-this-app`, and the out-of-package integration variants in
`automojo-integration-runtime`), and it tracks honestly the work that is still pending (the
CLI / bootstrap / server relocation, the integration-contract test relocation, the removal of
the drop-pending dependencies from `pyproject.toml`, and the downstream lockfile cascade).

**Scope / Not To Be Confused With:** This is the inter-package dependency spec. It is distinct
from `specs/dependencies` (the Dependency Injection registry) and `specs/coupling` (the
Coupling System DI mechanism). "Dependency" here always means a Python package dependency edge
declared in `pyproject.toml`, never an injectable resource or a coupling.

## Implementation Status

### Completed Tasks

#### Decoupled Test-Execution Core (`testjob.py`, `testgroup.py`, `verification.py`, `markers.py`, `constraints.py`, `entrypoints.py`, `sequencing/testsequencer.py`, default recorders)
- [x] Remove all real imports of the application/runtime/configuration layers from the core
  - Zero real imports of `automojo.configuration`, `automojo.runtime`, or `automojo.thisapp`
  - Any remaining mentions of those package names appear only in docstring negations
  - Core consumes the seams in place of the heavyweight providers
  - _Requirements: 3.1, 3.2, 3.4_
- [x] Prove core import isolation via import smoke tests
  - `import automojo.testbase.testjob` pulls in zero configuration/runtime/this-app modules
  - `import automojo.testbase.sequencing.testsequencer` pulls in zero higher-layer modules
  - `import automojo.testbase.entrypoints` pulls in zero higher-layer modules
  - Importing the default recorders pulls in zero higher-layer modules
  - _Requirements: 3.3, 3.5_

#### Dependency-Free Environment Accessor (`environment.py`)
- [x] Implement the dependency-free `os.environ` accessor module
  - Reads core environment knobs directly from `os.environ`
  - No real import of `automojo.runtime`, `automojo.thisapp`, or `automojo.configuration`
  - Replaces `RuntimeVariables` attribute access for the core
  - _Requirements: 4.1, 4.2, 4.4, 4.5_
- [x] Expose the core environment knob accessors
  - `AM_DEBUG_DEBUGGER`, `AM_DEBUG_BREAKPOINTS`
  - `AM_DIAGNOSTICS_PRERUN`, `AM_DIAGNOSTICS_POSTRUN`
  - `AM_TESTROOT`, `AM_OUTPUT_DIRECTORY`, `AM_RUN_ID`, `AM_TESTRUN_TIMEOUT`
  - _Requirements: 4.3_

#### Output-Location Seam (`output/outputcontext.py`)
- [x] Implement the `IOutputContext` seam and `SimpleOutputContext` default
  - Default roots all artefacts under a single base directory
  - `get_test_results_dir()`, `get_testcase_byproducts_dir(scope_id)`, `get_diagnostics_dir(label)`
  - `get_summary_template_source()`, `get_static_resource_source()`, `get_static_resource_destination()`
  - No real import of the higher layers; package names appear only in docstring negations
  - Replaces the `get_path_for_*` / well-known path family
  - _Requirements: 5.1, 5.5, 5.6_

#### Run-Identity Seam (`output/runmetadata.py`)
- [x] Implement the `IRunMetadata` seam and `StandaloneRunMetadata` default
  - Default sources identity from the environment module and standalone defaults
  - `run_id`, `apod`, `title`, `starttime`, `testrun_timeout`, `job_seed` properties
  - `build_info()`, `pipeline_info()`, `job_info()` methods
  - No real import of the higher layers; package names appear only in docstring negations
  - Replaces the `RuntimeVariables`-sourced CI/build/pipeline/job metadata
  - _Requirements: 5.2, 5.5, 5.6_

#### Standalone Default Recorder (`results/recorders/stdoutresultrecorder.py`)
- [x] Make `StdoutResultRecorder` the standalone default result recorder
  - Emits JSOS and JSON artefacts when an output directory is given
  - Emits a stdout summary; SKIPS HTML rendering
  - No real import of the higher layers
  - Replaces the heavyweight `JsonResultRecorder` (HTML) as the DEFAULT
  - _Requirements: 5.3, 5.4, 5.5, 5.6_

#### Out-of-Package Integration Variants (`automojo-integration-runtime`)
- [x] Stand up `automojo-integration-runtime` building ON TOP of testbase
  - Supplies `RuntimeOutputContext`, `RuntimeRunMetadata`, `JsonResultRecorder` (HTML)
  - Variants bound via `IntegratedTestJob` hook overrides, not by core branching
  - Declares `automojo-testbase`, `automojo-this-app`, `automojo-extension`, `automojo-errors`, `automojo-xmodules` (plus `debugpy`)
  - `automojo-testbase` declares no reverse dependency on `automojo-integration-runtime`
  - `automojo-testbase` declares no dependency on `automojo-extension`
  - _Requirements: 6.1, 6.2, 6.3, 6.5, 8.5, 8.6_
- [x] Move the runtime foundation into `automojo-this-app`
  - `automojo-this-app` now OWNS `RuntimeVariables`, well-known paths, `ActivationProfile`/`JobType`, `activate_profile_*`
  - Foundation absorbed from the retired `automojo-runtime` package
  - _Requirements: 6.4_

#### Import-Coupling Inventory (documentation of the as-built coupling boundary)
- [x] Enumerate the import-coupled CLI / bootstrap / server surface
  - Identified as `initialize.py`, `cli/testbase_command.py`, `cli/utilities.py`, `cli/cmdtree/testing/run.py`, `cli/cmdtree/testing/jobs.py`, `cli/cmdtree/testing/query.py`, `cli/cmdtree/services/results.py`, `server/resultserver.py`
  - Classified import-coupled only where a REAL `import` of the higher layers exists
  - _Requirements: 7.1, 7.2, 7.3_
- [x] Distinguish Docstring-Only Mentions from Import-Coupled files
  - `environment.py`, `output/outputcontext.py`, `output/runmetadata.py` classified Docstring-Only
  - A plain text grep over those files matches package names only inside docstring negations
  - _Requirements: 7.4_

#### As-Built Versus Pending Documentation
- [x] Record the current 8-dependency set as as-built and the 5-dependency target honestly
  - Current set documented: errors, arcli, this-app, configuration, runtime, interfaces, xmodules, waiting
  - Python version constraint documented as `>=3.10,<4.0`
  - Drop-pending set documented as this-app, configuration, runtime — NOT yet removed
  - _Requirements: 1.2, 2.1, 2.2, 9.1, 9.2, 9.3_
- [x] Document the Permanent-Unittest Exclusion Set and the extension nuance
  - Exclusion set: errors, interfaces, waiting, xmodules, arcli, extension
  - `automojo-extension` recorded as a member of the exclusion set and NOT a testbase dependency
  - _Requirements: 8.1, 8.4, 8.5, 8.6_
- [x] Record the TestJob chain as-built (siblings) rather than the linear Phase-5 target
  - `IntegratedTestJob` and `InteropLibraryTestJob` documented as current siblings extending `TestJob` directly
  - Linear `TestJob -> IntegratedTestJob -> InteropLibraryTestJob -> DistributedTestJob` marked as a Phase-5 target
  - _Requirements: 9.5, 9.6_

---

### In Progress

#### CLI / Bootstrap / Server Relocation (standalone-vs-integration split)
- [ ] Split the CLI into a standalone testbase-cli and an integration bootstrap
  - Move `initialize.py` bootstrap into `automojo-integration-runtime`
  - Move the import-coupled CLI surface (`cli/testbase_command.py`, `cli/utilities.py`, `cli/cmdtree/testing/run.py`, `cli/cmdtree/testing/jobs.py`, `cli/cmdtree/testing/query.py`, `cli/cmdtree/services/results.py`) to the standalone bootstrap layer
  - `cli/utilities.py` falls back to `AM_TESTROOT` via `environment.py` instead of `RuntimeVariables`
  - Relocate or refactor `server/resultserver.py` off `RuntimeVariables`/`RuntimeVariablesDesc`
  - On completion, no file under `automojo-testbase` retains a real import of `automojo.runtime`, `automojo.thisapp`, or `automojo.configuration`
  - _Requirements: 7.5, 9.3, 9.4_

---

### Planned Tasks

#### Integration-Contract Test Relocation
- [ ] Move tests that exercise runtime / this-app / configuration behavior out of testbase
  - Relocate integration-contract tests into `automojo-integration-runtime`
  - Leave behind only tests that exercise the dependency-free core and the standalone seam defaults
  - Ensure the relocated tests do not re-introduce a higher-layer import edge into testbase
  - _Requirements: 2.4, 9.4_

#### Drop the Drop-Pending Dependencies from `pyproject.toml`
- [ ] Remove `automojo-this-app`, `automojo-configuration`, and `automojo-runtime` from `[tool.poetry.dependencies]`
  - Predicated on the CLI relocation and integration-contract test relocation completing first
  - Leaves the target 5-dependency set: arcli, errors, interfaces, waiting, xmodules
  - Preserve the Python version constraint `>=3.10,<4.0`
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.3, 2.4, 2.5_

#### Lockfile Cascade (in dependency order)
- [ ] Regenerate `poetry.lock` across dependent packages after the drop
  - Run the cascade in dependency order so downstream consumers re-resolve cleanly (step-by-step order in the [Lockfile Cascade (worked example)](#lockfile-cascade-worked-example) section below)
  - Confirm no dependent package transitively re-introduces this-app/configuration/runtime through testbase
  - _Requirements: 2.4_

#### Dependency-Posture Verification (CI guard)
- [ ] Add a declared-dependency assertion test
  - Assert `[tool.poetry.dependencies]` is exactly the 8-package set today
  - Switch the assertion to the 5-package target set once the drop completes
  - Confirm the Python constraint is `>=3.10,<4.0`
  - _Requirements: 1.1, 1.2, 2.1_
- [ ] Add an import-direction static guard
  - Static check that no module under the test-execution core contains a real import of the higher layers
  - Confirm the import-coupled set is exactly the CLI/bootstrap/server surface and only that
  - Confirm the Docstring-Only Mention files contain no real import of the higher layers
  - _Requirements: 3.1, 7.1, 7.2, 7.3, 7.4_
- [ ] Add an integration-variant isolation guard
  - Confirm `RuntimeOutputContext`, `RuntimeRunMetadata`, `JsonResultRecorder` are sourced from `automojo-integration-runtime`, not testbase
  - Confirm testbase declares no dependency on `automojo-integration-runtime` and none on `automojo-extension`
  - _Requirements: 6.1, 6.5, 8.5, 8.6_

#### Phase-5 TestJob Linearization (deferred target)
- [ ] Linearize the TestJob inheritance chain
  - Target chain `TestJob -> IntegratedTestJob -> InteropLibraryTestJob -> DistributedTestJob`
  - Deferred; current state remains the sibling arrangement
  - _Requirements: 9.5, 9.6_

---

## Relocation Roadmap (sequencing checklist)

This checklist sequences the remaining package-dependency work and links the CLI / bootstrap /
server relocation to the dependency-drop and the lockfile cascade. It complements (does not
replace) the Planned Tasks above and the roadmap's CLI relocation PLAN; it expresses the same
work as an ordered three-phase gate so that the drop cannot run before its prerequisites. Every
item is unchecked because none of this phase has been performed yet.

#### Phase A — Relocate the import-coupled surface
- [ ] Keep the standalone testbase CLI minimal on the dependency-free core
  - The standalone testbase CLI keeps `testbase run` / `testbase query` on `DefaultTestJob` + the stdout recorder
  - The standalone CLI sources `AM_TESTROOT` and the core knobs from `environment.py`, never `RuntimeVariables`
- [ ] Move the rich CLI surface into a new `automojo-integration` CLI in `automojo-integration-runtime`
  - Relocate the rich `testing` / `run` / `query` / `jobs` command tree, the `services`, the `server`, and `optionoverrides`
  - Relocate the `initialize.py` bootstrap alongside the rich CLI surface
- [ ] On completion, no file under `automojo-testbase` retains a real import of `automojo.runtime`, `automojo.thisapp`, or `automojo.configuration`
  - See the In Progress task "CLI / Bootstrap / Server Relocation" for the per-file inventory
  - _Requirements: 7.5, 9.3, 9.4_

#### Phase B — Relocate the integration-contract tests
- [ ] Move the ~18 RuntimeVariables / presence / CI integration-contract tests dropped from testbase onto `IntegratedTestJob`
  - Rehome them into `automojo-integration-runtime` where the real `RuntimeVariables` / this-app facilities live
  - Leave behind in testbase only tests exercising the dependency-free core and the standalone seam defaults
  - Ensure the relocated tests do not re-introduce a higher-layer import edge into testbase
  - See the Planned task "Integration-Contract Test Relocation"
  - _Requirements: 2.4, 9.4_

#### Phase C — Drop the drop-pending edges and run the lockfile cascade
- [ ] Remove `automojo-this-app`, `automojo-configuration`, and `automojo-runtime` from testbase `pyproject.toml`
  - Gated on Phase A and Phase B completing first
  - Leaves the target 5-dependency set: arcli, errors, interfaces, waiting, xmodules
  - Preserve the Python version constraint `>=3.10,<4.0`
- [ ] Run the lockfile cascade in dependency order (see the Lockfile Cascade worked example below)
  - Confirm no dependent package transitively re-introduces this-app/configuration/runtime through testbase
  - _Requirements: 1.1, 1.3, 1.4, 1.5, 2.3, 2.4, 2.5_

---

## Lockfile Cascade (worked example)

The authoritative ordering is §6 of the roadmap (Dependency-update order & lockfile sequence);
this worked example reproduces it and MUST NOT contradict it. Each step lists the actual change
and an explicit `poetry lock`. **None of these locks have been run yet** — the environment is
stale and this is pending the rehome of the CLI / bootstrap / server surface and the
integration-contract tests (Phase A and Phase B above).

The three testbase-relevant steps are 1 (`this-app`), 2 (`integration-runtime`), and 3
(`testbase` drop), in that order; steps 4-13 are the downstream consumers that re-resolve after
the drop.

| # | Package | Change | Lock |
|---|---------|--------|------|
| 1 | this-app | Absorb the runtime modules; add `xmodules` | `poetry lock` (pending) |
| 2 | integration-runtime | Name `automojo-integration-runtime`; deps `testbase`, `this-app`, `extension`, `errors`, `xmodules` | `poetry lock` (pending) |
| 3 | testbase | Remove `configuration`, `runtime`, `this-app` -> target set `arcli`, `errors`, `interfaces`, `waiting`, `xmodules` | `poetry lock` (pending) |
| 4 | storage-database | Drop phantom `runtime` dep | `poetry lock` (pending) |
| 5 | webservice-flask | `runtime` -> `this-app` | `poetry lock` (pending) |
| 6 | taskplus | `runtime` -> `this-app` | `poetry lock` (pending) |
| 7 | landscaping | Repoint `runtime` imports -> `this-app` | `poetry lock` (pending) |
| 8 | interop | Add `integration-runtime` + `this-app` | `poetry lock` (pending) |
| 9 | interop-ext-upnp | Repoint `runtime` import -> `this-app` | `poetry lock` (pending) |
| 10 | testplus | `runtime` -> `this-app`; add `integration-runtime` | `poetry lock` (pending) |
| 11 | automation-kit | `runtime` -> `integration-runtime`; dedupe `testbase` ref | `poetry lock` (verify last, pending) |
| 12 | website-automationmojo / pychestrate-client | Reconcile `runtime` imports (census) | `poetry lock` (pending) |
| 13+ | each Phase-7 shifted package | Add `testbase` dev dep | `poetry lock` (pending) |

**Cycle-check:** `integration-runtime -> testbase` is one-way because testbase drops
`runtime` / `this-app` in step 3, so the cascade introduces no new dependency cycle.

_Requirements: 2.4_

---

## Enhancement Opportunities

### Short-term Improvements

1. **Dependency-Posture Guards**
   - Wire the declared-dependency and import-direction assertions into CI so regressions fail fast
   - Add a check that the import-coupled inventory in the design doc matches reality

2. **Relocation Sequencing Documentation**
   - Maintain a running checklist of which import-coupled file has been relocated
   - Track per-file removal of the last real higher-layer import

3. **Seam Documentation**
   - Document the standalone-vs-integration seam binding for downstream package authors
   - Provide a worked example of overriding the seams from an integration package

### Medium-term Improvements

1. **Target-Set Enforcement**
   - After the drop, lock the target 5-dependency set with a guard that forbids re-adding the higher layers
   - Add a guard that forbids adding `automojo-extension` as a direct testbase dependency

2. **Exclusion-Set Tooling**
   - Provide a helper that flags any attempt to use testbase to test a Permanent-Unittest Exclusion Set package
   - Surface the exclusion rationale in tooling error messages

### Long-term Improvements

1. **Monorepo Dependency-Graph Validation**
   - Static acyclicity check across all `automojo-*` packages
   - Automated detection of import-direction inversions before merge

2. **Phase-5 Linearization**
   - Complete the linear TestJob chain and retire the sibling arrangement
   - Re-validate the dependency posture after linearization

---

## Requirements Traceability

| Requirement | Status | Implementation / Documentation Location |
|-------------|--------|------------------------------------------|
| 1.1 | ⬜ Pending | Drop-pending removal from `pyproject.toml` (target 5-dep set) |
| 1.2 | ✅ Complete | `pyproject.toml` Python constraint `>=3.10,<4.0` |
| 1.3 | ⬜ Pending | Drop-pending removal of this-app/configuration/runtime |
| 1.4 | ✅ Complete | `pyproject.toml` (extension never declared) |
| 1.5 | ⬜ Pending | Reached only after the drop completes |
| 2.1 | ✅ Complete | `pyproject.toml` current 8-dependency set documented |
| 2.2 | ✅ Complete | Drop-pending set documented (this-app, configuration, runtime) |
| 2.3 | ⬜ Pending | Drop has NOT occurred; edges remain in `pyproject.toml` |
| 2.4 | ⬜ Pending | Sequenced: CLI relocation → contract-test relocation → lockfile cascade |
| 2.5 | ⬜ Pending | Drop-pending edges retained while CLI/server import-coupled |
| 3.1-3.2 | ✅ Complete | Core modules; zero real higher-layer imports |
| 3.3 | ✅ Complete | Import smoke tests (roadmap §11) |
| 3.4 | ✅ Complete | Docstring negations in core modules |
| 3.5 | ✅ Complete | Import smoke tests verify isolation |
| 4.1-4.2 | ✅ Complete | `environment.py` (`os.environ` accessors) |
| 4.3 | ✅ Complete | `environment.py` knob accessors |
| 4.4-4.5 | ✅ Complete | `environment.py` (no higher-layer import; no RuntimeVariables) |
| 5.1 | ✅ Complete | `output/outputcontext.py::IOutputContext`, `SimpleOutputContext` |
| 5.2 | ✅ Complete | `output/runmetadata.py::IRunMetadata`, `StandaloneRunMetadata` |
| 5.3-5.4 | ✅ Complete | `results/recorders/stdoutresultrecorder.py::StdoutResultRecorder` |
| 5.5 | ✅ Complete | Seam modules; zero real higher-layer imports |
| 5.6 | ✅ Complete | Seams replace RuntimeVariables / `get_path_for_*` / JSON-HTML default |
| 6.1-6.2 | ✅ Complete | `automojo-integration-runtime` variants via `IntegratedTestJob` hooks |
| 6.3 | ✅ Complete | `automojo-integration-runtime` `pyproject.toml` dependencies |
| 6.4 | ✅ Complete | `automojo-this-app` owns the absorbed runtime foundation |
| 6.5 | ✅ Complete | `pyproject.toml` (no reverse edge to integration-runtime) |
| 7.1-7.2 | ✅ Complete | Import-Coupling Inventory (design doc) |
| 7.3 | ✅ Complete | Real-import classification rule (design doc) |
| 7.4 | ✅ Complete | Docstring-Only Mention table (design doc) |
| 7.5 | ⬜ Pending | CLI/bootstrap/server relocation in progress |
| 8.1 | ✅ Complete | Permanent-Unittest Exclusion Set documented |
| 8.2-8.3 | ✅ Complete | Import-direction rule (design doc) |
| 8.4 | ✅ Complete | Extension recorded as exclusion-set member |
| 8.5 | ✅ Complete | `pyproject.toml` (extension not a dependency) |
| 8.6 | ✅ Complete | Extension attaches in `automojo-integration-runtime` |
| 9.1 | ✅ Complete | Core decoupling / seams / environment marked as-built |
| 9.2 | ✅ Complete | Drop-pending removal marked pending |
| 9.3 | ⬜ Pending | CLI/bootstrap/server relocation marked pending |
| 9.4 | ⬜ Pending | Sequence documented: CLI → contract tests → lockfile cascade |
| 9.5-9.6 | ✅ Complete | TestJob siblings as-built; linear chain marked Phase-5 target |

---

## Status Summary

| Work Stream | Status |
|-------------|--------|
| Decoupled test-execution core | ✅ Complete |
| Dependency-free environment accessor | ✅ Complete |
| Output / run-identity / recorder seams | ✅ Complete |
| Standalone default recorder | ✅ Complete |
| Runtime foundation moved into `automojo-this-app` | ✅ Complete |
| Out-of-package integration variants (`automojo-integration-runtime`) | ✅ Complete |
| Import-coupling inventory documented | ✅ Complete |
| CLI / bootstrap / server relocation | ⚠️ In Progress |
| Integration-contract test relocation | ⬜ Pending |
| Drop this-app / configuration / runtime from `pyproject.toml` | ⬜ Pending |
| Lockfile cascade (dependency order) | ⬜ Pending |
| Phase-5 TestJob linearization | ⬜ Deferred |

**Legend:** ✅ = Complete, ⚠️ = In Progress, ⬜ = Pending / Not Started

---

## Known Limitations

1. **Drop-Pending Edges Remain**: `automojo-testbase` still declares `automojo-this-app`,
   `automojo-configuration`, and `automojo-runtime` today; the target 5-dependency set is not
   yet reached.
2. **CLI / Bootstrap / Server Still Coupled**: `initialize.py`, the five CLI files, and
   `server/resultserver.py` retain real imports of the higher layers and hold testbase above
   them in the dependency tree until relocation completes.
3. **Sequenced Removal**: The drop cannot occur until the CLI relocation and the
   integration-contract test relocation are done; only then can the lockfile cascade run.
4. **Lockfile Cascade Pending**: Downstream `poetry.lock` regeneration across dependent
   packages has not yet been performed; the dependency posture of consumers will shift only
   after the cascade.
5. **TestJob Chain Not Linear**: `IntegratedTestJob` and `InteropLibraryTestJob` are currently
   siblings of `TestJob`; the linear Phase-5 chain is a target, not the current state.
</content>
</invoke>
