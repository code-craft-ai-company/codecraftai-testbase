
__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import Dict

from automojo.errors.exceptions import SemanticError

from automojo.testbase.resourcelifespan import ResourceLifespan

from automojo.testbase.sources.configurationsource import ConfigurationSource
from automojo.testbase.sources.integrationsource import IntegrationSource
from automojo.testbase.sources.resourcesource import ResourceSource
from automojo.testbase.sources.validatorsource import ValidatorSource

from automojo.testbase.origins.resourceorigin import ResourceOrigin
from automojo.testbase.origins.validatororigin import ValidatorOrigin

from automojo.testbase.injection.injectionmoment import InjectionMoment
from automojo.testbase.injection.injectionscope import InjectionScope


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
        # 1. After all the injection moments have been imported and injectable references have been created, we
        #    go through all of the injectable references and ensure we have a completely filled out scope
        #    tree.  As we go we mark scopes as relavant so we can later go back through the tree and prune
        #    scope nodes that are not relavant to executing an injectable.
        for _, inj_mom in inj_moments.items():
            self._scope_tree_root.ensure_injection_scopes_for_injection_moment(inj_mom)

        # 2. Walk through the entire scope tree and prune non-relevant nodes starting at the leaves and
        #    working backwards until a relavant node is reached or the root of the tree is reached.
        self._scope_tree_root.prune_unreference_scopes()

        # 3. Iterate over the injectable references and for each reference, walk through the now pruned
        #    scope tree utilizing a parameter visibility dictionary chain assigning usages to each
        #    ResourceOrigin object as a reference is found.  As we walk, we make sure that any parameters
        #    reference in the current scope are visible in the current parameter dictionary and if not
        #    store information about the missing parameter.
        for _, inj_mom in inj_moments.items():
            missing_params = []

            self._scope_tree_root.resolve_resource_originations_for_injection_moment(inj_mom, missing_params)

            if len(missing_params) > 0:
                self._unknown_parameters[inj_mom.name] = missing_params

        # 4. Go through all of the injectable references and for each reference, collect integration and
        #    scope couplings that are referenced so we can build a combined picture of everything that
        #    is being coupled into the execution run.
        for _, inj_mom in inj_moments.items():
            self._scope_tree_root.collect_integrations_and_configurations_for_injection_moment(self._referenced_integrations, self._referenced_configurations)

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


injection_registry = InjectionRegistry()
