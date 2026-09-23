"""
    .. module:: ccai.testbase.mocking
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module providing the functionality for mocking objects.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Callable, Coroutine, Dict, List, Optional, Tuple, Type, Union, get_type_hints

import asyncio
import enum
import inspect
import types
import weakref


class SpecViolationError(Exception):
    """
        Exception raised when a mock operation violates its specification.
        
        This exception is raised when:
        - An attribute is accessed that doesn't exist in the spec class
        - A method is called with arguments that don't match the spec's signature
        - An attribute is set that doesn't exist in the spec class
        
        Example::
        
            class MySpec:
                def method(self, x: int) -> str:
                    pass
            
            mock = create_spec_mock(MySpec)
            mock.nonexistent  # Raises SpecViolationError
    """
    pass


class MockType(str, enum.Enum):
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
        
        This class wraps a callable that is executed when the associated mock object is called.
        It supports default arguments that are used when call-time arguments are not provided.

        Example Usage::

            # Basic side effect
            def my_side_effect(x, y):
                return x + y
            
            side_effect = SideEffect(my_side_effect)
            result = side_effect(1, 2)  # Returns 3

            # Side effect with default arguments
            side_effect = SideEffect(my_side_effect, default_args=(10, 20))
            result = side_effect()  # Returns 30 (uses defaults)
            result = side_effect(5, 5)  # Returns 10 (overrides defaults)

            # Side effect with default keyword arguments
            def greet(name="World", greeting="Hello"):
                return f"{greeting}, {name}!"
            
            side_effect = SideEffect(greet, default_kwargs={"name": "User"})
            result = side_effect()  # Returns "Hello, User!"
    """
    # Changed default from None to ... for default_args and default_kwargs
    def __init__(self, callable: Callable, default_args: Optional[Union[List[Any], Tuple[Any]]] = ...,
                 default_kwargs: Dict[str, Any] = ...):
        """
            Initializes the SideEffect with the given callable function.
            
            :param callable: The callable function to use as the side effect. This function will be
                executed when the SideEffect instance is called.
            :param default_args: Optional default positional arguments to pass to the callable when
                no positional arguments are provided at call time. Can be a list or tuple.
                Defaults to None (no default args).
            :param default_kwargs: Optional default keyword arguments to pass to the callable when
                no keyword arguments are provided at call time. Must be a dictionary.
                Defaults to None (no default kwargs).

            Example::

                def compute(a, b, multiplier=1):
                    return (a + b) * multiplier
                
                # With default positional args
                se = SideEffect(compute, default_args=(5, 10))
                se()  # Returns 15
                
                # With default keyword args
                se = SideEffect(compute, default_kwargs={"multiplier": 2})
                se(3, 4)  # Returns 14
        """
        self._callable = callable
        self._default_args = default_args
        # Ensure default_kwargs is a dict if provided, or None if not (or explicitly None)
        if default_kwargs is ...:
            self._default_kwargs = None
        else:
            self._default_kwargs = default_kwargs
        return
    
    def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the side effect with the given arguments and keyword arguments.
            
            When called, this method executes the wrapped callable. If no positional arguments
            are provided at call time and default_args was configured, the default_args are used.
            Similarly, if no keyword arguments are provided and default_kwargs was configured,
            the default_kwargs are used.
            
            :param args: The positional arguments to pass to the side effect. If empty and
                default_args is configured, default_args will be used instead.
            :param kwargs: The keyword arguments to pass to the side effect. If empty and
                default_kwargs is configured, default_kwargs will be used instead.
            
            :return: The return value of the wrapped callable.

            :raises Exception: Any exception raised by the wrapped callable will propagate.

            Example::

                def divide(a, b):
                    if b == 0:
                        raise ValueError("Cannot divide by zero")
                    return a / b
                
                side_effect = SideEffect(divide, default_args=(10, 2))
                
                # Using default args
                result = side_effect()  # Returns 5.0
                
                # Overriding with call-time args
                result = side_effect(20, 4)  # Returns 5.0
                
                # Exception propagation
                result = side_effect(10, 0)  # Raises ValueError
        """
        pass_args = []
        pass_kwargs = {}

        if len(args) > 0:
            pass_args = args
        elif self._default_args is not ... and self._default_args is not None: # Check against ... and None
            pass_args = self._default_args

        if len(kwargs) > 0:
            pass_kwargs = kwargs
        elif self._default_kwargs is not ... and self._default_kwargs is not None: # Check against ... and None
            pass_kwargs = self._default_kwargs

        rtnval = self._callable(*pass_args, **pass_kwargs)
        
        return rtnval


class AsyncSideEffect:
    """
        A class to represent an async side effect of a mock object.
        
        This class wraps an async callable (coroutine function) that is executed when 
        the associated async mock object is awaited. It supports default arguments that 
        are used when call-time arguments are not provided.

        Example Usage::

            # Basic async side effect
            async def my_async_effect(x, y):
                await asyncio.sleep(0.1)
                return x + y
            
            side_effect = AsyncSideEffect(my_async_effect)
            result = await side_effect(1, 2)  # Returns 3

            # Async side effect with default arguments
            side_effect = AsyncSideEffect(my_async_effect, default_args=(10, 20))
            result = await side_effect()  # Returns 30 (uses defaults)
            result = await side_effect(5, 5)  # Returns 10 (overrides defaults)

            # Async side effect with default keyword arguments
            async def greet(name="World", greeting="Hello"):
                return f"{greeting}, {name}!"
            
            side_effect = AsyncSideEffect(greet, default_kwargs={"name": "User"})
            result = await side_effect()  # Returns "Hello, User!"
    """

    def __init__(self, callable: Callable[..., Coroutine], default_args: Optional[Union[List[Any], Tuple[Any]]] = ...,
                 default_kwargs: Dict[str, Any] = ...):
        """
            Initializes the AsyncSideEffect with the given async callable function.
            
            :param callable: The async callable function (coroutine function) to use as the side effect.
                This function will be executed when the AsyncSideEffect instance is awaited.
            :param default_args: Optional default positional arguments to pass to the callable when
                no positional arguments are provided at call time. Can be a list or tuple.
                Defaults to None (no default args).
            :param default_kwargs: Optional default keyword arguments to pass to the callable when
                no keyword arguments are provided at call time. Must be a dictionary.
                Defaults to None (no default kwargs).

            :raises TypeError: If the callable is not a coroutine function.

            Example::

                async def compute(a, b, multiplier=1):
                    return (a + b) * multiplier
                
                # With default positional args
                se = AsyncSideEffect(compute, default_args=(5, 10))
                await se()  # Returns 15
                
                # With default keyword args
                se = AsyncSideEffect(compute, default_kwargs={"multiplier": 2})
                await se(3, 4)  # Returns 14
        """
        if not asyncio.iscoroutinefunction(callable):
            raise TypeError(f"AsyncSideEffect requires a coroutine function, not {type(callable).__name__}")
        
        self._callable = callable
        self._default_args = default_args
        # Ensure default_kwargs is a dict if provided, or None if not (or explicitly None)
        if default_kwargs is ...:
            self._default_kwargs = None
        else:
            self._default_kwargs = default_kwargs
        return
    
    async def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the async side effect with the given arguments and keyword arguments.
            
            When called, this method executes the wrapped async callable. If no positional arguments
            are provided at call time and default_args was configured, the default_args are used.
            Similarly, if no keyword arguments are provided and default_kwargs was configured,
            the default_kwargs are used.
            
            :param args: The positional arguments to pass to the side effect. If empty and
                default_args is configured, default_args will be used instead.
            :param kwargs: The keyword arguments to pass to the side effect. If empty and
                default_kwargs is configured, default_kwargs will be used instead.
            
            :return: The return value of the wrapped async callable.

            :raises Exception: Any exception raised by the wrapped callable will propagate.

            Example::

                async def divide(a, b):
                    if b == 0:
                        raise ValueError("Cannot divide by zero")
                    return a / b
                
                side_effect = AsyncSideEffect(divide, default_args=(10, 2))
                
                # Using default args
                result = await side_effect()  # Returns 5.0
                
                # Overriding with call-time args
                result = await side_effect(20, 4)  # Returns 5.0
                
                # Exception propagation
                result = await side_effect(10, 0)  # Raises ValueError
        """
        pass_args = []
        pass_kwargs = {}

        if len(args) > 0:
            pass_args = args
        elif self._default_args is not ... and self._default_args is not None:
            pass_args = self._default_args

        if len(kwargs) > 0:
            pass_kwargs = kwargs
        elif self._default_kwargs is not ... and self._default_kwargs is not None:
            pass_kwargs = self._default_kwargs

        rtnval = await self._callable(*pass_args, **pass_kwargs)
        
        return rtnval


class MockContext:
    """
        A :class:`MockContext` stores all state and configuration for a mock object and provides
        methods for constructing deep mock objects through the addition of mock properties and methods.

        The MockContext is responsible for:
        - Storing mock configuration (return_value, side_effect, recursive, strict_attrs)
        - Tracking all calls made to the mock (call_count, call_args, call_args_list)
        - Managing mock attributes and child mocks
        - Providing assertion methods for verifying mock interactions

        Example Usage::

            from ccai.testbase.mocking import Mock

            # Create a mock and access its context
            mock = Mock()
            ctx = mock.mock_context()

            # Configure the mock through its context
            ctx.configure(return_value=42)
            
            # Add mock methods and properties
            ctx.mock_method('calculate', return_value=100)
            ctx.mock_property('name', return_value='test')
            
            # Call the mock and verify
            result = mock()  # Returns 42
            ctx.assert_called_once()
            
            # Access child mocks
            result = mock.calculate()  # Returns 100
            name = mock.name  # Returns 'test'
    """

    @staticmethod
    def determine_mock_type(reference: Any) -> MockType:
        """
            Determines the appropriate MockType from a reference object.
            
            This static method inspects the provided reference object and returns the
            corresponding MockType enumeration value based on the object's type.
            
            :param reference: The reference object to inspect. Can be any Python object
                including None, properties, functions, methods, classes, or instances.
            
            :return: A MockType enumeration value:
                - MockType.Generic: If reference is None
                - MockType.Property: If reference is a property object
                - MockType.Function: If reference is a function
                - MockType.Method: If reference is a bound method
                - MockType.Class: If reference is a class
                - MockType.Instance: If reference is an object instance

            Example::

                from ccai.testbase.mocking import MockContext, MockType

                class MyClass:
                    @property
                    def prop(self):
                        return "value"
                    
                    def method(self):
                        pass

                def my_function():
                    pass

                # Determine types
                MockContext.determine_mock_type(None)  # Returns MockType.Generic
                MockContext.determine_mock_type(my_function)  # Returns MockType.Function
                MockContext.determine_mock_type(MyClass)  # Returns MockType.Class
                MockContext.determine_mock_type(MyClass())  # Returns MockType.Instance
        """
        
        # ============================================================================
        # MOCK TYPE DETERMINATION ALGORITHM
        # ============================================================================
        # This algorithm determines the appropriate MockType for a given reference
        # object. The order of checks is critical because Python's type hierarchy
        # means some checks must come before others:
        #
        # 1. None check first - handles the case where no reference is provided
        # 2. Property check - must come before object check since properties are objects
        # 3. Function check - uses inspect.isfunction() to detect standalone functions
        # 4. Method check - uses inspect.ismethod() to detect bound methods
        # 5. Class check - uses inspect.isclass() to detect class types
        # 6. Instance check - catches all remaining objects (must be last since
        #    everything in Python is an object)
        #
        # The order matters because:
        # - Properties, functions, methods, and classes are all instances of 'object'
        # - If we checked isinstance(reference, object) first, it would match everything
        # - More specific checks must precede more general checks
        # ============================================================================
        
        mtype = MockType.Generic

        # Check 1: None reference - use Generic type as a catch-all
        if reference is None:
            mtype = MockType.Generic
        # Check 2: Property descriptor - detected via isinstance since property is a type
        elif isinstance(reference, property):
            mtype = MockType.Property
        # Check 3: Standalone function - uses inspect module for accurate detection
        # Note: This catches functions defined with 'def' at module level or nested
        elif inspect.isfunction(reference):
            mtype = MockType.Function
        # Check 4: Bound method - a function bound to an instance
        # Note: This catches methods accessed via an instance (e.g., obj.method)
        elif inspect.ismethod(reference):
            mtype = MockType.Method
        # Check 5: Class type - any class definition (not an instance)
        # Note: This catches classes themselves, not instances of classes
        elif inspect.isclass(reference):
            mtype = MockType.Class
        # Check 6: Object instance - catch-all for any remaining objects
        # Note: This must be last since all Python objects pass isinstance(x, object)
        elif isinstance(reference, object):
            mtype = MockType.Instance

        return mtype


    def __init__(self, mock: "Mock", mock_type: MockType, mock_attributes: Dict[str, Any], *, reference: Optional[Any] = None,
                 return_value: Optional[Any] = ..., side_effect: Optional[Union[Callable, SideEffect]] = ..., mock_owner: Optional["Mock"] = ...,
                 recursive: bool = False, strict_attrs: bool = False):
        """
            Creates an instance of a :class:`MockContext` object.

            :param mock: The Mock object that this context belongs to. A weak reference is stored
                to avoid circular reference memory leaks.
            :param mock_type: The type of the mock object (from MockType enumeration).
            :param mock_attributes: A dictionary of pre-defined attributes for the mock object.
            :param reference: Optional reference to the original object being mocked. Used for
                type determination and restoration during patch deactivation.
            :param return_value: The value to return when the mock is called. Defaults to None.
            :param side_effect: A callable or SideEffect instance to execute when the mock is called.
                If a callable is provided, it will be wrapped in a SideEffect instance.
                Defaults to None.
            :param mock_owner: The parent Mock object if this is a child mock. A weak reference
                is stored to avoid circular reference memory leaks.
            :param recursive: If True, accessing undefined attributes will automatically create
                and return new Mock objects. Defaults to False.
            :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
                Attempting to access or set undefined attributes will raise AttributeError.
                Defaults to False.

            :raises TypeError: If side_effect is provided but is neither a SideEffect instance
                nor a callable. Also raised if recursive or strict_attrs are not boolean values.

            Example::

                from ccai.testbase.mocking import Mock, MockContext, MockType

                # MockContext is typically created internally by Mock
                mock = Mock(return_value=42, recursive=True)
                ctx = mock.mock_context()
                
                # Access context properties
                print(ctx.return_value)  # 42
                print(ctx.recursive)  # True
                print(ctx.call_count)  # 0
        """

        self._mock_ref = weakref.ref(mock)
        self._mock_type = mock_type if mock_type is not None else MockType.Generic
        self._mock_attributes = mock_attributes
        
        self._reference = reference if reference is not ... else None
        self._return_value = return_value if return_value is not ... else None
        
        if side_effect is not ...:
            if side_effect is not None and not isinstance(side_effect, SideEffect):
                if callable(side_effect):
                    self._side_effect = SideEffect(side_effect)
                else:
                    raise TypeError(f"side_effect must be a SideEffect instance or a callable, not {type(side_effect)}.")
            else: # side_effect is None or already a SideEffect instance
                self._side_effect = side_effect
        else:
            self._side_effect = None # Default if not provided

        # Validate recursive is a boolean
        if not isinstance(recursive, bool):
            raise TypeError(f"'recursive' must be a boolean value, not {type(recursive).__name__}.")
        self._recursive = recursive
        
        # Validate strict_attrs is a boolean
        if not isinstance(strict_attrs, bool):
            raise TypeError(f"'strict_attrs' must be a boolean value, not {type(strict_attrs).__name__}.")
        self._strict_attrs = strict_attrs

        self._mock_owner_ref = None
        if mock_owner is not ... and mock_owner is not None:
            self._mock_owner_ref = weakref.ref(mock_owner)

        # Call tracking attributes
        self._call_count = 0
        self._call_args: Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]] = None
        self._call_args_list: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []
        self._mock_calls: List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]] = [] # For tracking calls on children too

        return

    @property
    def call_args(self) -> Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns the arguments of the last call to the mock.
            
            :return: A tuple of (args, kwargs) from the most recent call, where args is a tuple
                of positional arguments and kwargs is a dictionary of keyword arguments.
                Returns None if the mock has never been called.

            Example::

                mock = Mock()
                mock(1, 2, key="value")
                
                ctx = mock.mock_context()
                args, kwargs = ctx.call_args
                # args == (1, 2)
                # kwargs == {"key": "value"}
        """
        return self._call_args

    @property
    def call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all calls made to the mock.
            
            :return: A list of tuples, where each tuple is (args, kwargs) representing one call.
                The list is ordered chronologically (first call first).

            Example::

                mock = Mock()
                mock(1)
                mock(2, key="a")
                mock(3, 4)
                
                ctx = mock.mock_context()
                # ctx.call_args_list == [
                #     ((1,), {}),
                #     ((2,), {"key": "a"}),
                #     ((3, 4), {})
                # ]
        """
        return self._call_args_list

    @property
    def reference(self) -> Any:
        """
            Returns the reference object of this mock context.
            
            The reference is the original object that was being mocked, if any.
            This is used during patch deactivation to restore the original attribute.
            
            :return: The original reference object, or None if no reference was provided.
        """
        return self._reference

    @property
    def call_count(self) -> int:
        """
            Returns the number of times the mock was called.
            
            :return: An integer representing the total number of calls made to the mock.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                print(ctx.call_count)  # 0
                mock()
                print(ctx.call_count)  # 1
                mock()
                mock()
                print(ctx.call_count)  # 3
        """
        return self._call_count

    @property
    def mock_type(self) -> MockType:
        """
            Returns the type of this mock context.
            
            :return: A MockType enumeration value indicating what kind of object this mock represents
                (Generic, Class, Instance, Property, Function, or Method).
        """
        return self._mock_type
    
    @property
    def mock_attributes(self) -> Dict[str, Any]:
        """
            Returns the attributes dictionary of this mock context.
            
            :return: A dictionary mapping attribute names to their values. This includes
                both explicitly set attributes and child mocks created through recursive access.
        """
        return self._mock_attributes

    @property
    def return_value(self) -> Any:
        """
            Returns the configured return value of this mock context.
            
            :return: The value that will be returned when the mock is called, or None if not configured.
        """
        return self._return_value

    @property
    def recursive(self) -> bool:
        """
            Returns whether this mock context is set to be recursive.
            
            When recursive is True, accessing undefined attributes on the mock will automatically
            create and return new Mock objects instead of raising AttributeError.
            
            :return: True if recursive mode is enabled, False otherwise.
        """
        return self._recursive
    
    @recursive.setter
    def recursive(self, value: bool):
        """
            Sets the recursive behavior for this mock context.
            
            :param value: Boolean indicating whether to enable recursive mode.
            
            :raises TypeError: If value is not a boolean.
        """
        if not isinstance(value, bool):
            raise TypeError("recursive must be a boolean value.")
        self._recursive = value

    @property
    def side_effect(self) -> SideEffect:
        """
            Returns the side effect of this mock context.
            
            :return: The SideEffect instance that will be executed when the mock is called,
                or None if no side effect is configured.
        """
        return self._side_effect

    @property
    def mock_calls(self) -> List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all calls made to this mock and its children.
            
            Each call is represented as a tuple (name, args, kwargs), where name is an empty
            string for direct calls to this mock, or the attribute path for calls to child mocks.
            
            :return: A list of call tuples in chronological order.

            Example::

                mock = Mock(recursive=True)
                mock(1)
                mock.child(2)
                
                ctx = mock.mock_context()
                # ctx.mock_calls includes calls to mock and mock.child
        """
        # For simplicity, this currently only tracks direct calls to this mock.
        # A more complete implementation would involve children reporting calls to their parent.
        # For now, it mirrors call_args_list but with an empty name for direct calls.
        calls = [('', args, kwargs) for args, kwargs in self._call_args_list]
        return calls


    def assert_any_call(self, *args, **kwargs):
        """
            Assert that the mock was called at least once with the specified arguments.
            
            This method checks all recorded calls to find at least one that matches the
            provided arguments exactly.
            
            :param args: The expected positional arguments.
            :param kwargs: The expected keyword arguments.
            
            :raises AssertionError: If no call matches the specified arguments. The error
                message includes the expected call and all actual calls made with detailed
                formatting for readability.

            Example::

                mock = Mock()
                mock(1, 2)
                mock(3, 4)
                mock(5, key="value")
                
                ctx = mock.mock_context()
                ctx.assert_any_call(3, 4)  # Passes
                ctx.assert_any_call(5, key="value")  # Passes
                ctx.assert_any_call(1, 2, 3)  # Raises AssertionError
        """
        if not any(c_args == args and c_kwargs == kwargs for c_args, c_kwargs in self._call_args_list):
            expected_call_str = self._format_call_args(args, kwargs)
            
            # Build comprehensive error message
            error_parts = [
                f"Expected at least one call with {expected_call_str}",
            ]
            
            if self._call_args_list:
                error_parts.append(f"\nActual calls ({self._call_count} total):")
                error_parts.append(self._format_call_history())
            else:
                error_parts.append("\n  (no calls made)")
            
            raise AssertionError("\n".join(error_parts))


    def assert_called(self):
        """
            Assert that the mock was called at least once.
            
            :raises AssertionError: If the mock was never called.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # ctx.assert_called()  # Would raise AssertionError
                
                mock()
                ctx.assert_called()  # Passes
        """
        if self._call_count == 0:
            raise AssertionError("Expected mock to have been called.")


    def assert_called_once(self):
        """
            Assert that the mock was called exactly once.
            
            :raises AssertionError: If the mock was not called exactly once. The error
                message includes the actual call count and call history when there are
                multiple calls.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # ctx.assert_called_once()  # Raises: "Called 0 times"
                
                mock()
                ctx.assert_called_once()  # Passes
                
                mock()
                # ctx.assert_called_once()  # Raises: "Called 2 times"
        """
        if self._call_count != 1:
            error_parts = [
                f"Expected mock to have been called once. Called {self._call_count} times."
            ]
            
            # Include call history if there were multiple calls
            if self._call_count > 1:
                error_parts.append(f"\nCall history:")
                error_parts.append(self._format_call_history())
            
            raise AssertionError("\n".join(error_parts))


    def assert_called_once_with(self, *args, **kwargs):
        """
            Assert that the mock was called exactly once and with the specified arguments.
            
            This is a convenience method that combines assert_called_once() and
            assert_called_with().
            
            :param args: The expected positional arguments.
            :param kwargs: The expected keyword arguments.
            
            :raises AssertionError: If the mock was not called exactly once, or if the
                call arguments don't match.

            Example::

                mock = Mock()
                mock(1, 2, key="value")
                
                ctx = mock.mock_context()
                ctx.assert_called_once_with(1, 2, key="value")  # Passes
                
                mock(3, 4)
                # ctx.assert_called_once_with(3, 4)  # Raises: called 2 times
        """
        self.assert_called_once()
        self.assert_called_with(*args, **kwargs)


    def assert_called_with(self, *args, **kwargs):
        """
            Assert that the last call to the mock was with the specified arguments.
            
            :param args: The expected positional arguments.
            :param kwargs: The expected keyword arguments.
            
            :raises AssertionError: If the mock was never called, or if the last call's
                arguments don't match. The error message includes expected vs actual arguments
                and the complete call history for debugging.

            Example::

                mock = Mock()
                mock(1, 2)
                mock(3, 4, key="value")
                
                ctx = mock.mock_context()
                ctx.assert_called_with(3, 4, key="value")  # Passes (checks last call)
                # ctx.assert_called_with(1, 2)  # Raises: last call was (3, 4, key='value')
        """
        if self._call_args is None:
            raise AssertionError("Expected mock to have been called with specific arguments, but it was not called.")
        
        last_args, last_kwargs = self._call_args
        if last_args != args or last_kwargs != kwargs:
            # Format expected vs actual calls with detailed information
            expected_call_str = self._format_call_args(args, kwargs)
            actual_call_str = self._format_call_args(last_args, last_kwargs)
            
            # Build comprehensive error message with call history
            error_parts = [
                f"Expected last call with {expected_call_str}",
                f"Actual last call: {actual_call_str}",
            ]
            
            # Include call history if there were multiple calls
            if len(self._call_args_list) > 1:
                error_parts.append(f"\nCall history ({self._call_count} total calls):")
                error_parts.append(self._format_call_history())
            
            raise AssertionError("\n".join(error_parts))

    
    def assert_has_calls(self, calls: List[Tuple[Tuple[Any, ...], Dict[str, Any]]], any_order: bool = False):
        """
            Assert that the mock was called with a specific sequence of calls.
            
            :param calls: A list of expected calls, where each call is a tuple of
                (args_tuple, kwargs_dict). For example: [((1, 2), {"key": "value"})]
            :param any_order: If False (default), the calls must appear as a contiguous
                subsequence in the actual call history. If True, all expected calls must
                be present but can appear in any order.
            
            :raises TypeError: If calls is not a list.
            :raises ValueError: If any item in calls is not a tuple of (args_tuple, kwargs_dict).
            :raises AssertionError: If the expected call sequence is not found. The error
                message includes detailed expected vs actual call information.

            Example::

                mock = Mock()
                mock(1)
                mock(2)
                mock(3)
                
                ctx = mock.mock_context()
                
                # Check for exact sequence
                ctx.assert_has_calls([((1,), {}), ((2,), {})])  # Passes
                
                # Check for calls in any order
                ctx.assert_has_calls([((3,), {}), ((1,), {})], any_order=True)  # Passes
                
                # This would fail (not a contiguous sequence)
                # ctx.assert_has_calls([((1,), {}), ((3,), {})])  # Raises AssertionError
        """
        if not isinstance(calls, list):
            raise TypeError("Expected 'calls' to be a list of call arguments.")
        if not all(isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], tuple) and isinstance(c[1], dict) for c in calls):
            raise ValueError("Each item in 'calls' must be a tuple of (args_tuple, kwargs_dict).")

        actual_calls = self._call_args_list

        if any_order:
            # Check if all expected calls are present in actual_calls, regardless of order and count
            for expected_call in calls:
                if expected_call not in actual_calls:
                    expected_call_str = self._format_call_args(*expected_call)
                    
                    # Build comprehensive error message
                    error_parts = [
                        f"Expected call {expected_call_str} not found in actual calls.",
                    ]
                    
                    if actual_calls:
                        error_parts.append(f"\nActual calls ({len(actual_calls)} total):")
                        error_parts.append(self._format_call_history())
                    else:
                        error_parts.append("\n  (no calls made)")
                    
                    raise AssertionError("\n".join(error_parts))
        else:
            # Check for an exact sub-sequence
            if len(calls) > len(actual_calls):
                error_parts = [
                    f"Expected {len(calls)} calls, but only {len(actual_calls)} were made.",
                    "\nExpected calls:"
                ]
                for i, call in enumerate(calls, 1):
                    error_parts.append(f"  {i}. {self._format_call_args(*call)}")
                
                if actual_calls:
                    error_parts.append(f"\nActual calls ({len(actual_calls)} total):")
                    error_parts.append(self._format_call_history())
                else:
                    error_parts.append("\n  (no calls made)")
                
                raise AssertionError("\n".join(error_parts))
            
            # Naive subsequence check
            found_subsequence = False
            for i in range(len(actual_calls) - len(calls) + 1):
                if actual_calls[i:i+len(calls)] == calls:
                    found_subsequence = True
                    break
            
            if not found_subsequence:
                error_parts = [
                    "Expected call sequence not found.",
                    "\nExpected sequence:"
                ]
                for i, call in enumerate(calls, 1):
                    error_parts.append(f"  {i}. {self._format_call_args(*call)}")
                
                error_parts.append(f"\nActual calls ({len(actual_calls)} total):")
                error_parts.append(self._format_call_history())
                
                raise AssertionError("\n".join(error_parts))


    def assert_calls_in_order(self, calls: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]):
        """
            Assert that the specified calls occurred in the given order.
            
            Unlike assert_has_calls, this method verifies that the expected calls occurred
            in the specified order, but they do not need to be contiguous. Other calls
            may occur between the expected calls.
            
            This is useful for verifying that certain operations happened in a specific
            sequence without requiring them to be consecutive.
            
            :param calls: A list of expected calls in the order they should have occurred,
                where each call is a tuple of (args_tuple, kwargs_dict).
                For example: [((1, 2), {"key": "value"})]
            
            :raises TypeError: If calls is not a list.
            :raises ValueError: If any item in calls is not a tuple of (args_tuple, kwargs_dict).
            :raises AssertionError: If the expected calls did not occur in the specified order.
                The error message includes:
                - Which call violated the order
                - The expected order of calls
                - The actual call history with positions marked

            Example::

                mock = Mock()
                mock("first")
                mock("middle")
                mock("second")
                mock("other")
                mock("third")
                
                ctx = mock.mock_context()
                
                # Verify calls occurred in order (not necessarily contiguous)
                ctx.assert_calls_in_order([
                    (("first",), {}),
                    (("second",), {}),
                    (("third",), {})
                ])  # Passes - "first" came before "second" which came before "third"
                
                # This would fail - "third" came after "second", not before
                # ctx.assert_calls_in_order([
                #     (("first",), {}),
                #     (("third",), {}),
                #     (("second",), {})
                # ])  # Raises AssertionError
        """
        if not isinstance(calls, list):
            raise TypeError("Expected 'calls' to be a list of call arguments.")
        
        if len(calls) == 0:
            return  # Empty list always passes
        
        if not all(isinstance(c, tuple) and len(c) == 2 and isinstance(c[0], tuple) and isinstance(c[1], dict) for c in calls):
            raise ValueError("Each item in 'calls' must be a tuple of (args_tuple, kwargs_dict).")

        actual_calls = self._call_args_list
        
        # Track the position of each expected call in the actual call history
        call_positions = []
        search_start = 0
        
        for i, expected_call in enumerate(calls):
            # Find the expected call in the actual calls, starting from the last found position
            found_position = None
            for j in range(search_start, len(actual_calls)):
                if actual_calls[j] == expected_call:
                    found_position = j
                    break
            
            if found_position is None:
                # Call not found at all
                expected_call_str = self._format_call_args(*expected_call)
                
                error_parts = [
                    f"Call order verification failed.",
                    f"\nExpected call #{i + 1} {expected_call_str} was not found",
                ]
                
                if search_start > 0:
                    error_parts.append(f"after position {search_start} (after previous expected call).")
                else:
                    error_parts.append("in the call history.")
                
                error_parts.append("\nExpected call order:")
                for idx, call in enumerate(calls, 1):
                    marker = " <-- not found" if idx == i + 1 else ""
                    if idx <= len(call_positions):
                        marker = f" (found at position {call_positions[idx - 1] + 1})"
                    error_parts.append(f"  {idx}. {self._format_call_args(*call)}{marker}")
                
                if actual_calls:
                    error_parts.append(f"\nActual calls ({len(actual_calls)} total):")
                    error_parts.append(self._format_call_history_with_markers(call_positions))
                else:
                    error_parts.append("\n  (no calls made)")
                
                raise AssertionError("\n".join(error_parts))
            
            call_positions.append(found_position)
            search_start = found_position + 1  # Next search starts after this position

    def _format_call_history_with_markers(self, marked_positions: List[int], max_calls: int = 15) -> str:
        """
            Helper method to format the call history with position markers.
            
            :param marked_positions: List of positions to mark in the output.
            :param max_calls: Maximum number of calls to include in the output.
            
            :return: A formatted string showing the call history with markers.
        """
        if not self._call_args_list:
            return "  (no calls recorded)"
        
        lines = []
        total_calls = len(self._call_args_list)
        calls_to_show = min(total_calls, max_calls)
        
        for i in range(calls_to_show):
            args, kwargs = self._call_args_list[i]
            call_str = self._format_call_args(args, kwargs)
            marker = ""
            if i in marked_positions:
                order_num = marked_positions.index(i) + 1
                marker = f" <-- expected call #{order_num}"
            lines.append(f"  {i + 1}. {call_str}{marker}")
        
        if total_calls > max_calls:
            remaining = total_calls - max_calls
            # Check if any marked positions are in the truncated part
            truncated_markers = [p for p in marked_positions if p >= max_calls]
            if truncated_markers:
                lines.append(f"  ... and {remaining} more call(s) (including expected calls at positions {[p + 1 for p in truncated_markers]})")
            else:
                lines.append(f"  ... and {remaining} more call(s)")
        
        return "\n".join(lines)


    def configure(self, *, return_value: Optional[Any] = ..., side_effect: Optional[Union[Callable, SideEffect]] = ...,
                  recursive: Optional[bool] = ..., strict_attrs: Optional[bool] = ...):
        """
            Configures the mock's behavior.
            
            This method allows updating multiple mock settings at once. It uses the Ellipsis (...)
            as a sentinel value to distinguish between an argument being explicitly passed
            (even as None) and not being provided at all.
            
            :param return_value: The value to return when the mock is called. Pass None to
                explicitly set return_value to None.
            :param side_effect: A callable or SideEffect instance to execute when the mock
                is called. If a callable is provided, it will be wrapped in a SideEffect.
                Pass None to clear the side effect.
            :param recursive: If True, accessing undefined attributes will create new Mock
                objects. If False, accessing undefined attributes will raise AttributeError.
            :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
            
            :return: The Mock instance for fluent method chaining.
            
            :raises TypeError: If side_effect is provided but is neither a SideEffect instance
                nor a callable. Also raised if recursive or strict_attrs are not boolean.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # Configure multiple settings at once
                ctx.configure(return_value=42, recursive=True)
                
                # Fluent chaining
                mock.configure(return_value="hello").configure(recursive=True)
                
                # Clear side effect by passing None
                ctx.configure(side_effect=None)
                
                # Configure with a side effect
                ctx.configure(side_effect=lambda x: x * 2)
        """
        if return_value is not ...:
            # Directly set _return_value. None is a valid value.
            self._return_value = return_value
        
        if side_effect is not ...:
            # Logic moved from the old set_side_effect method
            if side_effect is not None and not isinstance(side_effect, SideEffect):
                if callable(side_effect):
                    self._side_effect = SideEffect(side_effect)
                else:
                    raise TypeError(f"configure: side_effect must be a SideEffect instance or a callable, not {type(side_effect)}.")
            else: # side_effect is None or already a SideEffect instance
                self._side_effect = side_effect

        if recursive is not ...:
            if not isinstance(recursive, bool):
                raise TypeError("configure: 'recursive' must be a boolean value.")
            self._recursive = recursive

        if strict_attrs is not ...:
            if not isinstance(strict_attrs, bool):
                raise TypeError("configure: 'strict_attrs' must be a boolean value.")
            self._strict_attrs = strict_attrs
        
        return self.get_mock() # Return the Mock instance for fluent chaining

    def get_attribute(self, name: str) -> Any:
        """
            Gets the value of an attribute from this mock context.
            
            :param name: The name of the attribute to retrieve.
            
            :return: The value of the attribute.
            
            :raises AttributeError: If the attribute does not exist in mock_attributes.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                ctx.set_attribute('name', 'test_value')
                value = ctx.get_attribute('name')  # Returns 'test_value'
                
                # ctx.get_attribute('nonexistent')  # Raises AttributeError
        """
        if not self.has_attribute(name):
            raise AttributeError(f"MockContext has no attribute '{name}'")

        rtnval = self._mock_attributes.get(name)

        return rtnval

    def get_mock(self) -> "Mock":
        """
            Returns the Mock object that this context belongs to.
            
            This method dereferences the weak reference to the Mock object.
            
            :return: The Mock object associated with this context.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                same_mock = ctx.get_mock()
                assert mock is same_mock  # True
        """
        rtnval = self._mock_ref()
        
        return rtnval
    
    def get_mock_owner(self) -> Any:
        """
            Returns the parent Mock object if this is a child mock.
            
            This method dereferences the weak reference to the parent Mock object.
            
            :return: The parent Mock object, or None if this mock has no parent.

            Example::

                parent_mock = Mock(recursive=True)
                child_mock = parent_mock.child  # Creates child mock
                
                child_ctx = child_mock.mock_context()
                owner = child_ctx.get_mock_owner()
                assert owner is parent_mock  # True
        """
        rtnval = None
        
        if self._mock_owner_ref is not None:
            rtnval = self._mock_owner_ref()
        
        return rtnval

    def has_attribute(self, name: str) -> bool:
        """
            Checks if this mock context has the given attribute.

            :param name: The name of the attribute to check for.
        
            :return: True if the attribute exists in mock_attributes, False otherwise.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                ctx.set_attribute('name', 'value')
                
                ctx.has_attribute('name')  # Returns True
                ctx.has_attribute('other')  # Returns False
        """
        rtnval = True if name in self._mock_attributes else False
        
        return rtnval

    def mock_method(self, name: str, return_value: Optional[Any] = ..., side_effect: Optional[Union[Callable, SideEffect]] = ...):
        """
            Creates a mock method and stores it as an attribute.
            
            This method creates a new Mock object with MockType.Method and stores it
            in the mock_attributes dictionary under the given name. The created mock
            inherits the recursive and strict_attrs settings from this context.
            
            :param name: The name of the method to create.
            :param return_value: The value the mock method should return when called.
                Defaults to None.
            :param side_effect: A callable or SideEffect to execute when the mock method
                is called. Defaults to None.

            :return: The created Mock object representing the method.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # Create a simple mock method
                ctx.mock_method('calculate', return_value=42)
                result = mock.calculate()  # Returns 42
                
                # Create a mock method with side effect
                ctx.mock_method('process', side_effect=lambda x: x * 2)
                result = mock.process(5)  # Returns 10
                
                # Verify the method was called
                mock.calculate.assert_called_once()
        """
        this_mock = self.get_mock()

        mock_method = Mock(return_value=return_value if return_value is not ... else None, side_effect=side_effect if side_effect is not ... else None, mtype=MockType.Method,
                           mock_owner=this_mock, recursive=self.recursive, strict_attrs=self._strict_attrs)

        self._mock_attributes[name] = mock_method

        return mock_method
    
    def mock_property(self, name: str, return_value: Optional[Any] = ..., side_effect: Optional[Union[Callable, SideEffect]] = ...,
                      setter_side_effect: Optional[Union[Callable, SideEffect]] = ...):
        """
            Creates a mock property and stores it as an attribute.
            
            This method creates a new PropertyMock object and stores it in the 
            mock_attributes dictionary under the given name. The PropertyMock provides
            separate tracking for getter and setter operations.
            
            :param name: The name of the property to create.
            :param return_value: The value the mock property should return when accessed (getter).
                Defaults to None.
            :param side_effect: A callable or SideEffect to execute when the mock property
                is accessed (getter). Defaults to None.
            :param setter_side_effect: A callable or SideEffect to execute when the mock
                property is set (setter). The callable receives the value being set.
                Defaults to None.
        
            :return: The created PropertyMock object representing the property.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # Create a simple mock property with getter
                ctx.mock_property('name', return_value='test_name')
                value = mock.name.get()  # Returns 'test_name'
                
                # Create a mock property with getter and setter
                def on_set(value):
                    print(f"Property set to: {value}")
                
                ctx.mock_property('status', return_value='active', setter_side_effect=on_set)
                print(mock.status.get())  # Returns 'active'
                mock.status.set('inactive')  # Prints: "Property set to: inactive"
                
                # Verify interactions
                mock.status.assert_getter_called()
                mock.status.assert_setter_called_with('inactive')
        """
        this_mock = self.get_mock()

        mock_property = PropertyMock(
            getter_return_value=return_value if return_value is not ... else None,
            getter_side_effect=side_effect if side_effect is not ... else None,
            setter_side_effect=setter_side_effect if setter_side_effect is not ... else None,
            mock_owner=this_mock
        )

        self._mock_attributes[name] = mock_property

        return mock_property

    def mock_async_method(self, name: str, return_value: Optional[Any] = ..., 
                          side_effect: Optional[Union[Callable[..., Coroutine], AsyncSideEffect]] = ...):
        """
            Creates an async mock method and stores it as an attribute.
            
            This method creates a new AsyncMock object with MockType.Method and stores it
            in the mock_attributes dictionary under the given name. The created async mock
            inherits the recursive and strict_attrs settings from this context.
            
            :param name: The name of the async method to create.
            :param return_value: The value the async mock method should return when awaited.
                Defaults to None.
            :param side_effect: An async callable or AsyncSideEffect to execute when the 
                async mock method is awaited. Defaults to None.

            :return: The created AsyncMock object representing the async method.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # Create a simple async mock method
                ctx.mock_async_method('fetch_data', return_value={'id': 1})
                result = await mock.fetch_data()  # Returns {'id': 1}
                
                # Create an async mock method with side effect
                async def async_process(x):
                    await asyncio.sleep(0.01)
                    return x * 2
                
                ctx.mock_async_method('process', side_effect=async_process)
                result = await mock.process(5)  # Returns 10
                
                # Verify the method was called
                mock.fetch_data.assert_called_once()
        """
        this_mock = self.get_mock()

        async_mock_method = AsyncMock(
            return_value=return_value if return_value is not ... else None, 
            side_effect=side_effect if side_effect is not ... else None, 
            mtype=MockType.Method,
            mock_owner=this_mock, 
            recursive=self.recursive, 
            strict_attrs=self._strict_attrs
        )

        self._mock_attributes[name] = async_mock_method

        return async_mock_method

    def reset(self):
        """
            Resets the mock context to its initial state.
            
            This method clears all configuration and call tracking data:
            - return_value is set to None
            - side_effect is set to None
            - call_count is reset to 0
            - call_args is cleared to None
            - call_args_list is cleared to an empty list
            - mock_calls is cleared to an empty list
            
            Note: This does not reset mock_attributes or child mocks.

            Example::

                mock = Mock(return_value=42)
                mock(1, 2)
                mock(3, 4)
                
                ctx = mock.mock_context()
                print(ctx.call_count)  # 2
                print(ctx.return_value)  # 42
                
                ctx.reset()
                
                print(ctx.call_count)  # 0
                print(ctx.return_value)  # None
                print(ctx.call_args)  # None
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
            Sets the value of an attribute in this mock context.

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                ctx.set_attribute('id', 123)
                ctx.set_attribute('name', 'test')
                
                print(mock.id)  # 123
                print(mock.name)  # 'test'
        """
        self._mock_attributes[name] = value

        return

    def _format_call_args(self, args: Tuple[Any, ...], kwargs: Dict[str, Any]) -> str:
        """
            Helper method to format call arguments for assertion error messages.
            
            Formats arguments in a readable way with proper indentation for complex
            arguments. Handles nested structures and long strings gracefully.
            
            :param args: The positional arguments tuple.
            :param kwargs: The keyword arguments dictionary.
            
            :return: A formatted string representation of the call arguments.
        """
        rtnval = ""

        call_parts = []
        if args:
            call_parts.extend(self._format_arg_value(arg) for arg in args)
        
        if kwargs:
            # Sort keyword arguments for consistent output order
            sorted_kwargs = sorted(kwargs.items())
            call_parts.extend(f"{k}={self._format_arg_value(v)}" for k, v in sorted_kwargs)
        
        rtnval = f"({', '.join(call_parts)})"

        return rtnval

    def _format_arg_value(self, value: Any) -> str:
        """
            Helper method to format a single argument value for readability.
            
            Handles special cases like long strings, large collections, and nested
            structures to produce more readable output in error messages.
            
            :param value: The argument value to format.
            
            :return: A formatted string representation of the value.
        """
        MAX_STRING_LENGTH = 100
        MAX_COLLECTION_ITEMS = 10
        
        if isinstance(value, str):
            if len(value) > MAX_STRING_LENGTH:
                return f"'{value[:MAX_STRING_LENGTH]}...' (truncated, {len(value)} chars)"
            return repr(value)
        
        if isinstance(value, (list, tuple, set, frozenset)):
            if len(value) > MAX_COLLECTION_ITEMS:
                items = list(value)[:MAX_COLLECTION_ITEMS]
                formatted_items = [self._format_arg_value(item) for item in items]
                type_name = type(value).__name__
                return f"{type_name}([{', '.join(formatted_items)}, ...]) ({len(value)} items)"
            return repr(value)
        
        if isinstance(value, dict):
            if len(value) > MAX_COLLECTION_ITEMS:
                items = list(value.items())[:MAX_COLLECTION_ITEMS]
                formatted_items = [f"{self._format_arg_value(k)}: {self._format_arg_value(v)}" for k, v in items]
                return f"{{" + ", ".join(formatted_items) + f", ...}} ({len(value)} items)"
            return repr(value)
        
        return repr(value)

    def _format_call_history(self, max_calls: int = 10) -> str:
        """
            Helper method to format the call history for inclusion in error messages.
            
            :param max_calls: Maximum number of calls to include in the output.
            
            :return: A formatted string showing the call history.
        """
        if not self._call_args_list:
            return "  (no calls recorded)"
        
        lines = []
        total_calls = len(self._call_args_list)
        calls_to_show = self._call_args_list[:max_calls]
        
        for i, (args, kwargs) in enumerate(calls_to_show, 1):
            call_str = self._format_call_args(args, kwargs)
            lines.append(f"  {i}. {call_str}")
        
        if total_calls > max_calls:
            lines.append(f"  ... and {total_calls - max_calls} more call(s)")
        
        return "\n".join(lines)


    def _record_call(self, *args, **kwargs):
        """
            Internal method to record a call to the mock.
            
            This method is called by Mock.__call__ to track invocation details.
            It updates call_count, call_args, and call_args_list.
            
            :param args: The positional arguments from the call.
            :param kwargs: The keyword arguments from the call.
        """
        # ============================================================================
        # CALL TRACKING MECHANISM
        # ============================================================================
        # This method implements the core call tracking functionality that enables
        # mock verification through assertion methods. Each call to the mock is
        # recorded with full argument information.
        #
        # Tracked Data:
        # -------------
        # 1. _call_count: Integer counter incremented on each call
        #    - Used by assert_called_once() to verify single invocation
        #    - Accessible via call_count property
        #
        # 2. _call_args: Tuple of (args, kwargs) from the MOST RECENT call
        #    - Overwrites previous value on each call
        #    - Used by assert_called_with() to verify last call arguments
        #    - Format: (tuple_of_positional_args, dict_of_keyword_args)
        #
        # 3. _call_args_list: List of ALL calls in chronological order
        #    - Appends each call, preserving complete history
        #    - Used by assert_any_call() and assert_has_calls()
        #    - Format: [(args1, kwargs1), (args2, kwargs2), ...]
        #
        # Design Decisions:
        # -----------------
        # - Arguments are stored as-is without copying, so mutable arguments
        #   could theoretically be modified after the call. This matches
        #   unittest.mock behavior for performance reasons.
        #
        # - The call_args stores the raw tuple and dict, not a custom Call object,
        #   for simplicity and direct comparison in assertions.
        #
        # - mock_calls tracking for child mocks is noted but not fully implemented
        #   in this version. A complete implementation would have child mocks
        #   propagate their calls to parent mocks with a dotted name path.
        # ============================================================================
        
        # Increment the call counter for assert_called_once() verification
        self._call_count += 1
        
        # Store the most recent call arguments for assert_called_with() verification
        # This overwrites any previous call_args value
        self._call_args = (args, kwargs)
        
        # Append to the call history list for assert_any_call() and assert_has_calls()
        # This preserves the complete chronological record of all calls
        self._call_args_list.append((args, kwargs))
        
        # Note: Full mock_calls implementation would propagate child calls to parent
        # For direct calls to this mock, the name would be empty string
        # self._mock_calls.append(('', args, kwargs))


class Mock:
    """
        The primary interface for creating and interacting with mock objects.
        
        Mock objects simulate the behavior of real objects, allowing you to:
        - Configure return values for when the mock is called
        - Execute side effects when the mock is called
        - Track all calls made to the mock
        - Verify interactions using assertion methods
        - Create nested mock hierarchies with recursive mode
        
        Example Usage::

            from ccai.testbase.mocking import Mock

            # Basic mock with return value
            mock = Mock(return_value=42)
            result = mock()  # Returns 42
            
            # Mock with side effect
            mock = Mock(side_effect=lambda x: x * 2)
            result = mock(5)  # Returns 10
            
            # Recursive mock for nested attribute access
            mock = Mock(recursive=True)
            mock.database.query.return_value = ["item1", "item2"]
            result = mock.database.query()  # Returns ["item1", "item2"]
            
            # Verify interactions
            mock = Mock()
            mock(1, 2, key="value")
            mock.assert_called_once_with(1, 2, key="value")
            
            # Configure through context
            mock = Mock()
            ctx = mock.mock_context()
            ctx.mock_method('calculate', return_value=100)
            ctx.set_attribute('name', 'test')
    """

    def __init__(self, *, mock_attributes: Optional[Dict[str, Any]] = None, return_value: Optional[Any] = None,
                 reference: Optional[Any] = None, mtype: Optional[MockType] = None, mock_owner: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None,
                 recursive: bool = False, strict_attrs: bool = False):
        """
            Creates a mock object with the given attributes and configuration.

            :param mock_attributes: A dictionary of pre-defined attributes for the mock.
                These attributes can be accessed on the mock object. Defaults to an empty dict.
            :param return_value: The value to return when the mock is called. Defaults to None.
            :param reference: The original object being mocked. Used for type determination
                and restoration during patch deactivation. Defaults to None.
            :param mtype: Explicit MockType for this mock. If not provided, the type is
                determined from the reference parameter. Defaults to MockType.Generic.
            :param mock_owner: The parent Mock object if this is a child mock. Used for
                tracking nested mock hierarchies. Defaults to None.
            :param side_effect: A callable or SideEffect instance to execute when the mock
                is called. If a callable is provided, it will be wrapped in a SideEffect.
                Defaults to None.
            :param recursive: If True, accessing undefined attributes will automatically
                create and return new Mock objects. This enables chained attribute access
                like mock.a.b.c without explicit setup. Defaults to False.
            :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
                Attempting to access undefined attributes raises AttributeError.
                Defaults to False.

            :raises TypeError: If side_effect is provided but is neither a SideEffect instance
                nor a callable. Also raised if recursive or strict_attrs are not boolean values.

            Example::

                from ccai.testbase.mocking import Mock, MockType

                # Simple mock
                mock = Mock()
                
                # Mock with return value
                mock = Mock(return_value=42)
                result = mock()  # Returns 42
                
                # Mock with pre-defined attributes
                mock = Mock(mock_attributes={'id': 1, 'name': 'test'})
                print(mock.id)  # 1
                
                # Recursive mock for chained access
                mock = Mock(recursive=True)
                mock.a.b.c.return_value = "deep"
                
                # Strict mock that only allows defined attributes
                mock = Mock(mock_attributes={'allowed': True}, strict_attrs=True)
                # mock.undefined  # Raises AttributeError
        """
        if mock_attributes is None:
            mock_attributes = {}

        if mtype is None:
            mtype = MockType.Generic
            if reference is not None:
                mtype = MockContext.determine_mock_type(reference if reference is not ... else None)

        self._mock_context = MockContext(self, mtype, mock_attributes, 
                                         reference=reference if reference is not ... else None, 
                                         return_value=return_value if return_value is not ... else None,
                                         side_effect=side_effect if side_effect is not ... else None, 
                                         mock_owner=mock_owner if mock_owner is not ... else None, 
                                         recursive=recursive, strict_attrs=strict_attrs)

        return


    def mock_context(self) -> MockContext:
        """
            Returns the MockContext for this mock object.
            
            The MockContext provides access to all mock configuration and state,
            including call tracking, assertion methods, and attribute management.
            
            :return: The MockContext instance associated with this mock.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                
                # Configure through context
                ctx.configure(return_value=42)
                ctx.mock_method('calculate', return_value=100)
                
                # Access call tracking
                mock()
                print(ctx.call_count)  # 1
        """
        return self._mock_context

    # --- Expose call tracking properties from context ---
    @property
    def call_count(self) -> int:
        """
            Returns the number of times this mock was called.
            
            :return: An integer representing the total call count.
        """
        return self._mock_context.call_count

    @property
    def call_args(self) -> Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns the arguments of the last call to this mock.
            
            :return: A tuple of (args, kwargs) from the most recent call,
                or None if the mock has never been called.
        """
        return self._mock_context.call_args

    @property
    def call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all calls made to this mock.
            
            :return: A list of (args, kwargs) tuples in chronological order.
        """
        return self._mock_context.call_args_list
    
    @property
    def mock_calls(self) -> List[Tuple[str, Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all calls made to this mock and its children.
            
            :return: A list of (name, args, kwargs) tuples where name identifies
                the call target (empty string for direct calls).
        """
        return self._mock_context.mock_calls

    def configure(self, *, return_value: Optional[Any] = ..., side_effect: Optional[Union[Callable, SideEffect]] = ...,
                  recursive: Optional[bool] = ..., strict_attrs: Optional[bool] = ...):
        """
            Configures this mock's behavior.
            
            This method delegates to MockContext.configure and returns self for
            fluent method chaining.
            
            :param return_value: The value to return when the mock is called.
            :param side_effect: A callable or SideEffect to execute when called.
            :param recursive: If True, enable automatic child mock creation.
            :param strict_attrs: If True, restrict attribute access to defined attributes.
            
            :return: This Mock instance for fluent chaining.
            
            :raises TypeError: If side_effect is not callable or SideEffect,
                or if recursive/strict_attrs are not boolean.

            Example::

                mock = Mock()
                
                # Fluent configuration
                mock.configure(return_value=42).configure(recursive=True)
                
                # Chain with attribute access
                mock.configure(recursive=True).child.configure(return_value="nested")
        """
        # The '...' sentinel is used by MockContext.configure to know if an arg was passed.
        self._mock_context.configure(return_value=return_value,
                                     side_effect=side_effect,
                                     recursive=recursive, strict_attrs=strict_attrs)
        return self

    def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the mock object with the given arguments.
            
            When called, the mock records the call for later verification and returns
            either the configured return_value or the result of executing the side_effect.

            :param args: The positional arguments to pass to the mock.
            :param kwargs: The keyword arguments to pass to the mock.

            :return: The configured return_value, or if side_effect is set, the result
                of executing the side_effect with the provided arguments.

            Example::

                # Return value
                mock = Mock(return_value=42)
                result = mock(1, 2)  # Returns 42
                
                # Side effect
                mock = Mock(side_effect=lambda x, y: x + y)
                result = mock(1, 2)  # Returns 3
                
                # Both configured (side_effect takes precedence)
                mock = Mock(return_value=0, side_effect=lambda: 100)
                result = mock()  # Returns 100
        """
        # ============================================================================
        # MOCK INVOCATION FLOW
        # ============================================================================
        # This method handles the core mock invocation behavior:
        #
        # 1. CALL RECORDING (always happens first)
        #    - Delegates to MockContext._record_call() to track the invocation
        #    - This ensures call tracking happens even if side_effect raises
        #    - Enables assertion methods like assert_called_with()
        #
        # 2. RETURN VALUE DETERMINATION
        #    - Default: return the configured return_value (may be None)
        #    - If side_effect is configured: execute it and return its result
        #    - Side effect takes precedence over return_value when both are set
        #
        # Execution Order:
        # ----------------
        # 1. Record the call with all arguments
        # 2. Get the default return value from context
        # 3. If side_effect exists, execute it with the call arguments
        # 4. Return either side_effect result or return_value
        #
        # Note: The side_effect receives the same arguments that were passed to
        # the mock, allowing it to compute dynamic return values based on input.
        # ============================================================================
        
        # Step 1: Record this call for later verification via assertion methods
        # This must happen first to ensure call tracking even if side_effect raises
        self._mock_context._record_call(*args, **kwargs)
        
        # Step 2: Get the default return value (may be None if not configured)
        rtnval = self._mock_context.return_value

        # Step 3: If side_effect is configured, execute it and use its return value
        # Side effect takes precedence over return_value when both are configured
        if self._mock_context.side_effect is not None:
            # Pass the same arguments to side_effect for dynamic behavior
            rtnval = self._mock_context.side_effect(*args, **kwargs)

        return rtnval


    def __repr__(self):
        """
            Returns a string representation of the mock object.
            
            :return: A string showing the mock's return_value and side_effect configuration.
        """
        rtnval = f"Mock(return_value={self._mock_context.return_value}, side_effect={self._mock_context.side_effect})"
        
        return rtnval


    def __str__(self):
        """
            Returns a human-readable string representation of the mock object.
            
            :return: A descriptive string showing the mock's configuration.
        """
        rtnval = f"Mock with return_value={self._mock_context.return_value} and side_effect={self._mock_context.side_effect}"
        
        return rtnval


    def __getattr__(self, name: str):
        """
            Gets an attribute of the mock object.
            
            This method handles attribute access with the following priority:
            1. Raises AttributeError for underscore-prefixed names (private attributes)
            2. Returns assertion methods from the context (assert_called, etc.)
            3. Returns stored attributes from mock_attributes
            4. Creates child mocks when recursive=True
            5. Raises AttributeError when strict_attrs=True or recursive=False

            :param name: The name of the attribute to get.
            
            :return: The attribute value, assertion method, or a new child Mock.

            :raises AttributeError: If the attribute starts with underscore, or if
                the attribute doesn't exist and (strict_attrs=True or recursive=False).

            Example::

                mock = Mock(recursive=True)
                
                # Access creates child mock
                child = mock.child  # Returns new Mock
                
                # Same attribute returns same mock
                assert mock.child is child
                
                # Assertion methods are accessible
                mock()
                mock.assert_called()  # Works
        """
        # ============================================================================
        # ATTRIBUTE ACCESS RESOLUTION ALGORITHM
        # ============================================================================
        # This method implements a multi-step resolution process for attribute access
        # on Mock objects. The resolution order is carefully designed to:
        #
        # 1. Protect internal state by blocking underscore-prefixed attributes
        # 2. Provide seamless access to assertion methods (assert_called, etc.)
        # 3. Return explicitly configured attributes
        # 4. Support recursive mock creation for undefined attributes
        # 5. Enforce strict attribute mode when enabled
        #
        # Resolution Steps:
        # -----------------
        # Step 1: PRIVATE ATTRIBUTE GUARD
        #   - Block access to underscore-prefixed names to prevent accidental
        #     access to internal Mock state (_mock_context, etc.)
        #   - This ensures mock.some_attr works but mock._internal raises error
        #
        # Step 2: ASSERTION METHOD DELEGATION
        #   - Check if the requested name is an assertion method on MockContext
        #   - This allows mock.assert_called() instead of mock.mock_context().assert_called()
        #   - Only methods starting with "assert_" are delegated
        #
        # Step 3: EXPLICIT ATTRIBUTE LOOKUP
        #   - Try to retrieve the attribute from mock_attributes dictionary
        #   - This returns attributes set via set_attribute() or mock_method()
        #
        # Step 4: STRICT MODE CHECK
        #   - If strict_attrs=True and attribute not found, raise AttributeError
        #   - This prevents accidental attribute access on strictly-typed mocks
        #
        # Step 5: RECURSIVE MOCK CREATION
        #   - If recursive=True and attribute not found, create a new child Mock
        #   - The child mock inherits recursive and strict_attrs settings
        #   - The child is stored in mock_attributes for consistent access
        #   - This enables chained access like mock.a.b.c without explicit setup
        #
        # Step 6: FINAL FALLBACK
        #   - If not recursive and attribute not found, raise AttributeError
        # ============================================================================
        
        # Step 1: Block access to private/internal attributes
        # This prevents accidental exposure of Mock internals like _mock_context
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Step 2: Delegate assertion methods to MockContext
        # This provides a convenient API: mock.assert_called() instead of mock.mock_context().assert_called()
        # We check for callable methods starting with "assert_" on the context
        if hasattr(self._mock_context, name) and callable(getattr(self._mock_context, name)) and name.startswith("assert_"):
            return getattr(self._mock_context, name)

        try:
            # Step 3: Attempt to retrieve an explicitly configured attribute
            # This includes attributes set via set_attribute(), mock_method(), or mock_property()
            return self._mock_context.get_attribute(name)
        except AttributeError:
            # Step 4: Enforce strict attribute mode
            # When strict_attrs=True, only pre-defined attributes are accessible
            # This is useful for mocking objects with a known interface
            if self._mock_context._strict_attrs:
                raise AttributeError(
                    f"'{self._mock_context._mock_type}' object has no attribute '{name}' (strict_attrs is True)"
                )

            # Step 5: Create child mock for recursive access
            # When recursive=True, undefined attributes automatically become new Mock objects
            # This enables fluent chained access patterns like mock.database.query.filter()
            if self._mock_context.recursive:
                # Create child mock with same recursive and strict_attrs settings
                new_mock = Mock(mock_owner=self, recursive=self._mock_context.recursive,
                                strict_attrs=self._mock_context._strict_attrs) # Propagate strict_attrs
                # Store the child mock so subsequent access returns the same object
                # This ensures mock.child is mock.child (identity consistency)
                self._mock_context.set_attribute(name, new_mock)
                return new_mock
            
            # Step 6: Final fallback - attribute not found and not recursive
            # Re-raise the AttributeError from get_attribute()
            raise


    def __setattr__(self, name: str, value: Any):
        """
            Sets an attribute on the mock object.
            
            This method handles attribute assignment with special cases:
            1. Underscore-prefixed names are set directly on the object
            2. 'return_value', 'side_effect', 'recursive' configure the mock
            3. Other attributes are stored in mock_attributes
            4. When strict_attrs=True, only pre-defined attributes can be set

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.

            :raises AttributeError: If strict_attrs=True and the attribute is not
                pre-defined and not a special mock configuration attribute.

            Example::

                mock = Mock()
                
                # Configure via attribute assignment
                mock.return_value = 42
                mock.side_effect = lambda: "effect"
                
                # Set custom attributes
                mock.custom_attr = "value"
                
                # Strict mode
                mock = Mock(mock_attributes={'allowed': True}, strict_attrs=True)
                mock.allowed = False  # Works
                # mock.new_attr = "x"  # Raises AttributeError
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
                self._mock_context.configure(return_value=value)
            elif name == "side_effect":
                self._mock_context.configure(side_effect=value)
            elif name == "recursive":
                self._mock_context.recursive = value
            else:
                # For other attributes, store them in the context's _mock_attributes
                self._mock_context.set_attribute(name, value)

        return


    def __eq__(self, other: Any):
        """
            Checks if this mock object is equal to another object.
            
            Two mocks are considered equal if they have the same:
            - return_value
            - side_effect
            - recursive setting
            - strict_attrs setting
            - mock_type
            - mock_attributes

            :param other: The other object to compare with.

            :return: True if the mocks are equal, False otherwise.
                Returns NotImplemented if other is not a Mock.

            Example::

                mock1 = Mock(return_value=42, recursive=True)
                mock2 = Mock(return_value=42, recursive=True)
                mock3 = Mock(return_value=0)
                
                mock1 == mock2  # True
                mock1 == mock3  # False
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
            Checks if this mock object is not equal to another object.
            
            :param other: The other object to compare with.
            
            :return: True if the mock objects are not equal, False otherwise.
        """
        rtnval = not self.__eq__(other)
        
        return rtnval


    def __hash__(self):
        """
            Returns the hash of the mock object.
            
            The hash is based on object identity (id) to ensure consistency
            even when mock state changes.
            
            :return: An integer hash value based on the mock's identity.
        """
        # Hashing can be tricky with mutable state.
        # A common approach for mocks is to use id() or make them unhashable if their state changes __eq__.
        rtnval = id(self) # Or make it more complex based on immutable parts of context
        
        return rtnval


    def __bool__(self):
        """ 
            Checks if the mock object is truthy.
            
            By default, mocks are truthy (return True). If return_value is set,
            the boolean value of return_value is returned instead.

            :return: True by default, or bool(return_value) if return_value is set.

            Example::

                mock = Mock()
                bool(mock)  # True (default)
                
                mock = Mock(return_value=0)
                bool(mock)  # False
                
                mock = Mock(return_value=[1, 2, 3])
                bool(mock)  # True
        """
        # Mocks are generally considered truthy by default, similar to unittest.mock.Mock.
        # If a specific boolean value is desired, it should be set via return_value.
        if self._mock_context.return_value is not None:
            rtnval = bool(self._mock_context.return_value)
        else:
            rtnval = True # Default truthiness for a Mock object itself
        return rtnval


    def __dir__(self) -> List[str]:
        """
            Returns a list of attributes for the mock object.
            
            This includes standard Mock attributes plus any attributes that have been
            defined in mock_attributes.
            
            :return: A sorted list of attribute names.

            Example::

                mock = Mock()
                ctx = mock.mock_context()
                ctx.set_attribute('custom', 'value')
                
                attrs = dir(mock)
                'custom' in attrs  # True
        """
        attributes = set(super().__dir__()) # Get attributes from Mock class and its bases

        # Add attributes from the mock context
        if self._mock_context and hasattr(self._mock_context, '_mock_attributes'):
            attributes.update(self._mock_context._mock_attributes.keys())
    
        attributes = list(attributes)
        attributes.sort()

        return attributes


    def __len__(self):
        """
            Returns the length of the mock object.
            
            This method delegates to len(return_value). If return_value is not set
            or doesn't support len(), a TypeError is raised.
            
            :return: The length of return_value.

            :raises TypeError: If return_value is None or doesn't support len().

            Example::

                mock = Mock(return_value=[1, 2, 3])
                len(mock)  # Returns 3
                
                mock = Mock(return_value="hello")
                len(mock)  # Returns 5
                
                mock = Mock()
                # len(mock)  # Raises TypeError
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
            Returns an iterator for the mock object.
            
            This method delegates to iter(return_value). If return_value is not set
            or is not iterable, a TypeError is raised.

            :return: An iterator over return_value.

            :raises TypeError: If return_value is None or not iterable.

            Example::

                mock = Mock(return_value=[1, 2, 3])
                list(mock)  # Returns [1, 2, 3]
                
                for item in mock:
                    print(item)  # Prints 1, 2, 3
                
                mock = Mock()
                # list(mock)  # Raises TypeError
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
            Checks if the mock object contains the given item.
            
            This method delegates to 'item in return_value'. If return_value is not set
            or doesn't support containment checks, a TypeError is raised.

            :param item: The item to check for.

            :return: True if item is in return_value, False otherwise.

            :raises TypeError: If return_value is None or doesn't support 'in' operator.

            Example::

                mock = Mock(return_value=[1, 2, 3])
                2 in mock  # True
                5 in mock  # False
                
                mock = Mock(return_value={'key': 'value'})
                'key' in mock  # True
                
                mock = Mock()
                # 'x' in mock  # Raises TypeError
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


class PropertyMock(Mock):
    """
        A mock object specifically designed for mocking property getters and setters.
        
        PropertyMock extends Mock to provide separate tracking and configuration for
        property getter and setter operations. This allows you to:
        - Configure what value the property returns when accessed (getter)
        - Configure what happens when the property is set (setter)
        - Track all getter accesses separately from setter calls
        - Verify getter and setter interactions independently
        
        Example Usage::

            from ccai.testbase.mocking import PropertyMock

            # Create a property mock
            prop_mock = PropertyMock(getter_return_value="initial_value")
            
            # Access the property (getter)
            value = prop_mock.get()  # Returns "initial_value"
            
            # Set the property (setter)
            prop_mock.set("new_value")
            
            # Verify interactions
            prop_mock.assert_getter_called()
            prop_mock.assert_setter_called_with("new_value")
            
            # Configure setter side effect
            def on_set(value):
                print(f"Property set to: {value}")
            
            prop_mock = PropertyMock(setter_side_effect=on_set)
            prop_mock.set("test")  # Prints: "Property set to: test"
    """

    def __init__(self, *, getter_return_value: Optional[Any] = None,
                 getter_side_effect: Optional[Union[Callable, SideEffect]] = None,
                 setter_side_effect: Optional[Union[Callable, SideEffect]] = None,
                 mock_owner: Optional["Mock"] = None):
        """
            Creates a property mock object with separate getter and setter configuration.

            :param getter_return_value: The value to return when the property is accessed (getter).
                Defaults to None.
            :param getter_side_effect: A callable or SideEffect instance to execute when the
                property is accessed (getter). If provided, its return value is used instead
                of getter_return_value. Defaults to None.
            :param setter_side_effect: A callable or SideEffect instance to execute when the
                property is set (setter). The callable receives the value being set as its
                argument. Defaults to None.
            :param mock_owner: The parent Mock object if this is a child mock. Used for
                tracking nested mock hierarchies. Defaults to None.

            :raises TypeError: If getter_side_effect or setter_side_effect is provided but
                is neither a SideEffect instance nor a callable.

            Example::

                from ccai.testbase.mocking import PropertyMock

                # Simple property mock with return value
                prop = PropertyMock(getter_return_value=42)
                value = prop.get()  # Returns 42
                
                # Property mock with dynamic getter
                counter = [0]
                def increment():
                    counter[0] += 1
                    return counter[0]
                
                prop = PropertyMock(getter_side_effect=increment)
                print(prop.get())  # Returns 1
                print(prop.get())  # Returns 2
                
                # Property mock with setter tracking
                def validate_setter(value):
                    if not isinstance(value, int):
                        raise ValueError("Must be an integer")
                
                prop = PropertyMock(setter_side_effect=validate_setter)
                prop.set(42)  # OK
                # prop.set("string")  # Raises ValueError
        """
        # Initialize base Mock with Property type
        super().__init__(
            return_value=getter_return_value,
            side_effect=getter_side_effect,
            mtype=MockType.Property,
            mock_owner=mock_owner,
            recursive=False,
            strict_attrs=False
        )
        
        # Store setter configuration separately
        self._setter_side_effect: Optional[SideEffect] = None
        if setter_side_effect is not None:
            if isinstance(setter_side_effect, SideEffect):
                self._setter_side_effect = setter_side_effect
            elif callable(setter_side_effect):
                self._setter_side_effect = SideEffect(setter_side_effect)
            else:
                raise TypeError(
                    f"setter_side_effect must be a SideEffect instance or a callable, "
                    f"not {type(setter_side_effect).__name__}"
                )
        
        # Separate tracking for getter and setter operations
        self._getter_call_count = 0
        self._getter_call_args_list: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []
        
        self._setter_call_count = 0
        self._setter_call_args: Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]] = None
        self._setter_call_args_list: List[Tuple[Tuple[Any, ...], Dict[str, Any]]] = []

    @property
    def getter_call_count(self) -> int:
        """
            Returns the number of times the property getter was accessed.
            
            :return: An integer representing the total getter access count.
        """
        return self._getter_call_count

    @property
    def getter_call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all getter accesses.
            
            :return: A list of (args, kwargs) tuples in chronological order.
                For property getters, args and kwargs are typically empty.
        """
        return self._getter_call_args_list

    @property
    def setter_call_count(self) -> int:
        """
            Returns the number of times the property setter was called.
            
            :return: An integer representing the total setter call count.
        """
        return self._setter_call_count

    @property
    def setter_call_args(self) -> Optional[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns the arguments of the last setter call.
            
            :return: A tuple of (args, kwargs) from the most recent setter call,
                or None if the setter has never been called.
        """
        return self._setter_call_args

    @property
    def setter_call_args_list(self) -> List[Tuple[Tuple[Any, ...], Dict[str, Any]]]:
        """
            Returns a list of all setter calls.
            
            :return: A list of (args, kwargs) tuples in chronological order.
        """
        return self._setter_call_args_list

    @property
    def setter_side_effect(self) -> Optional[SideEffect]:
        """
            Returns the setter side effect.
            
            :return: The SideEffect instance for the setter, or None if not configured.
        """
        return self._setter_side_effect

    def get(self, *args, **kwargs) -> Any:
        """
            Simulates accessing the property (getter operation).
            
            This method records the getter access and returns either the configured
            getter_return_value or the result of executing the getter_side_effect.
            
            :param args: Optional positional arguments (typically not used for properties).
            :param kwargs: Optional keyword arguments (typically not used for properties).
            
            :return: The configured getter_return_value, or if getter_side_effect is set,
                the result of executing the getter_side_effect.

            Example::

                prop = PropertyMock(getter_return_value="value")
                result = prop.get()  # Returns "value"
                
                # With side effect
                prop = PropertyMock(getter_side_effect=lambda: "dynamic")
                result = prop.get()  # Returns "dynamic"
        """
        # Record the getter access
        self._getter_call_count += 1
        self._getter_call_args_list.append((args, kwargs))
        
        # Also record in the base Mock's call tracking for compatibility
        self._mock_context._record_call(*args, **kwargs)
        
        # Return value determination
        rtnval = self._mock_context.return_value
        
        if self._mock_context.side_effect is not None:
            rtnval = self._mock_context.side_effect(*args, **kwargs)
        
        return rtnval

    def set(self, value: Any, *args, **kwargs) -> None:
        """
            Simulates setting the property (setter operation).
            
            This method records the setter call and executes the setter_side_effect
            if configured.
            
            :param value: The value being set on the property.
            :param args: Additional positional arguments (typically not used).
            :param kwargs: Additional keyword arguments (typically not used).

            Example::

                prop = PropertyMock()
                prop.set("new_value")
                
                # Verify the setter was called
                prop.assert_setter_called_with("new_value")
                
                # With side effect
                def validate(val):
                    if val < 0:
                        raise ValueError("Must be non-negative")
                
                prop = PropertyMock(setter_side_effect=validate)
                prop.set(10)  # OK
                # prop.set(-1)  # Raises ValueError
        """
        # Record the setter call
        self._setter_call_count += 1
        self._setter_call_args = ((value,) + args, kwargs)
        self._setter_call_args_list.append(((value,) + args, kwargs))
        
        # Execute setter side effect if configured
        if self._setter_side_effect is not None:
            self._setter_side_effect(value, *args, **kwargs)

    def __call__(self, *args, **kwargs) -> Any:
        """
            Calling the PropertyMock directly acts as a getter access.
            
            This allows PropertyMock to be used in contexts where the property
            might be called as a function.
            
            :param args: Positional arguments for the getter.
            :param kwargs: Keyword arguments for the getter.
            
            :return: The getter return value.
        """
        return self.get(*args, **kwargs)

    def configure_getter(self, *, return_value: Optional[Any] = ...,
                         side_effect: Optional[Union[Callable, SideEffect]] = ...) -> "PropertyMock":
        """
            Configures the getter behavior.
            
            :param return_value: The value to return when the property is accessed.
            :param side_effect: A callable or SideEffect to execute when accessed.
            
            :return: This PropertyMock instance for fluent chaining.

            Example::

                prop = PropertyMock()
                prop.configure_getter(return_value=42)
                print(prop.get())  # Returns 42
                
                # Fluent chaining
                prop.configure_getter(return_value=100).configure_setter(
                    side_effect=lambda v: print(f"Set to {v}")
                )
        """
        if return_value is not ...:
            self._mock_context._return_value = return_value
        
        if side_effect is not ...:
            if side_effect is not None and not isinstance(side_effect, SideEffect):
                if callable(side_effect):
                    self._mock_context._side_effect = SideEffect(side_effect)
                else:
                    raise TypeError(
                        f"getter side_effect must be a SideEffect instance or a callable, "
                        f"not {type(side_effect).__name__}"
                    )
            else:
                self._mock_context._side_effect = side_effect
        
        return self

    def configure_setter(self, *, side_effect: Optional[Union[Callable, SideEffect]] = ...) -> "PropertyMock":
        """
            Configures the setter behavior.
            
            :param side_effect: A callable or SideEffect to execute when the property is set.
                The callable receives the value being set as its first argument.
            
            :return: This PropertyMock instance for fluent chaining.

            Example::

                prop = PropertyMock()
                
                def on_set(value):
                    print(f"Property set to: {value}")
                
                prop.configure_setter(side_effect=on_set)
                prop.set("test")  # Prints: "Property set to: test"
        """
        if side_effect is not ...:
            if side_effect is not None and not isinstance(side_effect, SideEffect):
                if callable(side_effect):
                    self._setter_side_effect = SideEffect(side_effect)
                else:
                    raise TypeError(
                        f"setter side_effect must be a SideEffect instance or a callable, "
                        f"not {type(side_effect).__name__}"
                    )
            else:
                self._setter_side_effect = side_effect
        
        return self

    def assert_getter_called(self) -> None:
        """
            Assert that the property getter was accessed at least once.
            
            :raises AssertionError: If the getter was never accessed.

            Example::

                prop = PropertyMock(getter_return_value="value")
                # prop.assert_getter_called()  # Raises AssertionError
                
                prop.get()
                prop.assert_getter_called()  # Passes
        """
        if self._getter_call_count == 0:
            raise AssertionError("Expected property getter to have been accessed.")

    def assert_getter_called_once(self) -> None:
        """
            Assert that the property getter was accessed exactly once.
            
            :raises AssertionError: If the getter was not accessed exactly once.

            Example::

                prop = PropertyMock(getter_return_value="value")
                prop.get()
                prop.assert_getter_called_once()  # Passes
                
                prop.get()
                # prop.assert_getter_called_once()  # Raises AssertionError
        """
        if self._getter_call_count != 1:
            raise AssertionError(
                f"Expected property getter to have been accessed once. "
                f"Accessed {self._getter_call_count} times."
            )

    def assert_setter_called(self) -> None:
        """
            Assert that the property setter was called at least once.
            
            :raises AssertionError: If the setter was never called.

            Example::

                prop = PropertyMock()
                # prop.assert_setter_called()  # Raises AssertionError
                
                prop.set("value")
                prop.assert_setter_called()  # Passes
        """
        if self._setter_call_count == 0:
            raise AssertionError("Expected property setter to have been called.")

    def assert_setter_called_once(self) -> None:
        """
            Assert that the property setter was called exactly once.
            
            :raises AssertionError: If the setter was not called exactly once.

            Example::

                prop = PropertyMock()
                prop.set("value")
                prop.assert_setter_called_once()  # Passes
                
                prop.set("another")
                # prop.assert_setter_called_once()  # Raises AssertionError
        """
        if self._setter_call_count != 1:
            raise AssertionError(
                f"Expected property setter to have been called once. "
                f"Called {self._setter_call_count} times."
            )

    def assert_setter_called_with(self, value: Any, *args, **kwargs) -> None:
        """
            Assert that the last setter call was with the specified value.
            
            :param value: The expected value that was set.
            :param args: Additional expected positional arguments.
            :param kwargs: Additional expected keyword arguments.
            
            :raises AssertionError: If the setter was never called or the last call
                doesn't match the expected arguments.

            Example::

                prop = PropertyMock()
                prop.set("test_value")
                prop.assert_setter_called_with("test_value")  # Passes
                
                prop.set("other_value")
                # prop.assert_setter_called_with("test_value")  # Raises AssertionError
        """
        if self._setter_call_args is None:
            raise AssertionError(
                "Expected property setter to have been called with specific arguments, "
                "but it was not called."
            )
        
        expected_args = (value,) + args
        last_args, last_kwargs = self._setter_call_args
        
        if last_args != expected_args or last_kwargs != kwargs:
            raise AssertionError(
                f"Expected setter call with ({value!r}, *{args!r}, **{kwargs!r})\n"
                f"Actual last call: ({last_args!r}, **{last_kwargs!r})"
            )

    def assert_setter_called_once_with(self, value: Any, *args, **kwargs) -> None:
        """
            Assert that the setter was called exactly once with the specified value.
            
            :param value: The expected value that was set.
            :param args: Additional expected positional arguments.
            :param kwargs: Additional expected keyword arguments.
            
            :raises AssertionError: If the setter was not called exactly once or
                the call doesn't match the expected arguments.

            Example::

                prop = PropertyMock()
                prop.set("test_value")
                prop.assert_setter_called_once_with("test_value")  # Passes
        """
        self.assert_setter_called_once()
        self.assert_setter_called_with(value, *args, **kwargs)

    def assert_setter_any_call(self, value: Any, *args, **kwargs) -> None:
        """
            Assert that the setter was called at least once with the specified value.
            
            :param value: The expected value that was set.
            :param args: Additional expected positional arguments.
            :param kwargs: Additional expected keyword arguments.
            
            :raises AssertionError: If no setter call matches the expected arguments.

            Example::

                prop = PropertyMock()
                prop.set("first")
                prop.set("second")
                prop.set("third")
                
                prop.assert_setter_any_call("second")  # Passes
                # prop.assert_setter_any_call("fourth")  # Raises AssertionError
        """
        expected_args = (value,) + args
        
        for call_args, call_kwargs in self._setter_call_args_list:
            if call_args == expected_args and call_kwargs == kwargs:
                return
        
        raise AssertionError(
            f"Expected at least one setter call with ({value!r}, *{args!r}, **{kwargs!r})\n"
            f"Actual calls: {self._setter_call_args_list}"
        )

    def reset(self) -> None:
        """
            Resets all tracking state for both getter and setter.
            
            This clears:
            - Getter call count and history
            - Setter call count and history
            - Base Mock call tracking

            Example::

                prop = PropertyMock(getter_return_value="value")
                prop.get()
                prop.set("new")
                
                prop.reset()
                
                print(prop.getter_call_count)  # 0
                print(prop.setter_call_count)  # 0
        """
        # Reset getter tracking
        self._getter_call_count = 0
        self._getter_call_args_list = []
        
        # Reset setter tracking
        self._setter_call_count = 0
        self._setter_call_args = None
        self._setter_call_args_list = []
        
        # Reset base Mock tracking
        self._mock_context.reset()

    def __repr__(self) -> str:
        """
            Returns a string representation of the PropertyMock.
            
            :return: A string showing the getter return value and setter side effect.
        """
        return (
            f"PropertyMock(getter_return_value={self._mock_context.return_value!r}, "
            f"getter_side_effect={self._mock_context.side_effect!r}, "
            f"setter_side_effect={self._setter_side_effect!r})"
        )


class AsyncMock(Mock):
    """
        An async mock object that can be awaited.
        
        AsyncMock extends Mock to support async/await patterns. When awaited, it returns
        the configured return_value or executes the async side_effect. It tracks all calls
        made to it, including async calls, and provides the same assertion methods as Mock.

        Example Usage::

            from ccai.testbase.mocking import AsyncMock

            # Basic async mock with return value
            async_mock = AsyncMock(return_value=42)
            result = await async_mock()  # Returns 42
            
            # Async mock with async side effect
            async def fetch_data(url):
                await asyncio.sleep(0.1)
                return {"url": url, "data": "response"}
            
            async_mock = AsyncMock(side_effect=fetch_data)
            result = await async_mock("http://example.com")  # Returns {"url": "http://example.com", "data": "response"}
            
            # Verify interactions
            async_mock = AsyncMock()
            await async_mock(1, 2, key="value")
            async_mock.assert_called_once_with(1, 2, key="value")
            
            # Configure through context
            async_mock = AsyncMock()
            ctx = async_mock.mock_context()
            ctx.configure(return_value={"status": "ok"})
    """

    def __init__(self, *, mock_attributes: Optional[Dict[str, Any]] = None, return_value: Optional[Any] = None,
                 reference: Optional[Any] = None, mtype: Optional[MockType] = None, mock_owner: Optional[Any] = None, 
                 side_effect: Optional[Union[Callable[..., Coroutine], AsyncSideEffect]] = None,
                 recursive: bool = False, strict_attrs: bool = False):
        """
            Creates an async mock object with the given attributes and configuration.

            :param mock_attributes: A dictionary of pre-defined attributes for the mock.
                These attributes can be accessed on the mock object. Defaults to an empty dict.
            :param return_value: The value to return when the mock is awaited. Defaults to None.
            :param reference: The original object being mocked. Used for type determination
                and restoration during patch deactivation. Defaults to None.
            :param mtype: Explicit MockType for this mock. If not provided, the type is
                determined from the reference parameter. Defaults to MockType.Generic.
            :param mock_owner: The parent Mock object if this is a child mock. Used for
                tracking nested mock hierarchies. Defaults to None.
            :param side_effect: An async callable or AsyncSideEffect instance to execute when 
                the mock is awaited. If an async callable is provided, it will be wrapped in 
                an AsyncSideEffect. Defaults to None.
            :param recursive: If True, accessing undefined attributes will automatically
                create and return new AsyncMock objects. Defaults to False.
            :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
                Attempting to access undefined attributes raises AttributeError.
                Defaults to False.

            :raises TypeError: If side_effect is provided but is neither an AsyncSideEffect instance
                nor an async callable. Also raised if recursive or strict_attrs are not boolean values.

            Example::

                from ccai.testbase.mocking import AsyncMock, MockType

                # Simple async mock
                async_mock = AsyncMock()
                
                # Async mock with return value
                async_mock = AsyncMock(return_value=42)
                result = await async_mock()  # Returns 42
                
                # Async mock with pre-defined attributes
                async_mock = AsyncMock(mock_attributes={'id': 1, 'name': 'test'})
                print(async_mock.id)  # 1
                
                # Recursive async mock for chained access
                async_mock = AsyncMock(recursive=True)
                async_mock.a.b.c.return_value = "deep"
        """
        if mock_attributes is None:
            mock_attributes = {}

        if mtype is None:
            mtype = MockType.Generic
            if reference is not None:
                mtype = MockContext.determine_mock_type(reference if reference is not ... else None)

        # Store the async side effect separately - we'll handle it in __call__
        self._async_side_effect = None
        if side_effect is not None:
            if isinstance(side_effect, AsyncSideEffect):
                self._async_side_effect = side_effect
            elif asyncio.iscoroutinefunction(side_effect):
                self._async_side_effect = AsyncSideEffect(side_effect)
            else:
                raise TypeError(
                    f"AsyncMock side_effect must be an AsyncSideEffect instance or a coroutine function, "
                    f"not {type(side_effect).__name__}"
                )

        # Initialize the base Mock without side_effect (we handle it ourselves)
        super().__init__(
            mock_attributes=mock_attributes,
            reference=reference,
            return_value=return_value,
            mtype=mtype,
            side_effect=None,  # We handle async side_effect separately
            mock_owner=mock_owner,
            recursive=recursive,
            strict_attrs=strict_attrs
        )

        return

    @property
    def async_side_effect(self) -> Optional[AsyncSideEffect]:
        """
            Returns the async side effect of this mock.
            
            :return: The AsyncSideEffect instance that will be executed when the mock is awaited,
                or None if no async side effect is configured.
        """
        return self._async_side_effect

    def configure(self, *, return_value: Optional[Any] = ..., 
                  side_effect: Optional[Union[Callable[..., Coroutine], AsyncSideEffect]] = ...,
                  recursive: Optional[bool] = ..., strict_attrs: Optional[bool] = ...):
        """
            Configures the async mock's behavior.
            
            This method allows updating multiple mock settings at once. It uses the Ellipsis (...)
            as a sentinel value to distinguish between an argument being explicitly passed
            (even as None) and not being provided at all.
            
            :param return_value: The value to return when the mock is awaited. Pass None to
                explicitly set return_value to None.
            :param side_effect: An async callable or AsyncSideEffect instance to execute when 
                the mock is awaited. If an async callable is provided, it will be wrapped in 
                an AsyncSideEffect. Pass None to clear the side effect.
            :param recursive: If True, accessing undefined attributes will create new AsyncMock
                objects. If False, accessing undefined attributes will raise AttributeError.
            :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
            
            :return: The AsyncMock instance for fluent method chaining.
            
            :raises TypeError: If side_effect is provided but is neither an AsyncSideEffect instance
                nor an async callable.

            Example::

                async_mock = AsyncMock()
                
                # Configure multiple settings at once
                async_mock.configure(return_value=42, recursive=True)
                
                # Fluent chaining
                async_mock.configure(return_value="hello").configure(recursive=True)
                
                # Clear side effect by passing None
                async_mock.configure(side_effect=None)
                
                # Configure with an async side effect
                async def my_effect(x):
                    return x * 2
                async_mock.configure(side_effect=my_effect)
        """
        if return_value is not ...:
            self._mock_context._return_value = return_value
        
        if side_effect is not ...:
            if side_effect is None:
                self._async_side_effect = None
            elif isinstance(side_effect, AsyncSideEffect):
                self._async_side_effect = side_effect
            elif asyncio.iscoroutinefunction(side_effect):
                self._async_side_effect = AsyncSideEffect(side_effect)
            else:
                raise TypeError(
                    f"AsyncMock.configure: side_effect must be an AsyncSideEffect instance or a coroutine function, "
                    f"not {type(side_effect).__name__}"
                )

        if recursive is not ...:
            if not isinstance(recursive, bool):
                raise TypeError("configure: 'recursive' must be a boolean value.")
            self._mock_context._recursive = recursive

        if strict_attrs is not ...:
            if not isinstance(strict_attrs, bool):
                raise TypeError("configure: 'strict_attrs' must be a boolean value.")
            self._mock_context._strict_attrs = strict_attrs
        
        return self

    def __call__(self, *args, **kwargs) -> Coroutine:
        """
            Returns a coroutine that, when awaited, returns the configured value.
            
            This method records the call and returns a coroutine. When the coroutine
            is awaited, it returns the configured return_value or executes the async
            side_effect.

            :param args: Positional arguments for the call.
            :param kwargs: Keyword arguments for the call.

            :return: A coroutine that returns the configured return_value or side_effect result.

            Example::

                async_mock = AsyncMock(return_value=42)
                result = await async_mock(1, 2)  # Returns 42
                
                # With async side effect
                async def effect(x, y):
                    return x + y
                async_mock = AsyncMock(side_effect=effect)
                result = await async_mock(1, 2)  # Returns 3
        """
        # Record the call for tracking
        self._mock_context._record_call(*args, **kwargs)
        
        # Return a coroutine that will be awaited
        async def _async_return():
            if self._async_side_effect is not None:
                return await self._async_side_effect(*args, **kwargs)
            return self._mock_context.return_value
        
        return _async_return()

    def __await__(self):
        """
            Makes the AsyncMock directly awaitable.
            
            This allows using `await async_mock` without calling it first.
            When awaited directly, it behaves as if called with no arguments.

            :return: An iterator for the coroutine.

            Example::

                async_mock = AsyncMock(return_value="result")
                result = await async_mock  # Returns "result"
        """
        return self().__await__()

    def __getattr__(self, name: str):
        """
            Gets an attribute of the async mock object.
            
            This method handles attribute access with the following priority:
            1. Raises AttributeError for underscore-prefixed names (private attributes)
            2. Returns assertion methods from the context (assert_called, etc.)
            3. Returns stored attributes from mock_attributes
            4. Creates child AsyncMocks when recursive=True
            5. Raises AttributeError when strict_attrs=True or recursive=False

            :param name: The name of the attribute to get.
            
            :return: The attribute value, assertion method, or a new child AsyncMock.

            :raises AttributeError: If the attribute starts with underscore, or if
                the attribute doesn't exist and (strict_attrs=True or recursive=False).
        """
        # Block access to private/internal attributes
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Delegate assertion methods to MockContext
        if hasattr(self._mock_context, name) and callable(getattr(self._mock_context, name)) and name.startswith("assert_"):
            return getattr(self._mock_context, name)

        try:
            return self._mock_context.get_attribute(name)
        except AttributeError:
            if self._mock_context._strict_attrs:
                raise AttributeError(
                    f"'{self._mock_context._mock_type}' object has no attribute '{name}' (strict_attrs is True)"
                )

            if self._mock_context.recursive:
                # Create child AsyncMock with same recursive and strict_attrs settings
                new_mock = AsyncMock(mock_owner=self, recursive=self._mock_context.recursive,
                                     strict_attrs=self._mock_context._strict_attrs)
                self._mock_context.set_attribute(name, new_mock)
                return new_mock
            
            raise

    def __setattr__(self, name: str, value: Any):
        """
            Sets an attribute on the async mock object.
            
            This method handles attribute assignment with special cases:
            1. Underscore-prefixed names are set directly on the object
            2. 'return_value', 'side_effect', 'recursive' configure the mock
            3. Other attributes are stored in mock_attributes
            4. When strict_attrs=True, only pre-defined attributes can be set

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.

            :raises AttributeError: If strict_attrs=True and the attribute is not
                pre-defined and not a special mock configuration attribute.
        """
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            if self._mock_context._strict_attrs and \
               name not in ["return_value", "side_effect", "recursive"] and \
               not self._mock_context.has_attribute(name):
                raise AttributeError(
                    f"Cannot set new attribute '{name}' on async mock with strict_attrs=True "
                    f"unless it's a pre-defined attribute or mock config."
                )

            if name == "return_value":
                self._mock_context._return_value = value
            elif name == "side_effect":
                self.configure(side_effect=value)
            elif name == "recursive":
                self._mock_context._recursive = value
            else:
                self._mock_context.set_attribute(name, value)

        return

    def __repr__(self):
        """
            Returns a string representation of the async mock object.
            
            :return: A string showing the mock's return_value and async_side_effect configuration.
        """
        return f"AsyncMock(return_value={self._mock_context.return_value}, async_side_effect={self._async_side_effect})"


class PatchType(str, enum.Enum):
    """
        Enumeration defining the types of targets that can be patched.
        
        - Module: For patching attributes on module objects
        - Class: For patching attributes on class objects
        - Instance: For patching attributes on object instances
    """

    Module = "Module"
    Class = "Class"
    Instance = "Instance"


class Patch:
    """
        Manages the lifecycle of patching an attribute with a mock object.
        
        The Patch class provides a way to temporarily replace an attribute on a module,
        class, or instance with a mock object. It supports both explicit activation/deactivation
        and context manager usage for automatic cleanup.

        Example Usage::

            from ccai.testbase.mocking import Patch, PatchType, create_module_patch
            import some_module

            # Using factory function (recommended)
            patch = create_module_patch(some_module, 'function_name')
            mock = patch.activate()
            mock.return_value = "mocked"
            # ... use the mock ...
            patch.deactivate()  # Restores original

            # Using context manager (recommended for automatic cleanup)
            with create_module_patch(some_module, 'function_name') as mock:
                mock.return_value = "mocked"
                result = some_module.function_name()  # Returns "mocked"
            # Original is automatically restored

            # Direct instantiation
            patch = Patch(some_module, 'attr_name', PatchType.Module)
            with patch as mock:
                mock.configure(return_value=42)
    """

    def __init__(self, owner: Any, target_name: str, patch_type: PatchType, recursive: bool = False,
                 strict_attrs: bool = False):
        """
            Creates a Patch instance for patching an attribute.
            
            :param owner: The module, class, or instance that owns the attribute to patch.
            :param target_name: The name of the attribute to patch.
            :param patch_type: The type of patch (Module, Class, or Instance).
            :param recursive: If True, the created mock will automatically create child
                mocks for undefined attribute access. Defaults to False.
            :param strict_attrs: If True, the created mock will only allow access to
                pre-defined attributes. Defaults to False.
            
            :raises TypeError: If the owner type doesn't match the patch_type:
                - Class owner requires PatchType.Class
                - Module owner requires PatchType.Module
                - Instance owner requires PatchType.Instance

            Example::

                import some_module

                # Patch a module attribute
                patch = Patch(some_module, 'function', PatchType.Module)
                
                # Patch a class attribute
                patch = Patch(MyClass, 'method', PatchType.Class)
                
                # Patch an instance attribute
                obj = MyClass()
                patch = Patch(obj, 'attribute', PatchType.Instance)
        """
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
            Returns the owner of the patch (module, class, or instance).
            
            :return: The object that owns the attribute being patched.
        """
        return self._owner
    

    @property
    def patch_type(self) -> PatchType:
        """
            Returns the type of the patch.
            
            :return: A PatchType enumeration value (Module, Class, or Instance).
        """
        return self._patch_type


    @property
    def target_name(self) -> str:
        """
            Returns the name of the attribute being patched.
            
            :return: The attribute name as a string.
        """
        return self._target_name

    
    def __enter__(self) -> Mock:
        """
            Enters the patch context and activates the patch.
            
            :return: The Mock object that replaced the target attribute.

            Example::

                with create_module_patch(module, 'func') as mock:
                    mock.return_value = 42
                    # module.func is now the mock
        """
        mock = self.activate()

        return mock


    def __exit__(self, exc_type: Type[BaseException], exc_val: BaseException, exc_tb: types.TracebackType) -> bool:
        """
            Exits the patch context and deactivates the patch.
            
            The original attribute is restored regardless of whether an exception occurred.
            Exceptions are not suppressed.
            
            :param exc_type: The type of the exception, if any.
            :param exc_val: The exception instance, if any.
            :param exc_tb: The traceback, if any.

            :return: False to indicate that exceptions should not be suppressed.
        """

        self.deactivate()

        return False
    

    def activate(self) -> Mock:
        """
            Activates the patch by replacing the target attribute with a mock.
            
            This method creates a mock (if not already created), stores the original
            attribute value, and replaces the attribute with the mock.
            
            :return: The Mock object that replaced the target attribute.
            
            :raises ValueError: If the target attribute is already a Mock from this
                framework (to prevent double-patching).

            Example::

                patch = create_module_patch(module, 'function')
                mock = patch.activate()
                mock.return_value = "mocked"
                
                result = module.function()  # Returns "mocked"
                
                patch.deactivate()  # Restore original
        """

        mock = self.mock()

        target = getattr(self._owner, self._target_name)
        if isinstance(target, Mock) and hasattr(target, '_mock_context') and isinstance(target._mock_context, MockContext):
            raise ValueError(f"Cannot patch '{self._target_name}' because it is already a Mock object from this framework.")

        setattr(self._owner, self._target_name, mock)

        return self._mock
    

    def deactivate(self):
        """
            Deactivates the patch by restoring the original attribute.
            
            If the patch was never activated, this method does nothing.

            Example::

                patch = create_module_patch(module, 'function')
                mock = patch.activate()
                # ... use mock ...
                patch.deactivate()  # Original function is restored
        """

        if self._mock is not None:
            target = self._mock.mock_context().reference
            # Restore the original attribute, even if it was None
            setattr(self._owner, self._target_name, target)

        return


    def mock(self) -> Mock:
        """
            Returns the mock object associated with this patch.
            
            If the mock has not been created yet, it will be created with the target
            attribute as its reference. The mock inherits the recursive and strict_attrs
            settings from the patch.
            
            :return: The Mock object for this patch.

            Example::

                patch = create_module_patch(module, 'function')
                
                # Get mock before activation to configure it
                mock = patch.mock()
                mock.return_value = 42
                
                # Then activate
                patch.activate()
        """

        if self._mock is None:

            target = getattr(self._owner, self._target_name)
            # Let Mock determine its type from the reference.
            # The reference (original target) will be stored in the Mock's MockContext.
            self._mock = Mock(reference=target, recursive=self._recursive, strict_attrs=self._strict_attrs)

        return self._mock



def create_module_patch(module: types.ModuleType, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch for replacing a module attribute with a mock object.
        
        This is the recommended factory function for patching module-level attributes
        such as functions, classes, or variables defined in a module.

        :param module: The module containing the attribute to patch. Must be a module object.
        :param target_name: The name of the attribute to patch. Must be a string.
        :param recursive: If True, the created mock will automatically create child mocks
            for undefined attribute access. Defaults to False.
        :param strict_attrs: If True, the created mock will only allow access to pre-defined
            attributes. Defaults to False.

        :return: A Patch object that can be used to activate/deactivate the patch or
            used as a context manager.
        
        :raises TypeError: If module is not a module object or target_name is not a string.

        Example::

            import some_module
            from ccai.testbase.mocking import create_module_patch

            # Basic usage with context manager
            with create_module_patch(some_module, 'some_function') as mock:
                mock.return_value = "mocked result"
                result = some_module.some_function()  # Returns "mocked result"
            # Original function is restored here

            # Manual activation/deactivation
            patch = create_module_patch(some_module, 'some_function')
            mock = patch.activate()
            mock.return_value = 42
            # ... run tests ...
            patch.deactivate()

            # With recursive mocks
            with create_module_patch(some_module, 'client', recursive=True) as mock:
                mock.database.query.return_value = ["item1", "item2"]
    """
    if not isinstance(module, types.ModuleType):
        raise TypeError(f"module must be a module, not {type(module)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(module, target_name, PatchType.Module, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope


def create_class_patch(cls: Type, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch for replacing a class attribute with a mock object.
        
        This is the recommended factory function for patching class-level attributes
        such as class methods, static methods, or class variables.

        :param cls: The class containing the attribute to patch. Must be a class (type).
        :param target_name: The name of the attribute to patch. Must be a string.
        :param recursive: If True, the created mock will automatically create child mocks
            for undefined attribute access. Defaults to False.
        :param strict_attrs: If True, the created mock will only allow access to pre-defined
            attributes. Defaults to False.

        :return: A Patch object that can be used to activate/deactivate the patch or
            used as a context manager.
        
        :raises TypeError: If cls is not a class or target_name is not a string.

        Example::

            from ccai.testbase.mocking import create_class_patch

            class MyService:
                @classmethod
                def fetch_data(cls):
                    return "real data"

            # Patch a class method
            with create_class_patch(MyService, 'fetch_data') as mock:
                mock.return_value = "mocked data"
                result = MyService.fetch_data()  # Returns "mocked data"
            # Original method is restored here

            # Manual activation/deactivation
            patch = create_class_patch(MyService, 'fetch_data')
            mock = patch.activate()
            mock.return_value = "test data"
            # ... run tests ...
            patch.deactivate()
    """
    if not isinstance(cls, type):
        raise TypeError(f"cls must be a class, not {type(cls)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(cls, target_name, PatchType.Class, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope


def create_instance_patch(instance: object, target_name: str, recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a patch for replacing an instance attribute with a mock object.
        
        This is the recommended factory function for patching instance-level attributes
        such as instance methods or instance variables on a specific object.

        :param instance: The object instance containing the attribute to patch.
        :param target_name: The name of the attribute to patch. Must be a string.
        :param recursive: If True, the created mock will automatically create child mocks
            for undefined attribute access. Defaults to False.
        :param strict_attrs: If True, the created mock will only allow access to pre-defined
            attributes. Defaults to False.

        :return: A Patch object that can be used to activate/deactivate the patch or
            used as a context manager.
        
        :raises TypeError: If target_name is not a string.

        Example::

            from ccai.testbase.mocking import create_instance_patch

            class MyService:
                def process(self):
                    return "real processing"

            service = MyService()

            # Patch an instance method
            with create_instance_patch(service, 'process') as mock:
                mock.return_value = "mocked processing"
                result = service.process()  # Returns "mocked processing"
            # Original method is restored here

            # Manual activation/deactivation
            patch = create_instance_patch(service, 'process')
            mock = patch.activate()
            mock.return_value = "test result"
            # ... run tests ...
            patch.deactivate()

            # Patching with recursive mocks
            with create_instance_patch(service, 'client', recursive=True) as mock:
                mock.api.get.return_value = {"data": "value"}
    """
    if not isinstance(instance, object):
        raise TypeError(f"instance must be an object, not {type(instance)}")

    if not isinstance(target_name, str):
        raise TypeError(f"'target_name' must be a string, not {type(target_name)}")

    patch_scope = Patch(instance, target_name, PatchType.Instance, recursive=recursive, strict_attrs=strict_attrs)

    return patch_scope


class SpecMock(Mock):
    """
        A mock object that validates attribute access and method calls against a specification class.
        
        SpecMock extends Mock to provide spec-based validation:
        - Only attributes defined in the spec class can be accessed
        - Method calls are validated against the spec's method signatures
        - Setting attributes is restricted to those defined in the spec
        
        This is useful for ensuring that mocks accurately represent the interface
        of the objects they're replacing, catching typos and interface mismatches
        early in testing.

        Example Usage::

            from ccai.testbase.mocking import SpecMock, create_spec_mock

            class DatabaseClient:
                def __init__(self):
                    self.connection_string = ""
                
                def connect(self, host: str, port: int) -> bool:
                    pass
                
                def query(self, sql: str) -> list:
                    pass

            # Create a spec-based mock
            mock_db = create_spec_mock(DatabaseClient)
            
            # Valid attribute access
            mock_db.connect.return_value = True
            mock_db.query.return_value = [{"id": 1}]
            
            # Invalid attribute access raises SpecViolationError
            # mock_db.nonexistent  # Raises SpecViolationError
            
            # Method signature validation
            mock_db.connect("localhost", 5432)  # Valid
            # mock_db.connect("localhost", "invalid")  # Raises SpecViolationError if validate_signatures=True
    """

    def __init__(self, spec: Type, *, mock_attributes: Optional[Dict[str, Any]] = None,
                 return_value: Optional[Any] = None, side_effect: Optional[Union[Callable, SideEffect]] = None,
                 validate_signatures: bool = False, spec_set: bool = False):
        """
            Creates a spec-based mock object.

            :param spec: The specification class that defines the allowed interface.
                All attribute access and method calls will be validated against this class.
            :param mock_attributes: A dictionary of pre-defined attributes for the mock.
                These must be valid attributes according to the spec.
            :param return_value: The value to return when the mock is called. Defaults to None.
            :param side_effect: A callable or SideEffect instance to execute when the mock
                is called. Defaults to None.
            :param validate_signatures: If True, method calls will be validated against
                the spec's method signatures. This includes checking argument types
                if type hints are available. Defaults to False.
            :param spec_set: If True, only attributes that exist on the spec can be set.
                If False, new attributes can be set but accessing undefined attributes
                still raises SpecViolationError. Defaults to False.

            :raises TypeError: If spec is not a class.

            Example::

                class MyService:
                    def process(self, data: str) -> dict:
                        pass
                    
                    @property
                    def status(self) -> str:
                        pass

                # Basic spec mock
                mock = SpecMock(MyService)
                
                # With signature validation
                mock = SpecMock(MyService, validate_signatures=True)
                
                # With spec_set (strict attribute setting)
                mock = SpecMock(MyService, spec_set=True)
        """
        if not inspect.isclass(spec):
            raise TypeError(f"spec must be a class, not {type(spec).__name__}")

        # Store spec-related attributes before calling super().__init__
        # These need to be set directly to avoid triggering __setattr__ validation
        object.__setattr__(self, '_spec', spec)
        object.__setattr__(self, '_validate_signatures', validate_signatures)
        object.__setattr__(self, '_spec_set', spec_set)
        object.__setattr__(self, '_spec_attributes', self._get_spec_attributes(spec))
        object.__setattr__(self, '_spec_methods', self._get_spec_methods(spec))

        # Initialize the base Mock with strict_attrs=True to leverage existing validation
        super().__init__(
            mock_attributes=mock_attributes,
            return_value=return_value,
            side_effect=side_effect,
            recursive=False,  # Spec mocks don't auto-create children
            strict_attrs=False  # We handle our own validation
        )

    @staticmethod
    def _get_spec_attributes(spec: Type) -> Dict[str, Any]:
        """
            Extracts all attributes from the spec class.
            
            This includes instance attributes (from __init__ if available),
            class attributes, and properties.
            
            :param spec: The specification class to analyze.
            
            :return: A dictionary mapping attribute names to their types or values.
        """
        attributes = {}
        
        # Get class-level attributes (excluding methods and special attributes)
        for name, value in inspect.getmembers(spec):
            if name.startswith('_'):
                continue
            if inspect.isfunction(value) or inspect.ismethod(value):
                continue
            if isinstance(value, property):
                attributes[name] = value
            elif not callable(value):
                attributes[name] = value
        
        # Try to get instance attributes from __init__ by analyzing the source code
        # and looking for self.attr = assignments
        if hasattr(spec, '__init__'):
            try:
                source = inspect.getsource(spec.__init__)
                # Simple pattern matching for self.attr = assignments
                import re
                # Match patterns like "self.name = " or "self.value = "
                pattern = r'self\.([a-zA-Z_][a-zA-Z0-9_]*)\s*='
                matches = re.findall(pattern, source)
                for attr_name in matches:
                    if not attr_name.startswith('_'):
                        attributes[attr_name] = Any
            except (OSError, TypeError):
                # Source not available (e.g., built-in classes)
                pass
            
            # Also check __init__ signature for parameters that might be stored
            try:
                init_sig = inspect.signature(spec.__init__)
                for param_name, param in init_sig.parameters.items():
                    if param_name == 'self':
                        continue
                    # These are potential instance attributes
                    if not param_name.startswith('_'):
                        attributes[param_name] = param.annotation if param.annotation != inspect.Parameter.empty else Any
            except (ValueError, TypeError):
                # Signature not introspectable (e.g., some built-in or C-implemented
                # initializers); the spec simply contributes no parameter-derived attributes.
                pass
        
        # Get type hints for the class (includes annotated attributes)
        try:
            hints = get_type_hints(spec)
            for name, type_hint in hints.items():
                if not name.startswith('_'):
                    attributes[name] = type_hint
        except Exception:
            # Type hints could not be resolved (e.g., unresolvable forward references);
            # the spec simply contributes no annotation-derived attributes.
            pass
        
        return attributes

    @staticmethod
    def _get_spec_methods(spec: Type) -> Dict[str, inspect.Signature]:
        """
            Extracts all methods from the spec class with their signatures.
            
            :param spec: The specification class to analyze.
            
            :return: A dictionary mapping method names to their signatures.
        """
        methods = {}
        
        for name, value in inspect.getmembers(spec):
            if name.startswith('_') and name != '__call__':
                continue
            if inspect.isfunction(value) or inspect.ismethod(value):
                try:
                    methods[name] = inspect.signature(value)
                except (ValueError, TypeError):
                    methods[name] = None
        
        return methods

    @property
    def spec(self) -> Type:
        """
            Returns the specification class for this mock.
            
            :return: The class used as the specification.
        """
        return self._spec

    @property
    def spec_attributes(self) -> Dict[str, Any]:
        """
            Returns the attributes defined in the spec.
            
            :return: A dictionary of attribute names to their types/values.
        """
        return self._spec_attributes

    @property
    def spec_methods(self) -> Dict[str, Optional[inspect.Signature]]:
        """
            Returns the methods defined in the spec with their signatures.
            
            :return: A dictionary of method names to their signatures.
        """
        return self._spec_methods

    def _is_valid_spec_attribute(self, name: str) -> bool:
        """
            Checks if an attribute name is valid according to the spec.
            
            :param name: The attribute name to check.
            
            :return: True if the attribute exists in the spec, False otherwise.
        """
        return name in self._spec_attributes or name in self._spec_methods

    def _validate_method_call(self, method_name: str, args: Tuple, kwargs: Dict) -> None:
        """
            Validates a method call against the spec's signature.
            
            :param method_name: The name of the method being called.
            :param args: The positional arguments passed to the method.
            :param kwargs: The keyword arguments passed to the method.
            
            :raises SpecViolationError: If the call doesn't match the spec's signature.
        """
        if not self._validate_signatures:
            return
        
        if method_name not in self._spec_methods:
            return
        
        sig = self._spec_methods[method_name]
        if sig is None:
            return
        
        try:
            # Try to bind the arguments to the signature
            # Skip 'self' parameter for instance methods
            params = list(sig.parameters.values())
            if params and params[0].name == 'self':
                params = params[1:]
            
            # Create a new signature without 'self'
            new_sig = sig.replace(parameters=params)
            new_sig.bind(*args, **kwargs)
        except TypeError as e:
            raise SpecViolationError(
                f"Method '{method_name}' called with invalid arguments: {e}\n"
                f"Expected signature: {sig}"
            )

    def __getattr__(self, name: str):
        """
            Gets an attribute of the spec mock object.
            
            This method validates that the attribute exists in the spec before
            returning it. If the attribute is a method in the spec, a child
            SpecMethodMock is created to track calls and validate signatures.

            :param name: The name of the attribute to get.
            
            :return: The attribute value or a mock for the method.

            :raises SpecViolationError: If the attribute doesn't exist in the spec.
        """
        # Block access to private attributes
        if name.startswith('_'):
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # Delegate assertion methods to MockContext
        if hasattr(self._mock_context, name) and callable(getattr(self._mock_context, name)) and name.startswith("assert_"):
            return getattr(self._mock_context, name)

        # Check if attribute exists in mock_attributes first
        if self._mock_context.has_attribute(name):
            return self._mock_context.get_attribute(name)

        # Validate against spec
        if not self._is_valid_spec_attribute(name):
            raise SpecViolationError(
                f"'{self._spec.__name__}' spec has no attribute '{name}'. "
                f"Available attributes: {sorted(list(self._spec_attributes.keys()) + list(self._spec_methods.keys()))}"
            )

        # If it's a method in the spec, create a method mock
        if name in self._spec_methods:
            method_mock = _SpecMethodMock(
                self,
                name,
                self._spec_methods[name],
                validate_signatures=self._validate_signatures
            )
            self._mock_context.set_attribute(name, method_mock)
            return method_mock

        # For attributes, create a simple mock
        attr_mock = Mock(recursive=False, strict_attrs=False)
        self._mock_context.set_attribute(name, attr_mock)
        return attr_mock

    def __setattr__(self, name: str, value: Any):
        """
            Sets an attribute on the spec mock object.
            
            This method validates that the attribute exists in the spec when
            spec_set is True.

            :param name: The name of the attribute to set.
            :param value: The value to set for the attribute.

            :raises SpecViolationError: If spec_set is True and the attribute
                doesn't exist in the spec.
        """
        # Allow setting private attributes directly
        if name.startswith('_'):
            object.__setattr__(self, name, value)
            return

        # Handle special mock configuration attributes
        if name in ["return_value", "side_effect", "recursive"]:
            if name == "return_value":
                self._mock_context.configure(return_value=value)
            elif name == "side_effect":
                self._mock_context.configure(side_effect=value)
            elif name == "recursive":
                self._mock_context.recursive = value
            return

        # Validate against spec if spec_set is True
        if self._spec_set and not self._is_valid_spec_attribute(name):
            raise SpecViolationError(
                f"Cannot set attribute '{name}' on spec mock: "
                f"'{self._spec.__name__}' spec has no such attribute. "
                f"Available attributes: {sorted(list(self._spec_attributes.keys()) + list(self._spec_methods.keys()))}"
            )

        # Store the attribute
        self._mock_context.set_attribute(name, value)

    def __dir__(self) -> List[str]:
        """
            Returns a list of attributes for the spec mock object.
            
            This includes all attributes and methods from the spec, plus
            any attributes that have been set on the mock.
            
            :return: A sorted list of attribute names.
        """
        attributes = set(super().__dir__())
        attributes.update(self._spec_attributes.keys())
        attributes.update(self._spec_methods.keys())
        return sorted(attributes)


class _SpecMethodMock(Mock):
    """
        Internal mock class for methods on a SpecMock.
        
        This class wraps method calls to validate them against the spec's
        method signature when validate_signatures is enabled.
    """

    def __init__(self, parent: SpecMock, method_name: str, signature: Optional[inspect.Signature],
                 validate_signatures: bool = False):
        """
            Creates a spec method mock.

            :param parent: The parent SpecMock that owns this method.
            :param method_name: The name of the method being mocked.
            :param signature: The method's signature from the spec.
            :param validate_signatures: Whether to validate call signatures.
        """
        super().__init__(recursive=False, strict_attrs=False)
        object.__setattr__(self, '_parent_spec_mock', parent)
        object.__setattr__(self, '_method_name', method_name)
        object.__setattr__(self, '_method_signature', signature)
        object.__setattr__(self, '_validate_signatures', validate_signatures)

    def __call__(self, *args, **kwargs) -> Any:
        """
            Calls the mock method with signature validation.

            :param args: Positional arguments for the method.
            :param kwargs: Keyword arguments for the method.

            :return: The configured return value or side effect result.

            :raises SpecViolationError: If validate_signatures is True and
                the arguments don't match the spec's signature.
        """
        # Validate the call signature if enabled
        if self._validate_signatures and self._method_signature is not None:
            self._validate_call(args, kwargs)

        # Delegate to parent Mock.__call__
        return super().__call__(*args, **kwargs)

    def _validate_call(self, args: Tuple, kwargs: Dict) -> None:
        """
            Validates the call arguments against the method signature.

            :param args: Positional arguments for the method.
            :param kwargs: Keyword arguments for the method.

            :raises SpecViolationError: If the arguments don't match the signature.
        """
        sig = self._method_signature
        if sig is None:
            return

        try:
            # Skip 'self' parameter for instance methods
            params = list(sig.parameters.values())
            if params and params[0].name == 'self':
                params = params[1:]

            # Create a new signature without 'self'
            new_sig = sig.replace(parameters=params)
            new_sig.bind(*args, **kwargs)
        except TypeError as e:
            raise SpecViolationError(
                f"Method '{self._method_name}' called with invalid arguments: {e}\n"
                f"Expected signature: {sig}"
            )


def create_spec_mock(spec: Type, *, return_value: Optional[Any] = None,
                     side_effect: Optional[Union[Callable, SideEffect]] = None,
                     validate_signatures: bool = False, spec_set: bool = False) -> SpecMock:
    """
        Creates a mock object that validates against a specification class.
        
        This is the recommended factory function for creating spec-based mocks.
        The created mock will only allow access to attributes and methods that
        exist on the specification class.

        :param spec: The specification class that defines the allowed interface.
            Must be a class (not an instance).
        :param return_value: The value to return when the mock is called directly.
            Defaults to None.
        :param side_effect: A callable or SideEffect to execute when the mock
            is called directly. Defaults to None.
        :param validate_signatures: If True, method calls will be validated against
            the spec's method signatures, including argument count and names.
            Defaults to False.
        :param spec_set: If True, only attributes that exist on the spec can be set
            on the mock. If False, new attributes can be set but accessing undefined
            attributes still raises SpecViolationError. Defaults to False.

        :return: A SpecMock object configured with the given specification.

        :raises TypeError: If spec is not a class.

        Example::

            from ccai.testbase.mocking import create_spec_mock

            class UserService:
                def __init__(self):
                    self.cache = {}
                
                def get_user(self, user_id: int) -> dict:
                    pass
                
                def create_user(self, name: str, email: str) -> dict:
                    pass
                
                @property
                def is_connected(self) -> bool:
                    pass

            # Basic spec mock
            mock_service = create_spec_mock(UserService)
            mock_service.get_user.return_value = {"id": 1, "name": "Test"}
            
            # Valid usage
            result = mock_service.get_user(1)  # Returns {"id": 1, "name": "Test"}
            
            # Invalid usage raises SpecViolationError
            # mock_service.nonexistent_method()  # Raises SpecViolationError
            
            # With signature validation
            mock_service = create_spec_mock(UserService, validate_signatures=True)
            mock_service.get_user(1)  # Valid
            # mock_service.get_user()  # Raises SpecViolationError (missing user_id)
            
            # With spec_set (strict attribute setting)
            mock_service = create_spec_mock(UserService, spec_set=True)
            mock_service.cache = {"key": "value"}  # Valid (cache is in spec)
            # mock_service.new_attr = "value"  # Raises SpecViolationError
    """
    if not inspect.isclass(spec):
        raise TypeError(f"spec must be a class, not {type(spec).__name__}")

    return SpecMock(
        spec,
        return_value=return_value,
        side_effect=side_effect,
        validate_signatures=validate_signatures,
        spec_set=spec_set
    )


def create_async_mock(*, return_value: Optional[Any] = None,
                      side_effect: Optional[Union[Callable[..., Coroutine], AsyncSideEffect]] = None,
                      recursive: bool = False, strict_attrs: bool = False) -> AsyncMock:
    """
        Creates an async mock object that can be awaited.
        
        This is the recommended factory function for creating async mocks.
        The created mock can be awaited and will return the configured return_value
        or execute the async side_effect.

        :param return_value: The value to return when the mock is awaited.
            Defaults to None.
        :param side_effect: An async callable or AsyncSideEffect to execute when 
            the mock is awaited. If an async callable is provided, it will be 
            wrapped in an AsyncSideEffect. Defaults to None.
        :param recursive: If True, accessing undefined attributes will automatically
            create and return new AsyncMock objects. Defaults to False.
        :param strict_attrs: If True, only pre-defined attributes can be accessed or set.
            Defaults to False.

        :return: An AsyncMock object configured with the given settings.

        :raises TypeError: If side_effect is provided but is neither an AsyncSideEffect 
            instance nor an async callable.

        Example::

            from ccai.testbase.mocking import create_async_mock
            import asyncio

            # Basic async mock with return value
            async_mock = create_async_mock(return_value={"status": "ok"})
            result = await async_mock()  # Returns {"status": "ok"}
            
            # Async mock with async side effect
            async def fetch_data(url):
                await asyncio.sleep(0.1)
                return {"url": url, "data": "response"}
            
            async_mock = create_async_mock(side_effect=fetch_data)
            result = await async_mock("http://example.com")
            # Returns {"url": "http://example.com", "data": "response"}
            
            # Recursive async mock for chained access
            async_mock = create_async_mock(recursive=True)
            async_mock.database.query.return_value = ["item1", "item2"]
            result = await async_mock.database.query()  # Returns ["item1", "item2"]
            
            # Verify interactions
            async_mock = create_async_mock()
            await async_mock(1, 2, key="value")
            async_mock.assert_called_once_with(1, 2, key="value")
    """
    return AsyncMock(
        return_value=return_value,
        side_effect=side_effect,
        recursive=recursive,
        strict_attrs=strict_attrs
    )


def create_property_mock(*, getter_return_value: Optional[Any] = None,
                         getter_side_effect: Optional[Union[Callable, SideEffect]] = None,
                         setter_side_effect: Optional[Union[Callable, SideEffect]] = None) -> PropertyMock:
    """
        Creates a property mock object with separate getter and setter tracking.
        
        This is the recommended factory function for creating property mocks.
        The created mock provides separate tracking and configuration for property
        getter and setter operations.

        :param getter_return_value: The value to return when the property is accessed (getter).
            Defaults to None.
        :param getter_side_effect: A callable or SideEffect to execute when the property
            is accessed (getter). If provided, its return value is used instead of
            getter_return_value. Defaults to None.
        :param setter_side_effect: A callable or SideEffect to execute when the property
            is set (setter). The callable receives the value being set as its argument.
            Defaults to None.

        :return: A PropertyMock object configured with the given settings.

        :raises TypeError: If getter_side_effect or setter_side_effect is provided but
            is neither a SideEffect instance nor a callable.

        Example::

            from ccai.testbase.mocking import create_property_mock

            # Basic property mock with return value
            prop_mock = create_property_mock(getter_return_value="initial_value")
            value = prop_mock.get()  # Returns "initial_value"
            
            # Property mock with dynamic getter
            counter = [0]
            def increment():
                counter[0] += 1
                return counter[0]
            
            prop_mock = create_property_mock(getter_side_effect=increment)
            print(prop_mock.get())  # Returns 1
            print(prop_mock.get())  # Returns 2
            
            # Property mock with setter tracking
            def validate_setter(value):
                if not isinstance(value, int):
                    raise ValueError("Must be an integer")
            
            prop_mock = create_property_mock(setter_side_effect=validate_setter)
            prop_mock.set(42)  # OK
            # prop_mock.set("string")  # Raises ValueError
            
            # Verify interactions
            prop_mock = create_property_mock(getter_return_value="test")
            prop_mock.get()
            prop_mock.set("new_value")
            
            prop_mock.assert_getter_called()
            prop_mock.assert_setter_called_with("new_value")
            
            # Property mock with both getter and setter
            stored_value = ["initial"]
            
            def getter():
                return stored_value[0]
            
            def setter(value):
                stored_value[0] = value
            
            prop_mock = create_property_mock(
                getter_side_effect=getter,
                setter_side_effect=setter
            )
            
            print(prop_mock.get())  # Returns "initial"
            prop_mock.set("updated")
            print(prop_mock.get())  # Returns "updated"
    """
    return PropertyMock(
        getter_return_value=getter_return_value,
        getter_side_effect=getter_side_effect,
        setter_side_effect=setter_side_effect
    )


# =============================================================================
# AUTOMATIC MOCK CLEANUP
# =============================================================================
# This section provides functionality for automatic mock cleanup to prevent
# mock leakage between tests. The MockRegistry tracks all mocks and patches
# created during test execution and provides methods to clean them up.
# =============================================================================


class MockRegistry:
    """
        A registry for tracking mocks and patches for automatic cleanup.
        
        The MockRegistry provides a centralized way to track all Mock objects and
        Patch instances created during test execution. This enables automatic cleanup
        at the end of each test to prevent mock leakage between tests.
        
        The registry uses a thread-local storage pattern to ensure that mocks are
        isolated between concurrent test executions.
        
        Example Usage::

            from ccai.testbase.mocking import MockRegistry, Mock, create_module_patch
            
            # Get the global registry instance
            registry = MockRegistry.get_instance()
            
            # Register mocks for automatic cleanup
            mock = Mock()
            registry.register_mock(mock)
            
            # Register patches for automatic cleanup
            patch = create_module_patch(some_module, 'function')
            registry.register_patch(patch)
            patch.activate()
            
            # At the end of the test, cleanup all registered items
            registry.cleanup_all()
            # All mocks are reset and all patches are deactivated
            
            # Or use the convenience function
            from ccai.testbase.mocking import cleanup_all_mocks
            cleanup_all_mocks()
        
        Integration with Test Lifecycle::

            # In test setup
            def setUp(self):
                # Mocks created here will be tracked
                pass
            
            # In test teardown
            def tearDown(self):
                cleanup_all_mocks()  # Clean up all mocks
    """
    
    _instance = None
    _lock = None
    
    def __init__(self):
        """
            Initializes the MockRegistry.
            
            This constructor should not be called directly. Use get_instance() instead.
        """
        import threading
        self._local = threading.local()
        return
    
    @classmethod
    def get_instance(cls) -> "MockRegistry":
        """
            Returns the singleton instance of the MockRegistry.
            
            This method is thread-safe and ensures only one registry instance exists.
            
            :return: The global MockRegistry instance.
            
            Example::

                registry = MockRegistry.get_instance()
                registry.register_mock(my_mock)
        """
        import threading
        
        if cls._lock is None:
            cls._lock = threading.Lock()
        
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        
        return cls._instance
    
    def _get_mocks(self) -> List[Mock]:
        """
            Returns the list of registered mocks for the current thread.
            
            :return: A list of Mock objects registered in the current thread.
        """
        if not hasattr(self._local, 'mocks'):
            self._local.mocks = []
        return self._local.mocks
    
    def _get_patches(self) -> List[Patch]:
        """
            Returns the list of registered patches for the current thread.
            
            :return: A list of Patch objects registered in the current thread.
        """
        if not hasattr(self._local, 'patches'):
            self._local.patches = []
        return self._local.patches
    
    def register_mock(self, mock: Mock) -> Mock:
        """
            Registers a mock for automatic cleanup.
            
            The mock will be reset when cleanup_all() is called.
            
            :param mock: The Mock object to register.
            
            :return: The same Mock object (for fluent chaining).
            
            Example::

                mock = registry.register_mock(Mock(return_value=42))
                # mock is now tracked for cleanup
        """
        mocks = self._get_mocks()
        if mock not in mocks:
            mocks.append(mock)
        return mock
    
    def register_patch(self, patch: Patch) -> Patch:
        """
            Registers a patch for automatic cleanup.
            
            The patch will be deactivated when cleanup_all() is called.
            
            :param patch: The Patch object to register.
            
            :return: The same Patch object (for fluent chaining).
            
            Example::

                patch = registry.register_patch(create_module_patch(module, 'func'))
                mock = patch.activate()
                # patch is now tracked for cleanup
        """
        patches = self._get_patches()
        if patch not in patches:
            patches.append(patch)
        return patch
    
    def unregister_mock(self, mock: Mock) -> None:
        """
            Removes a mock from the registry.
            
            :param mock: The Mock object to unregister.
            
            Example::

                registry.unregister_mock(mock)
                # mock will no longer be cleaned up automatically
        """
        mocks = self._get_mocks()
        if mock in mocks:
            mocks.remove(mock)
        return
    
    def unregister_patch(self, patch: Patch) -> None:
        """
            Removes a patch from the registry.
            
            :param patch: The Patch object to unregister.
            
            Example::

                registry.unregister_patch(patch)
                # patch will no longer be cleaned up automatically
        """
        patches = self._get_patches()
        if patch in patches:
            patches.remove(patch)
        return
    
    def cleanup_all(self, reset_mocks: bool = True, deactivate_patches: bool = True) -> None:
        """
            Cleans up all registered mocks and patches.
            
            This method should be called at the end of each test to ensure that
            mocks don't leak between tests.
            
            :param reset_mocks: If True, reset all registered mocks to their initial state.
                Defaults to True.
            :param deactivate_patches: If True, deactivate all registered patches to restore
                original attributes. Defaults to True.
            
            Example::

                # At the end of a test
                registry.cleanup_all()
                
                # Only deactivate patches, don't reset mocks
                registry.cleanup_all(reset_mocks=False)
                
                # Only reset mocks, don't deactivate patches
                registry.cleanup_all(deactivate_patches=False)
        """
        # Deactivate patches first (in reverse order of registration)
        # This ensures that nested patches are deactivated in the correct order
        if deactivate_patches:
            patches = self._get_patches()
            for patch in reversed(patches):
                try:
                    patch.deactivate()
                except Exception:
                    # Ignore errors during deactivation to ensure all patches are processed
                    pass
            patches.clear()
        
        # Reset mocks
        if reset_mocks:
            mocks = self._get_mocks()
            for mock in mocks:
                try:
                    mock.mock_context().reset()
                except Exception:
                    # Ignore errors during reset to ensure all mocks are processed
                    pass
            mocks.clear()
        
        return
    
    def get_registered_mock_count(self) -> int:
        """
            Returns the number of registered mocks.
            
            :return: The count of registered Mock objects.
            
            Example::

                count = registry.get_registered_mock_count()
                print(f"There are {count} mocks registered")
        """
        return len(self._get_mocks())
    
    def get_registered_patch_count(self) -> int:
        """
            Returns the number of registered patches.
            
            :return: The count of registered Patch objects.
            
            Example::

                count = registry.get_registered_patch_count()
                print(f"There are {count} patches registered")
        """
        return len(self._get_patches())
    
    def clear(self) -> None:
        """
            Clears all registered mocks and patches without cleaning them up.
            
            This method removes all items from the registry without resetting mocks
            or deactivating patches. Use cleanup_all() instead if you want to
            properly clean up the registered items.
            
            Example::

                # Clear the registry without cleanup (use with caution)
                registry.clear()
        """
        self._get_mocks().clear()
        self._get_patches().clear()
        return


# =============================================================================
# CONVENIENCE FUNCTIONS FOR AUTOMATIC CLEANUP
# =============================================================================


def get_mock_registry() -> MockRegistry:
    """
        Returns the global MockRegistry instance.
        
        This is a convenience function for accessing the singleton MockRegistry.
        
        :return: The global MockRegistry instance.
        
        Example::

            from ccai.testbase.mocking import get_mock_registry
            
            registry = get_mock_registry()
            registry.register_mock(my_mock)
    """
    return MockRegistry.get_instance()


def register_mock(mock: Mock) -> Mock:
    """
        Registers a mock for automatic cleanup.
        
        This is a convenience function that registers the mock with the global
        MockRegistry.
        
        :param mock: The Mock object to register.
        
        :return: The same Mock object (for fluent chaining).
        
        Example::

            from ccai.testbase.mocking import Mock, register_mock
            
            mock = register_mock(Mock(return_value=42))
            # mock is now tracked for automatic cleanup
    """
    return get_mock_registry().register_mock(mock)


def register_patch(patch: Patch) -> Patch:
    """
        Registers a patch for automatic cleanup.
        
        This is a convenience function that registers the patch with the global
        MockRegistry.
        
        :param patch: The Patch object to register.
        
        :return: The same Patch object (for fluent chaining).
        
        Example::

            from ccai.testbase.mocking import create_module_patch, register_patch
            
            patch = register_patch(create_module_patch(module, 'func'))
            mock = patch.activate()
            # patch is now tracked for automatic cleanup
    """
    return get_mock_registry().register_patch(patch)


def cleanup_all_mocks(reset_mocks: bool = True, deactivate_patches: bool = True) -> None:
    """
        Cleans up all registered mocks and patches.
        
        This is a convenience function that calls cleanup_all() on the global
        MockRegistry. It should be called at the end of each test to prevent
        mock leakage between tests.
        
        :param reset_mocks: If True, reset all registered mocks to their initial state.
            Defaults to True.
        :param deactivate_patches: If True, deactivate all registered patches to restore
            original attributes. Defaults to True.
        
        Example::

            from ccai.testbase.mocking import cleanup_all_mocks
            
            class MyTest(unittest.TestCase):
                def tearDown(self):
                    cleanup_all_mocks()
                
                def test_something(self):
                    mock = register_mock(Mock())
                    patch = register_patch(create_module_patch(module, 'func'))
                    patch.activate()
                    # ... test code ...
                    # cleanup_all_mocks() is called automatically in tearDown
    """
    get_mock_registry().cleanup_all(reset_mocks=reset_mocks, deactivate_patches=deactivate_patches)
    return


def create_tracked_mock(*, mock_attributes: Optional[Dict[str, Any]] = None, return_value: Optional[Any] = None,
                        reference: Optional[Any] = None, mtype: Optional[MockType] = None, 
                        side_effect: Optional[Union[Callable, SideEffect]] = None,
                        recursive: bool = False, strict_attrs: bool = False) -> Mock:
    """
        Creates a Mock object and registers it for automatic cleanup.
        
        This is a convenience function that combines Mock creation with automatic
        registration in the MockRegistry.
        
        :param mock_attributes: A dictionary of pre-defined attributes for the mock.
        :param return_value: The value to return when the mock is called.
        :param reference: The original object being mocked.
        :param mtype: Explicit MockType for this mock.
        :param side_effect: A callable or SideEffect to execute when called.
        :param recursive: If True, enable automatic child mock creation.
        :param strict_attrs: If True, restrict attribute access to defined attributes.
        
        :return: A Mock object registered for automatic cleanup.
        
        Example::

            from ccai.testbase.mocking import create_tracked_mock, cleanup_all_mocks
            
            # Create a mock that will be automatically cleaned up
            mock = create_tracked_mock(return_value=42, recursive=True)
            
            # Use the mock
            result = mock()  # Returns 42
            mock.child.return_value = "nested"
            
            # Clean up at the end of the test
            cleanup_all_mocks()
    """
    mock = Mock(
        mock_attributes=mock_attributes,
        return_value=return_value,
        reference=reference,
        mtype=mtype,
        side_effect=side_effect,
        recursive=recursive,
        strict_attrs=strict_attrs
    )
    return register_mock(mock)


def create_tracked_patch(owner: Any, target_name: str, patch_type: PatchType, 
                         recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a Patch object and registers it for automatic cleanup.
        
        This is a convenience function that combines Patch creation with automatic
        registration in the MockRegistry.
        
        :param owner: The module, class, or instance that owns the attribute to patch.
        :param target_name: The name of the attribute to patch.
        :param patch_type: The type of patch (Module, Class, or Instance).
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attributes.
        
        :return: A Patch object registered for automatic cleanup.
        
        Example::

            from ccai.testbase.mocking import create_tracked_patch, PatchType, cleanup_all_mocks
            
            # Create a patch that will be automatically cleaned up
            patch = create_tracked_patch(some_module, 'function', PatchType.Module)
            mock = patch.activate()
            mock.return_value = "mocked"
            
            # Use the patched function
            result = some_module.function()  # Returns "mocked"
            
            # Clean up at the end of the test
            cleanup_all_mocks()
    """
    patch = Patch(owner, target_name, patch_type, recursive=recursive, strict_attrs=strict_attrs)
    return register_patch(patch)


def create_tracked_module_patch(module: types.ModuleType, target_name: str, 
                                recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a module patch and registers it for automatic cleanup.
        
        This is a convenience function that combines create_module_patch with automatic
        registration in the MockRegistry.
        
        :param module: The module containing the attribute to patch.
        :param target_name: The name of the attribute to patch.
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attributes.
        
        :return: A Patch object registered for automatic cleanup.
        
        :raises TypeError: If module is not a module object or target_name is not a string.
        
        Example::

            from ccai.testbase.mocking import create_tracked_module_patch, cleanup_all_mocks
            import os
            
            # Create a tracked module patch
            patch = create_tracked_module_patch(os.path, 'exists')
            mock = patch.activate()
            mock.return_value = True
            
            # Use the patched function
            result = os.path.exists('/any/path')  # Returns True
            
            # Clean up at the end of the test
            cleanup_all_mocks()
    """
    patch = create_module_patch(module, target_name, recursive=recursive, strict_attrs=strict_attrs)
    return register_patch(patch)


def create_tracked_class_patch(cls: Type, target_name: str, 
                               recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates a class patch and registers it for automatic cleanup.
        
        This is a convenience function that combines create_class_patch with automatic
        registration in the MockRegistry.
        
        :param cls: The class containing the attribute to patch.
        :param target_name: The name of the attribute to patch.
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attributes.
        
        :return: A Patch object registered for automatic cleanup.
        
        :raises TypeError: If cls is not a class or target_name is not a string.
        
        Example::

            from ccai.testbase.mocking import create_tracked_class_patch, cleanup_all_mocks
            
            class MyService:
                @classmethod
                def fetch_data(cls):
                    return "real data"
            
            # Create a tracked class patch
            patch = create_tracked_class_patch(MyService, 'fetch_data')
            mock = patch.activate()
            mock.return_value = "mocked data"
            
            # Use the patched method
            result = MyService.fetch_data()  # Returns "mocked data"
            
            # Clean up at the end of the test
            cleanup_all_mocks()
    """
    patch = create_class_patch(cls, target_name, recursive=recursive, strict_attrs=strict_attrs)
    return register_patch(patch)


def create_tracked_instance_patch(instance: object, target_name: str, 
                                  recursive: bool = False, strict_attrs: bool = False) -> Patch:
    """
        Creates an instance patch and registers it for automatic cleanup.
        
        This is a convenience function that combines create_instance_patch with automatic
        registration in the MockRegistry.
        
        :param instance: The object instance containing the attribute to patch.
        :param target_name: The name of the attribute to patch.
        :param recursive: If True, the created mock will be recursive.
        :param strict_attrs: If True, the created mock will have strict attributes.
        
        :return: A Patch object registered for automatic cleanup.
        
        :raises TypeError: If target_name is not a string.
        
        Example::

            from ccai.testbase.mocking import create_tracked_instance_patch, cleanup_all_mocks
            
            class MyService:
                def process(self):
                    return "real processing"
            
            service = MyService()
            
            # Create a tracked instance patch
            patch = create_tracked_instance_patch(service, 'process')
            mock = patch.activate()
            mock.return_value = "mocked processing"
            
            # Use the patched method
            result = service.process()  # Returns "mocked processing"
            
            # Clean up at the end of the test
            cleanup_all_mocks()
    """
    patch = create_instance_patch(instance, target_name, recursive=recursive, strict_attrs=strict_attrs)
    return register_patch(patch)
