"""
    .. module:: automojo.testbase.features
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing hierarchical, type-safe feature tagging for test categorization and filtering.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

Feature Tagging System
======================

This module provides a hierarchical, type-safe mechanism for categorizing and filtering
objects based on feature capabilities. It is designed to integrate with the testbase
test framework to enable feature-based test selection and execution.

Feature Tag Hierarchy Patterns
------------------------------

Feature tags are defined using a class-based hierarchy where nested classes create
hierarchical identifiers. The metaclass automatically generates unique IDs from the
class hierarchy path.

**Basic Hierarchy Pattern**::

    class DeviceFeatures(FeatureTag):
        '''Top-level feature category for device capabilities.'''
        
        class Network(FeatureTag):
            '''Network-related features.'''
            
            class Wifi(FeatureTag):
                '''WiFi connectivity feature.'''
                pass
            
            class Bluetooth(FeatureTag):
                '''Bluetooth connectivity feature.'''
                
                class BLE(FeatureTag):
                    '''Bluetooth Low Energy support.'''
                    pass
                
                class Classic(FeatureTag):
                    '''Classic Bluetooth support.'''
                    pass

    # Generated IDs:
    # DeviceFeatures.ID == 'devicefeatures'
    # DeviceFeatures.Network.ID == 'devicefeatures/network'
    # DeviceFeatures.Network.Wifi.ID == 'devicefeatures/network/wifi'
    # DeviceFeatures.Network.Bluetooth.BLE.ID == 'devicefeatures/network/bluetooth/ble'

**Domain-Specific Hierarchy Pattern**::

    class TestFeatures(FeatureTag):
        '''Features for categorizing test requirements.'''
        
        class Environment(FeatureTag):
            '''Environment-specific features.'''
            
            class Cloud(FeatureTag):
                pass
            
            class OnPremise(FeatureTag):
                pass
        
        class Performance(FeatureTag):
            '''Performance testing features.'''
            
            class LoadTest(FeatureTag):
                pass
            
            class StressTest(FeatureTag):
                pass

Integration with Test Execution
-------------------------------

The feature tagging system integrates with test execution through the
:class:`FeatureAttachedObject` mixin and :class:`FeatureFilter` utility.

**Attaching Features to Test Objects**::

    class MyTestContainer(FeatureAttachedObject):
        '''Test container with default features.'''
        
        FEATURE_TAGS = [DeviceFeatures.Network.Wifi]
        
        def test_wifi_connection(self):
            '''Test that requires WiFi capability.'''
            pass

**Filtering Tests by Feature**::

    # Create a filter for WiFi tests, excluding legacy devices
    test_filter = FeatureFilter(
        required_features=[DeviceFeatures.Network.Wifi],
        excluded_features=[DeviceFeatures.Legacy]
    )
    
    # Apply filter to test collection
    wifi_tests = test_filter.filter(all_tests)

**Dynamic Feature Assignment**::

    test_obj = MyTestContainer()
    
    # Add features at runtime based on environment
    if has_bluetooth_hardware():
        test_obj.extend_features([DeviceFeatures.Network.Bluetooth])
    
    # Check feature availability before execution
    if test_obj.has_feature(DeviceFeatures.Network.Bluetooth):
        run_bluetooth_tests()

**Using Feature Masks for Declarative Requirements**::

    # Define feature requirements declaratively
    wifi_only_mask = FeatureMask(
        required_features=[DeviceFeatures.Network.Wifi],
        excluded_features=[DeviceFeatures.Legacy]
    )
    
    # Pass mask to test execution engine
    execute_tests(test_suite, feature_mask=wifi_only_mask)

Best Practices for Feature Organization
---------------------------------------

1. **Use Meaningful Hierarchies**
   
   Organize features in a logical hierarchy that reflects your domain model.
   Group related features under common parent tags::
   
       class Features(FeatureTag):
           class Hardware(FeatureTag):
               class CPU(FeatureTag):
                   pass
               class Memory(FeatureTag):
                   pass
           class Software(FeatureTag):
               class OS(FeatureTag):
                   pass
               class Drivers(FeatureTag):
                   pass

2. **Keep Hierarchies Shallow**
   
   Avoid deeply nested hierarchies (more than 3-4 levels). Deep nesting makes
   IDs long and harder to work with. If you need more specificity, consider
   using multiple top-level categories instead.

3. **Define Features in a Central Location**
   
   Create a dedicated module (e.g., ``features.py`` or ``feature_tags.py``)
   in your test package to define all feature tags. This ensures consistency
   and makes it easy to discover available features::
   
       # myproject/tests/feature_tags.py
       from automojo.testbase.features import FeatureTag
       
       class ProjectFeatures(FeatureTag):
           class API(FeatureTag):
               class REST(FeatureTag):
                   pass
               class GraphQL(FeatureTag):
                   pass

4. **Use Class-Level FEATURE_TAGS for Defaults**
   
   Define default features at the class level using ``FEATURE_TAGS`` to ensure
   all instances of a test class have consistent base features::
   
       class NetworkTests(FeatureAttachedObject):
           FEATURE_TAGS = [Features.Network]
           
           # All instances will have 'features/network' by default

5. **Prefer FeatureTag Classes Over Strings**
   
   Use :class:`FeatureTag` subclasses instead of string identifiers when
   possible. This provides type safety and IDE autocompletion::
   
       # Preferred - type-safe
       obj.extend_features([Features.Network.Wifi])
       obj.has_feature(Features.Network.Wifi)
       
       # Avoid - error-prone
       obj.extend_features(['features/network/wifi'])
       obj.has_feature('features/network/wifi')

6. **Document Feature Semantics**
   
   Add docstrings to feature tag classes explaining what capability or
   requirement each feature represents::
   
       class Features(FeatureTag):
           class RequiresInternet(FeatureTag):
               '''Tests requiring active internet connection.'''
               pass
           
           class Destructive(FeatureTag):
               '''Tests that modify system state and cannot be safely parallelized.'''
               pass

7. **Use Filters for Test Selection**
   
   Create reusable :class:`FeatureFilter` instances for common test selection
   patterns::
   
       # Define common filters
       QUICK_TESTS = FeatureFilter(excluded_features=[Features.SlowTest])
       NETWORK_TESTS = FeatureFilter(required_features=[Features.Network])
       SAFE_TESTS = FeatureFilter(excluded_features=[Features.Destructive])

8. **Avoid Duplicate Features**
   
   The ``extend_features`` method does not prevent duplicates. Ensure you
   don't add the same feature multiple times, or use the ``feature_tags``
   property (which returns a frozenset) when checking for features.

Module Components
-----------------

- :class:`FeatureTagNodeMeta` - Metaclass for automatic ID generation
- :class:`FeatureTag` - Base class for defining feature tags
- :class:`FeatureAttachedObject` - Mixin for attaching features to objects
- :class:`FeatureMask` - Dictionary wrapper for declarative feature requirements
- :class:`FeatureFilter` - Utility for filtering objects by feature criteria

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

        This metaclass automatically generates unique identifiers for feature tag classes
        based on their qualified name. The ID is derived by converting the class's
        ``__qualname__`` to lowercase and replacing periods with forward slashes.

        Example::

            class DeviceFeatures(FeatureTag):
                class Network(FeatureTag):
                    class Wifi(FeatureTag):
                        pass

            # DeviceFeatures.ID == 'devicefeatures'
            # DeviceFeatures.Network.ID == 'devicefeatures/network'
            # DeviceFeatures.Network.Wifi.ID == 'devicefeatures/network/wifi'
    """

    def __new__(metacls, name, bases, namespace, **kwargs):
        """
            Creates a new :class:`FeatureTag` derived type.

            The method automatically assigns an ``ID`` attribute to the new class
            based on its qualified name, converted to lowercase with periods replaced
            by forward slashes.

            :param name: Name of the class being created.
            :type name: str
            :param bases: Base classes of the new type.
            :type bases: tuple
            :param namespace: Attribute dictionary for the type.
            :type namespace: dict
            :param kwargs: Additional keyword arguments passed to the metaclass.

            :returns: The newly created class with an automatically assigned ``ID`` attribute.
            :rtype: type

            Example::

                class MyFeature(FeatureTag):
                    pass

                # MyFeature.ID == 'myfeature'
        """
        cls = super().__new__(metacls, name, bases, namespace, **kwargs)
        cls.ID = cls.__qualname__.lower().replace(".", "/")
        return cls

    def __repr__(self):
        """
            Returns a representation for the tag class.

            The representation wraps the ID string in single quotes for clarity
            when debugging or logging.

            :returns: The tag identifier string wrapped in single quotes.
            :rtype: str

            Example::

                class Alpha(FeatureTag):
                    pass

                repr(Alpha)  # Returns "'alpha'"
        """
        return "'{}'".format(self.ID)

    def __str__(self):
        """
            Returns the string form of the tag class.

            :returns: The tag identifier string without quotes.
            :rtype: str

            Example::

                class Alpha(FeatureTag):
                    pass

                str(Alpha)  # Returns 'alpha'
        """
        return "{}".format(self.ID)


class FeatureTag(metaclass=FeatureTagNodeMeta):
    """
        Base type used to declare feature tag identifiers.

        Feature tags are defined by creating classes that inherit from :class:`FeatureTag`.
        The metaclass :class:`FeatureTagNodeMeta` automatically generates a unique ``ID``
        attribute for each tag class based on its qualified name.

        Feature tags can be nested to create hierarchical feature definitions, where
        the ID reflects the full hierarchy path.

        :cvar ID: The automatically generated identifier for this feature tag.
        :vartype ID: str

        Example::

            class DeviceFeatures(FeatureTag):
                class Bluetooth(FeatureTag):
                    class BLE(FeatureTag):
                        pass
                    class Classic(FeatureTag):
                        pass
                class Display(FeatureTag):
                    class OLED(FeatureTag):
                        pass

            # Access IDs:
            # DeviceFeatures.Bluetooth.ID == 'devicefeatures/bluetooth'
            # DeviceFeatures.Bluetooth.BLE.ID == 'devicefeatures/bluetooth/ble'
            # DeviceFeatures.Display.OLED.ID == 'devicefeatures/display/oled'
    """

    ID = None


class FeatureAttachedObject:
    """
        Mixin class providing feature tag support to derived objects.

        This mixin enables any derived class to have feature tags attached to it,
        which can then be used for filtering and categorization. Feature tags are
        stored internally in a sorted list for efficient lookup.

        Classes deriving from :class:`FeatureAttachedObject` can define default
        feature tags using the ``FEATURE_TAGS`` class attribute.

        :cvar FEATURE_TAGS: Default list of feature tags for all instances of the class.
        :vartype FEATURE_TAGS: List[Union[FeatureTag, str]]

        Example::

            class NetworkFeatures(FeatureTag):
                class Wifi(FeatureTag):
                    pass
                class Bluetooth(FeatureTag):
                    pass

            class WifiDevice(FeatureAttachedObject):
                FEATURE_TAGS = [NetworkFeatures.Wifi]

            device = WifiDevice()
            device.has_feature(NetworkFeatures.Wifi)  # Returns True
            device.extend_features([NetworkFeatures.Bluetooth])
            device.has_feature(NetworkFeatures.Bluetooth)  # Returns True
    """

    FEATURE_TAGS = []

    def __init__(self):
        """
            Initializes a new :class:`FeatureAttachedObject`.

            The constructor initializes an empty internal feature tags list and
            seeds the object with any default feature tags defined by ``FEATURE_TAGS``
            on the derived class.

            Example::

                class MyFeatures(FeatureTag):
                    class Alpha(FeatureTag):
                        pass

                class MyObject(FeatureAttachedObject):
                    FEATURE_TAGS = [MyFeatures.Alpha]

                obj = MyObject()
                # obj now has 'myfeatures/alpha' in its feature tags
        """
        self._feature_tags = []
        self.extend_features(self.FEATURE_TAGS)
        return

    @property
    def feature_tags(self) -> FrozenSet[str]:
        """
            The set of feature tag identifiers assigned to this object.

            Returns an immutable frozen set containing all feature tag identifiers
            currently attached to this object. The frozen set prevents external
            modification of the feature tags.

            :returns: Frozen set of feature tag identifier strings.
            :rtype: FrozenSet[str]

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass
                    class Beta(FeatureTag):
                        pass

                obj = FeatureAttachedObject()
                obj.extend_features([Features.Alpha, Features.Beta])
                tags = obj.feature_tags
                # tags == frozenset({'features/alpha', 'features/beta'})
        """
        return frozenset(self._feature_tags)

    def extend_features(self, features_to_add: Union[List[FeatureTag], List[str]]):
        """
            Extends the feature tags associated with this object.

            Adds the specified features to the object's internal feature tags list.
            Features are inserted in sorted order using binary insertion for efficient
            lookup. The method accepts either a list of :class:`FeatureTag` subclasses
            or a list of string identifiers.

            .. note::
                All items in the list must be of the same type (all strings or all
                FeatureTag subclasses). Mixed lists are not supported and may cause
                unexpected behavior.

            .. note::
                This method does not prevent duplicate feature additions. The same
                feature ID can appear multiple times in the internal list.

            :param features_to_add: List of feature tags to add. Can be either
                :class:`FeatureTag` subclasses or string identifiers.
            :type features_to_add: Union[List[FeatureTag], List[str]]

            :raises SemanticError: If the list contains items that are neither
                :class:`FeatureTag` subclasses nor strings.

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass

                obj = FeatureAttachedObject()

                # Using FeatureTag classes
                obj.extend_features([Features.Alpha])

                # Using string identifiers
                obj.extend_features(['custom/feature'])
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

            Checks whether the object has every feature in the provided list.
            Returns ``True`` only if all features are present; returns ``False``
            if any feature is missing.

            .. note::
                All items in the list must be of the same type (all strings or all
                FeatureTag subclasses). Mixed lists are not supported.

            :param feature_list: List of feature tag identifiers or
                :class:`FeatureTag` types to validate.
            :type feature_list: Union[List[FeatureTag], List[str]]

            :returns: ``True`` if the object has all of the given features,
                ``False`` otherwise.
            :rtype: bool

            :raises SemanticError: If ``feature_list`` is empty.
            :raises SemanticError: If the list contains items that are neither
                :class:`FeatureTag` subclasses nor strings.

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass
                    class Beta(FeatureTag):
                        pass

                obj = FeatureAttachedObject()
                obj.extend_features([Features.Alpha])

                obj.has_all_features([Features.Alpha])  # Returns True
                obj.has_all_features([Features.Alpha, Features.Beta])  # Returns False
                obj.has_all_features(['features/alpha'])  # Returns True
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

            Checks whether the object has at least one feature from the provided list.
            Returns ``True`` if any feature is present; returns ``False`` if none
            of the features are present.

            .. note::
                All items in the list must be of the same type (all strings or all
                FeatureTag subclasses). Mixed lists are not supported.

            :param feature_list: List of feature identifiers or
                :class:`FeatureTag` types to check.
            :type feature_list: Union[List[FeatureTag], List[str]]

            :returns: ``True`` if any feature is present, ``False`` otherwise.
            :rtype: bool

            :raises SemanticError: If ``feature_list`` is empty.
            :raises SemanticError: If the list contains items that are neither
                :class:`FeatureTag` subclasses nor strings.

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass
                    class Beta(FeatureTag):
                        pass

                obj = FeatureAttachedObject()
                obj.extend_features([Features.Alpha])

                obj.has_any_feature([Features.Alpha, Features.Beta])  # Returns True
                obj.has_any_feature([Features.Beta])  # Returns False
                obj.has_any_feature(['features/alpha'])  # Returns True
        """

        has_any = False

        if len(feature_list) == 0:
            errmsg = "has_any_feature: 'feature_list' cannot be empty."
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

            Determines whether a single feature is present on this object.

            :param feature: The feature identifier string or :class:`FeatureTag`
                subclass to check for.
            :type feature: Union[FeatureTag, str]

            :returns: ``True`` if the feature is present, ``False`` otherwise.
            :rtype: bool

            :raises SemanticError: If ``feature`` is neither a :class:`FeatureTag`
                subclass nor a string.

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass

                obj = FeatureAttachedObject()
                obj.extend_features([Features.Alpha])

                obj.has_feature(Features.Alpha)  # Returns True
                obj.has_feature('features/alpha')  # Returns True
                obj.has_feature('nonexistent')  # Returns False
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

        A :class:`FeatureMask` is a specialized dictionary that stores required
        and excluded features for declarative feature requirement specifications.
        It inherits from ``dict`` and supports standard dictionary access patterns.

        The mask stores features under the keys ``'required_features'`` and
        ``'excluded_features'``.

        Example::

            class Features(FeatureTag):
                class Wifi(FeatureTag):
                    pass
                class Bluetooth(FeatureTag):
                    pass
                class Legacy(FeatureTag):
                    pass

            # Create a mask requiring Wifi but excluding Legacy devices
            mask = FeatureMask(
                required_features=[Features.Wifi],
                excluded_features=[Features.Legacy]
            )

            # Access features via dictionary keys
            mask['required_features']  # [Features.Wifi]
            mask['excluded_features']  # [Features.Legacy]
    """

    def __init__(self, *, required_features: Optional[List[FeatureTag]]=None, excluded_features: Optional[List[FeatureTag]]=None, **kwargs):
        """
            Creates a new :class:`FeatureMask` with the specified feature requirements.

            :param required_features: List of :class:`FeatureTag` subclasses that
                must be present on matching objects. Defaults to ``None``.
            :type required_features: Optional[List[FeatureTag]]
            :param excluded_features: List of :class:`FeatureTag` subclasses that
                must not be present on matching objects. Defaults to ``None``.
            :type excluded_features: Optional[List[FeatureTag]]
            :param kwargs: Additional keyword arguments passed to the dict constructor.

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass

                # Create a mask with required features
                mask = FeatureMask(required_features=[Features.Alpha])

                # Create a mask with excluded features
                mask = FeatureMask(excluded_features=[Features.Alpha])

                # Create a mask with both
                mask = FeatureMask(
                    required_features=[Features.Alpha],
                    excluded_features=[Features.Beta]
                )
        """
        super().__init__(required_features=required_features, excluded_features=excluded_features, **kwargs)
        return


class FeatureFilter:
    """
        Utility for filtering :class:`FeatureAttachedObject` instances by feature tags.

        A :class:`FeatureFilter` encapsulates filtering criteria (required and excluded
        features) and can be applied to collections of feature-attached objects to
        select only those matching the criteria.

        Objects are included in the filtered result if they:
        - Have all required features (when ``required_features`` is specified)
        - Have none of the excluded features (when ``excluded_features`` is specified)

        Example::

            class Features(FeatureTag):
                class Wifi(FeatureTag):
                    pass
                class Bluetooth(FeatureTag):
                    pass
                class Legacy(FeatureTag):
                    pass

            # Create devices with different features
            class Device(FeatureAttachedObject):
                pass

            wifi_device = Device()
            wifi_device.extend_features([Features.Wifi])

            bluetooth_device = Device()
            bluetooth_device.extend_features([Features.Bluetooth])

            legacy_device = Device()
            legacy_device.extend_features([Features.Wifi, Features.Legacy])

            devices = [wifi_device, bluetooth_device, legacy_device]

            # Filter for Wifi devices, excluding Legacy
            filter = FeatureFilter(
                required_features=[Features.Wifi],
                excluded_features=[Features.Legacy]
            )
            result = filter.filter(devices)
            # result contains only wifi_device (legacy_device is excluded)
    """

    def __init__(self, *, required_features: Optional[List[FeatureTag]]=None, excluded_features: Optional[List[FeatureTag]]=None, **kwargs):
        """
            Creates a new :class:`FeatureFilter` with the specified criteria.

            :param required_features: List of :class:`FeatureTag` subclasses that
                must be present on objects to be included. If ``None``, no required
                feature filtering is applied. Defaults to ``None``.
            :type required_features: Optional[List[FeatureTag]]
            :param excluded_features: List of :class:`FeatureTag` subclasses that
                disqualify objects from inclusion. If ``None``, no exclusion filtering
                is applied. Defaults to ``None``.
            :type excluded_features: Optional[List[FeatureTag]]
            :param kwargs: Additional keyword arguments (reserved for future use).

            Example::

                class Features(FeatureTag):
                    class Alpha(FeatureTag):
                        pass

                # Filter requiring Alpha feature
                filter = FeatureFilter(required_features=[Features.Alpha])

                # Filter excluding Alpha feature
                filter = FeatureFilter(excluded_features=[Features.Alpha])

                # Filter with both criteria
                filter = FeatureFilter(
                    required_features=[Features.Alpha],
                    excluded_features=[Features.Beta]
                )
        """
        self._required_features = required_features
        self._excluded_features = excluded_features
        return

    def filter(self, device_list: List[FeatureAttachedObject]) -> List[FeatureAttachedObject]:
        """
            Filters a list of feature attached objects based on the configured criteria.

            Iterates through the provided list and returns a new list containing only
            objects that match the filter criteria:

            - If ``required_features`` is set, objects must have all required features
            - If ``excluded_features`` is set, objects must not have any excluded features
            - If both are set, both conditions must be satisfied

            The original order of matching objects is preserved in the returned list.

            :param device_list: List of :class:`FeatureAttachedObject` instances to filter.
            :type device_list: List[FeatureAttachedObject]

            :returns: A new list containing only objects that match the filter criteria.
            :rtype: List[FeatureAttachedObject]

            Example::

                class Features(FeatureTag):
                    class Wifi(FeatureTag):
                        pass
                    class Bluetooth(FeatureTag):
                        pass

                class Device(FeatureAttachedObject):
                    pass

                device1 = Device()
                device1.extend_features([Features.Wifi])

                device2 = Device()
                device2.extend_features([Features.Bluetooth])

                device3 = Device()
                device3.extend_features([Features.Wifi, Features.Bluetooth])

                devices = [device1, device2, device3]

                # Filter for devices with Wifi
                wifi_filter = FeatureFilter(required_features=[Features.Wifi])
                wifi_devices = wifi_filter.filter(devices)
                # wifi_devices contains [device1, device3]

                # Filter for devices without Bluetooth
                no_bt_filter = FeatureFilter(excluded_features=[Features.Bluetooth])
                no_bt_devices = no_bt_filter.filter(devices)
                # no_bt_devices contains [device1]
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
