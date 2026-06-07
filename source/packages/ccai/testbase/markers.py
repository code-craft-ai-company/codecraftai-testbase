"""
    .. module:: ccai.testbase.markers
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for test markers and metadata-based filtering.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>

Test Markers and Metadata
=========================

This module provides mechanisms for annotating tests and test modules with metadata
that can be used for filtering, categorization, and prioritization during test execution.

Overview
--------

The markers system supports two types of markers:

1. **Function-Level Markers**: Decorators that attach metadata directly to individual
   test functions via the ``_metadata_`` attribute.

2. **Module-Level Descendent Markers**: Functions that apply metadata to a module,
   which then propagates to all tests within that module's hierarchy.

Marker Expression Syntax
------------------------

Marker expressions are string-based filter specifications used to select or exclude
tests based on their metadata. The general syntax is::

    (+ | -) <group> (== | ~= | !=) <value>

**Components:**

- ``+`` or ``-``: Include (``+``) or exclude (``-``) modifier
- ``<group>``: The metadata key to filter on (e.g., ``categories``, ``keywords``, ``priority``)
- ``==``, ``~=``, ``!=``: Comparison operator
- ``<value>``: The value to compare against

**Operators:**

+----------+------------------------+--------------------------------------------------+
| Operator | Filter Class           | Description                                      |
+==========+========================+==================================================+
| ``==``   | MetaFilterEquals       | Exact equality match                             |
+----------+------------------------+--------------------------------------------------+
| ``~=``   | MetaFilterContains     | Substring match (strings) or membership (lists)  |
+----------+------------------------+--------------------------------------------------+
| ``!=``   | MetaFilterNotEquals    | Inverse of equality match                        |
+----------+------------------------+--------------------------------------------------+

**Examples:**

- ``+categories~=smoke`` - Include tests where categories contain 'smoke'
- ``-priority==3`` - Exclude tests where priority equals '3'
- ``+keywords~=api`` - Include tests where keywords contain 'api'
- ``-categories!=integration`` - Exclude tests where categories do NOT equal 'integration'

Metadata Propagation Behavior
-----------------------------

Metadata can be applied at two levels, with specific propagation rules:

**Function-Level Metadata:**

When a decorator like ``@mark_categories`` is applied to a test function, the metadata
is stored directly on that function's ``_metadata_`` dictionary. This metadata applies
only to that specific test.

Example::

    @mark_categories(categories=["smoke", "api"])
    @mark_priority(priority=1)
    def test_user_login():
        pass

**Module-Level Metadata (Descendent Markers):**

When a descendent marker function like ``mark_descendent_categories()`` is called at
module scope, the metadata is stored on the module's ``_metadata_`` dictionary. This
metadata propagates to ALL tests that reside under that module in the test hierarchy.

Example::

    # In test_api_module.py
    from ccai.testbase.markers import mark_descendent_categories, mark_descendent_priority

    mark_descendent_categories(categories=["api"])
    mark_descendent_priority(priority=2)

    def test_endpoint_a():
        # Inherits categories=["api"] and priority="2" from module
        pass

    def test_endpoint_b():
        # Also inherits categories=["api"] and priority="2" from module
        pass

**Metadata Resolution Order:**

During test collection and filtering, metadata is resolved in the following order:

1. Function-level metadata (highest priority, most specific)
2. Module-level metadata (inherited from containing module)
3. Parent module metadata (inherited from parent modules in hierarchy)

Function-level metadata takes precedence over module-level metadata when both define
the same key.

Integration with Test Execution
-------------------------------

The markers system integrates with the test execution engine through the following flow:

1. **Test Collection Phase:**
   - Test functions are discovered and their ``_metadata_`` attributes are read
   - Module ``_metadata_`` attributes are collected for inheritance resolution
   - ``TestRef`` and ``TestGroup`` objects store resolved metadata

2. **Filter Application Phase:**
   - Marker expressions from command-line arguments or configuration are parsed
   - ``parse_marker_expression()`` converts strings to ``MetaFilter`` objects
   - Each filter's ``should_include()`` method is called with test metadata

3. **Test Selection Phase:**
   - Tests passing all include filters are selected for execution
   - Tests matching any exclude filter are removed from selection
   - Multiple filters can be combined for complex selection criteria

**Command-Line Usage:**

Marker expressions can be specified via command-line arguments::

    testbase --marker "+categories~=smoke" --marker "-priority==3"

This would run all smoke tests except those with priority 3.

**Programmatic Usage:**

Filters can also be created and applied programmatically::

    from ccai.testbase.markers import parse_marker_expression

    # Parse expression into filter
    filter_obj = parse_marker_expression("+categories~=smoke")

    # Apply filter to test metadata
    test_metadata = {"categories": ["smoke", "api"], "priority": "1"}
    should_run = filter_obj.should_include(test_metadata)  # Returns True

Available Markers
-----------------

**Function-Level Decorators:**

- :func:`mark_categories` - Assign category labels to a test
- :func:`mark_keywords` - Assign searchable keywords to a test
- :func:`mark_priority` - Assign execution priority to a test

**Module-Level Functions:**

- :func:`mark_descendent_categories` - Apply categories to all descendant tests
- :func:`mark_descendent_keywords` - Apply keywords to all descendant tests
- :func:`mark_descendent_priority` - Apply priority to all descendant tests

**Filter Classes:**

- :class:`MetaFilter` - Abstract base class for metadata filters
- :class:`MetaFilterContains` - Containment/membership filter (``~=`` operator)
- :class:`MetaFilterEquals` - Exact equality filter (``==`` operator)
- :class:`MetaFilterNotEquals` - Not-equals filter (``!=`` operator)

**Parser Function:**

- :func:`parse_marker_expression` - Convert string expressions to MetaFilter objects

Error Handling
--------------

The ``parse_marker_expression`` function raises :class:`SemanticError` for invalid
expressions:

- Missing include/exclude symbol (``+`` or ``-``)
- Missing or invalid operator (``==``, ``~=``, ``!=``)
- Missing value component after operator

Example error messages::

    SemanticError: Marker expressions must begin with a + (include) or - (exclude) symbol.
    SemanticError: Marker expressions must be in the form (+ or -)(group)/(marker)(= or ~)(value).
    SemanticError: Expressions using the "==", "~=", "!=" operators must have a value component.

"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Callable, Dict, List

import inspect


from ccai.errors.exceptions import SemanticError


def mark_categories(*, categories: List[str]):
    """
        Used to mark a test with category markers.
    """

    def decorator(func: Callable) -> Callable:

        if not hasattr(func, "_metadata_"):
            func._metadata_ = {}

        func._metadata_["categories"] = categories

        return func

    return decorator


def mark_keywords(*, keywords: List[str]):
    """
        Used to mark a test with a list of keywords.
    """

    def decorator(func: Callable) -> Callable:

        if not hasattr(func, "_metadata_"):
            func._metadata_ = {}

        func._metadata_["keywords"] = keywords

        return func

    return decorator


def mark_priority(*, priority: int):
    """
        Used to mark a test with a priority.
    """

    def decorator(func: Callable) -> Callable:

        if not hasattr(func, "_metadata_"):
            func._metadata_ = {}

        func._metadata_["priority"] = str(priority)

        return func

    return decorator


def mark_descendent_categories(*, categories: List[str]):
    """
        Used to mark a module and all tests that reside under it in scope with a list of categories.

        :param categories: A list of categories to assign to descendent groups and tests
    """
    
    caller_frame = inspect.stack()[1]
    calling_module = inspect.getmodule(caller_frame[0])

    if not hasattr(calling_module, "_metadata_"):
        calling_module._metadata_ = {}

    calling_module._metadata_["categories"] = categories

    return


def mark_descendent_keywords(*, keywords: List[str]):
    """
        Used to mark a module and all tests that reside under it in scope with a list of keywords.

        :param keywords: A list of keywords to assign to descendent groups and tests
    """
    
    caller_frame = inspect.stack()[1]
    calling_module = inspect.getmodule(caller_frame[0])

    if not hasattr(calling_module, "_metadata_"):
        calling_module._metadata_ = {}

    calling_module._metadata_["keywords"] = keywords

    return


def mark_descendent_priority(*, priority: int):
    """
        Used to mark a module and all tests that reside under it in scope with a priority.

        :param priority: A priority to assign te descendent groups and tests.
    """

    caller_frame = inspect.stack()[1]
    calling_module = inspect.getmodule(caller_frame[0])

    if not hasattr(calling_module, "_metadata_"):
        calling_module._metadata_ = {}

    calling_module._metadata_["priority"] = str(priority)

    return


class MetaFilter:
    """
        Base class for metadata-based include or exclude filters used to select tests
        based on their metadata attributes.

        The MetaFilter class provides the foundation for metadata-based test filtering.
        It stores an include flag indicating whether the filter is for inclusion or exclusion,
        and a group string identifying the metadata key to filter on. Derived classes must
        implement the :meth:`should_include` method to define specific matching behavior.

        :param include: When True, the filter operates in include mode (tests matching the
            filter are included). When False, the filter operates in exclude mode (tests
            matching the filter are excluded).
        :param group: The metadata key to filter on (e.g., 'categories', 'keywords', 'priority').

        Example usage::

            # Create a custom filter by extending MetaFilter
            class MyCustomFilter(MetaFilter):
                def __init__(self, include: bool, group: str, pattern: str):
                    super().__init__(include, group)
                    self._pattern = pattern
                    return

                def should_include(self, metadata: Dict[str, Any]) -> bool:
                    # Custom matching logic here
                    pass

        .. note::
            This is an abstract base class. Calling :meth:`should_include` directly on
            a MetaFilter instance will raise NotImplementedError. Use one of the concrete
            implementations: :class:`MetaFilterContains`, :class:`MetaFilterEquals`, or
            :class:`MetaFilterNotEquals`.
    """

    def __init__(self, include: bool, group: str):
        self._include = include
        self._group = group
        return

    @property
    def group(self) -> str:
        """
            The metadata key that this filter operates on.

            :returns: The group string identifying the metadata key (e.g., 'categories',
                'keywords', 'priority').
        """
        return self._group

    @property
    def include(self) -> bool:
        """
            Indicates whether this filter operates in include or exclude mode.

            :returns: True if the filter is in include mode (matching tests are included),
                False if in exclude mode (matching tests are excluded).
        """
        return self._include

    def should_include(self, metadata: Dict[str, Any]) -> bool:
        """
            Determines whether a test with the given metadata should be included in execution.

            This method must be implemented by derived classes to define the specific
            matching behavior for the filter type.

            :param metadata: A dictionary containing the test's metadata attributes.
                Expected keys include 'categories', 'keywords', and 'priority'.

            :returns: True if the test should be included in execution, False otherwise.

            :raises: NotImplementedError when called on the base MetaFilter class.
        """
        errmsg = "MetaFilter.should_include must be implemented in derived classes."
        raise NotImplementedError(errmsg)


class MetaFilterContains(MetaFilter):
    """
        Filter that checks if a metadata value contains a substring or list member.

        This filter is used with the ``~=`` operator in marker expressions. It performs
        containment checks based on the type of the metadata value:

        - For string metadata values: Returns True if the filter value is a substring
          of the metadata value.
        - For list or tuple metadata values: Returns True if the filter value is a
          member of the collection.

        :param include: When True, tests with matching metadata are included. When False,
            tests with matching metadata are excluded.
        :param group: The metadata key to filter on (e.g., 'categories', 'keywords').
        :param value: The value to search for within the metadata.

        Example usage::

            # Include tests where categories contain 'smoke'
            filter_include = MetaFilterContains(include=True, group='categories', value='smoke')

            # Exclude tests where keywords contain 'slow'
            filter_exclude = MetaFilterContains(include=False, group='keywords', value='slow')

            # Check if a test should be included
            metadata = {'categories': ['smoke', 'api'], 'keywords': ['fast', 'unit']}
            result = filter_include.should_include(metadata)  # Returns True

            # String containment example
            metadata_str = {'priority': 'high-priority'}
            filter_str = MetaFilterContains(include=True, group='priority', value='high')
            result = filter_str.should_include(metadata_str)  # Returns True

        .. note::
            When metadata is None or does not contain the specified group key, the filter
            returns False in include mode and True in exclude mode.
    """

    def __init__(self, include: bool, group: str, value: str):
        super().__init__(include, group)
        self._value = value
        return
    
    def should_include(self, metadata: Dict[str, Any]) -> bool:
        """
            Determines whether a test should be included based on containment matching.

            The method checks if the filter value is contained within the metadata value
            for the specified group key. The containment check varies based on the type
            of the metadata value:

            - String: Checks if filter value is a substring
            - List/Tuple: Checks if filter value is a member

            :param metadata: A dictionary containing the test's metadata attributes.
                If None or missing the group key, returns False for include mode
                and True for exclude mode.

            :returns: In include mode, returns True if the metadata value contains the
                filter value. In exclude mode, returns the inverse (True if NOT contained).
        """

        include = False

        if metadata is not None:
            if self._group in metadata:
                found_marker = metadata[self._group]
                if isinstance(found_marker, str):
                    if found_marker.find(self._value) > -1:
                        include = True
                elif isinstance(found_marker, list) or isinstance(found_marker, tuple):
                    if self._value in found_marker:
                        include = True

        # If this is an exclude based match, then negate the logic
        # of the match
        if not self._include:
            include = False if include else True

        return include

class MetaFilterEquals(MetaFilter):
    """
        Filter that checks if a metadata value exactly equals a target value.

        This filter is used with the ``==`` operator in marker expressions. It performs
        exact equality comparison between the filter value and the metadata value for
        the specified group key.

        :param include: When True, tests with matching metadata are included. When False,
            tests with matching metadata are excluded.
        :param group: The metadata key to filter on (e.g., 'priority', 'categories').
        :param value: The exact value to match against the metadata.

        Example usage::

            # Include tests where priority equals '1'
            filter_include = MetaFilterEquals(include=True, group='priority', value='1')

            # Exclude tests where priority equals '3'
            filter_exclude = MetaFilterEquals(include=False, group='priority', value='3')

            # Check if a test should be included
            metadata = {'priority': '1', 'categories': ['smoke']}
            result = filter_include.should_include(metadata)  # Returns True

            # Non-matching example
            metadata_no_match = {'priority': '2'}
            result = filter_include.should_include(metadata_no_match)  # Returns False

        .. note::
            When metadata is None or does not contain the specified group key, the filter
            returns False in include mode and True in exclude mode.
    """

    def __init__(self, include: bool, group: str, value: str):
        super().__init__(include, group)
        self._value = value
        return

    def should_include(self, metadata: Dict[str, Any]) -> bool:
        """
            Determines whether a test should be included based on exact equality matching.

            The method checks if the metadata value for the specified group key exactly
            equals the filter value.

            :param metadata: A dictionary containing the test's metadata attributes.
                If None or missing the group key, returns False for include mode
                and True for exclude mode.

            :returns: In include mode, returns True if the metadata value exactly equals
                the filter value. In exclude mode, returns the inverse (True if NOT equal).
        """

        include = False

        if metadata is not None:
            if self._group in metadata:
                found_marker = metadata[self._group]
                if found_marker == self._value:
                    include = True

        # If this is an exclude based match, then negate the logic
        # of the match
        if not self._include:
            include = False if include else True

        return include

class MetaFilterNotEquals(MetaFilterEquals):
    """
        Filter that matches when a metadata value does not equal the target value.

        This filter is used with the ``!=`` operator in marker expressions. It extends
        :class:`MetaFilterEquals` and inverts the equality result, returning True when
        the values do NOT match.

        :param include: When True, tests where metadata does NOT equal the value are
            included. When False, tests where metadata does NOT equal the value are
            excluded.
        :param group: The metadata key to filter on (e.g., 'priority', 'categories').
        :param value: The value to compare against (tests NOT matching this value pass).

        Example usage::

            # Include tests where priority is NOT '3' (low priority)
            filter_include = MetaFilterNotEquals(include=True, group='priority', value='3')

            # Exclude tests where priority is NOT '1' (exclude non-high-priority)
            filter_exclude = MetaFilterNotEquals(include=False, group='priority', value='1')

            # Check if a test should be included
            metadata = {'priority': '1', 'categories': ['smoke']}
            result = filter_include.should_include(metadata)  # Returns True (1 != 3)

            # Matching value example (should NOT include)
            metadata_match = {'priority': '3'}
            result = filter_include.should_include(metadata_match)  # Returns False (3 == 3)

        .. note::
            The not-equals logic is applied first, then the include/exclude mode inversion
            is applied. This means in exclude mode, the result is inverted twice:
            once for not-equals and once for exclude mode.
    """

    def __init__(self, include: bool, group: str, value: str):
        super().__init__(include, group, value)
        return

    def should_include(self, metadata: Dict[str, Any]) -> bool:
        """
            Determines whether a test should be included based on not-equals matching.

            The method first evaluates the equals condition using the parent class logic,
            then inverts the result. This means:

            - If the metadata value equals the filter value, returns False (in include mode)
            - If the metadata value does NOT equal the filter value, returns True (in include mode)

            :param metadata: A dictionary containing the test's metadata attributes.
                If None or missing the group key, the parent class returns False for
                include mode, which is then inverted to True.

            :returns: In include mode, returns True if the metadata value does NOT equal
                the filter value. In exclude mode, the result is inverted again.
        """

        include = super().should_include(metadata)
        include = False if include else True

        return include


def parse_marker_expression(expression: str):

    include = True
    group = None
    marker = None

    working_expr = expression.strip()

    include_symbol = working_expr[0]
    if include_symbol == "+":
        include = True
    elif include_symbol == "-":
        include = False
    else:
        errmsg = "Marker expressions must begin with a + (include) or - (exclude) symbol. expression={}".format(expression)
        raise SemanticError(errmsg)

    # Strip off the include or exclude
    working_expr = working_expr[1:].lstrip()

    errmsg = "Marker expressions must be in the form (+ or -)(group)/(marker)(= or ~)(value). expression={}".format(expression)

    operator = None
    # Equals
    if working_expr.find("==") > 0:
        operator = "=="
        working_expr.split(operator)
    # Contains
    elif working_expr.find("~=") > 0:
        operator = "~="
    # Not Equal
    elif working_expr.find("!=") > 0:
        operator = "!="
    else:
        raise SemanticError(errmsg)

    marker_group = None
    marker_value = None

    next_parts = working_expr.split(operator)
    if len(next_parts) == 1:
        if operator in ["==", "~=", "!="]:
            errmsg = 'Expressions using the "==", "~=", "!=" operators must have a value component. expression={}'.format(expression)
            raise SemanticError(errmsg)
        marker_group = next_parts[0]
    elif len(next_parts) == 2:
        marker_group, marker_value = next_parts
    else:
        raise SemanticError(errmsg)

    if operator == "==":
        metafilter = MetaFilterEquals(include, marker_group, marker_value)
    elif operator == "~=":
        metafilter = MetaFilterContains(include, marker_group, marker_value)
    elif operator == "!=":
        metafilter = MetaFilterNotEquals(include, marker_group, marker_value)
    else:
        errmsg = "Uh Oh. Did someone partially implement a new operator. expression={}".format(expression)
        raise SemanticError(errmsg)

    return metafilter