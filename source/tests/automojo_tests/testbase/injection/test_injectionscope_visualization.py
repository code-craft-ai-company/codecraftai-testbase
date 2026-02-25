"""
    Unit tests for InjectionScope visualization methods.

    Tests cover:
    - to_tree_diagram() for ASCII tree generation
    - to_dict() for dictionary conversion
    - to_json() for JSON export
"""

import json
import unittest

from automojo.testbase.injection.injectionscope import InjectionScope
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


class InjectionScopeTreeDiagramTests(unittest.TestCase):
    """Tests for to_tree_diagram() method."""

    def test_empty_root_scope_diagram(self):
        """Test tree diagram for empty root scope."""
        root = InjectionScope()

        diagram = root.to_tree_diagram()

        self.assertIn("<session>", diagram)

    def test_root_scope_with_relevant_flag(self):
        """Test tree diagram shows relevant flag."""
        root = InjectionScope()
        root._is_relevant = True

        diagram = root.to_tree_diagram()

        self.assertIn("[relevant]", diagram)

    def test_single_child_scope_diagram(self):
        """Test tree diagram with single child scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#func", "resource_id", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg#func", origin)

        diagram = root.to_tree_diagram()

        self.assertIn("<session>", diagram)
        self.assertIn("pkg", diagram)
        self.assertIn("func", diagram)

    def test_nested_scope_diagram(self):
        """Test tree diagram with nested scopes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.subpkg.module#test_func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.subpkg.module#test_func", origin)

        diagram = root.to_tree_diagram()

        self.assertIn("pkg", diagram)
        self.assertIn("subpkg", diagram)
        self.assertIn("module", diagram)
        self.assertIn("test_func", diagram)

    def test_diagram_shows_parameters(self):
        """Test tree diagram includes parameter names when include_details=True."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "my_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        diagram = root.to_tree_diagram(include_details=True)

        self.assertIn("Parameters:", diagram)
        self.assertIn("my_param", diagram)

    def test_diagram_shows_validators(self):
        """Test tree diagram includes validator names when include_details=True."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("<session>", "my_validator", "suffix", source)
        root.add_descendent_validator_origination("<session>", validator)

        diagram = root.to_tree_diagram(include_details=True)

        self.assertIn("Validators:", diagram)
        self.assertIn("my_validator", diagram)

    def test_diagram_without_details(self):
        """Test tree diagram excludes details when include_details=False."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "my_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        diagram = root.to_tree_diagram(include_details=False)

        self.assertNotIn("Parameters:", diagram)

    def test_diagram_shows_injection_scope_flag(self):
        """Test tree diagram shows inj_scope flag for injection moment scopes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#test_func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg#test_func", origin)

        diagram = root.to_tree_diagram()

        self.assertIn("[inj_scope]", diagram)

    def test_diagram_multiple_children(self):
        """Test tree diagram with multiple children at same level."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("pkg.module#func1", "res1", ResourceLifespan.Test, source)
        origin2 = ResourceOrigin("pkg.module#func2", "res2", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func1", origin1)
        root.add_descendent_resource_origination("pkg.module#func2", origin2)

        diagram = root.to_tree_diagram()

        self.assertIn("func1", diagram)
        self.assertIn("func2", diagram)


class InjectionScopeToDictTests(unittest.TestCase):
    """Tests for to_dict() method."""

    def test_empty_root_scope_dict(self):
        """Test dictionary conversion for empty root scope."""
        root = InjectionScope()

        result = root.to_dict()

        self.assertEqual(result["name"], "<session>")
        self.assertIsNone(result["package"])
        self.assertFalse(result["is_injection_scope"])
        self.assertFalse(result["is_relevant"])
        self.assertEqual(result["parameters"], {})
        self.assertEqual(result["validators"], {})
        self.assertEqual(result["children"], {})

    def test_dict_with_parameters(self):
        """Test dictionary includes parameter originations."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "my_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        result = root.to_dict()

        self.assertIn("my_param", result["parameters"])
        param_info = result["parameters"]["my_param"]
        self.assertEqual(param_info["identifier"], "my_param")
        self.assertEqual(param_info["originating_scope"], "<session>")
        self.assertEqual(param_info["lifespan"], "Session")

    def test_dict_with_validators(self):
        """Test dictionary includes validator originations."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        validator = ValidatorOrigin("<session>", "my_validator", "suffix", source)
        root.add_descendent_validator_origination("<session>", validator)

        result = root.to_dict()

        self.assertIn("my_validator", result["validators"])
        val_info = result["validators"]["my_validator"]
        self.assertEqual(val_info["identifier"], "my_validator")
        self.assertEqual(val_info["suffix"], "suffix")

    def test_dict_with_children(self):
        """Test dictionary includes child scopes."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg#func", origin)

        result = root.to_dict()

        self.assertIn("pkg", result["children"])
        pkg_dict = result["children"]["pkg"]
        self.assertEqual(pkg_dict["name"], "pkg")
        self.assertIn("func", pkg_dict["children"])

    def test_dict_without_origins(self):
        """Test dictionary with include_origins=False returns only identifiers."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "my_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        result = root.to_dict(include_origins=False)

        self.assertEqual(result["parameters"], ["my_param"])
        self.assertEqual(result["validators"], [])

    def test_dict_nested_structure(self):
        """Test dictionary preserves nested scope structure."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.subpkg.module#test_func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.subpkg.module#test_func", origin)

        result = root.to_dict()

        self.assertIn("pkg", result["children"])
        self.assertIn("subpkg", result["children"]["pkg"]["children"])
        self.assertIn("module", result["children"]["pkg"]["children"]["subpkg"]["children"])
        self.assertIn("test_func", result["children"]["pkg"]["children"]["subpkg"]["children"]["module"]["children"])

    def test_dict_relevant_flag(self):
        """Test dictionary includes is_relevant flag."""
        root = InjectionScope()
        root._is_relevant = True

        result = root.to_dict()

        self.assertTrue(result["is_relevant"])


class InjectionScopeToJsonTests(unittest.TestCase):
    """Tests for to_json() method."""

    def test_empty_root_scope_json(self):
        """Test JSON export for empty root scope."""
        root = InjectionScope()

        json_str = root.to_json()

        self.assertIsInstance(json_str, str)
        data = json.loads(json_str)
        self.assertEqual(data["name"], "<session>")

    def test_json_is_valid(self):
        """Test that exported JSON is valid and parseable."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func", origin)

        json_str = root.to_json()

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError:
            self.fail("to_json() produced invalid JSON")

        self.assertIn("children", data)
        self.assertIn("pkg", data["children"])

    def test_json_with_indent(self):
        """Test JSON export with custom indentation."""
        root = InjectionScope()

        json_str = root.to_json(indent=4)

        self.assertIn("    ", json_str)

    def test_json_without_indent(self):
        """Test JSON export without indentation (compact)."""
        root = InjectionScope()

        json_str = root.to_json(indent=None)

        self.assertNotIn("\n", json_str)

    def test_json_without_origins(self):
        """Test JSON export with include_origins=False."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "my_param", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)

        json_str = root.to_json(include_origins=False)
        data = json.loads(json_str)

        self.assertEqual(data["parameters"], ["my_param"])

    def test_json_preserves_structure(self):
        """Test JSON export preserves complete tree structure."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "session_param", ResourceLifespan.Session, source)
        origin2 = ResourceOrigin("pkg#func", "test_param", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("<session>", origin1)
        root.add_descendent_resource_origination("pkg#func", origin2)

        json_str = root.to_json()
        data = json.loads(json_str)

        self.assertIn("session_param", data["parameters"])
        self.assertIn("pkg", data["children"])
        func_scope = data["children"]["pkg"]["children"]["func"]
        self.assertIn("test_param", func_scope["parameters"])


class InjectionScopeVisualizationIntegrationTests(unittest.TestCase):
    """Integration tests for visualization methods."""

    def test_roundtrip_dict_to_json(self):
        """Test that to_dict and to_json produce consistent results."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#func", "res", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#func", origin)

        dict_result = root.to_dict()
        json_str = root.to_json()
        json_result = json.loads(json_str)

        self.assertEqual(dict_result, json_result)

    def test_complex_tree_visualization(self):
        """Test visualization of a complex tree structure."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)

        root.add_descendent_resource_origination("<session>", 
            ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source))
        root.add_descendent_resource_origination("tests.unit.test_auth#test_login",
            ResourceOrigin("tests.unit.test_auth#test_login", "auth_token", ResourceLifespan.Test, source))
        root.add_descendent_resource_origination("tests.unit.test_auth#test_logout",
            ResourceOrigin("tests.unit.test_auth#test_logout", "logout_data", ResourceLifespan.Test, source))
        root.add_descendent_resource_origination("tests.integration.test_api#test_endpoint",
            ResourceOrigin("tests.integration.test_api#test_endpoint", "api_client", ResourceLifespan.Test, source))

        diagram = root.to_tree_diagram()
        json_str = root.to_json()
        dict_result = root.to_dict()

        self.assertIn("tests", diagram)
        self.assertIn("unit", diagram)
        self.assertIn("integration", diagram)
        self.assertIn("test_auth", diagram)
        self.assertIn("test_api", diagram)

        data = json.loads(json_str)
        self.assertIn("tests", data["children"])
        self.assertIn("unit", data["children"]["tests"]["children"])
        self.assertIn("integration", data["children"]["tests"]["children"])


if __name__ == "__main__":
    unittest.main()
