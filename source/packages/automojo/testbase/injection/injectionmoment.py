"""
    .. module:: automojo.testbase.injection.injectionmoment
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for injectionmoment.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []



from typing import Any, Dict, List, OrderedDict, Optional, Sequence

from types import FunctionType


import collections
import inspect


from automojo.testbase.markers import MetaFilter


class InjectionMoment:
    """
        The :class:`InjectiionMoment` objects are used to record the details around the injection of executable content and resource creation code into an execution scope.
        :class:`InjectiionMoment` instances provide a reference to factory or test function, the injection location, the lifespan and any other constraints associated with
        a injection. 

        The :class:`InjectiionMoment` object allows us to delay the creation of injectable runtime instance data and state until it is necessary to instantiate it and allows
        us to cleanup the runtime instance and state as soon as it is no longer being used.
    """

    def __init__(self, injfunc: FunctionType, monikers: Optional[List[str]] = None, pivots: Optional[OrderedDict[str, Any]] = None):
        """
            Initializes the injectable reference object.
        """
        if monikers is None:
            monikers = []

        if pivots is None:
            pivots = collections.OrderedDict()
 
        self._inj_function = injfunc
        self._monikers = monikers
        self._pivots = pivots
        self._subscriptions = {}
        self._finalized = False
        return

    @property
    def finalized(self) -> bool:
        return self._finalized

    @property
    def monikers(self) -> List[str]:
        return self._monikers

    @property
    def pivots(self) -> OrderedDict[str, Any]:
        return self._pivots

    @property
    def scope_name(self) -> str:
        return self.name

    @property
    def subscriptions(self):
        return self._subscriptions

    @subscriptions.setter
    def subscriptions(self, val):
        self._subscriptions = val
        return

    @property
    def base_name(self) -> str:
        tbname = self._inj_function.__name__
        return tbname

    @property
    def function(self) -> FunctionType:
        """
            The injectable function 
        """
        return self._inj_function

    @property
    def function_parameters(self):
        signature = inspect.signature(self._inj_function)
        return signature.parameters

    @property
    def module_name(self) -> str:
        return self._inj_function.__module__

    @property
    def name(self) -> str:
        """
            The fully qualified name of the injectable that is referenced.
        """
        tf = self._inj_function
        inj_name = "%s#%s" % (tf.__module__, tf.__name__)
        return inj_name

    def finalize(self):
        self._finalized = True
        return

    def is_member_of_metaset(self, metafilters: Sequence[MetaFilter]):
        """
            Indicates if the associated injection belongs to a set that is associated with a collection of metafilters.
        """
        include = True

        for mfilter in metafilters:
            if not mfilter.should_include(self._metadata):
                include = False

        return include

    def resolve_metadata(self, parent_metadata: Optional[Dict[str, str]]=None):

        reference_metadata = self._reference_metadata()

        if parent_metadata is not None:
            if reference_metadata is not None:
                self._metadata = {}
                self._metadata.update(parent_metadata)
                self._metadata.update(reference_metadata)
            else:
                self._metadata = parent_metadata
        else:
            self._metadata = reference_metadata

        return

    def _reference_metadata(self):
        """
            Looks up the metadata if any on the module associated with this group.
        """
        
        refmd = None
        if hasattr(self._inj_function, "_metadata_"):
            refmd = self._inj_function._metadata_

        return refmd

    def __str__(self):
        return self.name
