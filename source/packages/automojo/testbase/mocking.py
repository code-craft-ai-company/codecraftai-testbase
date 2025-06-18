"""
    .. module:: automojo.testbase.mocking
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing the functionality for mocking objects.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

import enum
import inspect
import types
import weakref


class MockType(enum.StrEnum):
    """
        The type of the mock object.
    """

    Generic = "MockGeneric"
    Class = "MockClass"
    Instance = "MockInstance"
    Property = "MockProperty"
    Function = "MockFunction"
    Method = "MockMethod"


class SideEffect:
    """
        A class to represent a side effect of a mock object.
        
        This class is used to store the side effect of a mock object, which is a callable that is executed when the
        mock object is called.
    """

    def __init__(self, callable: Callable, default_args: Optional[Union[List[Any], Tuple[Any]]] = None,
                 default_kwargs: Dict[str, Any] = None):
        """
            Initializes the SideEffect with the given callable function.
            
            :param func: The callable function to use as the side effect.
        """
        self._callable = callable
        self._default_args = default_args
        self._default_kwargs = default_kwargs
        return
    
    def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the side effect with the given arguments and keyword arguments.
            
            :param args: The positional arguments to pass to the side effect.
            :param kwargs: The keyword arguments to pass to the side effect.
            :return: The return value of the side effect.
        """
        pass_args = []
        pass_kwargs = {}

        if len(args) > 0:
            pass_args = args
        elif self._default_args is not None:
            pass_args = self._default_args

        if len(kwargs) > 0:
            pass_kwargs = kwargs
        elif self._default_kwargs is not None:
            pass_kwargs = self._default_kwargs

        rtnval = self._callable(*pass_args, **pass_kwargs)
        
        return rtnval


class MockContext:
    """
        A :class:`MockClassContext` is a used to store the mock context information and provide the methods that can be used
        to construct deep mock objects through the addition of mock properties and methods.
    """

    @staticmethod
    def determine_mock_type(reference: Any) -> MockType:
        """
            Creates a mock object from a reference object.
            
            :param reference: The reference object to use to determine the MockType.
            :return: A Mock object.
        """
        
        mtype = MockType.Generic

        if isinstance(reference, property):
            mtype = MockType.Property
        elif inspect.isfunction(reference):
            mtype = MockType.Function
        elif inspect.ismethod(reference):
            mtype = MockType.Method
        elif inspect.isclass(reference):
            mtype = MockType.Class
        elif isinstance(reference, object):
            mtype = MockType.Instance

        return mtype


    def __init__(self, mock: "Mock", mock_type: MockType, mock_attributes: Dict[str, Any], *, reference: Optional[Any] = None,
                 return_value: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None, mock_owner: Optional["Mock"] = None,
                 recursive: bool = False, strict_attrs: bool = False):
        """
            Creates an instance of a :class:`MockClassContext` object.

            :param mock: The mock object to use to create the context.
            :param mock_type: The type of the mock object.
            :param mock_attributes: The attributes of the mock object.
            :param reference: The reference object to use to determine the MockType.
            :param return_value: The return value of the mock object.
            :param side_effect: The side effect of the mock object.
            :param mock_owner: The owner of the mock object.
            :param recursive: If True, undefined attributes will return new Mock objects.
            :param strict_attrs: If True, only attributes defined in mock_attributes can be accessed or set.
        """

        self._mock_ref = weakref.ref(mock)
        self._mock_type = mock_type if mock_type is not None else MockType.Generic
        self._mock_attributes = mock_attributes

        self._reference = reference
        self._return_value = return_value
        
        if side_effect is not None and not isinstance(side_effect, SideEffect):
            if callable(side_effect):
                self._side_effect = SideEffect(side_effect)
            else:
                raise TypeError(f"side_effect must be a SideEffect instance or a callable, not {type(side_effect)}.")
        else:
            self._side_effect = side_effect
        self._recursive = recursive
        self._strict_attrs = strict_attrs

        self._mock_owner_ref = None
        if mock_owner is not None:
            self._mock_owner_ref = weakref.ref(mock_owner)

        # Call tracking attributes
        self._call_count = 0
        self._call_args: Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]] = None
        self._call_args_list: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []
        self._mock_calls: List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]] = [] # For tracking calls on children too

        return

    @property
    def reference(self) -> Any:
        """
            Returns the reference object of this mock context.
        """
        return self._reference

    @property
    def return_value(self) -> Any:
        """
            Returns the return value of this mock context.
        """
        return self._return_value
    
    @property
    def side_effect(self) -> SideEffect:
        """
            Returns the side effect of this mock context.
        """
        return self._side_effect

    @property
    def recursive(self) -> bool:
        """
            Returns whether this mock context is set to be recursive.
        """
        return self._recursive
    
    @recursive.setter
    def recursive(self, value: bool):
        """
            Sets the recursive behavior for this mock context.
        """
        if not isinstance(value, bool):
            raise TypeError("recursive must be a boolean value.")
        self._recursive = value

    @property
    def call_count(self) -> int:
        """Returns the number of times the mock was called."""
        return self._call_count

    @property
    def call_args(self) -> Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """Returns the arguments of the last call to the mock as a tuple (args, kwargs)."""
        return self._call_args

    @property
    def call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """Returns a list of all calls made to the mock. Each call is a tuple (args, kwargs)."""
        return self._call_args_list
    
    @property
    def mock_calls(self) -> List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]]:
        """
        Returns a list of all calls made to this mock and its children (attributes that are also mocks).
        Each call is a tuple (name, args, kwargs), where name is '' for the mock itself.
        """
        # For simplicity, this currently only tracks direct calls to this mock.
        # A more complete implementation would involve children reporting calls to their parent.
        # For now, it mirrors call_args_list but with an empty name for direct calls.
        return [('', args, kwargs) for args, kwargs in self._call_args_list]


    def get_attribute(self, name: str) -> Any:

        if not self.has_attribute(name):
            raise AttributeError(f"MockContext has no attribute '{name}'")

        rtnval = self._mock_attributes.get(name)

        return rtnval

    def get_mock(self) -> "Mock":
        """
            Returns the owner of this mock context.
        """
        rtnval = self._mock_ref()
        
        return rtnval
    
    def get_mock_owner(self) -> Any:
        """
            Returns the owner of this mock context.
        """
        rtnval = None
        
        if self._mock_owner_ref is not None:
            rtnval = self._mock_owner_ref()
        
        return rtnval

    def has_attribute(self, name: str) -> bool:
        """
            Checks if this mock context has the given attribute.

            :param name: The name of the attribute to check for.
        
            :return: True if the mock context has the attribute, False otherwise.
        """
        rtnval = True if name in self._mock_attributes else False
        
        return rtnval

    def mock_method(self, name: str, return_value: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None):
        """
            Creates a mock method for the given name.
            
            :param name: The name of the method to create.
            :param return_value: The return value of the mock method.
            :param side_effect: The side effect of the mock method.

            :return: A mock method object.
        """
        this_mock = self.get_mock()

        mock_method = Mock(return_value=return_value, side_effect=side_effect, mtype=MockType.Method,
                           mock_owner=this_mock, recursive=self.recursive, strict_attrs=self._strict_attrs)

        self._mock_attributes[name] = mock_method

        return mock_method
    
    def mock_property(self, name: str, return_value: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None):
        """
            Creates a mock property for the given name.
            
            :param name: The name of the property to create.
        
            :return: A mock property object.
        """
        this_mock = self.get_mock()

        mock_property = Mock(return_value=return_value, side_effect=side_effect, mtype=MockType.Property,
                             mock_owner=this_mock, recursive=self.recursive, strict_attrs=self._strict_attrs)

        self._mock_attributes[name] = mock_property

        return mock_property

    def reset(self):
        """
            Resets the mock context to its initial state.
        """
        self._return_value = None
        self._side_effect = None
        # Reset call tracking
        self._call_count = 0
        self._call_args = None
        self._call_args_list = []
        self._mock_calls = [] # If implementing deeper mock_calls tracking

        return

    def set_attribute(self, name: str, value: Any):
        """
            Sets the value of the given attribute in this mock context.

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.
        """
        self._mock_attributes[name] = value

        return
    
    def set_return_value(self, value: Any):
        """
            Sets the return value of this mock context.
        
            :param value: The value to set as the return value.
        """
        self._return_value = value

        return

    def set_side_effect(self, side_effect: Optional[Union[Callable, SideEffect]]):
        """
            Sets the side effect of this mock context.

            :param side_effect: The callable to set as the side effect.
        """
        if side_effect is not None and not isinstance(side_effect, SideEffect):
            if callable(side_effect):
                self._side_effect = SideEffect(side_effect)
            else:
                raise TypeError(f"side_effect must be a SideEffect instance or a callable, not {type(side_effect)}.")
        else:
            self._side_effect = side_effect

        return

    def _record_call(self, *args, **kwargs):
        """Internal method to record a call to the mock."""
        self._call_count += 1
        self._call_args = (args, kwargs)
        self._call_args_list.append((args, kwargs))
        # If implementing full mock_calls for children, this is where child calls would propagate.
        # For direct calls to this mock, the name is empty.
        # self._mock_calls.append(('', args, kwargs))

    # --- Assertion Helpers ---
    def assert_called(self):
        """Assert that the mock was called at least once."""
        if self._call_count == 0:
            raise AssertionError("Expected mock to have been called.")

    def assert_called_once(self):
        """Assert that the mock was called exactly once."""
        if self._call_count != 1:
            raise AssertionError(f"Expected mock to have been called once. Called {self._call_count} times.")

    def assert_called_with(self, *args, **kwargs):
        """Assert that the last call to the mock was with the specified arguments."""
        if self._call_args is None:
            raise AssertionError("Expected mock to have been called with specific arguments, but it was not called.")
        
        last_args, last_kwargs = self._call_args
        if last_args != args or last_kwargs != kwargs:
            # Helper for formatting expected vs actual calls
            expected_call_str = self._format_call_args(args, kwargs)
            actual_call_str = self._format_call_args(last_args, last_kwargs)
            raise AssertionError(f"Expected last call with {expected_call_str}, but was called with {actual_call_str}.")

    def assert_called_once_with(self, *args, **kwargs):
        """Assert that the mock was called exactly once and with the specified arguments."""
        self.assert_called_once()
        self.assert_called_with(*args, **kwargs)

    def assert_any_call(self, *args, **kwargs):
        """Assert that the mock was called at least once with the specified arguments."""
        if not any(c_args == args and c_kwargs == kwargs for c_args, c_kwargs in self._call_args_list):
            expected_call_str = self._format_call_args(args, kwargs)
            actual_calls_str = "\n".join([self._format_call_args(ca, ck) for ca, ck in self._call_args_list])
            if not actual_calls_str:
                actual_calls_str = " (no calls made)"
            raise AssertionError(f"Expected at least one call with {expected_call_str}. Actual calls:\n{actual_calls_str}")

    def assert_has_calls(self, calls: List[Tuple[Tuple[Any, ...], Dict[str, Any]]], any_order: bool = False):
        """
        Assert that the mock was called with a specific sequence of calls.
        Each call in `calls` should be a tuple (args, kwargs).
        """
        if not isinstance(calls, list):
            raise TypeError("Expected 'calls' to be a list of call arguments.")
        if not all(isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], tuple) and isinstance(c[1], dict) for c in calls):
            raise ValueError("Each item in 'calls' must be a tuple of (args_tuple, kwargs_dict).")

        actual_calls = self._call_args_list

        if any_order:
            # Check if all expected calls are present in actual_calls, regardless of order and count
            # This is a simplified check; unittest.mock's version is more sophisticated
            for expected_call in calls:
                if expected_call not in actual_calls:
                    expected_call_str = self._format_call_args(*expected_call)
                    raise AssertionError(f"Expected call {expected_call_str} not found in actual calls.")
        else:
            # Check for an exact sub-sequence
            if len(calls) > len(actual_calls):
                raise AssertionError(f"Expected {len(calls)} calls, but only {len(actual_calls)} were made.")
            
            # Naive subsequence check
            found_subsequence = False
            for i in range(len(actual_calls) - len(calls) + 1):
                if actual_calls[i:i+len(calls)] == calls:
                    found_subsequence = True
                    break
            if not found_subsequence:
                expected_calls_str = "\n".join([self._format_call_args(*c) for c in calls])
                actual_calls_str = "\n".join([self._format_call_args(*c) for c in actual_calls])
                raise AssertionError(f"Expected call sequence not found.\nExpected:\n{expected_calls_str}\nActual:\n{actual_calls_str}")

    def _format_call_args(self, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
        """Helper to format call arguments for assertion messages."""
        arg_str = ", ".join(map(repr, args))
        kwarg_str = ", ".join(f"{k}={v!r}" for k, v in sorted(kwargs.items()))
        if arg_str and kwarg_str:
            return f"({arg_str}, {kwarg_str})"
        elif kwarg_str:
            return f"({kwarg_str})"
        return f"({arg_str})"

        return


class Mock:

    def __init__(self, *, mock_attributes: Optional[Dict[str, Any]] = None, return_value: Optional[Any] = None,
                 reference: Optional[Any] = None, mtype: Optional[MockType] = None, mock_owner: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None,
                 recursive: bool = False, strict_attrs: bool = False):
        """
            Creates a mock object with the given attributes and context.

            :param mock_attributes: The attributes of the mock object.
            :param return_value: The return value of the mock object.
            :param side_effect: The side effect of the mock object.
            :param reference: The reference object to use to determine the MockType.
            :param mtype: The type of the mock object.
            :param mock_owner: The owner of the mock object.
            :param recursive: If True, undefined attributes will return new Mock objects.
            :param strict_attrs: If True, only attributes defined in mock_attributes can be accessed or set.

            :raises TypeError: If the mock_attributes is not a dictionary.
            :raises ValueError: If the reference is not a callable or a class.
        """
        if mock_attributes is None:
            mock_attributes = {}

        if mtype is None:
            mtype = MockType.Generic
            if reference is not None:
                mtype = MockContext.determine_mock_type(reference)

        self._mock_context = MockContext(self, mtype, mock_attributes, reference=reference, return_value=return_value,
                                         side_effect=side_effect, mock_owner=mock_owner, recursive=recursive,
                                         strict_attrs=strict_attrs)

        return


    def mock_context(self) -> MockContext:
        """
            Returns the mock context for this mock object.
        """
        return self._mock_context

    # --- Expose call tracking properties from context ---
    @property
    def call_count(self) -> int:
        return self._mock_context.call_count

    @property
    def call_args(self) -> Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        return self._mock_context.call_args

    @property
    def call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        return self._mock_context.call_args_list
    
    @property
    def mock_calls(self) -> List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]]:
        return self._mock_context.mock_calls

    def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the mock object with the given arguments and keyword arguments.

            :param args: The positional arguments to pass to the mock object.
            :param kwargs: The keyword arguments to pass to the mock object.

            :return: The return value of the mock object, or the side effect if it is set.
        """
        self._mock_context._record_call(*args, **kwargs)
        rtnval = self._mock_context.return_value

        if self._mock_context.side_effect is not None:
            rtnval = self._mock_context.side_effect(*args, **kwargs)

        return rtnval


    def __repr__(self):
        """
            Returns a string representation of the mock object.
        """
        rtnval = f"Mock(return_value={self._mock_context.return_value}, side_effect={self._mock_context.side_effect})"
        
        return rtnval


    def __str__(self):
        """
            Returns a string representation of the mock object.
        """
        rtnval = f"Mock with return_value={self._mock_context.return_value} and side_effect={self._mock_context.side_effect}"
        
        return rtnval


    def __getattr__(self, name: str):
        """
            Gets the attribute of the mock object with the given name. If the attribute does not exist, it raises an
            AttributeError. If the attribute starts with an underscore, it raises an AttributeError.

            :param name: The name of the attribute to get.
            
            :return: A new Mock object if the attribute does not exist, otherwise the attribute value.

            :raises AttributeError: If the attribute does not exist or starts with an underscore.
        """
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Prioritize assertion methods from context
        if hasattr(self._mock_context, name) and callable(getattr(self._mock_context, name)) and name.startswith("assert_"):
            return getattr(self._mock_context, name)

        try:
            # Attempt to get an explicitly set attribute
            return self._mock_context.get_attribute(name)
        except AttributeError:
            # If strict_attrs is True, and attribute is not found, raise error even if recursive
            if self._mock_context._strict_attrs:
                raise AttributeError(
                    f"'{self._mock_context._mock_type}' object has no attribute '{name}' (strict_attrs is True)"
                )

            # If the attribute doesn't exist and the mock is recursive,
            # create a new mock, store it, and return it.
            if self._mock_context.recursive:
                new_mock = Mock(mock_owner=self, recursive=self._mock_context.recursive,
                                strict_attrs=self._mock_context._strict_attrs) # Propagate strict_attrs
                self._mock_context.set_attribute(name, new_mock)
                return new_mock
            # If not recursive, re-raise the AttributeError
            raise



    def __setattr__(self, name: str, value: Any):
        """
            Sets the attribute of the mock object with the given name to the given value. If the attribute starts with
            an underscore, it allows setting the attribute. Otherwise, it raises an AttributeError.

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.

            :raises AttributeError: If the attribute does not start with an underscore.
        """
        if name.startswith('_'):
            super().__setattr__(name, value)
        else:
            # If strict_attrs is True, only allow setting attributes that are already defined
            # or are special mock config attributes.
            if self._mock_context._strict_attrs and \
               name not in ["return_value", "side_effect", "recursive"] and \
               not self._mock_context.has_attribute(name):
                raise AttributeError(f"Cannot set new attribute '{name}' on mock with strict_attrs=True unless it's a pre-defined attribute or mock config.")

            # Handle special mock configuration attributes
            if name == "return_value":
                self._mock_context.set_return_value(value)
            elif name == "side_effect":
                self._mock_context.set_side_effect(value)
            elif name == "recursive":
                self._mock_context.recursive = value
            else:
                # For other attributes, store them in the context's _mock_attributes
                self._mock_context.set_attribute(name, value)

        return


    def __eq__(self, other: Any):
        """
            Checks if this mock object is equal to another object. It compares the return value and side effect of both
            mock objects.

            :param other: The other object to compare with.

            :return: True if the mock objects are equal, False otherwise.
        """
        rtnval = False

        if self is other:
            return True
        if not isinstance(other, Mock):
            return NotImplemented # Allows other object to attempt comparison

        # A more robust __eq__ might consider more aspects, or simply be identity-based
        # if configuration comparison is too complex or not desired.
        # For now, comparing key configuration aspects.
        rtnval = (self._mock_context.return_value == other._mock_context.return_value and
                  self._mock_context.side_effect == other._mock_context.side_effect and # Compares the side_effect objects themselves
                  self._mock_context.recursive == other._mock_context.recursive and
                  self._mock_context._strict_attrs == other._mock_context._strict_attrs and
                  self._mock_context._mock_type == other._mock_context._mock_type and
                  self._mock_context._mock_attributes == other._mock_context._mock_attributes) # Potentially deep
        
        return rtnval


    def __ne__(self, other):
        """
            Checks if this mock object is not equal to another object. It compares the return value and side effect of
            both mock objects.
            
            :param other: The other object to compare with.
            
            :return: True if the mock objects are not equal, False otherwise.
        """
        rtnval = not self.__eq__(other)
        
        return rtnval


    def __hash__(self):
        """
            Returns the hash of the mock object.
            
            :return: The hash of the mock object.
        """
        # Hashing can be tricky with mutable state.
        # A common approach for mocks is to use id() or make them unhashable if their state changes __eq__.
        rtnval = id(self) # Or make it more complex based on immutable parts of context
        
        return rtnval


    def __bool__(self):
        """ 
            Checks if the mock object is truthy. It checks if the return value or side effect of the mock object is
            truthy. If the return value or side effect is not None and evaluates to True, it returns True, otherwise
            it returns False.

            :return: True if the mock object is truthy, False otherwise.
        """
        # Mocks are generally considered truthy by default, similar to unittest.mock.Mock.
        # If a specific boolean value is desired, it should be set via return_value.
        if self._mock_context.return_value is not None:
            rtnval = bool(self._mock_context.return_value)
        else:
            rtnval = True # Default truthiness for a Mock object itself
        return rtnval


    def __len__(self):
        """
            Returns the length of the mock object.  It checks if the return value or side effect of the mock object is
            iterable. If the return value or side effect is not None and has a length, it returns the length, otherwise
            it raises a TypeError.
            
            :return: The length of the mock object.

            :raises TypeError: If the return value or side effect is None or does not have a length.
        """
        if self._mock_context.return_value is not None:
            try:
                rtnval = len(self._mock_context.return_value)
            except TypeError:
                raise TypeError(
                    f"'{self._mock_context._mock_type}' object's return_value of type "
                    f"'{type(self._mock_context.return_value).__name__}' has no len()"
                )
        else:
            raise TypeError(
                f"'{self._mock_context._mock_type}' object has no len() because return_value is not set")
        return rtnval


    def __iter__(self):
        """
            Returns an iterator for the mock object.  It checks if the return value or side effect of the mock object is
            iterable. If the return value or side effect is not None and is iterable, it returns an iterator, otherwise
            it raises a TypeError.

            :return: An iterator for the mock object.

            :raises TypeError: If the return value or side effect is None or not iterable.
        """
        if self._mock_context.return_value is not None:
            try:
                # This will yield from the iterator of return_value
                return iter(self._mock_context.return_value)
            except TypeError:
                raise TypeError(
                    f"'{self._mock_context._mock_type}' object's return_value of type "
                    f"'{type(self._mock_context.return_value).__name__}' is not iterable")
        else:
            raise TypeError(
                f"'{self._mock_context._mock_type}' object is not iterable because return_value is not set")

    def __contains__(self, item):
        """
            Checks if the mock object contains the given item. It checks if the return value or side effect of the
            mock object is iterable. If the return value or side effect is not None and contains the item, it returns
            True, otherwise it returns False.

            :param item: The item to check for.

            :return: True if the mock object contains the item, False otherwise.
        """
        rtnval = False
        if self._mock_context.return_value is not None:
            try:
                rtnval = item in self._mock_context.return_value
            except TypeError:
                # 'in' operator on a non-container type raises TypeError.
                raise TypeError(
                    f"'in <{type(item).__name__}>' requires container support from "
                    f"'{self._mock_context._mock_type}' object's return_value of type "
                    f"'{type(self._mock_context.return_value).__name__}'")
        else:
            # If return_value is None, 'item in None' would raise TypeError.
            raise TypeError(
                f"'in <{type(item).__name__}>' requires container support, but "
                f"'{self._mock_context._mock_type}' object's return_value is not set")
        return rtnval


class PatchType(enum.StrEnum):
    """
        The type of the patch.
    """

    Module = "Module"
    Class = "Class"
    Instance = "Instance"


class Patch:
    """
        The :class:`Patch` class provides a way to manage the context associated with patching the functionality of a
        module, class, or instance with a mock object. 
    """

    def __init__(self, owner: Any, target_name: str, patch_type: PatchType, recursive: bool = False,
                 strict_attrs: bool = False):

        if isinstance(owner, type):
            if not issubclass(owner, object):
                raise TypeError(f"owner must be a class, not {type(owner)}")
            elif patch_type != PatchType.Class:
                raise TypeError(f"If 'owner' is a 'class' patch_type must be {PatchType.Class}, not {patch_type}")
        elif isinstance(owner, types.ModuleType):
            if patch_type != PatchType.Module:
                raise TypeError(f"If 'owner' is a 'module' patch_type must be {PatchType.Module}, not {patch_type}")
        elif isinstance(owner, object):
            if patch_type != PatchType.Instance:
                raise TypeError(f"If 'owner' is an 'instance' patch_type must be {PatchType.Instance}, not {patch_type}")

        self._owner = owner
        self._target_name = target_name
        self._patch_type = patch_type
        self._mock = None
        self._recursive = recursive
        self._strict_attrs = strict_attrs

        return


    @property
    def owner(self) -> Any:
        """
            Returns the owner of the patch.
        """
        return self._owner
    

    @property
    def patch_type(self) -> PatchType:
        """
            Returns the type of the patch.
        """
        return self._patch_type


    @property
    def target_name(self) -> str:
        """
            Returns the name of the target to patch.
        """
        return self._target_name

    
    def __enter__(self) -> Mock:
        """
            Enters the patch scope.
        """
        mock = self.activate()

        return mock


    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType) -> bool:
        """
            Exits the patch scope.
            
            :param exc_type: The type of the exception.
            :param exc_val: The value of the exception.
            :param exc_tb: The traceback of the exception.

            :return: False to indicate that the exception should be not be suppressed (raised).
        """

        self.deactivate()

        return False
    

    def activate(self) -> Mock:
        """
            Activates the patch scope.
        """

        mock = self.mock()

        target = getattr(self._owner, self._target_name)
        if isinstance(target, Mock) and hasattr(target, '_mock_context') and isinstance(target._mock_context, MockContext):
            raise ValueError(f"Cannot patch '{self._target_name}' because it is already a Mock object from this framework.")

        setattr(self._owner, self._target_name, mock)

        return self._mock
    

    def deactivate(self):
        """
            Deactivates the patch scope.
        """

        if self._mock is not None:
            target = self._mock.mock_context().reference
            # Restore the original attribute, even if it was None
            setattr(self._owner, self._target_name, target)

        return


    def mock(self) -> Mock:
        """
            Returns the mock object associated with this patch. If the does not have an associated mock object yet,
            it will be created.
        """

        if self._mock is None:

            target = getattr(self._owner, self._target_name)
            # Let Mock determine its type from the reference.
            # The reference (original target) will be stored in the Mock's MockContext.
            self._mock = Mock(reference=target, recursive=self._recursive, strict_attrs=self._strict_attrs)

        return self._mock



def create_module_patch(module: types.ModuleType, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch that will patch the given module by replacing the target attribute with a mock object

        :param module: The module to patch.
        :param target_name: The name of the attributed to patch.

        :return: A :class:`PatchScope` object that can be used to trigger
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attribute checking.
                 the activation and deactivation of the patch.
    """
    if not isinstance(module, types.ModuleType):
        raise TypeError(f"module must be a module, not {type(module)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(module, target_name, PatchType.Module, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope


def create_class_patch(cls: Type, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch that will patch the given class by replacing the target attribute with a mock object.

        :param cls: The class to patch.
        :param target_name: The name of the attributed to patch.
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attribute checking.

        :return: A :class:`Patch` object that can be used to trigger
                 the activation and deactivation of the patch.
    """
    if not isinstance(cls, type):
        raise TypeError(f"cls must be a class, not {type(cls)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(cls, target_name, PatchType.Class, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope


def create_instance_patch(instance: object, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch that will patch the given instance by replacing the target attribute with a mock object.

        :param instance: The instance to patch.
        :param target_name: The name of the attributed to patch.
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attribute checking.

        :return: A :class:`Patch` object that can be used to trigger
                 the activation and deactivation of the patch.
    """
    if not isinstance(instance, object):
        raise TypeError(f"instance must be an object, not {type(instance)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(instance, target_name, PatchType.Instance, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope
