"""
    Property-based tests for InjectionScope scope tree invariants.

    Tests cover:
    - All registered origins are retrievable (Requirements 6.1, 6.2, 6.3)
    - Pruning preserves relevant scopes (Requirements 7.3, 7.4)
    - Parameter visibility inheritance (Requirements 8.2, 8.3, 8.6)

    **Feature: dependencies, Property 1: Registered origins retrievable**
    **Validates: Requirements 6.1, 6.2, 6.3**

    **Feature: dependencies, Property 2: Pruning preserves relevant scopes**
    **Validates: Requirements 7.3, 7.4**

    **Feature: dependencies, Property 3: Parameter visibility inheritance**
    **Validates: Requirements 8.2, 8.3, 8.6**
"""

import unittest

from hypothesis import given, settings, assume, HealthCheck
from hypothesis import strategies as st

from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.injection.injectionmoment import InjectionMoment
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.origins.validatororigin import ValidatorOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.sourcebase import SourceBase


def sample_source_func():
    """Sample source function for testing."""
    return "resource"


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


# Strategies for generating test data
identifier_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_'),
    min_size=1,
    max_size=20
).filter(lambda x: x[0].isalpha() or x[0] == '_')

scope_component_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('Ll', 'Lu'), whitelist_characters='_'),
    min_size=1,
    max_size=15
).filter(lambda x: x[0].isalpha())

lifespan_strategy = st.sampled_from([
    ResourceLifespan.Session,
    ResourceLifespan.Package,
    ResourceLifespan.Test,
    ResourceLifespan.Task
])


@st.composite
def scope_path_strategy(draw, min_depth=1, max_depth=4):
    """Generate a valid scope path like 'pkg.module#func'."""
    depth = draw(st.integers(min_value=min_depth, max_value=max_depth))
    components = [draw(scope_component_strategy) for _ in range(depth)]
    
    # Last component is the function name (after #)
    if depth > 1:
        module_path = ".".join(components[:-1])
        func_name = components[-1]
        return f"{module_path}#{func_name}"
    else:
        return f"{components[0]}#test_func"


@st.composite
def resource_origin_strategy(draw):
    """Generate a ResourceOrigin with valid scope path and identifier."""
    scope_path = draw(scope_path_strategy())
    identifier = draw(identifier_strategy)
    lifespan = draw(lifespan_strategy)
    source = MockSourceBase(sample_source_func)
    return ResourceOrigin(scope_path, identifier, lifespan, source)


@st.composite
def validator_origin_strategy(draw):
    """Generate a ValidatorOrigin with valid scope path and identifier."""
    scope_path = draw(scope_path_strategy())
    identifier = draw(identifier_strategy)
    suffix = draw(st.text(min_size=1, max_size=10, alphabet='abcdefghijklmnopqrstuvwxyz'))
    source = MockSourceBase(sample_source_func)
    return ValidatorOrigin(scope_path, identifier, suffix, source)


@st.composite
def multiple_origins_strategy(draw, min_count=1, max_count=5):
    """Generate multiple resource origins with unique identifiers per scope."""
    count = draw(st.integers(min_value=min_count, max_value=max_count))
    origins = []
    seen_scope_ids = set()
    
    for _ in range(count):
        scope_path = draw(scope_path_strategy())
        identifier = draw(identifier_strategy)
        
        # Ensure unique (scope, identifier) pairs
        key = (scope_path, identifier)
        if key in seen_scope_ids:
            continue
        seen_scope_ids.add(key)
        
        lifespan = draw(lifespan_strategy)
        source = MockSourceBase(sample_source_func)
        origins.append(ResourceOrigin(scope_path, identifier, lifespan, source))
    
    assume(len(origins) > 0)
    return origins


class InjectionScopePropertyTests(unittest.TestCase):
    """Property-based tests for InjectionScope invariants."""

    @given(resource_origin_strategy())
    @settings(max_examples=100)
    def test_property_registered_resource_origin_is_retrievable(self, origin):
        """
        **Feature: dependencies, Property 1: Registered origins retrievable**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        *For any* resource origin registered in the scope tree,
        the origin should be retrievable via has_descendent_resource.
        """
        root = InjectionScope()
        
        # Register the origin
        root.add_descendent_resource_origination(origin.originating_scope, origin)
        
        # Verify it's retrievable
        self.assertTrue(
            root.has_descendent_resource(origin.originating_scope, origin.identifier),
            f"Origin '{origin.identifier}' at scope '{origin.originating_scope}' should be retrievable"
        )

    @given(validator_origin_strategy())
    @settings(max_examples=100)
    def test_property_registered_validator_origin_is_retrievable(self, validator):
        """
        **Feature: dependencies, Property 1: Registered origins retrievable**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        *For any* validator origin registered in the scope tree,
        the origin should be retrievable via has_descendent_validator.
        """
        root = InjectionScope()
        
        # Register the validator
        root.add_descendent_validator_origination(validator.originating_scope, validator)
        
        # Verify it's retrievable
        self.assertTrue(
            root.has_descendent_validator(validator.originating_scope, validator.identifier),
            f"Validator '{validator.identifier}' at scope '{validator.originating_scope}' should be retrievable"
        )

    @given(multiple_origins_strategy())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_property_all_registered_origins_are_retrievable(self, origins):
        """
        **Feature: dependencies, Property 1: Registered origins retrievable**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        *For any* set of resource origins registered in the scope tree,
        all origins should be retrievable via has_descendent_resource.
        """
        root = InjectionScope()
        
        # Register all origins
        for origin in origins:
            root.add_descendent_resource_origination(origin.originating_scope, origin)
        
        # Verify all are retrievable
        for origin in origins:
            self.assertTrue(
                root.has_descendent_resource(origin.originating_scope, origin.identifier),
                f"Origin '{origin.identifier}' at scope '{origin.originating_scope}' should be retrievable"
            )

    @given(resource_origin_strategy())
    @settings(max_examples=100)
    def test_property_scope_lookup_returns_correct_scope(self, origin):
        """
        **Feature: dependencies, Property 1: Registered origins retrievable**
        **Validates: Requirements 6.1, 6.2, 6.3**
        
        *For any* resource origin registered in the scope tree,
        looking up the scope should return a scope containing the origin.
        """
        root = InjectionScope()
        
        # Register the origin
        root.add_descendent_resource_origination(origin.originating_scope, origin)
        
        # Lookup the scope
        scope = root.lookup_scope(origin.originating_scope)
        
        # Verify scope exists and contains the origin
        self.assertIsNotNone(scope, f"Scope '{origin.originating_scope}' should exist")
        self.assertIn(
            origin.identifier,
            scope.parameter_originations,
            f"Scope should contain origin '{origin.identifier}'"
        )


class InjectionScopePruningPropertyTests(unittest.TestCase):
    """Property-based tests for scope pruning invariants."""

    def _create_injection_moment(self, module_name, func_name):
        """Helper to create an InjectionMoment with a mock function."""
        def mock_func():
            pass
        mock_func.__module__ = module_name
        mock_func.__name__ = func_name
        return InjectionMoment(mock_func)

    @given(scope_path_strategy())
    @settings(max_examples=100)
    def test_property_pruning_preserves_relevant_scopes(self, scope_path):
        """
        **Feature: dependencies, Property 2: Pruning preserves relevant scopes**
        **Validates: Requirements 7.3, 7.4**
        
        *For any* scope path that has an injection moment,
        after pruning, all scopes along the path should be preserved.
        """
        root = InjectionScope()
        
        # Parse scope path to create injection moment
        if "#" in scope_path:
            module_path, func_name = scope_path.split("#")
        else:
            module_path = scope_path
            func_name = "test_func"
        
        inj_mom = self._create_injection_moment(module_path, func_name)
        
        # Ensure injection scopes (marks them as relevant)
        root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # Prune unreferenced scopes
        root.prune_unreference_scopes()
        
        # Verify the scope path still exists
        scope = root.lookup_scope(scope_path)
        self.assertIsNotNone(
            scope,
            f"Scope '{scope_path}' should be preserved after pruning"
        )

    @given(st.lists(scope_path_strategy(), min_size=1, max_size=5, unique=True))
    @settings(max_examples=100)
    def test_property_pruning_preserves_all_relevant_scope_paths(self, scope_paths):
        """
        **Feature: dependencies, Property 2: Pruning preserves relevant scopes**
        **Validates: Requirements 7.3, 7.4**
        
        *For any* set of scope paths with injection moments,
        after pruning, all scope paths should be preserved.
        """
        root = InjectionScope()
        injection_moments = []
        
        # Create injection moments for all paths
        for scope_path in scope_paths:
            if "#" in scope_path:
                module_path, func_name = scope_path.split("#")
            else:
                module_path = scope_path
                func_name = "test_func"
            
            inj_mom = self._create_injection_moment(module_path, func_name)
            injection_moments.append((scope_path, inj_mom))
            root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # Prune unreferenced scopes
        root.prune_unreference_scopes()
        
        # Verify all scope paths still exist
        for scope_path, _ in injection_moments:
            scope = root.lookup_scope(scope_path)
            self.assertIsNotNone(
                scope,
                f"Scope '{scope_path}' should be preserved after pruning"
            )

    @given(scope_path_strategy(), scope_path_strategy())
    @settings(max_examples=100)
    def test_property_pruning_removes_non_relevant_scopes(self, relevant_path, non_relevant_path):
        """
        **Feature: dependencies, Property 2: Pruning preserves relevant scopes**
        **Validates: Requirements 7.3, 7.4**
        
        *For any* two distinct scope paths where only one has an injection moment,
        after pruning, only the relevant scope path should be preserved.
        """
        # Skip if paths are the same or one is a prefix of the other
        assume(relevant_path != non_relevant_path)
        relevant_normalized = relevant_path.replace("#", ".")
        non_relevant_normalized = non_relevant_path.replace("#", ".")
        assume(not relevant_normalized.startswith(non_relevant_normalized))
        assume(not non_relevant_normalized.startswith(relevant_normalized))
        
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        
        # Add origin to non-relevant path (but don't create injection moment)
        origin = ResourceOrigin(non_relevant_path, "test_id", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination(non_relevant_path, origin)
        
        # Create injection moment only for relevant path
        if "#" in relevant_path:
            module_path, func_name = relevant_path.split("#")
        else:
            module_path = relevant_path
            func_name = "test_func"
        
        inj_mom = self._create_injection_moment(module_path, func_name)
        root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # Prune unreferenced scopes
        root.prune_unreference_scopes()
        
        # Verify relevant scope exists
        relevant_scope = root.lookup_scope(relevant_path)
        self.assertIsNotNone(
            relevant_scope,
            f"Relevant scope '{relevant_path}' should be preserved"
        )
        
        # Verify non-relevant scope is removed (unless it shares a path with relevant)
        non_relevant_scope = root.lookup_scope(non_relevant_path)
        self.assertIsNone(
            non_relevant_scope,
            f"Non-relevant scope '{non_relevant_path}' should be pruned"
        )


class InjectionScopeVisibilityPropertyTests(unittest.TestCase):
    """Property-based tests for parameter visibility inheritance."""

    def _create_injection_moment(self, module_name, func_name):
        """Helper to create an InjectionMoment with a mock function."""
        def mock_func():
            pass
        mock_func.__module__ = module_name
        mock_func.__name__ = func_name
        return InjectionMoment(mock_func)

    @given(identifier_strategy, scope_path_strategy())
    @settings(max_examples=100)
    def test_property_session_params_visible_to_all_scopes(self, identifier, child_scope_path):
        """
        **Feature: dependencies, Property 3: Parameter visibility inheritance**
        **Validates: Requirements 8.2, 8.3, 8.6**
        
        *For any* parameter defined at session scope,
        it should be visible to all child scopes during resolution.
        """
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        
        # Add parameter at session scope
        session_origin = ResourceOrigin("<session>", identifier, ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", session_origin)
        
        # Create injection moment at child scope
        if "#" in child_scope_path:
            module_path, func_name = child_scope_path.split("#")
        else:
            module_path = child_scope_path
            func_name = "test_func"
        
        inj_mom = self._create_injection_moment(module_path, func_name)
        root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # Resolve parameters - session param should be visible
        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)
        
        # Session parameter should not be in missing params
        missing_names = [mp[0] for mp in missing_params]
        self.assertNotIn(
            identifier,
            missing_names,
            f"Session parameter '{identifier}' should be visible at scope '{child_scope_path}'"
        )

    @given(identifier_strategy)
    @settings(max_examples=100)
    def test_property_local_params_shadow_parent_params(self, identifier):
        """
        **Feature: dependencies, Property 3: Parameter visibility inheritance**
        **Validates: Requirements 8.2, 8.3, 8.6**
        
        *For any* parameter identifier,
        a local definition should shadow a parent definition with the same name.
        """
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        
        # Add parameter at session scope
        session_origin = ResourceOrigin("<session>", identifier, ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", session_origin)
        
        # Add parameter with same identifier at child scope
        child_scope = "pkg.module#test_func"
        child_origin = ResourceOrigin(child_scope, identifier, ResourceLifespan.Test, source)
        root.add_descendent_resource_origination(child_scope, child_origin)
        
        # Create injection moment
        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # Lookup the child scope and verify local origin is present
        scope = root.lookup_scope(child_scope)
        self.assertIsNotNone(scope)
        self.assertIn(identifier, scope.parameter_originations)
        
        # The local origin should be the one in the child scope
        local_origin = scope.parameter_originations[identifier]
        self.assertEqual(local_origin.originating_scope, child_scope)

    @given(st.lists(identifier_strategy, min_size=1, max_size=3, unique=True))
    @settings(max_examples=100)
    def test_property_parameter_visibility_accumulates_down_tree(self, identifiers):
        """
        **Feature: dependencies, Property 3: Parameter visibility inheritance**
        **Validates: Requirements 8.2, 8.3, 8.6**
        
        *For any* set of parameters defined at different scope levels,
        all parameters should be visible at the deepest scope.
        """
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        
        # Define parameters at different levels
        scopes = ["<session>", "pkg", "pkg.module"]
        for i, identifier in enumerate(identifiers):
            scope = scopes[i % len(scopes)]
            if scope == "<session>":
                origin = ResourceOrigin(scope, identifier, ResourceLifespan.Session, source)
            elif scope == "pkg":
                origin = ResourceOrigin(scope, identifier, ResourceLifespan.Package, source)
            else:
                origin = ResourceOrigin(scope, identifier, ResourceLifespan.Test, source)
            root.add_descendent_resource_origination(scope, origin)
        
        # Create injection moment at deepest scope
        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)
        
        # All parameters should be visible (not missing)
        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)
        
        missing_names = [mp[0] for mp in missing_params]
        for identifier in identifiers:
            self.assertNotIn(
                identifier,
                missing_names,
                f"Parameter '{identifier}' should be visible at deepest scope"
            )


if __name__ == "__main__":
    unittest.main()
