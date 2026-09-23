"""
    Unit tests for parameter dependency analysis functionality.

    Tests cover:
    - collect_all_parameters() for parameter collection
    - build_dependency_graph() for graph generation
    - get_parameter_dependencies() for dependency analysis
    - DependencyGraph visualization methods
"""

import unittest

from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.injection.injectionregistry import InjectionRegistry
from ccai.testbase.injection.introspection import (
    DependencyGraph,
    DependencyGraphNode,
    DependencyGraphEdge,
    DependencyAnalysisResult,
)
from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.resourcelifespan import ResourceLifespan
from ccai.testbase.sources.sourcebase import SourceBase


def sample_source_func():
    """Sample source function with no dependencies."""
    return "resource"


def dependent_source_func(session_config):
    """Sample source function that depends on session_config."""
    return f"resource using {session_config}"


def multi_dep_source_func(session_config, auth_token):
    """Sample source function with multiple dependencies."""
    return f"resource using {session_config} and {auth_token}"


class MockSourceBase(SourceBase):
    """Mock source for testing purposes."""

    def __init__(self, source_func, resource_type=str):
        super().__init__(source_func, None, resource_type, {})


class CollectAllParametersTests(unittest.TestCase):
    """Tests for collect_all_parameters() method."""

    def test_empty_scope_returns_empty_dict(self):
        """Test that empty scope tree returns empty dictionary."""
        root = InjectionScope()
        
        result = root.collect_all_parameters()
        
        self.assertEqual(result, {})

    def test_session_scope_parameter_collected(self):
        """Test that session-level parameters are collected."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)
        
        result = root.collect_all_parameters()
        
        self.assertIn("<session>:session_config", result)
        self.assertEqual(result["<session>:session_config"]["identifier"], "session_config")
        self.assertEqual(result["<session>:session_config"]["scope"], "<session>")

    def test_nested_scope_parameters_collected(self):
        """Test that parameters at nested scopes are collected."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg.module#test_func", "test_param", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg.module#test_func", origin)
        
        result = root.collect_all_parameters()
        
        self.assertIn("pkg.module#test_func:test_param", result)

    def test_multiple_parameters_collected(self):
        """Test that multiple parameters across scopes are collected."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        
        origin1 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        origin2 = ResourceOrigin("pkg#test_func", "test_param", ResourceLifespan.Test, source)
        
        root.add_descendent_resource_origination("<session>", origin1)
        root.add_descendent_resource_origination("pkg#test_func", origin2)
        
        result = root.collect_all_parameters()
        
        self.assertEqual(len(result), 2)
        self.assertIn("<session>:session_config", result)
        self.assertIn("pkg#test_func:test_param", result)


class BuildDependencyGraphTests(unittest.TestCase):
    """Tests for build_dependency_graph() method."""

    def test_empty_scope_returns_empty_graph(self):
        """Test that empty scope tree returns empty graph."""
        root = InjectionScope()
        
        graph = root.build_dependency_graph()
        
        self.assertEqual(len(graph.nodes), 0)
        self.assertEqual(len(graph.edges), 0)

    def test_single_parameter_creates_node(self):
        """Test that a single parameter creates a node in the graph."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)
        
        graph = root.build_dependency_graph()
        
        self.assertEqual(len(graph.nodes), 1)
        self.assertIn("<session>:session_config", graph.nodes)
        node = graph.nodes["<session>:session_config"]
        self.assertEqual(node.identifier, "session_config")
        self.assertEqual(node.scope, "<session>")
        self.assertEqual(node.lifespan, "Session")

    def test_parameter_with_dependency_creates_edge(self):
        """Test that a parameter with dependency creates an edge."""
        root = InjectionScope()
        
        # Create session_config (no dependencies)
        source1 = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source1)
        root.add_descendent_resource_origination("<session>", origin1)
        
        # Create auth_token that depends on session_config
        source2 = MockSourceBase(dependent_source_func)
        origin2 = ResourceOrigin("<session>", "auth_token", ResourceLifespan.Session, source2)
        root.add_descendent_resource_origination("<session>", origin2)
        
        graph = root.build_dependency_graph()
        
        self.assertEqual(len(graph.nodes), 2)
        self.assertEqual(len(graph.edges), 1)
        
        edge = graph.edges[0]
        self.assertEqual(edge.from_param, "auth_token")
        self.assertEqual(edge.to_param, "session_config")

    def test_root_parameters_identified(self):
        """Test that root parameters (no dependencies) are identified."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)
        
        graph = root.build_dependency_graph()
        
        self.assertIn("<session>:session_config", graph.root_parameters)

    def test_leaf_parameters_identified(self):
        """Test that leaf parameters (nothing depends on them) are identified."""
        root = InjectionScope()
        
        # Create session_config (no dependencies)
        source1 = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source1)
        root.add_descendent_resource_origination("<session>", origin1)
        
        # Create auth_token that depends on session_config
        source2 = MockSourceBase(dependent_source_func)
        origin2 = ResourceOrigin("<session>", "auth_token", ResourceLifespan.Session, source2)
        root.add_descendent_resource_origination("<session>", origin2)
        
        graph = root.build_dependency_graph()
        
        # auth_token is a leaf (nothing depends on it)
        self.assertIn("<session>:auth_token", graph.leaf_parameters)
        # session_config is not a leaf (auth_token depends on it)
        self.assertNotIn("<session>:session_config", graph.leaf_parameters)


class DependencyGraphVisualizationTests(unittest.TestCase):
    """Tests for DependencyGraph visualization methods."""

    def setUp(self):
        """Set up a sample dependency graph for testing."""
        self.graph = DependencyGraph()
        
        # Add nodes
        self.graph.nodes["<session>:session_config"] = DependencyGraphNode(
            identifier="session_config",
            scope="<session>",
            source_function_name="create_session_config",
            lifespan="Session",
            is_implied=False
        )
        self.graph.nodes["<session>:auth_token"] = DependencyGraphNode(
            identifier="auth_token",
            scope="<session>",
            source_function_name="create_auth_token",
            lifespan="Session",
            is_implied=False
        )
        
        # Add edge
        self.graph.edges.append(DependencyGraphEdge(
            from_param="auth_token",
            to_param="session_config",
            from_scope="<session>",
            to_scope="<session>"
        ))
        
        self.graph.root_parameters = ["<session>:session_config"]
        self.graph.leaf_parameters = ["<session>:auth_token"]

    def test_to_mermaid_generates_valid_output(self):
        """Test that to_mermaid generates valid Mermaid diagram."""
        mermaid = self.graph.to_mermaid()
        
        self.assertIn("graph TB", mermaid)
        self.assertIn("session_config", mermaid)
        self.assertIn("auth_token", mermaid)
        self.assertIn("-->", mermaid)

    def test_to_mermaid_with_direction(self):
        """Test that to_mermaid respects direction parameter."""
        mermaid = self.graph.to_mermaid(direction="LR")
        
        self.assertIn("graph LR", mermaid)

    def test_to_dot_generates_valid_output(self):
        """Test that to_dot generates valid DOT format."""
        dot = self.graph.to_dot()
        
        self.assertIn("digraph", dot)
        self.assertIn("session_config", dot)
        self.assertIn("auth_token", dot)
        self.assertIn("->", dot)

    def test_to_dot_with_custom_name(self):
        """Test that to_dot respects graph_name parameter."""
        dot = self.graph.to_dot(graph_name="MyGraph")
        
        self.assertIn("digraph MyGraph", dot)

    def test_to_adjacency_list_returns_dict(self):
        """Test that to_adjacency_list returns correct structure."""
        adj_list = self.graph.to_adjacency_list()
        
        self.assertIsInstance(adj_list, dict)
        self.assertIn("<session>:session_config", adj_list)
        self.assertIn("<session>:auth_token", adj_list)
        
        # auth_token depends on session_config
        self.assertIn("<session>:session_config", adj_list["<session>:auth_token"])
        # session_config has no dependencies
        self.assertEqual(adj_list["<session>:session_config"], [])

    def test_to_dict_returns_complete_structure(self):
        """Test that to_dict returns complete graph structure."""
        result = self.graph.to_dict()
        
        self.assertIn("nodes", result)
        self.assertIn("edges", result)
        self.assertIn("root_parameters", result)
        self.assertIn("leaf_parameters", result)
        
        self.assertEqual(len(result["nodes"]), 2)
        self.assertEqual(len(result["edges"]), 1)

    def test_get_dependencies_for_returns_dependencies(self):
        """Test that get_dependencies_for returns correct dependencies."""
        deps = self.graph.get_dependencies_for("auth_token")
        
        self.assertEqual(len(deps), 1)
        self.assertIn("<session>:session_config", deps)

    def test_get_dependents_for_returns_dependents(self):
        """Test that get_dependents_for returns correct dependents."""
        dependents = self.graph.get_dependents_for("session_config")
        
        self.assertEqual(len(dependents), 1)
        self.assertIn("<session>:auth_token", dependents)


class GetParameterDependenciesTests(unittest.TestCase):
    """Tests for get_parameter_dependencies() method."""

    def test_returns_none_for_nonexistent_parameter(self):
        """Test that get_parameter_dependencies returns None for non-existent parameter."""
        root = InjectionScope()
        
        result = root.get_parameter_dependencies("nonexistent")
        
        self.assertIsNone(result)

    def test_returns_result_for_existing_parameter(self):
        """Test that get_parameter_dependencies returns result for existing parameter."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        root.add_descendent_resource_origination("<session>", origin)
        
        result = root.get_parameter_dependencies("session_config")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, DependencyAnalysisResult)
        self.assertEqual(result.parameter.identifier, "session_config")

    def test_returns_direct_dependencies(self):
        """Test that get_parameter_dependencies returns direct dependencies."""
        root = InjectionScope()
        
        # Create session_config (no dependencies)
        source1 = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source1)
        root.add_descendent_resource_origination("<session>", origin1)
        
        # Create auth_token that depends on session_config
        source2 = MockSourceBase(dependent_source_func)
        origin2 = ResourceOrigin("<session>", "auth_token", ResourceLifespan.Session, source2)
        root.add_descendent_resource_origination("<session>", origin2)
        
        result = root.get_parameter_dependencies("auth_token")
        
        self.assertEqual(len(result.direct_dependencies), 1)
        self.assertEqual(result.direct_dependencies[0].identifier, "session_config")

    def test_returns_transitive_dependencies(self):
        """Test that get_parameter_dependencies returns transitive dependencies."""
        root = InjectionScope()
        
        # Create base_config (no dependencies)
        source1 = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "base_config", ResourceLifespan.Session, source1)
        root.add_descendent_resource_origination("<session>", origin1)
        
        # Create session_config that depends on base_config
        def session_config_func(base_config):
            return f"session using {base_config}"
        source2 = MockSourceBase(session_config_func)
        origin2 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source2)
        root.add_descendent_resource_origination("<session>", origin2)
        
        # Create auth_token that depends on session_config
        source3 = MockSourceBase(dependent_source_func)
        origin3 = ResourceOrigin("<session>", "auth_token", ResourceLifespan.Session, source3)
        root.add_descendent_resource_origination("<session>", origin3)
        
        result = root.get_parameter_dependencies("auth_token")
        
        # Direct dependency is session_config
        self.assertEqual(len(result.direct_dependencies), 1)
        self.assertEqual(result.direct_dependencies[0].identifier, "session_config")
        
        # Transitive dependency includes base_config
        trans_identifiers = [d.identifier for d in result.transitive_dependencies]
        self.assertIn("base_config", trans_identifiers)

    def test_finds_parameter_by_scope(self):
        """Test that get_parameter_dependencies finds parameter by scope."""
        root = InjectionScope()
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("pkg#test_func", "test_param", ResourceLifespan.Test, source)
        root.add_descendent_resource_origination("pkg#test_func", origin)
        
        result = root.get_parameter_dependencies("test_param", "pkg#test_func")
        
        self.assertIsNotNone(result)
        self.assertEqual(result.parameter.scope, "pkg#test_func")


class InjectionRegistryDependencyAPITests(unittest.TestCase):
    """Tests for InjectionRegistry dependency analysis API."""

    def setUp(self):
        """Reset the singleton registry before each test."""
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False
        self.registry = InjectionRegistry()

    def tearDown(self):
        """Reset the singleton registry after each test."""
        InjectionRegistry._instance = None
        InjectionRegistry._initialized = False

    def test_generate_dependency_graph_returns_graph(self):
        """Test that generate_dependency_graph returns a DependencyGraph."""
        graph = self.registry.generate_dependency_graph()
        
        self.assertIsInstance(graph, DependencyGraph)

    def test_list_all_parameters_returns_dict(self):
        """Test that list_all_parameters returns a dictionary."""
        result = self.registry.list_all_parameters()
        
        self.assertIsInstance(result, dict)

    def test_get_parameter_dependencies_returns_result(self):
        """Test that get_parameter_dependencies returns result for existing parameter."""
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        self.registry.register_resource_origin("session_config", origin)
        
        result = self.registry.get_parameter_dependencies("session_config")
        
        self.assertIsNotNone(result)

    def test_find_parameters_by_scope_returns_list(self):
        """Test that find_parameters_by_scope returns a list."""
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        self.registry.register_resource_origin("session_config", origin)
        
        result = self.registry.find_parameters_by_scope("<session>")
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["identifier"], "session_config")

    def test_find_parameters_with_dependency_returns_list(self):
        """Test that find_parameters_with_dependency returns correct parameters."""
        # Create session_config (no dependencies)
        source1 = MockSourceBase(sample_source_func)
        origin1 = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source1)
        self.registry.register_resource_origin("session_config", origin1)
        
        # Create auth_token that depends on session_config
        source2 = MockSourceBase(dependent_source_func)
        origin2 = ResourceOrigin("<session>", "auth_token", ResourceLifespan.Session, source2)
        self.registry.register_resource_origin("auth_token", origin2)
        
        result = self.registry.find_parameters_with_dependency("session_config")
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["identifier"], "auth_token")

    def test_get_dependency_chain_returns_list(self):
        """Test that get_dependency_chain returns ordered list."""
        source = MockSourceBase(sample_source_func)
        origin = ResourceOrigin("<session>", "session_config", ResourceLifespan.Session, source)
        self.registry.register_resource_origin("session_config", origin)
        
        result = self.registry.get_dependency_chain("session_config")
        
        self.assertIsInstance(result, list)
        self.assertIn("<session>:session_config", result)


if __name__ == "__main__":
    unittest.main()
