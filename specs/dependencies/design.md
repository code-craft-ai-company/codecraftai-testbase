# Dependency Injection System - Design Document

## Overview

The Dependency Injection (DI) System is a core component of the TestBase framework that manages the resolution, instantiation, and lifecycle of injectable resources during test execution. It provides a hierarchical scope tree for parameter visibility, supports multiple resource lifespans, and enables automatic dependency resolution for test functions and resource factories.

The system works in conjunction with the Test Declaration and Registration system to transform registered sources and origins into a runtime dependency graph that can be traversed during test execution.

## Architecture

### High-Level Component Diagram

```mermaid
graph TB
    subgraph "Registry Layer"
        IR[InjectionRegistry]
        ST[Scope Tree Root]
    end
    
    subgraph "Scope Management"
        IS[InjectionScope]
        ISC[Child Scopes]
    end
    
    subgraph "Grouping Layer"
        IG[InjectionGroup]
        IGC[Child Groups]
    end
    
    subgraph "Moment Layer"
        IM[InjectionMoment]
        SUB[Subscriptions]
    end
    
    subgraph "Source Layer"
        SB[SourceBase]
        IS2[IntegrationSource]
        RS[ResourceSource]
        CS[ConfigurationSource]
        VS[ValidatorSource]
    end
    
    subgraph "Origin Layer"
        RO[ResourceOrigin]
        VO[ValidatorOrigin]
    end
    
    subgraph "Coupling Layer"
        IC[IntegrationCoupling]
        CC[ConfigurationCoupling]
    end
    
    IR --> ST
    ST --> IS
    IS --> ISC
    IS --> RO
    IS --> VO
    
    IG --> IGC
    IG --> IM
    IM --> SUB
    
    IR --> IS2
    IR --> RS
    IR --> CS
    IR --> VS
    
    SB --> IS2
    SB --> RS
    SB --> CS
    SB --> VS
    
    RO --> SB
    VO --> SB
    
    IS2 --> IC
    CS --> CC
```

### Components

#### 1. InjectionRegistry (Singleton)

The `InjectionRegistry` is the central singleton that orchestrates the entire dependency injection system. It maintains:

- Source tables for different resource types (integration, resource, configuration, validator)
- A scope tree for hierarchical parameter resolution
- Tables for tracking unknown parameters and referenced couplings

```mermaid
classDiagram
    class InjectionRegistry {
        -instance: InjectionRegistry
        -initialized: bool
        -Dict _integration_source
        -Dict _resource_source
        -Dict _configuration_source
        -Dict _validator_source
        -Dict _unknown_parameters
        -Dict _identifier_subscription_table
        -InjectionScope _scope_tree_root
        -Dict _referenced_integrations
        -Dict _referenced_configurations
        +referenced_integrations: Dict
        +referenced_configurations: Dict
        +unknown_parameters: Dict
        +add_implied_session_resource(identifier)
        +finalize_startup(inj_moments)
        +lookup_resource_scope(scope_name)
        +lookup_resource_source(source_func)
        +lookup_validator_source(source_func)
        +register_integration_source(source)
        +register_resource_source(source)
        +register_configuration_source(source)
        +register_validator_source(source)
        +register_resource_origin(identifier, origin)
        +register_validator_origin(identifier, origin)
        +rename_resource_origins_from_main(new_origin)
    }
```

**Key Responsibilities:**

| Method | Purpose |
|--------|---------|
| `finalize_startup()` | Completes the injection setup after all moments are discovered |
| `register_*_source()` | Registers factory functions for different resource types |
| `register_*_origin()` | Registers parameter origins in the scope tree |
| `lookup_*_source()` | Retrieves source objects by factory function |
| `lookup_resource_scope()` | Finds a scope node by its full path name |

#### 2. InjectionScope

The `InjectionScope` class represents a node in the hierarchical scope tree. Each scope can contain:

- Child scopes (forming a tree structure)
- Parameter originations (resources available at this scope)
- Validator originations (validators available at this scope)

```mermaid
classDiagram
    class InjectionScope {
        -str _name
        -str _package
        -Dict[str, InjectionScope] _children
        -OrderedDict _parameter_originations
        -OrderedDict _validator_originations
        -bool _is_inj_scope
        -bool _is_relevant
        +children: Dict
        +is_relevant: bool
        +name: str
        +package: str
        +parameter_originations: Dict
        +validator_originations: Dict
        +add_descendent_resource_origination(scope, origin)
        +add_descendent_validator_origination(scope, origin)
        +collect_integrations_and_configurations_for_injection_moment(...)
        +ensure_injection_scopes_for_injection_moment(inj_mom)
        +has_descendent_resource(scope_name, identifier)
        +has_descendent_validator(scope_name, identifier)
        +lookup_scope(scope_name)
        +prune_unreference_scopes()
        +rename_resource_origins_from_main(new_origin)
        +resolve_resource_originations_for_injection_moment(inj_mom, missing)
    }
```

**Scope Tree Structure:**

```
<session> (root)
├── package_a
│   ├── module_1
│   │   ├── test_function_1 (injection moment)
│   │   └── test_function_2 (injection moment)
│   └── module_2
│       └── test_function_3 (injection moment)
└── package_b
    └── module_3
        └── test_function_4 (injection moment)
```

#### 3. InjectionGroup

The `InjectionGroup` class organizes injection moments into a hierarchical tree based on module paths. It provides:

- Grouping of related injection moments
- Metadata resolution and propagation
- Resource scope lookup

```mermaid
classDiagram
    class InjectionGroup {
        -str _name
        -str _package
        -Dict _children
        -bool _finalized
        -Dict _metadata
        +children: Dict
        +finalized: bool
        +name: str
        +package: str
        +scope_name: str
        +add_descendent(child_ref, group_type)
        +finalize()
        +get_resource_scope()
        +resolve_metadata(parent_metadata)
    }
```

#### 4. InjectionMoment

The `InjectionMoment` class represents a point in the execution flow where injection occurs. It captures:

- The injectable function reference
- Monikers for test variations
- Pivots for parameterized execution
- Subscription information for dependencies

```mermaid
classDiagram
    class InjectionMoment {
        -FunctionType _inj_function
        -List[str] _monikers
        -OrderedDict _pivots
        -Dict _subscriptions
        -bool _finalized
        +finalized: bool
        +monikers: List[str]
        +pivots: OrderedDict
        +scope_name: str
        +subscriptions: Dict
        +base_name: str
        +function: FunctionType
        +function_parameters
        +module_name: str
        +name: str
        +finalize()
        +is_member_of_metaset(metafilters)
        +resolve_metadata(parent_metadata)
    }
```

#### 5. Source Classes

Source classes wrap factory functions and provide metadata about injectable resources:

```mermaid
classDiagram
    class SourceBase {
        -Callable _source_func
        -Callable _query_func
        -Type _resource_type
        -dict _constraints
        -_subscriptions
        +constraints: dict
        +module_name: str
        +query_function: Callable
        +resource_type: Type
        +source_function: Callable
        +source_signature: Signature
        +source_id: str
        +subscriptions
    }
    
    class IntegrationSource {
        +__init__(source_func, integration_type, constraints)
    }
    
    class ResourceSource {
        +__init__(source_func, query_func, resource_type, constraints)
    }
    
    class ConfigurationSource {
        +__init__(source_func, query_func, config_type, constraints)
    }
    
    class ValidatorSource {
        +__init__(source_func, query_func, validator_type, constraints)
    }
    
    SourceBase <|-- IntegrationSource
    SourceBase <|-- ResourceSource
    SourceBase <|-- ConfigurationSource
    SourceBase <|-- ValidatorSource
```

#### 6. Origin Classes

Origin classes describe where injectable parameters come from:

```mermaid
classDiagram
    class ResourceOrigin {
        -str _originating_scope
        -str _identifier
        -ResourceLifespan _life_span
        -SourceBase _source
        -bool _implied
        -str _constraints_key
        +constraints_key: str
        +identifier: str
        +implied: bool
        +life_span: ResourceLifespan
        +originating_scope: str
        +source_function: Callable
        +source_function_name: str
        +source_signature: Signature
        +source_id: str
        +source_module_name: str
        +source_resource_type: Type
        +describe_source()
        +generate_call(constraints)
    }
    
    class ValidatorOrigin {
        -str _originating_scope
        -str _identifier
        -str _suffix
        -ResourceLifespan _life_span
        -SourceBase _source
        -bool _implied
        -str _constraints_key
        +constraints_key: str
        +identifier: str
        +implied: bool
        +life_span: ResourceLifespan
        +originating_scope: str
        +suffix: str
        +source_function: Callable
        +source_function_name: str
        +source_signature: Signature
        +source_id: str
        +source_module_name: str
        +source_resource_type: Type
        +describe_source()
        +generate_call(constraints)
    }
```

### Data Flow

#### Injection Startup Finalization Flow

The `finalize_startup()` method orchestrates the complete injection setup:

```mermaid
flowchart TD
    A[finalize_startup called] --> B[Step 1: Ensure Injection Scopes]
    B --> C[For each InjectionMoment]
    C --> D[ensure_injection_scopes_for_injection_moment]
    D --> E[Create scope nodes along path]
    E --> F[Mark scopes as relevant]
    
    F --> G[Step 2: Prune Unreferenced Scopes]
    G --> H[prune_unreference_scopes]
    H --> I[Remove non-relevant leaf nodes]
    I --> J[Work backwards to root]
    
    J --> K[Step 3: Resolve Resource Originations]
    K --> L[For each InjectionMoment]
    L --> M[resolve_resource_originations_for_injection_moment]
    M --> N[Walk scope path with param table]
    N --> O{All params resolved?}
    O -->|No| P[Add to missing_params]
    O -->|Yes| Q[Continue]
    
    P --> R[Store in unknown_parameters]
    Q --> S[Step 4: Collect Integrations/Configurations]
    S --> T[collect_integrations_and_configurations]
    T --> U[Build referenced_integrations table]
    T --> V[Build referenced_configurations table]
    
    U --> W[Finalization Complete]
    V --> W
```

#### Parameter Resolution Flow

```mermaid
flowchart TD
    A[Test Function Execution] --> B[Get function parameters]
    B --> C[For each parameter]
    C --> D[Lookup in scope tree]
    D --> E{Found in current scope?}
    E -->|Yes| F[Get ResourceOrigin]
    E -->|No| G[Check parent scope]
    G --> H{At root?}
    H -->|No| D
    H -->|Yes| I[Parameter not found]
    
    F --> J[Get source function]
    J --> K[Check source dependencies]
    K --> L{Has dependencies?}
    L -->|Yes| M[Resolve dependencies recursively]
    L -->|No| N[Call source function]
    M --> N
    N --> O[Return resource instance]
    
    I --> P[Raise UnknownParameterError]
```

#### Scope Tree Construction

```mermaid
flowchart TD
    A[Module Import] --> B[Decorator Execution]
    B --> C[Create Source Object]
    C --> D[Register with InjectionRegistry]
    
    D --> E{Origin Type?}
    E -->|Resource| F[register_resource_origin]
    E -->|Validator| G[register_validator_origin]
    
    F --> H[Parse scope path]
    G --> H
    H --> I[add_descendent_*_origination]
    I --> J[Walk/Create scope nodes]
    J --> K[Insert origin at target scope]
```

### Design Patterns

#### 1. Singleton Pattern

The `InjectionRegistry` uses the singleton pattern to ensure a single global registry:

```python
class InjectionRegistry:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(InjectionRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        thisType = type(self)
        if not thisType._initialized:
            thisType._initialized = True
            # Initialize instance variables
```

#### 2. Composite Pattern

`InjectionScope` and `InjectionGroup` form composite tree structures where nodes can contain other nodes or leaf elements (origins/moments).

#### 3. Chain of Responsibility Pattern

Parameter resolution walks up the scope tree, checking each scope until a matching origin is found or the root is reached.

#### 4. Template Method Pattern

The `SourceBase` class defines the interface for all source types, with subclasses providing specific implementations.

#### 5. Visitor Pattern

The scope tree traversal methods (`ensure_injection_scopes_for_injection_moment`, `resolve_resource_originations_for_injection_moment`) implement visitor-like behavior to process tree nodes.

## Integration Points

### With Test Declaration System

- Sources registered via decorators are stored in the registry's source tables
- Origins created by attachment decorators are inserted into the scope tree
- The registry provides lookup methods for the declaration system

### With Test Execution Engine

- The execution engine calls `finalize_startup()` before test execution
- Resolved parameters are passed to test functions during execution
- The `referenced_integrations` and `referenced_configurations` tables inform the execution engine about required couplings

### With Coupling System

- `IntegrationCoupling` and `ConfigurationCoupling` types are tracked through the source tables
- The `collect_integrations_and_configurations_for_injection_moment()` method identifies all couplings needed for execution

### With Constraints System

- Origins can have associated constraints via `constraints_key`
- The `ConstraintsCatalog` manages constraint storage and lookup
- Constraints are passed to source functions during resource creation

## Configuration

### Resource Lifespan Options

| Lifespan | Scope Level | Description |
|----------|-------------|-------------|
| `Session` | Root (`<session>`) | Resource persists for entire test session |
| `Package` | Package nodes | Resource persists within package scope |
| `Test` | Injection moment | Resource created/destroyed per test |
| `Task` | Sub-test level | Resource created/destroyed per task |

### Scope Naming Convention

Scopes follow a hierarchical naming pattern:

| Pattern | Example | Description |
|---------|---------|-------------|
| `<session>` | `<session>` | Root session scope |
| `package.module` | `tests.unit.test_auth` | Module scope |
| `package.module#function` | `tests.unit.test_auth#test_login` | Injection moment scope |

### Reserved Parameter Names

The following parameter names are reserved and handled specially:

| Name | Purpose |
|------|---------|
| `constraints` | Passes constraint dictionary to source functions |

## Error Handling

### Semantic Errors

`SemanticError` is raised for:

- Attempting to call `add_descendent` on non-root scope
- Duplicate identifier registration in the same scope
- Invalid scope path operations

### Unknown Parameter Tracking

The registry tracks unknown parameters in `_unknown_parameters`:

```python
{
    "module#test_function": [
        ["param_name", param_origin_info],
        ...
    ]
}
```

### Scope Resolution Failures

When a parameter cannot be resolved:

1. The parameter is added to `missing_params` list
2. After finalization, `unknown_parameters` contains all unresolved dependencies
3. The execution engine can report these before test execution

## Testing Strategy

### Unit Testing Focus Areas

1. **InjectionRegistry**
   - Singleton behavior verification
   - Source registration and lookup
   - Origin registration and scope tree insertion
   - Finalization process

2. **InjectionScope**
   - Tree construction and traversal
   - Parameter origination management
   - Scope pruning logic
   - Resource resolution

3. **InjectionGroup**
   - Hierarchical grouping
   - Metadata resolution
   - Descendent management

4. **InjectionMoment**
   - Function reference handling
   - Moniker and pivot management
   - Subscription tracking

5. **Source Classes**
   - Source metadata extraction
   - Signature inspection
   - Constraint handling

6. **Origin Classes**
   - Origin property access
   - Call generation
   - Constraint key management

### Integration Testing

- End-to-end dependency resolution
- Cross-scope parameter visibility
- Integration with execution engine
- Coupling collection verification

### Property-Based Testing Candidates

1. **Scope Tree Invariants**
   - All registered origins are retrievable
   - Pruning preserves relevant scopes
   - No orphaned scope nodes after finalization

2. **Parameter Resolution**
   - Parameters visible in parent scopes are visible in child scopes
   - Local parameters shadow parent parameters with same name
   - Resolution order is deterministic

