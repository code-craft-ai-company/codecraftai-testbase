"""
    Unit tests for InjectionScope class.

    Tests cover:
    - Scope tree construction with nested paths
    - Parameter origination insertion and lookup
    - Scope pruning logic
    - Parameter resolution with visibility inheritance
"""

import collections
import unittest

from automojo.errors.exceptions import SemanticError

from automojo.testbase.injection.injectionscope import InjectionScope
from automojo.testbase.injection.injectionmoment import InjectionMoment
from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.origins.validatororigin import ValidatorOrigin
from automojo.testbase.resourcelifespan import ResourceLifespan
from automojo.testbase.sources.sourcebase import SourceBase


def sample_source_func():
    """Sample source function for testing."""
    return "resource"


def source_with_params(param_a, param_b):
    """Source function with parameters for dependency testing."""
    return f"{param_a}_{param_b}"


def source_with_constraints(constraints):
    """Source function with constraints parameter."""
    return constraints


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class InjectionScopeTreeConstructionTests(unittest.TestCase):
    """Tests for scope tree construction with nested paths."""

    def test_root_scope_initialization(self):
        """Test that root scope initializes with correct default values."""
        root = InjectionScope()

        self.assertIsNone(root.name)
        self.assertIsNone(root.package)
        self.assertEqual(root.children, {})
        self.assertEqual(root.parameter_originations, {})
        self.assertEqual(root.validator_originations, {})
        self.assertFalse(root.is_relevant)

    def test_named_scope_initialization(self):
        """Test that named scope initializes with provided values."""
        scope = InjectionScope(name="test_scope", package="pkg.module", is_inj_scope=True)

        self.assertEqual(scope.name, "test_scope")
        self.assertEqual(scope.package, "pkg.module")

    def test_add_descendent_creates_single_level_scope(self):
        """Test adding a descendent at a single level path."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#func", "resource_id", ResourceLifespan.Test, source)

        root.add_descendent_resource_origination("pkg#func", origin)

        self.assertIn("pkg", root.children)
        pkg_scope = root.children["pkg"]
        self.assertIn("func", pkg_scope.children)
        func_scope = pkg_scope.children["func"]
        self.assertIn("resource_id", func_scope.parameter_originations)

    def test_add_descendent_creates_nested_scope_path(self):
        """Test adding a descendent at a nested path creates all intermediate scopes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.subpkg.module#test_func", "res", ResourceLifespan.Test, source)

        root.add_descendent_resource_origination("pkg.subpkg.module#test_func", origin)

        self.assertIn("pkg", root.children)
        self.assertIn("subpkg", root.children["pkg"].children)
        self.assertIn("module", root.children["pkg"].children["subpkg"].children)
        self.assertIn("test_func", root.children["pkg"].children["subpkg"].children["module"].children)

    def test_add_descendent_to_session_scope(self):
        """Test adding a descendent to the session scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_res", ResourceLifespan.Session, source)

        root.add_descendent_resource_origination("<session>", origin)

        self.assertIn("session_res", root.parameter_originations)
        self.assertIs(root.parameter_originations["session_res"], origin)

    def test_add_descendent_reuses_existing_scope_nodes(self):
        """Test that adding multiple descendents reuses existing scope nodes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("pkg.module#func1", "res1", ResourceLifespan.Test, source)
        origin2 = ResourceOrigin("pkg.module#func2", "res2", ResourceLifespan.Test, source)

        root.add_descendent_resource_origination("pkg.module#func1", origin1)
        root.add_descendent_resource_origination("pkg.module#func2", origin2)

        self.assertEqual(len(root.children), 1)
        self.assertEqual(len(root.children["pkg"].children), 1)
        module_scope = root.children["pkg"].children["module"]
        self.assertEqual(len(module_scope.children), 2)
        self.assertIn("func1", module_scope.children)
        self.assertIn("func2", module_scope.children)

    def test_add_descendent_on_non_root_raises_error(self):
        """Test that calling add_descendent on non-root scope raises SemanticError."""
        non_root = InjectionScope(name="child", package="pkg")
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#func", "res", ResourceLifespan.Test, source)

        with self.assertRaises(SemanticError):
            non_root.add_descendent_resource_origination("pkg#func", origin)


class InjectionScopeValidatorOriginationTests(unittest.TestCase):
    """Tests for validator origination insertion."""

    def test_add_validator_to_session_scope(self):
        """Test adding a validator origin to session scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("<session>", "validator_id", "suffix", source)

        root.add_descendent_validator_origination("<session>", validator)

        self.assertIn("validator_id", root.validator_originations)
        self.assertIs(root.validator_originations["validator_id"], validator)

    def test_add_validator_to_nested_scope(self):
        """Test adding a validator origin to a nested scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("pkg.module#test", "val", "suffix", source)

        root.add_descendent_validator_origination("pkg.module#test", validator)

        test_scope = root.children["pkg"].children["module"].children["test"]
        self.assertIn("val", test_scope.validator_originations)

    def test_add_validator_on_non_root_raises_error(self):
        """Test that calling add_descendent_validator on non-root raises SemanticError."""
        non_root = InjectionScope(name="child", package="pkg")
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("pkg#func", "val", "suffix", source)

        with self.assertRaises(SemanticError):
            non_root.add_descendent_validator_origination("pkg#func", validator)


class InjectionScopeLookupTests(unittest.TestCase):
    """Tests for scope lookup functionality."""

    def test_lookup_session_scope(self):
        """Test looking up the session scope returns root."""
        root = InjectionScope()

        result = root.lookup_scope("<session>")

        self.assertIs(result, root)

    def test_lookup_existing_scope(self):
        """Test looking up an existing scope returns the correct node."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func", origin)

        result = root.lookup_scope("pkg.module#func")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "func")

    def test_lookup_nonexistent_scope_returns_none(self):
        """Test looking up a non-existent scope returns None."""
        root = InjectionScope()

        result = root.lookup_scope("nonexistent.path")

        self.assertIsNone(result)

    def test_lookup_partial_path(self):
        """Test looking up a partial path returns the intermediate scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func", origin)

        result = root.lookup_scope("pkg.module")

        self.assertIsNotNone(result)
        self.assertEqual(result.name, "module")

    def test_has_descendent_resource_returns_true_when_exists(self):
        """Test has_descendent_resource returns True when resource exists."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#func", "my_resource", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg#func", origin)

        result = root.has_descendent_resource("pkg#func", "my_resource")

        self.assertTrue(result)

    def test_has_descendent_resource_returns_false_when_not_exists(self):
        """Test has_descendent_resource returns False when resource doesn't exist."""
        root = InjectionScope()

        result = root.has_descendent_resource("pkg#func", "nonexistent")

        self.assertFalse(result)

    def test_has_descendent_resource_at_session_scope(self):
        """Test has_descendent_resource at session scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_res", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        self.assertTrue(root.has_descendent_resource("<session>", "session_res"))
        self.assertFalse(root.has_descendent_resource("<session>", "other"))

    def test_has_descendent_validator_returns_true_when_exists(self):
        """Test has_descendent_validator returns True when validator exists."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("pkg#func", "my_validator", "suffix", source)
        root.add_descendent_validator_origination("pkg#func", validator)

        result = root.has_descendent_validator("pkg#func", "my_validator")

        self.assertTrue(result)

    def test_has_descendent_validator_returns_false_when_not_exists(self):
        """Test has_descendent_validator returns False when validator doesn't exist."""
        root = InjectionScope()

        result = root.has_descendent_validator("pkg#func", "nonexistent")

        self.assertFalse(result)


class InjectionScopePruningTests(unittest.TestCase):
    """Tests for scope pruning logic."""

    def test_prune_removes_non_relevant_leaf_nodes(self):
        """Test that pruning removes non-relevant leaf nodes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func", origin)

        root.prune_unreference_scopes()

        self.assertEqual(len(root.children), 0)

    def test_prune_preserves_relevant_scopes(self):
        """Test that pruning preserves relevant scopes."""
        root = InjectionScope()
        root._is_relevant = True

        child = InjectionScope(name="child", package="child")
        child._is_relevant = True
        root._children["child"] = child

        grandchild = InjectionScope(name="grandchild", package="child.grandchild")
        grandchild._is_relevant = True
        child._children["grandchild"] = grandchild

        root.prune_unreference_scopes()

        self.assertIn("child", root.children)
        self.assertIn("grandchild", root.children["child"].children)

    def test_prune_removes_non_relevant_branches(self):
        """Test that pruning removes entire non-relevant branches."""
        root = InjectionScope()
        root._is_relevant = True

        relevant_child = InjectionScope(name="relevant", package="relevant")
        relevant_child._is_relevant = True
        root._children["relevant"] = relevant_child

        non_relevant_child = InjectionScope(name="non_relevant", package="non_relevant")
        non_relevant_child._is_relevant = False
        root._children["non_relevant"] = non_relevant_child

        root.prune_unreference_scopes()

        self.assertIn("relevant", root.children)
        self.assertNotIn("non_relevant", root.children)

    def test_prune_works_backwards_from_leaves(self):
        """Test that pruning works backwards from leaves toward root."""
        root = InjectionScope()
        root._is_relevant = True

        child = InjectionScope(name="child", package="child")
        child._is_relevant = False
        root._children["child"] = child

        grandchild = InjectionScope(name="grandchild", package="child.grandchild")
        grandchild._is_relevant = False
        child._children["grandchild"] = grandchild

        root.prune_unreference_scopes()

        self.assertNotIn("child", root.children)


class InjectionScopeEnsureInjectionScopesTests(unittest.TestCase):
    """Tests for ensure_injection_scopes_for_injection_moment."""

    def _create_injection_moment(self, module_name, func_name):
        """Helper to create an InjectionMoment with a mock function."""
        def mock_func():
            pass
        mock_func.__module__ = module_name
        mock_func.__name__ = func_name
        return InjectionMoment(mock_func)

    def test_ensure_creates_scope_nodes_along_path(self):
        """Test that ensure creates scope nodes along the injection moment path."""
        root = InjectionScope()
        inj_mom = self._create_injection_moment("pkg.module", "test_func")

        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        self.assertIn("pkg", root.children)
        self.assertIn("module", root.children["pkg"].children)
        self.assertIn("test_func", root.children["pkg"].children["module"].children)

    def test_ensure_marks_scopes_as_relevant(self):
        """Test that ensure marks all scopes along the path as relevant."""
        root = InjectionScope()
        inj_mom = self._create_injection_moment("pkg.module", "test_func")

        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        self.assertTrue(root.is_relevant)
        self.assertTrue(root.children["pkg"].is_relevant)
        self.assertTrue(root.children["pkg"].children["module"].is_relevant)
        self.assertTrue(root.children["pkg"].children["module"].children["test_func"].is_relevant)

    def test_ensure_reuses_existing_scope_nodes(self):
        """Test that ensure reuses existing scope nodes."""
        root = InjectionScope()
        inj_mom1 = self._create_injection_moment("pkg.module", "test_func1")
        inj_mom2 = self._create_injection_moment("pkg.module", "test_func2")

        root.ensure_injection_scopes_for_injection_moment(inj_mom1)
        root.ensure_injection_scopes_for_injection_moment(inj_mom2)

        self.assertEqual(len(root.children), 1)
        self.assertEqual(len(root.children["pkg"].children), 1)
        module_scope = root.children["pkg"].children["module"]
        self.assertEqual(len(module_scope.children), 2)


class InjectionScopeParameterResolutionTests(unittest.TestCase):
    """Tests for parameter resolution with visibility inheritance."""

    def _create_injection_moment(self, module_name, func_name):
        """Helper to create an InjectionMoment with a mock function."""
        def mock_func():
            pass
        mock_func.__module__ = module_name
        mock_func.__name__ = func_name
        return InjectionMoment(mock_func)

    def test_resolve_finds_parameters_in_parent_scope(self):
        """Test that resolution finds parameters defined in parent scopes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

        self.assertEqual(len(missing_params), 0)

    def test_resolve_tracks_missing_parameters(self):
        """Test that resolution tracks missing parameters."""
        root = InjectionScope()
        source = MockSourceBase(source_with_params)
        origin = ResourceOrigin("pkg.module#test_func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#test_func", origin)

        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

        self.assertEqual(len(missing_params), 2)
        missing_names = [mp[0] for mp in missing_params]
        self.assertIn("param_a", missing_names)
        self.assertIn("param_b", missing_names)

    def test_resolve_skips_reserved_parameter_names(self):
        """Test that resolution skips reserved parameter names like 'constraints'."""
        root = InjectionScope()
        source = MockSourceBase(source_with_constraints)
        origin = ResourceOrigin("pkg.module#test_func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#test_func", origin)

        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

        self.assertEqual(len(missing_params), 0)

    def test_resolve_with_parameter_visibility_inheritance(self):
        """Test that parameters from parent scopes are visible to child scopes."""
        root = InjectionScope()

        parent_source = MockSourceBase(sample_source_func)
        parent_origin = ResourceOrigin("<session>", "param_a", ResourceLifespan.Session, parent_source)
        root.add_descendent_resource_origination("<session>", parent_origin)

        parent_origin_b = ResourceOrigin("pkg", "param_b", ResourceLifespan.Package, parent_source)
        root.add_descendent_resource_origination("pkg", parent_origin_b)

        child_source = MockSourceBase(source_with_params)
        child_origin = ResourceOrigin("pkg.module#test_func", "child_res", ResourceLifespan.Test, child_source)
        root.add_descendent_resource_origination("pkg.module#test_func", child_origin)

        inj_mom = self._create_injection_moment("pkg.module", "test_func")
        root.ensure_injection_scopes_for_injection_moment(inj_mom)

        missing_params = []
        root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

        self.assertEqual(len(missing_params), 0)


class InjectionScopeOriginationOrderTests(unittest.TestCase):
    """Tests for parameter origination insertion order preservation."""

    def test_parameter_originations_preserve_insertion_order(self):
        """Test that parameter originations preserve insertion order."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)

        origin1 = ResourceOrigin("<session>", "first", ResourceLifespan.Session, source)
        origin2 = ResourceOrigin("<session>", "second", ResourceLifespan.Session, source)
        origin3 = ResourceOrigin("<session>", "third", ResourceLifespan.Session, source)

        root.add_descendent_resource_origination("<session>", origin1)
        root.add_descendent_resource_origination("<session>", origin2)
        root.add_descendent_resource_origination("<session>", origin3)

        keys = list(root.parameter_originations.keys())
        self.assertEqual(keys, ["first", "second", "third"])

    def test_validator_originations_preserve_insertion_order(self):
        """Test that validator originations preserve insertion order."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)

        val1 = ValidatorOrigin("<session>", "first_val", "suffix", source)
        val2 = ValidatorOrigin("<session>", "second_val", "suffix", source)
        val3 = ValidatorOrigin("<session>", "third_val", "suffix", source)

        root.add_descendent_validator_origination("<session>", val1)
        root.add_descendent_validator_origination("<session>", val2)
        root.add_descendent_validator_origination("<session>", val3)

        keys = list(root.validator_originations.keys())
        self.assertEqual(keys, ["first_val", "second_val", "third_val"])


if __name__ == "__main__":
    unittest.main()
