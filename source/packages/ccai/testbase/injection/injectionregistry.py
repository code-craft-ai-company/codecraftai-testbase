"""
    .. module:: ccai.testbase.injection.injectionregistry
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for injectionregistry.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []



from typing import Callable, Dict, List, Optional, Set, Type

import warnings

from ccai.errors.exceptions import SemanticError

from ccai.testbase.resourcelifespan import ResourceLifespan

from ccai.testbase.sources.configurationsource import ConfigurationSource
from ccai.testbase.sources.integrationsource import IntegrationSource
from ccai.testbase.sources.resourcesource import ResourceSource
from ccai.testbase.sources.validatorsource import ValidatorSource

from ccai.testbase.origins.resourceorigin import ResourceOrigin
from ccai.testbase.origins.validatororigin import ValidatorOrigin

from ccai.testbase.injection.injectionmoment import InjectionMoment
from ccai.testbase.injection.injectionscope import InjectionScope
from ccai.testbase.injection.introspection import (
    FactoryType,
    FactoryMetadata,
    FactoryListResult,
    ParameterDependency,
    DependencyAnalysisResult,
    DependencyGraph,
    DependencyGraphNode,
    DependencyGraphEdge
)


class InjectionRegistry:
    """
        1. During the injectable discovery process, the origination functions and parameter decorators are
           executed and the resource identifier names and source functions are registered and available for
           consumption via a query interface or by a execution sequencer when generating the injectable
           execution flow code.

           The source functions and identifiers being registered are stored in the scope tree in
           order to build data structure that allows for the resolution of scope for the parameters
           and associated identifiers that will be consumed by injection moments during the execution sequence
           flow. (This is an implicit step)

        2. After all the injection moments have been imported and injectable references have been created, we go
           through all of the injectable references and ensure we have a completely filled out scope tree
           for all of the injection moments.  As we go we mark scopes as relavant so we can later go back through
           the tree and prune scope nodes that are not relavant to executing a injectable.

        3. Walk through the entire scope tree and prune non-relevant nodes starting at the leaves and
           working backwards until a relavant node is reached or the root of the tree is reached.

        4. Iterate over the injectable references and for each injectable reference, walk through the now
           pruned scope tree utilizing a parameter visibility dictionary chain assigning usages to each
           ResourceOrigin object as a reference is found.  As we walk, we make sure that any parameters
           reference in the current scope are visible in the current parameter dictionary and if not
           store information about the missing parameter.

        5. Go through all of the injectable references and for each injectable reference, collect integration
           and scope couplings that are referenced so we can build a combined picture of everything that
           is being coupled into the execution run.
    """
    _instance = None
    _initialized = False

    # Warning categories for filtering
    class UnusedSourceWarning(UserWarning):
        """Warning raised when a registered source is not used by any injection moment."""
        pass

    class ShadowedParameterWarning(UserWarning):
        """Warning raised when a parameter shadows another parameter in a parent scope."""
        pass

    def __new__(cls):
        """
            Constructs new instances of the ResourceRegistry object.
        """
        if cls._instance is None:
            cls._instance = super(InjectionRegistry, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
            Initializes the SubscriptionRegistry object the first time this singleton is created.
        """
        thisType = type(self)

        if not thisType._initialized:
            thisType._initialized = True

            # The source tables are how integration, configuration and resource sources are
            # registered and they help to lookup any factory functions that generate
            # a given type of resource.
            self._integration_source = {}
            self._resource_source = {}
            self._configuration_source = {}
            self._validator_source = {}

            # The unknown parameter table gets populated with the names of subscribe functions
            # that have unknown paramters and the list of parameters names the could not be
            # resolved to a parameter source function.
            self._unknown_parameters = {}

            # The identifier subscription table contains a list of identifiers that are used by
            # injection moments and the associated contexts in which they were used.
            self._identifier_subscription_table = {}

            #TODO: Drop this once we 

            # The scope tree is used to keep a list of scopes associated with a
            # sequence run and the variable names that originate from a given scope.
            self._scope_tree_root = InjectionScope()

            self._referenced_integrations = {}
            self._referenced_configurations = {}
        return

    @property
    def referenced_integrations(self):
        return self._referenced_integrations

    @property
    def referenced_configurations(self):
        return self._referenced_configurations

    @property
    def unknown_parameters(self):
        return self._unknown_parameters

    def add_implied_session_resource(self, identifier: str):
        """
            Adds an implied session resources that is inherent to the code generation of the
            test framework.
        """
        origin = ResourceOrigin("<session>", identifier, ResourceLifespan.Session, source=None, implied=True)
        self._scope_tree_root.add_descendent_resource_origination("<session>", origin)
        return

    def finalize_startup(self, inj_moments: Dict[str, InjectionMoment]):
        """
            ..note: During injectable discovery process, the parameter decorators are executed and the resource
                    identifier names and source functions are registered and available for consumption via
                    a query interface or by the sequencer when generating the injectable execution flow code.

                    The source functions and identifiers being registered are stored in the scope tree in
                    order to build data structure that allows for the resolution of scope for the parameters
                    that and associated identifiers that will be consumed by injection moments during the execution of
                    the execution sequence flow. (This is an implicit step)
        """
        # =====================================================================
        # INJECTION FINALIZATION ORCHESTRATION
        # =====================================================================
        # This method orchestrates the complete injection setup after all test
        # discovery is complete. It runs four phases in sequence:
        #
        # Phase 1: Ensure Scopes - Create scope nodes for all injection moments
        # Phase 2: Prune Tree - Remove non-relevant scope nodes
        # Phase 3: Resolve Parameters - Validate parameter dependencies
        # Phase 4: Collect Couplings - Identify required integrations/configurations
        #
        # These phases MUST run in order because each depends on the previous:
        # - Pruning requires scopes to be marked relevant (Phase 1)
        # - Resolution requires a pruned tree for efficiency (Phase 2)
        # - Coupling collection requires resolved parameters (Phase 3)
        # =====================================================================

        # =====================================================================
        # PHASE 1: ENSURE INJECTION SCOPES
        # =====================================================================
        # After all the injection moments have been imported and injectable references have been created, we
        # go through all of the injectable references and ensure we have a completely filled out scope
        # tree.  As we go we mark scopes as relevant so we can later go back through the tree and prune
        # scope nodes that are not relevant to executing an injectable.
        #
        # This phase creates the complete scope tree structure and marks which
        # scopes are actually needed for test execution.
        for _, inj_mom in inj_moments.items():
            self._scope_tree_root.ensure_injection_scopes_for_injection_moment(inj_mom)

        # =====================================================================
        # PHASE 2: PRUNE UNREFERENCED SCOPES
        # =====================================================================
        # Walk through the entire scope tree and prune non-relevant nodes starting at the leaves and
        # working backwards until a relevant node is reached or the root of the tree is reached.
        #
        # This optimization reduces memory usage and speeds up subsequent
        # traversals by removing scope nodes that have no injection moments.
        self._scope_tree_root.prune_unreference_scopes()

        # =====================================================================
        # PHASE 3: RESOLVE PARAMETER DEPENDENCIES
        # =====================================================================
        # Iterate over the injectable references and for each reference, walk through the now pruned
        # scope tree utilizing a parameter visibility dictionary chain assigning usages to each
        # ResourceOrigin object as a reference is found.  As we walk, we make sure that any parameters
        # reference in the current scope are visible in the current parameter dictionary and if not
        # store information about the missing parameter.
        #
        # This phase validates that all parameter dependencies can be satisfied
        # and records any missing parameters for error reporting.
        for _, inj_mom in inj_moments.items():
            missing_params = []

            self._scope_tree_root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

            # Track missing parameters by injection moment name for error reporting
            # These will be reported to the user before test execution begins
            if len(missing_params) > 0:
                self._unknown_parameters[inj_mom.name] = missing_params

        # =====================================================================
        # PHASE 4: COLLECT INTEGRATIONS AND CONFIGURATIONS
        # =====================================================================
        # Go through all of the injectable references and for each reference, collect integration and
        # scope couplings that are referenced so we can build a combined picture of everything that
        # is being coupled into the execution run.
        #
        # This phase identifies all external dependencies (integrations and
        # configurations) that must be established before test execution.
        for _, inj_mom in inj_moments.items():
            self._scope_tree_root.collect_integrations_and_configurations_for_injection_moment(self._referenced_integrations, self._referenced_configurations)

        # =====================================================================
        # PHASE 5: WARN ABOUT POTENTIAL ISSUES
        # =====================================================================
        # After all resolution is complete, check for potential issues that
        # may indicate configuration problems:
        # - Unused registered sources (sources that were registered but never used)
        # - Shadowed parameters (parameters that hide parent scope parameters)
        #
        # These warnings help developers identify potential misconfigurations
        # without failing the test run.
        self._warn_unused_sources()
        self._scope_tree_root.warn_shadowed_parameters()

        return

    def _warn_unused_sources(self):
        """
        Warn about registered sources that are not used by any parameter origination.
        
        This method collects all source functions that are referenced by parameter
        originations in the scope tree and compares them against all registered
        sources. Any registered source that is not referenced generates a warning.
        
        This helps identify:
        - Sources that were registered but never attached to any scope
        - Sources that may have been intended for use but were misconfigured
        - Dead code in the form of unused factory functions
        """
        # Collect all source functions that are actually used in the scope tree
        used_sources: Set[Callable] = set()
        self._scope_tree_root.collect_used_sources(used_sources)
        
        # Check integration sources
        for source_func, source in self._integration_source.items():
            if source_func not in used_sources:
                warnings.warn(
                    f"Registered integration source '{source.source_id}' "
                    f"(function: {source_func.__name__}, module: {source.module_name}) "
                    f"is not used by any parameter origination.",
                    InjectionRegistry.UnusedSourceWarning,
                    stacklevel=2
                )
        
        # Check resource sources
        for source_func, source in self._resource_source.items():
            if source_func not in used_sources:
                warnings.warn(
                    f"Registered resource source '{source.source_id}' "
                    f"(function: {source_func.__name__}, module: {source.module_name}) "
                    f"is not used by any parameter origination.",
                    InjectionRegistry.UnusedSourceWarning,
                    stacklevel=2
                )
        
        # Check configuration sources
        for source_func, source in self._configuration_source.items():
            if source_func not in used_sources:
                warnings.warn(
                    f"Registered configuration source '{source.source_id}' "
                    f"(function: {source_func.__name__}, module: {source.module_name}) "
                    f"is not used by any parameter origination.",
                    InjectionRegistry.UnusedSourceWarning,
                    stacklevel=2
                )
        
        # Check validator sources
        for source_func, source in self._validator_source.items():
            if source_func not in used_sources:
                warnings.warn(
                    f"Registered validator source '{source.source_id}' "
                    f"(function: {source_func.__name__}, module: {source.module_name}) "
                    f"is not used by any parameter origination.",
                    InjectionRegistry.UnusedSourceWarning,
                    stacklevel=2
                )
        
        return

    def lookup_resource_scope(self, scope_name):
        resource_scope = self._scope_tree_root.lookup_scope(scope_name)
        return resource_scope

    def lookup_resource_source(self, source_func) -> ResourceSource:

        source = None

        if source_func in self._integration_source:
            source = self._integration_source[source_func]
        elif source_func in self._configuration_source:
            source = self._configuration_source[source_func]
        elif source_func in self._resource_source:
            source = self._resource_source[source_func]

        return source
    
    def lookup_validator_source(self, source_func) -> ValidatorSource:

        source = None

        if source_func in self._validator_source:
            source = self._validator_source[source_func]

        return source

    def register_integration_source(self, source: IntegrationSource):
        """
            This method is called by the 'integration' decorator in order to register a
            factory function that generates an 'IntegrationCoupling' object. 
        """
        source_func = source.source_function

        if source_func not in self._integration_source:
            self._integration_source[source_func] = source

        return

    def register_resource_origin(self, identifier: str, origin: ResourceOrigin):
        """
            The :method:`register_resource_origin` is used to register an alias as a wellknown parameter
            so that subscriber functions can consume the parameter as an input parameter.
        """

        originating_scope = origin.originating_scope

        if self._scope_tree_root.has_descendent_resource(originating_scope, identifier):
            errmsg = "A wellknown variable identified as '{}' has already been assigned to scope '{}'.".format(identifier, originating_scope)
            raise SemanticError(errmsg) from None

        # Add the parameter origin to the identifiers_for_scope table for this scope so we
        # can lookup identifiers by scope
        self._scope_tree_root.add_descendent_resource_origination(originating_scope, origin)

        return

    def register_resource_source(self, source: ResourceSource):
        """
            This method is called by the 'resource' decorator in order to register a
            factory function that generate an arbitrary parameter resources.
        """
        source_func = source.source_function
        
        if source_func not in self._resource_source:
            self._resource_source[source_func] = source

        return

    def register_configuration_source(self, source: ConfigurationSource):
        """
            This method is called by the 'scope' decorator in order to register a factory
            function that generates an 'ScopeCoupling' object. 
        """
        source_func = source.source_function

        if source_func not in self._configuration_source:
            self._configuration_source[source_func] = source

        return
    
    def register_validator_source(self, source: ValidatorSource):
        """
        This method is called by the 'validator' decorator in order to register a factory
            function that generates an 'ValidatorCoupling' object. 
        """
        source_func = source.source_function

        if source_func not in self._validator_source:
            self._validator_source[source_func] = source

        return

    def register_validator_origin(self, identifier: str, origin: ValidatorOrigin):
        """
            The :method:`register_validator_origin` is used to register an alias as a wellknown parameter
            so that subscriber functions can consume the parameter as an input parameter.
        """

        originating_scope = origin.originating_scope

        if self._scope_tree_root.has_descendent_validator(originating_scope, identifier):
            errmsg = "A wellknown variable identified as '{}' has already been assigned to scope '{}'.".format(identifier, originating_scope)
            raise SemanticError(errmsg) from None

        # Add the parameter origin to the identifiers_for_scope table for this scope so we
        # can lookup identifiers by scope
        self._scope_tree_root.add_descendent_validator_origination(originating_scope, origin)

        return

    def rename_resource_origins_from_main(self, new_origin):
        """
            Walks the scope tree and corrects the resource origin name for resources.

            ..note: This is a special use method that is typically use to replace the
            name '__main__' in resources loaded from a injectable file that is being debugged
            from a script entry point.
        """
        self._scope_tree_root.rename_resource_origins_from_main(new_origin)
        return

    # =========================================================================
    # Factory Introspection API
    # =========================================================================

    def list_factories(self, factory_type: Optional[FactoryType] = None) -> FactoryListResult:
        """
            Lists all registered factory functions, optionally filtered by type.
            
            :param factory_type: Optional filter to return only factories of a specific type.
                                 If None, returns all registered factories.
            :return: A FactoryListResult containing metadata for all matching factories.
            
            Example usage:
                registry = InjectionRegistry()
                
                # List all factories
                all_factories = registry.list_factories()
                print(f"Total factories: {all_factories.total_count}")
                
                # List only integration factories
                integrations = registry.list_factories(FactoryType.INTEGRATION)
                for factory in integrations.integration_factories:
                    print(f"  {factory.function_name}: {factory.resource_type}")
        """
        result = FactoryListResult()

        if factory_type is None or factory_type == FactoryType.INTEGRATION:
            for source in self._integration_source.values():
                metadata = FactoryMetadata.from_source(FactoryType.INTEGRATION, source)
                result.integration_factories.append(metadata)

        if factory_type is None or factory_type == FactoryType.RESOURCE:
            for source in self._resource_source.values():
                metadata = FactoryMetadata.from_source(FactoryType.RESOURCE, source)
                result.resource_factories.append(metadata)

        if factory_type is None or factory_type == FactoryType.CONFIGURATION:
            for source in self._configuration_source.values():
                metadata = FactoryMetadata.from_source(FactoryType.CONFIGURATION, source)
                result.configuration_factories.append(metadata)

        if factory_type is None or factory_type == FactoryType.VALIDATOR:
            for source in self._validator_source.values():
                metadata = FactoryMetadata.from_source(FactoryType.VALIDATOR, source)
                result.validator_factories.append(metadata)

        return result

    def get_factory_metadata(self, source_func: Callable) -> Optional[FactoryMetadata]:
        """
            Retrieves metadata for a specific factory function.
            
            :param source_func: The factory function to query metadata for.
            :return: FactoryMetadata if the function is registered, None otherwise.
            
            Example usage:
                @register.resource_factory()
                def my_resource() -> MyResource:
                    return MyResource()
                
                registry = InjectionRegistry()
                metadata = registry.get_factory_metadata(my_resource)
                if metadata:
                    print(f"Factory type: {metadata.factory_type}")
                    print(f"Resource type: {metadata.resource_type}")
                    print(f"Constraints: {metadata.constraints}")
        """
        # Check integration sources
        if source_func in self._integration_source:
            source = self._integration_source[source_func]
            return FactoryMetadata.from_source(FactoryType.INTEGRATION, source)

        # Check resource sources
        if source_func in self._resource_source:
            source = self._resource_source[source_func]
            return FactoryMetadata.from_source(FactoryType.RESOURCE, source)

        # Check configuration sources
        if source_func in self._configuration_source:
            source = self._configuration_source[source_func]
            return FactoryMetadata.from_source(FactoryType.CONFIGURATION, source)

        # Check validator sources
        if source_func in self._validator_source:
            source = self._validator_source[source_func]
            return FactoryMetadata.from_source(FactoryType.VALIDATOR, source)

        return None

    def find_factories_by_resource_type(self, resource_type: Type) -> List[FactoryMetadata]:
        """
            Finds all factories that produce a specific resource type.
            
            :param resource_type: The resource type to search for.
            :return: A list of FactoryMetadata for factories producing the specified type.
            
            Example usage:
                registry = InjectionRegistry()
                factories = registry.find_factories_by_resource_type(MyIntegration)
                for factory in factories:
                    print(f"Found factory: {factory.function_name}")
        """
        results = []

        for source in self._integration_source.values():
            if source.resource_type == resource_type:
                results.append(FactoryMetadata.from_source(FactoryType.INTEGRATION, source))

        for source in self._resource_source.values():
            if source.resource_type == resource_type:
                results.append(FactoryMetadata.from_source(FactoryType.RESOURCE, source))

        for source in self._configuration_source.values():
            if source.resource_type == resource_type:
                results.append(FactoryMetadata.from_source(FactoryType.CONFIGURATION, source))

        for source in self._validator_source.values():
            if source.resource_type == resource_type:
                results.append(FactoryMetadata.from_source(FactoryType.VALIDATOR, source))

        return results

    def find_factories_by_module(self, module_name: str) -> List[FactoryMetadata]:
        """
            Finds all factories defined in a specific module.
            
            :param module_name: The module name to search for.
            :return: A list of FactoryMetadata for factories defined in the specified module.
            
            Example usage:
                registry = InjectionRegistry()
                factories = registry.find_factories_by_module("myapp.integrations")
                for factory in factories:
                    print(f"Found factory: {factory.function_name}")
        """
        results = []

        for source in self._integration_source.values():
            if source.module_name == module_name:
                results.append(FactoryMetadata.from_source(FactoryType.INTEGRATION, source))

        for source in self._resource_source.values():
            if source.module_name == module_name:
                results.append(FactoryMetadata.from_source(FactoryType.RESOURCE, source))

        for source in self._configuration_source.values():
            if source.module_name == module_name:
                results.append(FactoryMetadata.from_source(FactoryType.CONFIGURATION, source))

        for source in self._validator_source.values():
            if source.module_name == module_name:
                results.append(FactoryMetadata.from_source(FactoryType.VALIDATOR, source))

        return results

    def find_factories_with_constraints(self, constraint_key: Optional[str] = None) -> List[FactoryMetadata]:
        """
            Finds all factories that have constraints defined.
            
            :param constraint_key: Optional key to filter factories that have a specific constraint.
                                   If None, returns all factories with any constraints.
            :return: A list of FactoryMetadata for factories with matching constraints.
            
            Example usage:
                registry = InjectionRegistry()
                
                # Find all factories with any constraints
                constrained = registry.find_factories_with_constraints()
                
                # Find factories with a specific constraint key
                platform_specific = registry.find_factories_with_constraints("platform")
        """
        results = []

        all_sources = [
            (FactoryType.INTEGRATION, self._integration_source.values()),
            (FactoryType.RESOURCE, self._resource_source.values()),
            (FactoryType.CONFIGURATION, self._configuration_source.values()),
            (FactoryType.VALIDATOR, self._validator_source.values()),
        ]

        for factory_type, sources in all_sources:
            for source in sources:
                constraints = source.constraints
                if constraints:
                    if constraint_key is None or constraint_key in constraints:
                        results.append(FactoryMetadata.from_source(factory_type, source))

        return results

    # =========================================================================
    # Parameter Dependency Analysis API
    # =========================================================================

    def get_parameter_dependencies(self, identifier: str, scope: Optional[str] = None) -> Optional[DependencyAnalysisResult]:
        """
        Get detailed dependency information for a specific parameter.
        
        This method analyzes a parameter's dependencies, including both
        direct dependencies (parameters required by its source function)
        and transitive dependencies (dependencies of dependencies).
        
        :param identifier: The parameter identifier to analyze.
        :param scope: The scope where the parameter is defined. If None, searches
                      all scopes for the parameter.
        :return: A DependencyAnalysisResult object containing dependency information,
                 or None if the parameter is not found.
        
        Example usage:
            registry = InjectionRegistry()
            
            # Get dependencies for a specific parameter
            result = registry.get_parameter_dependencies("auth_token", "tests.unit#test_login")
            if result:
                print(f"Direct dependencies: {[d.identifier for d in result.direct_dependencies]}")
                print(f"Transitive dependencies: {[d.identifier for d in result.transitive_dependencies]}")
                if result.has_circular_dependency:
                    print(f"Circular dependency detected: {result.circular_path}")
        """
        return self._scope_tree_root.get_parameter_dependencies(identifier, scope)

    def generate_dependency_graph(self) -> DependencyGraph:
        """
        Generate a complete dependency graph for all parameters in the scope tree.
        
        This method builds a graph showing all parameter dependencies in the
        injection system. The graph can be exported to various formats for
        visualization and analysis.
        
        :return: A DependencyGraph object containing nodes and edges.
        
        Example usage:
            registry = InjectionRegistry()
            
            # Generate the dependency graph
            graph = registry.generate_dependency_graph()
            
            # Get Mermaid diagram for documentation
            print(graph.to_mermaid())
            
            # Get DOT format for Graphviz
            print(graph.to_dot())
            
            # Get adjacency list for programmatic analysis
            adj_list = graph.to_adjacency_list()
            
            # Find root parameters (no dependencies)
            print(f"Root parameters: {graph.root_parameters}")
            
            # Find leaf parameters (nothing depends on them)
            print(f"Leaf parameters: {graph.leaf_parameters}")
        """
        return self._scope_tree_root.build_dependency_graph()

    def list_all_parameters(self) -> Dict[str, Dict]:
        """
        List all parameters registered in the scope tree.
        
        This method returns a dictionary of all parameter originations,
        keyed by "scope:identifier".
        
        :return: A dictionary mapping "scope:identifier" to parameter information.
        
        Example usage:
            registry = InjectionRegistry()
            
            # List all parameters
            all_params = registry.list_all_parameters()
            for key, info in all_params.items():
                print(f"{key}: lifespan={info.get('lifespan')}")
        """
        all_params = self._scope_tree_root.collect_all_parameters()
        
        # Transform to a more user-friendly format
        result = {}
        for key, info in all_params.items():
            origin = info["origin"]
            
            param_info = {
                "identifier": info["identifier"],
                "scope": info["scope"],
                "source_function_name": None,
                "source_module": None,
                "lifespan": None,
                "is_implied": False,
                "direct_dependencies": []
            }
            
            if hasattr(origin, 'implied'):
                param_info["is_implied"] = origin.implied
            
            if not param_info["is_implied"] and origin._source is not None:
                try:
                    param_info["source_function_name"] = origin.source_function_name
                    param_info["source_module"] = origin.source_module_name
                except (AttributeError, TypeError):
                    pass
            
            if hasattr(origin, 'life_span') and origin.life_span is not None:
                param_info["lifespan"] = origin.life_span.name
            
            # Get direct dependencies from source signature
            if not param_info["is_implied"] and origin._source is not None:
                try:
                    source_params = origin.source_signature.parameters
                    param_info["direct_dependencies"] = [
                        name for name in source_params.keys()
                        if name != "constraints"
                    ]
                except (AttributeError, TypeError):
                    pass
            
            result[key] = param_info
        
        return result

    def find_parameters_by_scope(self, scope: str) -> List[Dict]:
        """
        Find all parameters defined at a specific scope.
        
        :param scope: The scope to search (e.g., "<session>", "tests.unit#test_login").
        :return: A list of parameter information dictionaries.
        
        Example usage:
            registry = InjectionRegistry()
            
            # Find all session-level parameters
            session_params = registry.find_parameters_by_scope("<session>")
            for param in session_params:
                print(f"{param['identifier']}: {param['lifespan']}")
        """
        all_params = self.list_all_parameters()
        return [
            info for key, info in all_params.items()
            if info["scope"] == scope
        ]

    def find_parameters_with_dependency(self, dependency_name: str) -> List[Dict]:
        """
        Find all parameters that depend on a specific parameter.
        
        :param dependency_name: The name of the dependency to search for.
        :return: A list of parameter information dictionaries for parameters
                 that depend on the specified parameter.
        
        Example usage:
            registry = InjectionRegistry()
            
            # Find all parameters that depend on "session_config"
            dependents = registry.find_parameters_with_dependency("session_config")
            for param in dependents:
                print(f"{param['identifier']} depends on session_config")
        """
        all_params = self.list_all_parameters()
        return [
            info for key, info in all_params.items()
            if dependency_name in info.get("direct_dependencies", [])
        ]

    def get_dependency_chain(self, identifier: str, scope: Optional[str] = None) -> List[str]:
        """
        Get the complete dependency chain for a parameter.
        
        This method returns an ordered list of parameter identifiers showing
        the full dependency path from the specified parameter to all its
        transitive dependencies.
        
        :param identifier: The parameter identifier to analyze.
        :param scope: The scope where the parameter is defined. If None, searches
                      all scopes for the parameter.
        :return: A list of parameter keys (scope:identifier) in dependency order.
        
        Example usage:
            registry = InjectionRegistry()
            
            # Get the dependency chain for auth_token
            chain = registry.get_dependency_chain("auth_token", "tests.unit#test_login")
            print(f"Dependency chain: {' -> '.join(chain)}")
        """
        result = self.get_parameter_dependencies(identifier, scope)
        if result is None:
            return []
        return result.dependency_chain


injection_registry = InjectionRegistry()
