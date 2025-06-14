"""
    .. module:: automojo.testbase.features
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for features.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import FrozenSet, List, Union, Optional


import bisect


from automojo.errors.exceptions import SemanticError


class FeatureTagNodeMeta(type):
    """
        Metaclass for creating :class:`FeatureTag` derived types.
    """

    def __new__(metacls, name, bases, namespace, **kwargs):
        """
            Creates a new :class:`FeatureTag` derived type.

            :param name: Name of the class being created.
            :param bases: Base classes of the new type.
            :param namespace: Attribute dictionary for the type.
            :param kwargs: Additional keyword arguments.

            :returns: The newly created class.
        """
        cls = super().__new__(metacls, name, bases, namespace, **kwargs)
        cls.ID = cls.__qualname__.lower().replace(".", "/")
        return cls

    def __repr__(self):
        """
            Returns a representation for the tag class.

            :returns: The tag identifier string.
        """
        return "'{}'".format(self.ID)

    def __str__(self):
        """
            Returns the string form of the tag class.

            :returns: The tag identifier string.
        """
        return "{}".format(self.ID)


class FeatureTag(metaclass=FeatureTagNodeMeta):
    """
        Base type used to declare feature tag identifiers.
    """

    ID = None


class FeatureAttachedObject:
    """
        Mixin class providing feature tag support to derived objects.
    """

    FEATURE_TAGS = []

    def __init__(self):
        """
            Initializes a new :class:`FeatureAttachedObject`.

            The constructor seeds the object with any default feature tags
            defined by ``FEATURE_TAGS`` on the derived class.
        """
        self._feature_tags = []
        self.extend_features(self.FEATURE_TAGS)
        return

    @property
    def feature_tags(self) -> FrozenSet[str]:
        """
            The set of feature tag identifiers assigned to this object.

            :returns: Frozen set of feature tag strings.
        """
        return frozenset(self._feature_tags)

    def extend_features(self, features_to_add: Union[List[FeatureTag], List[str]]):
        """
            Used by derived class and mixins to extend the feature tags associated with
            a feature attached object.
        """

        if len(features_to_add) > 0:
            first_item = features_to_add[0]
            if isinstance(first_item, str):
                # We insert the features into the list sorted so we can make finding
                # features faster.
                for ft in features_to_add:
                    bisect.insort(self._feature_tags, ft)
            elif issubclass(first_item, FeatureTag):
                # We insert the features into the list sorted so we can make finding
                # features faster.
                for ft in features_to_add:
                    bisect.insort(self._feature_tags, ft.ID)
            else:
                errmsg = "The 'features_to_add' parameter must contain items of type 'FeatureTag' or 'str'. item={}".format(
                    repr(first_item)
                )
                raise SemanticError(errmsg)

        return
    
    def has_all_features(self, feature_list: Union[List[FeatureTag], List[str]]):
        """
            Determines if all specified features are present on this object.

            :param feature_list: List of feature tag identifiers or
                :class:`FeatureTag` types to validate.

            :returns: ``True`` if the object has all of the given features.
        """

        has_all = True

        if len(feature_list) == 0:
            errmsg = "has_all_features: 'feature_list' cannot be empty."
            raise SemanticError(errmsg)

        first_item = feature_list[0]
        if isinstance(first_item, str):
            for feature in feature_list:
                fid = feature
                hasfeature = fid in self._feature_tags
                if not hasfeature:
                    has_all = False
                    break
        elif issubclass(first_item, FeatureTag):
            for feature in feature_list:
                fid = feature.ID
                hasfeature = fid in self._feature_tags
                if not hasfeature:
                    has_all = False
                    break
        else:
            errmsg = "The 'feature_list' parameter must contain items of type 'FeatureTag' or 'str'. item={}".format(
                repr(first_item)
            )
            raise SemanticError(errmsg)

        return has_all

    def has_any_feature(self, feature_list: List[FeatureTag]):
        """
            Determines if any feature from the list is present on this object.

            :param feature_list: List of feature identifiers or
                :class:`FeatureTag` types.

            :returns: ``True`` if any feature is present.
        """

        has_any = False

        if len(feature_list) == 0:
            errmsg = "has_all_features: 'feature_list' cannot be empty."
            raise SemanticError(errmsg)

        first_item = feature_list[0]
        if isinstance(first_item, str):
            for feature in feature_list:
                fid = feature

                hasfeature = fid in self._feature_tags
                if hasfeature:
                    has_any = True
                    break
        elif issubclass(first_item, FeatureTag):
            for feature in feature_list:
                fid = feature.ID

                hasfeature = fid in self._feature_tags
                if hasfeature:
                    has_any = True
                    break
        else:
            errmsg = "The 'feature_list' parameter must contain items of type 'FeatureTag' or 'str'. item={}".format(
                repr(first_item)
            )
            raise SemanticError(errmsg)

        return has_any

    def has_feature(self, feature: Union[FeatureTag, str]):
        """
            Checks for a specific feature on this object.

            :param feature: The feature identifier or :class:`FeatureTag` type.

            :returns: ``True`` if the feature is present.
        """
        fid = None

        if isinstance(feature, str):
            fid = feature
        elif issubclass(feature, FeatureTag):
            fid = feature.ID
        else:
            errmsg = "The 'feature' parameter must be of type 'FeatureTag' or 'str'. item={}".format(
                repr(feature)
            )
            raise SemanticError(errmsg)

        hasfeature = fid in self._feature_tags

        return hasfeature


class FeatureMask(dict):
    """
        Dictionary wrapper used to describe feature requirements.
    """

    def __init__(self, *, required_features: Optional[List[FeatureTag]]=None, excluded_features: Optional[List[FeatureTag]]=None, **kwargs):
        """
            :param required_features: Features that must be present.
            :param excluded_features: Features that must not be present.
        """
        super().__init__(required_features=required_features, excluded_features=excluded_features, **kwargs)
        return


class FeatureFilter:
    """
        Utility for filtering :class:`FeatureAttachedObject` instances by feature tags.
    """

    def __init__(self, *, required_features: Optional[List[FeatureTag]]=None, excluded_features: Optional[List[FeatureTag]]=None, **kwargs):
        """
            Utility for filtering objects that have feature tags.

            :param required_features: Features that must be present on an object.
            :param excluded_features: Features that disqualify an object.
        """
        self._required_features = required_features
        self._excluded_features = excluded_features
        return

    def filter(self, device_list: List[FeatureAttachedObject]) -> List[FeatureAttachedObject]:
        """
            Filters a list of feature attached objects based on the configured
            required and excluded features.

            :param device_list: The devices to be filtered.

            :returns: List of devices that match the feature criteria.
        """

        matching_devices = []

        for fd in device_list:
            if self._required_features is not None:
                has_req_features = fd.has_all_features(self._required_features)
            else:
                has_req_features = True

            if self._excluded_features is not None:
                has_excl_features = fd.has_any_feature(self._excluded_features)
            else:
                has_excl_features = False

            if has_req_features and not has_excl_features:
                matching_devices.append(fd)

        return matching_devices
