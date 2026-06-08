# Package Dependencies - Requirements Document

## Introduction

The Package Dependencies posture defines where the `codecraftai-testbase` package sits within the ccai monorepo dependency tree, the decoupling that has already been achieved, the seam architecture that enables that decoupling, and the remaining work required to reach the target dependency set. The overarching design goal is that `codecraftai-testbase` must be usable to TEST almost every other `codecraftai-*` package; to satisfy that goal the test-execution core must sit at a low position in the dependency tree and must not depend on the application, runtime, or configuration layers. This document captures the inter-package dependency contract of the package: the current declared dependencies, the target declared dependencies, the dependencies pending removal, the import-level decoupling of the execution core, the seams that make the decoupling possible, and the honest as-built-versus-pending boundary that still keeps the CLI, bootstrap, and server surface coupled to higher layers.

### Scope / Not To Be Confused With

This specification describes PACKAGE-LEVEL (inter-package) dependencies — which `codecraftai-*` packages `codecraftai-testbase` declares in its `pyproject.toml` and where it sits in the monorepo dependency tree. It is deliberately distinct from two other testbase specifications whose names invite confusion:

- **`specs/dependencies`** describes the Dependency Injection System (the InjectionRegistry singleton, parameter and validator originations, the scope tree, and resource lifespans). That spec covers WHAT gets injected and HOW the injection registry resolves it at runtime. It does NOT cover which packages `codecraftai-testbase` depends on.
- **`specs/coupling`** describes the Coupling System (the IntegrationCoupling, ConfigurationCoupling, and ValidatorCoupling classes and their integration with the Dependency Injection System). That spec covers HOW couplings register external resources and attach via the DI system. It does NOT cover which packages `codecraftai-testbase` depends on.

When this document refers to "dependencies" it means Python package dependencies declared in `pyproject.toml`, never injectable resources or couplings.

## Glossary

- **Dependency Tree**: The directed acyclic graph of inter-package dependencies among the `codecraftai-*` monorepo packages, where an edge from package A to package B means A declares B in its `[tool.poetry.dependencies]`
- **Current Dependency Set**: The eight packages presently declared in the `codecraftai-testbase` `pyproject.toml`: `codecraftai-errors`, `codecraftai-arcli`, `codecraftai-this-app`, `codecraftai-configuration`, `codecraftai-runtime`, `codecraftai-interfaces`, `codecraftai-xmodules`, `codecraftai-waiting`
- **Target Dependency Set**: The five packages that `codecraftai-testbase` is intended to declare after the decoupling work completes: `codecraftai-arcli`, `codecraftai-errors`, `codecraftai-interfaces`, `codecraftai-waiting`, `codecraftai-xmodules`
- **Drop-Pending Set**: The three packages slated for removal from the dependency set once the CLI relocation, integration-contract test relocation, and lockfile cascade complete: `codecraftai-this-app`, `codecraftai-configuration`, `codecraftai-runtime`
- **Test-Execution Core**: The dependency-free heart of the package — `testjob.py`, `testgroup.py`, `verification.py`, `markers.py`, `constraints.py`, `entrypoints.py`, `sequencing/testsequencer.py`, and the default recorders — that orchestrates test discovery, sequencing, execution, and result recording
- **Seam**: A dependency-free abstraction (interface plus a standalone default implementation) inserted between the test-execution core and a capability previously sourced from the runtime/this-app/configuration layers
- **IOutputContext**: The seam through which artefact locations (test results, per-testcase by-products, diagnostics) are resolved; default implementation is `SimpleOutputContext`
- **IRunMetadata**: The seam through which run-identity and CI/build/pipeline/job context is resolved; default implementation is `StandaloneRunMetadata`
- **ResultRecorder**: The component that records test results during execution; the standalone default is `StdoutResultRecorder`
- **environment module**: The dependency-free `ccai.testbase.environment` module that reads core environment knobs from `os.environ` without consulting RuntimeVariables
- **Import-Coupled File**: A source file that contains a real `import` statement referencing `ccai.runtime`, `ccai.thisapp`, or `ccai.configuration`, thereby holding the package above those layers in the dependency tree
- **Docstring-Only Mention**: A source file that names the runtime/this-app/configuration packages solely within docstring negations (e.g., "replaces RuntimeVariables reads") and contains NO real import referencing them
- **Integration Runtime**: The `codecraftai-integration-runtime` package, which builds on top of `codecraftai-testbase` to supply the rich integration variants of the seams via hook overrides
- **Permanent-Unittest Exclusion Set**: The set of foundation packages that `codecraftai-testbase` must NOT be used to test and must NOT sit above in the dependency tree: `codecraftai-errors`, `codecraftai-interfaces`, `codecraftai-waiting`, `codecraftai-xmodules`, `codecraftai-arcli`, `codecraftai-extension`
- **Lockfile Cascade**: The downstream `poetry.lock` regeneration across dependent packages that must follow once the drop-pending dependencies are removed from `codecraftai-testbase`

## Requirements

### Requirement 1: Target Dependency Set

**User Story:** As a framework developer, I want `codecraftai-testbase` to declare only the foundation packages it genuinely needs, so that it sits low enough in the dependency tree to test almost every other `codecraftai-*` package.

#### Acceptance Criteria

1. THE Target Dependency Set SHALL consist of exactly five packages: `codecraftai-arcli`, `codecraftai-errors`, `codecraftai-interfaces`, `codecraftai-waiting`, and `codecraftai-xmodules`
2. THE `codecraftai-testbase` package SHALL declare a Python version constraint of `>=3.10,<4.0`
3. THE Target Dependency Set SHALL NOT include `codecraftai-this-app`, `codecraftai-configuration`, or `codecraftai-runtime`
4. THE Target Dependency Set SHALL NOT include `codecraftai-extension`
5. WHEN the Target Dependency Set is reached, THE `codecraftai-testbase` package SHALL declare no dependency on any application, runtime, or configuration layer package

### Requirement 2: Current Dependency Set and Drop-Pending State

**User Story:** As a framework developer, I want the current declared dependencies and the dependencies pending removal recorded honestly, so that the gap between as-built and target state is unambiguous.

#### Acceptance Criteria

1. THE Current Dependency Set SHALL be documented as the eight packages presently declared: `codecraftai-errors`, `codecraftai-arcli`, `codecraftai-this-app`, `codecraftai-configuration`, `codecraftai-runtime`, `codecraftai-interfaces`, `codecraftai-xmodules`, and `codecraftai-waiting`
2. THE Drop-Pending Set SHALL be documented as `codecraftai-this-app`, `codecraftai-configuration`, and `codecraftai-runtime`
3. THE specification SHALL NOT claim that the Drop-Pending Set has already been removed from the declared dependencies
4. THE removal of the Drop-Pending Set SHALL be predicated on completion of the CLI relocation, the integration-contract test relocation, and the lockfile cascade
5. WHILE the CLI, bootstrap, and server surface remains import-coupled to the higher layers, THE `pyproject.toml` SHALL continue to declare the Drop-Pending Set

### Requirement 3: Decoupled Test-Execution Core

**User Story:** As a framework developer, I want the test-execution core to depend on none of the application, runtime, or configuration layers, so that the core can be imported and exercised independently of those layers.

#### Acceptance Criteria

1. THE Test-Execution Core SHALL contain zero real imports from `ccai.configuration`, `ccai.runtime`, or `ccai.thisapp`
2. THE Test-Execution Core SHALL comprise at minimum `testjob.py`, `testgroup.py`, `verification.py`, `markers.py`, `constraints.py`, `entrypoints.py`, `sequencing/testsequencer.py`, and the default recorders
3. WHEN `ccai.testbase.testjob`, `ccai.testbase.sequencing.testsequencer`, `ccai.testbase.entrypoints`, or the default recorders are imported, THE import SHALL pull in zero modules from `ccai.configuration`, `ccai.runtime`, or `ccai.thisapp`
4. WHERE a core module names the runtime, this-app, or configuration packages, THE mention SHALL appear only within docstring negations and SHALL NOT constitute a real import
5. THE decoupling of the Test-Execution Core SHALL be verifiable by import smoke tests

### Requirement 4: Dependency-Free Environment Access

**User Story:** As a framework developer, I want the core to read environment knobs through a dependency-free accessor, so that environment reads do not pull in the runtime variable machinery.

#### Acceptance Criteria

1. THE Test-Execution Core SHALL read core environment knobs through the `ccai.testbase.environment` module
2. THE `ccai.testbase.environment` module SHALL read its values directly from `os.environ`
3. THE `ccai.testbase.environment` module SHALL expose accessors for `AM_DEBUG_DEBUGGER`, `AM_DEBUG_BREAKPOINTS`, `AM_DIAGNOSTICS_PRERUN`, `AM_DIAGNOSTICS_POSTRUN`, `AM_TESTROOT`, `AM_OUTPUT_DIRECTORY`, `AM_RUN_ID`, and `AM_TESTRUN_TIMEOUT`
4. THE `ccai.testbase.environment` module SHALL contain zero real imports from `ccai.runtime`, `ccai.thisapp`, or `ccai.configuration`
5. THE Test-Execution Core SHALL NOT read these environment knobs via `RuntimeVariables` or `ThisApplicationSingleton`

### Requirement 5: Output, Run-Identity, and Recording Seams

**User Story:** As a framework developer, I want artefact locations, run identity, and result recording resolved through dependency-free seams with standalone defaults, so that the core stays decoupled while richer behavior can be injected from above.

#### Acceptance Criteria

1. THE Test-Execution Core SHALL resolve artefact locations through the `IOutputContext` seam, defaulting to `SimpleOutputContext`
2. THE Test-Execution Core SHALL resolve run identity and CI/build/pipeline/job context through the `IRunMetadata` seam, defaulting to `StandaloneRunMetadata`
3. THE Test-Execution Core SHALL record results through a `ResultRecorder`, defaulting to `StdoutResultRecorder`
4. THE `StdoutResultRecorder` default SHALL emit JSOS and JSON artefacts when an output directory is given and SHALL skip HTML rendering
5. THE `IOutputContext`, `IRunMetadata`, and recorder seam modules SHALL contain zero real imports from `ccai.runtime`, `ccai.thisapp`, or `ccai.configuration`
6. THE seams SHALL replace the prior reliance on `RuntimeVariables`, the `get_path_for_*` path family, and the heavyweight JSON/HTML recorder default

### Requirement 6: Out-of-Package Integration Variants

**User Story:** As a framework developer, I want the rich integration variants of the seams to live outside `codecraftai-testbase`, so that the heavyweight runtime/this-app behavior never re-enters the testbase dependency set.

#### Acceptance Criteria

1. THE rich integration variants of the output context, run metadata, and result recorder SHALL live in the `codecraftai-integration-runtime` package
2. THE `codecraftai-integration-runtime` package SHALL supply its variants by overriding hooks via `IntegratedTestJob`
3. THE `codecraftai-integration-runtime` package SHALL declare `codecraftai-testbase`, `codecraftai-this-app`, `codecraftai-extension`, `codecraftai-errors`, and `codecraftai-xmodules` as dependencies
4. THE runtime foundation absorbed from the retired `codecraftai-runtime` package SHALL be owned by `codecraftai-this-app`
5. THE `codecraftai-testbase` package SHALL NOT depend on `codecraftai-integration-runtime`

### Requirement 7: Import-Coupled CLI, Bootstrap, and Server Surface

**User Story:** As a framework developer, I want the files that still couple `codecraftai-testbase` to the higher layers identified precisely, so that the remaining decoupling work has a definite scope.

#### Acceptance Criteria

1. THE specification SHALL identify the import-coupled surface as the CLI, bootstrap, and server files ONLY
2. THE import-coupled files SHALL be enumerated as `initialize.py`, `cli/testbase_command.py`, `cli/utilities.py`, `cli/cmdtree/testing/run.py`, `cli/cmdtree/testing/jobs.py`, `cli/cmdtree/testing/query.py`, `cli/cmdtree/services/results.py`, and `server/resultserver.py`
3. THE specification SHALL classify a file as import-coupled only when it contains a real `import` statement referencing `ccai.runtime`, `ccai.thisapp`, or `ccai.configuration`
4. THE specification SHALL classify `environment.py`, `output/outputcontext.py`, and `output/runmetadata.py` as Docstring-Only Mentions and SHALL NOT classify them as import-coupled
5. WHILE the import-coupled surface retains its real imports, THE `codecraftai-testbase` package SHALL remain above the runtime, this-app, and configuration layers in the dependency tree

### Requirement 8: Permanent-Unittest Exclusion Set

**User Story:** As a framework developer, I want a permanent set of foundation packages that `codecraftai-testbase` must never be used to test, so that no circular dependency is introduced and the package stays low in the dependency tree.

#### Acceptance Criteria

1. THE Permanent-Unittest Exclusion Set SHALL consist of `codecraftai-errors`, `codecraftai-interfaces`, `codecraftai-waiting`, `codecraftai-xmodules`, `codecraftai-arcli`, and `codecraftai-extension`
2. THE `codecraftai-testbase` package SHALL NOT be used to test any package in the Permanent-Unittest Exclusion Set
3. THE `codecraftai-testbase` package SHALL NOT sit above any package in the Permanent-Unittest Exclusion Set in the dependency tree
4. THE `codecraftai-extension` package SHALL be a member of the Permanent-Unittest Exclusion Set
5. THE `codecraftai-extension` package SHALL NOT be a declared dependency of `codecraftai-testbase`
6. WHERE integration with the extension machinery is required, THE attachment SHALL occur in `codecraftai-integration-runtime` rather than in `codecraftai-testbase`

### Requirement 9: As-Built Versus Pending Honesty

**User Story:** As a framework developer, I want the document to clearly separate what is true today from what is targeted, so that readers do not mistake aspirational state for delivered state.

#### Acceptance Criteria

1. THE specification SHALL mark the decoupling of the Test-Execution Core, the dependency-free seams, and the dependency-free environment module as delivered (as-built) state
2. THE specification SHALL mark the removal of the Drop-Pending Set from `pyproject.toml` as pending state
3. THE specification SHALL mark the relocation of the import-coupled CLI, bootstrap, and server surface as pending state
4. THE specification SHALL state that the dependency-set reduction is sequenced as CLI relocation, then integration-contract test relocation, then lockfile cascade
5. THE specification SHALL NOT describe the linear TestJob inheritance chain `TestJob -> IntegratedTestJob -> InteropLibraryTestJob -> DistributedTestJob` as the current state
6. WHERE the TestJob chain is mentioned, THE specification SHALL describe `IntegratedTestJob` and `InteropLibraryTestJob` as current siblings that both extend `TestJob` directly, with the linear chain marked as a Phase-5 target
