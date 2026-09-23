"""
    .. module:: ccai.testbase.injection.introspection
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing factory function introspection utilities.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

    This module provides introspection utilities for the dependency injection system,
    including:
    
    - Factory metadata extraction and querying
    - Parameter dependency analysis
    - Dependency graph generation for visualization
    
    Dependency Analysis
    -------------------
    The dependency analysis feature allows querying parameter dependencies in the
    injection scope tree. This is useful for:
    
    - Understanding the dependency chain for a specific parameter
    - Debugging injection issues
    - Visualizing the dependency graph
    - Identifying circular dependencies
    
    Example usage::
    
        from ccai.testbase.injection.injectionregistry import InjectionRegistry
        
        registry = InjectionRegistry()
        
        # Get dependencies for a specific parameter
        deps = registry.get_parameter_dependencies("my_param", "tests.unit#test_func")
        print(f"Direct dependencies: {deps.direct_dependencies}")
        print(f"Transitive dependencies: {deps.transitive_dependencies}")
        
        # Generate a dependency graph
        graph = registry.generate_dependency_graph()
        print(graph.to_mermaid())
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type

import inspect


class FactoryType(Enum):
    """
        Enumeration of factory types supported by the injection registry.
    """
    INTEGRATION = "integration"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    VALIDATOR = "validator"


@dataclass
class FactoryMetadata:
    """
        Metadata container for a registered factory function.
        
        Provides detailed information about a factory function including its
        source function, resource type, constraints, and registration details.
    """
    factory_type: FactoryType
    source_function: Callable
    resource_type: Type
    module_name: str
    function_name: str
    source_id: str
    constraints: Optional[Dict[str, Any]] = field(default_factory=dict)
    query_function: Optional[Callable] = None
    signature: Optional[inspect.Signature] = None
    docstring: Optional[str] = None

    @classmethod
    def from_source(cls, factory_type: FactoryType, source) -> "FactoryMetadata":
        """
            Creates a FactoryMetadata instance from a source object.
            
            :param factory_type: The type of factory (integration, resource, etc.)
            :param source: The source object containing factory information
            :return: A FactoryMetadata instance populated with source data
        """
        source_func = source.source_function
        return cls(
            factory_type=factory_type,
            source_function=source_func,
            resource_type=source.resource_type,
            module_name=source.module_name,
            function_name=source_func.__name__,
            source_id=source.source_id,
            constraints=source.constraints or {},
            query_function=source.query_function,
            signature=source.source_signature,
            docstring=source_func.__doc__
        )


@dataclass
class FactoryListResult:
    """
        Result container for listing registered factories.
        
        Groups factories by type and provides summary counts.
    """
    integration_factories: List[FactoryMetadata] = field(default_factory=list)
    resource_factories: List[FactoryMetadata] = field(default_factory=list)
    configuration_factories: List[FactoryMetadata] = field(default_factory=list)
    validator_factories: List[FactoryMetadata] = field(default_factory=list)

    @property
    def total_count(self) -> int:
        """Returns the total number of registered factories."""
        return (
            len(self.integration_factories) +
            len(self.resource_factories) +
            len(self.configuration_factories) +
            len(self.validator_factories)
        )

    @property
    def counts_by_type(self) -> Dict[FactoryType, int]:
        """Returns a dictionary of factory counts by type."""
        return {
            FactoryType.INTEGRATION: len(self.integration_factories),
            FactoryType.RESOURCE: len(self.resource_factories),
            FactoryType.CONFIGURATION: len(self.configuration_factories),
            FactoryType.VALIDATOR: len(self.validator_factories),
        }

    def all_factories(self) -> List[FactoryMetadata]:
        """Returns a flat list of all registered factories."""
        return (
            self.integration_factories +
            self.resource_factories +
            self.configuration_factories +
            self.validator_factories
        )


@dataclass
class ParameterDependency:
    """
    Represents a single parameter dependency relationship.
    
    This class captures the relationship between a parameter and its
    dependencies (parameters required by its source function).
    
    Attributes
    ----------
    identifier : str
        The parameter identifier.
    scope : str
        The scope where this parameter is defined.
    source_function_name : str
        The name of the source function that creates this parameter.
    source_module : str
        The module where the source function is defined.
    lifespan : str
        The resource lifespan (Session, Package, Test, Task).
    direct_dependencies : List[str]
        List of parameter identifiers that this parameter directly depends on.
    is_implied : bool
        Whether this is an implied (built-in) parameter.
    """
    identifier: str
    scope: str
    source_function_name: Optional[str] = None
    source_module: Optional[str] = None
    lifespan: Optional[str] = None
    direct_dependencies: List[str] = field(default_factory=list)
    is_implied: bool = False


@dataclass
class DependencyAnalysisResult:
    """
    Result container for parameter dependency analysis.
    
    This class provides a comprehensive view of a parameter's dependencies,
    including both direct dependencies (parameters required by the source
    function) and transitive dependencies (dependencies of dependencies).
    
    Attributes
    ----------
    parameter : ParameterDependency
        The parameter being analyzed.
    direct_dependencies : List[ParameterDependency]
        Parameters directly required by this parameter's source function.
    transitive_dependencies : List[ParameterDependency]
        All parameters in the dependency chain (recursive).
    dependency_chain : List[str]
        Ordered list of parameter identifiers showing the dependency path.
    has_circular_dependency : bool
        Whether a circular dependency was detected.
    circular_path : List[str]
        If circular, the path showing the cycle.
    """
    parameter: ParameterDependency
    direct_dependencies: List[ParameterDependency] = field(default_factory=list)
    transitive_dependencies: List[ParameterDependency] = field(default_factory=list)
    dependency_chain: List[str] = field(default_factory=list)
    has_circular_dependency: bool = False
    circular_path: List[str] = field(default_factory=list)


@dataclass
class DependencyGraphNode:
    """
    Represents a node in the dependency graph.
    
    Attributes
    ----------
    identifier : str
        The parameter identifier.
    scope : str
        The scope where this parameter is defined.
    source_function_name : str
        The name of the source function.
    lifespan : str
        The resource lifespan.
    is_implied : bool
        Whether this is an implied parameter.
    """
    identifier: str
    scope: str
    source_function_name: Optional[str] = None
    lifespan: Optional[str] = None
    is_implied: bool = False


@dataclass
class DependencyGraphEdge:
    """
    Represents an edge (dependency relationship) in the dependency graph.
    
    Attributes
    ----------
    from_param : str
        The parameter that has the dependency.
    to_param : str
        The parameter being depended upon.
    from_scope : str
        The scope of the dependent parameter.
    to_scope : str
        The scope of the dependency.
    """
    from_param: str
    to_param: str
    from_scope: str
    to_scope: str


@dataclass
class DependencyGraph:
    """
    A complete dependency graph for the injection scope tree.
    
    This class represents the entire dependency graph, including all
    parameters and their relationships. It provides methods for
    visualization and analysis.
    
    Attributes
    ----------
    nodes : Dict[str, DependencyGraphNode]
        All parameter nodes in the graph, keyed by "scope:identifier".
    edges : List[DependencyGraphEdge]
        All dependency relationships in the graph.
    root_parameters : List[str]
        Parameters with no dependencies (entry points).
    leaf_parameters : List[str]
        Parameters that nothing depends on (end points).
    
    Examples
    --------
    Generate and visualize a dependency graph::
    
        from ccai.testbase.injection.injectionregistry import InjectionRegistry
        
        registry = InjectionRegistry()
        graph = registry.generate_dependency_graph()
        
        # Get Mermaid diagram
        print(graph.to_mermaid())
        
        # Get DOT format for Graphviz
        print(graph.to_dot())
        
        # Get adjacency list
        adj_list = graph.to_adjacency_list()
    """
    nodes: Dict[str, DependencyGraphNode] = field(default_factory=dict)
    edges: List[DependencyGraphEdge] = field(default_factory=list)
    root_parameters: List[str] = field(default_factory=list)
    leaf_parameters: List[str] = field(default_factory=list)

    def to_mermaid(self, direction: str = "TB") -> str:
        """
        Generate a Mermaid diagram representation of the dependency graph.
        
        Parameters
        ----------
        direction : str, optional
            The direction of the graph. Options: "TB" (top-bottom),
            "BT" (bottom-top), "LR" (left-right), "RL" (right-left).
            Default is "TB".
        
        Returns
        -------
        str
            A Mermaid diagram string that can be rendered in Markdown.
        
        Examples
        --------
        ::
        
            graph = registry.generate_dependency_graph()
            mermaid_str = graph.to_mermaid()
            
            # Output:
            # graph TB
            #     session_config["session_config<br/>(Session)"]
            #     auth_token["auth_token<br/>(Test)"]
            #     auth_token --> session_config
        """
        lines = [f"graph {direction}"]
        
        # Add nodes with labels
        for node_key, node in self.nodes.items():
            # Create a safe node ID (replace special chars)
            node_id = node_key.replace(":", "_").replace("#", "_").replace(".", "_")
            lifespan_str = f"<br/>({node.lifespan})" if node.lifespan else ""
            implied_str = "<br/>[implied]" if node.is_implied else ""
            label = f'{node.identifier}{lifespan_str}{implied_str}'
            lines.append(f'    {node_id}["{label}"]')
        
        # Add edges
        for edge in self.edges:
            from_id = f"{edge.from_scope}:{edge.from_param}".replace(":", "_").replace("#", "_").replace(".", "_")
            to_id = f"{edge.to_scope}:{edge.to_param}".replace(":", "_").replace("#", "_").replace(".", "_")
            lines.append(f"    {from_id} --> {to_id}")
        
        return "\n".join(lines)

    def to_dot(self, graph_name: str = "DependencyGraph") -> str:
        """
        Generate a DOT format representation for Graphviz.
        
        Parameters
        ----------
        graph_name : str, optional
            The name of the graph. Default is "DependencyGraph".
        
        Returns
        -------
        str
            A DOT format string that can be rendered with Graphviz.
        
        Examples
        --------
        ::
        
            graph = registry.generate_dependency_graph()
            dot_str = graph.to_dot()
            
            # Save to file and render with Graphviz:
            # dot -Tpng graph.dot -o graph.png
        """
        lines = [f"digraph {graph_name} {{"]
        lines.append("    rankdir=TB;")
        lines.append("    node [shape=box];")
        lines.append("")
        
        # Add nodes with labels
        for node_key, node in self.nodes.items():
            node_id = node_key.replace(":", "_").replace("#", "_").replace(".", "_")
            lifespan_str = f"\\n({node.lifespan})" if node.lifespan else ""
            implied_str = "\\n[implied]" if node.is_implied else ""
            label = f'{node.identifier}{lifespan_str}{implied_str}'
            lines.append(f'    {node_id} [label="{label}"];')
        
        lines.append("")
        
        # Add edges
        for edge in self.edges:
            from_id = f"{edge.from_scope}:{edge.from_param}".replace(":", "_").replace("#", "_").replace(".", "_")
            to_id = f"{edge.to_scope}:{edge.to_param}".replace(":", "_").replace("#", "_").replace(".", "_")
            lines.append(f"    {from_id} -> {to_id};")
        
        lines.append("}")
        return "\n".join(lines)

    def to_adjacency_list(self) -> Dict[str, List[str]]:
        """
        Generate an adjacency list representation of the graph.
        
        Returns
        -------
        Dict[str, List[str]]
            A dictionary where keys are parameter identifiers (scope:param)
            and values are lists of parameters they depend on.
        
        Examples
        --------
        ::
        
            graph = registry.generate_dependency_graph()
            adj_list = graph.to_adjacency_list()
            
            # Output:
            # {
            #     "tests.unit#test_login:auth_token": ["<session>:session_config"],
            #     "<session>:session_config": []
            # }
        """
        adj_list: Dict[str, List[str]] = {key: [] for key in self.nodes.keys()}
        
        for edge in self.edges:
            from_key = f"{edge.from_scope}:{edge.from_param}"
            to_key = f"{edge.to_scope}:{edge.to_param}"
            if from_key in adj_list:
                adj_list[from_key].append(to_key)
        
        return adj_list

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the dependency graph to a dictionary representation.
        
        Returns
        -------
        Dict[str, Any]
            A dictionary containing nodes, edges, and metadata.
        """
        return {
            "nodes": {
                key: {
                    "identifier": node.identifier,
                    "scope": node.scope,
                    "source_function_name": node.source_function_name,
                    "lifespan": node.lifespan,
                    "is_implied": node.is_implied
                }
                for key, node in self.nodes.items()
            },
            "edges": [
                {
                    "from_param": edge.from_param,
                    "to_param": edge.to_param,
                    "from_scope": edge.from_scope,
                    "to_scope": edge.to_scope
                }
                for edge in self.edges
            ],
            "root_parameters": self.root_parameters,
            "leaf_parameters": self.leaf_parameters
        }

    def get_dependencies_for(self, identifier: str, scope: Optional[str] = None) -> List[str]:
        """
        Get all direct dependencies for a parameter.
        
        Parameters
        ----------
        identifier : str
            The parameter identifier.
        scope : str, optional
            The scope to search in. If None, searches all scopes.
        
        Returns
        -------
        List[str]
            List of parameter keys (scope:identifier) that this parameter depends on.
        """
        dependencies = []
        for edge in self.edges:
            if edge.from_param == identifier:
                if scope is None or edge.from_scope == scope:
                    dependencies.append(f"{edge.to_scope}:{edge.to_param}")
        return dependencies

    def get_dependents_for(self, identifier: str, scope: Optional[str] = None) -> List[str]:
        """
        Get all parameters that depend on a given parameter.
        
        Parameters
        ----------
        identifier : str
            The parameter identifier.
        scope : str, optional
            The scope to search in. If None, searches all scopes.
        
        Returns
        -------
        List[str]
            List of parameter keys (scope:identifier) that depend on this parameter.
        """
        dependents = []
        for edge in self.edges:
            if edge.to_param == identifier:
                if scope is None or edge.to_scope == scope:
                    dependents.append(f"{edge.from_scope}:{edge.from_param}")
        return dependents

