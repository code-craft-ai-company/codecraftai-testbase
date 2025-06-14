"""
    .. module:: automojo.testbase.constraints
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for constraints.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"


from typing import Any, Dict, List, Union

from enum import Enum

from automojo.testbase.features import FeatureMask, FeatureTag


class ConstraintsOrigin(str, Enum):
    SITE_PARAMETER = "site-parameter"
    OVERRIDE_PARAMETER = "override-parameter"


class Constraints(dict):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        return

    def __call__(self, **kwargs: Any):
        inst = dict(self)
        inst.update(kwargs)
        return inst


class ConstraintsCatalog:
    """
        The :class:`ConstraintsCatalog` object is a singleton that stores the constraints for an automation run
        and provides a way to pass constraints from multiple sources to tests.
    """

    _instance = None
    _initialized = False


    def __new__(cls):
        """
            Constructs new instances of the ResourceRegistry object.
        """
        if cls._instance is None:
            cls._instance = super(ConstraintsCatalog, cls).__new__(cls)

        return cls._instance


    def __init__(self):
        """
            Initializes the SubscriptionRegistry object the first time this singleton is created.
        """
        thisType = type(self)

        if not thisType._initialized:
            thisType._initialized = True

            self._site_constraints: Dict[str, ConstraintsRef] = {}
            self._override_constraints: Dict[str, ConstraintsRef] = {}

        return


    def add_constraints(self, origin: ConstraintsOrigin, originating_scope: str, identifier: str, constraints: Union[Constraints, "FeatureConstraints", Dict[str, Any]]) -> str:

        ckey = create_constraint_key(originating_scope, identifier)

        cref = ConstraintsRef(origin, originating_scope, identifier, constraints)

        if origin == ConstraintsOrigin.SITE_PARAMETER:
            self._site_constraints[ckey] = cref
        elif origin == ConstraintsOrigin.OVERRIDE_PARAMETER:
            self._override_constraints[ckey] = cref
        else:
            raise ValueError(f"Unkown constraint origin='{origin}' scope='{originating_scope}' identifier={identifier}")
        
        return ckey
    

    def lookup_constraints(self, constraints_key: str) -> Union[Constraints, "FeatureConstraints", Dict[str, Any]]:
        """
            Looks up a constraint by its 'scope' name based on order of priority.  Override constraints take
            priority over factory site constraints.
        """

        rtnval = None

        if constraints_key in self._override_constraints:
            cref = self._override_constraints[constraints_key]
            rtnval = cref.constraints
        elif constraints_key in self._site_constraints:
            cref = self._site_constraints[constraints_key]
            rtnval = cref.constraints
        
        return rtnval


    def prune_constraints(self, keep_scopes: List[str]):
        """
            Prunes the constraints catalog down to a specified list of scopes that are relevant to the current
            injection environment.
        """
        
        pruned_constraints = {}
        for scope in keep_scopes:
            if scope in self._site_constraints:
                pruned_constraints[scope] = self._site_constraints[scope]

        self._site_constraints = pruned_constraints

        pruned_constraints = {}
        for scope in keep_scopes:
            if scope in self._override_constraints:
                pruned_constraints[scope] = self._override_constraints[scope]

        self._override_constraints = pruned_constraints

        return


class ConstraintsRef:

    def __init__(self, origin: ConstraintsOrigin, originating_scope: str, identifier: str, constraints: Constraints):
        self._origin = origin
        self._originating_scope = originating_scope
        self._identifier = identifier
        self._constraints = constraints
        return

    @property
    def constraints(self) ->  Union[Constraints, "FeatureConstraints", Dict[str, Any]]:
        return self._constraints
    
    @property
    def identifier(self) -> str:
        return self._identifier

    @property
    def origin(self) -> ConstraintsOrigin:
        return self._origin

    @property
    def originating_scope(self) -> str:
        return self._originating_scope


class FeatureConstraintKeys(str, Enum):
    REQUIRED_FEATURES = "required_features"
    EXCLUDED_FEATURES = "excluded_features"


class FeatureConstraints(FeatureMask):

    def __init__(self, *, required_features: List[FeatureTag]=None,
                       excluded_features: List[FeatureTag]=None,
                       checkout: bool=False, **kwargs):
        super().__init__(required_features=required_features,
                         excluded_features=excluded_features,
                         checkout=checkout, **kwargs)
        return

    def __call__(self, **kwargs: Any):
        inst = dict(self)
        inst.update(kwargs)
        return inst


def create_constraint_key(source: str, identifier: str):
    return f"{source}:{identifier}"


def merge_constraints(*args: Union[Constraints, dict]) -> Constraints:
    """
        Takes a sequence of :class:`Contraints` objects and merges them into a single
        :class:`Constraints` object.

        ..note: In cases where this method is provided with constraints with overlapping
                values, the last constraint with a give value will overwrite any previous
                values.
    """

    combined: Constraints = Constraints()

    for av in args:
        combined.update(av)
    
    return combined

