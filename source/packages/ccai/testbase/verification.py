"""
    .. module:: ccai.testbase.verification
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for verification.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""


__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, List, Optional, Union, Type

import os
import re

from pprint import pformat

from ccai.xmodules.xformatting import indent_lines, indent_lines_list

from ccai.errors.exceptions import SemanticError
from ccai.errors.xtraceback import TracebackFormatPolicy


__traceback_format_policy__ = TracebackFormatPolicy.Hide


PREFIX_STD = "Result"
PREFIX_API = "'{}' API result"


def assert_dict_response_has_keys(to_inspect: dict, expected_keys: List[str], api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected keys.  If the
        verification fails then an :class:`AssertionError` is created and return, otherwise None is returned. It
        is the resposibility of the calling test to raise the returned error.

        :param to_inspect: The dictionary being inspected
        :param expected_keys: The list of expected keys
        :param api: The optional name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    template = "    '{}' key not found."

    content_errors = verify_dict_has_keys(to_inspect, expected_keys, template)
    if len(content_errors) > 0:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed with the following errors:".format(msg_prefix)
        ]

        for nxtce in content_errors:
            err_msg_lines.append(nxtce)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_dict_response_has_paths(to_inspect: dict, expected_paths: List[str], api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected paths.  If the
        verification fails then an :class:`AssertionError` is created and return, otherwise None is returned. It
        is the resposibility of the calling test to raise the returned error.

        :param to_inspect: The dictionary being inspected
        :param expected_paths: The list of expected slash-separated paths, see :func:`verify_dict_has_paths`
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    template = "    '{}' path not found."

    content_errors = verify_dict_has_paths(to_inspect, expected_paths, template)
    if len(content_errors) > 0:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed with the following errors:".format(msg_prefix)
        ]

        for nxtce in content_errors:
            err_msg_lines.append(nxtce)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_equal(found: Any, expected: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected value.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to be compared
        :param expected: The expected value
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if found != expected:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value did not match expected value:".format(msg_prefix)
        ]

        exp_format_lines = pformat(expected, indent=4).strip().splitlines()
        if len(exp_format_lines) == 1:
            err_msg_lines.append("EXPECTED: {}".format(exp_format_lines[0]))
        elif len(exp_format_lines) > 1:
            err_msg_lines.append("EXPECTED:")
            exp_format_lines = indent_lines_list(exp_format_lines, 1)
            err_msg_lines.extend(exp_format_lines)

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_expression(found: str, expr: Union[str, re.Pattern], api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected value.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to be compared
        :param expr: An expression to match with the found value.
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if not isinstance(expr, re.Pattern):
        expr = re.compile(expr)

    mobj = expr.match(found)
    if mobj is None:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value did not match expression provided.".format(msg_prefix),
            "FOUND: {}".format(found),
            "EXPR: {}".format(expr)
        ]

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_true(found: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API is true.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to be evaluated
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if not found:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value evaluated to False.".format(msg_prefix)
        ]

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_false(found: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API is false.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to be evaluated
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if found:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value evaluated to True.".format(msg_prefix)
        ]

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_greater(found: Any, boundary: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has a value greater than the
        boundary specified. If the verification fails then an :class:`AssertionError` is created
        and returned, otherwise None is returned. It is the resposibility of the calling test to raise
        the returned error.

        :param found: The value being compared
        :param boundary: The boundary value being compared against
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if not found > boundary:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value was not greater than the boundary value:".format(msg_prefix)
        ]

        bndry_format_lines = pformat(boundary, indent=4).strip().splitlines()
        if len(bndry_format_lines) == 1:
            err_msg_lines.append("BOUNDARY: {}".format(bndry_format_lines[0]))
        elif len(bndry_format_lines) > 1:
            err_msg_lines.append("BOUNDARY:")
            bndry_format_lines = indent_lines_list(bndry_format_lines, 1)
            err_msg_lines.extend(bndry_format_lines)

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_lessthan(found: Any, boundary: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has a value less than the
        boundary specified. If the verification fails then an :class:`AssertionError` is created
        and returned, otherwise None is returned. It is the resposibility of the calling test to raise
        the returned error.

        :param found: The value being compared
        :param boundary: The boundary value being compared against
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if not found < boundary:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value was not less than the boundary value:".format(msg_prefix)
        ]

        bndry_format_lines = pformat(boundary, indent=4).strip().splitlines()
        if len(bndry_format_lines) == 1:
            err_msg_lines.append("BOUNDARY: {}".format(bndry_format_lines[0]))
        elif len(bndry_format_lines) > 1:
            err_msg_lines.append("BOUNDARY:")
            bndry_format_lines = indent_lines_list(bndry_format_lines, 1)
            err_msg_lines.extend(bndry_format_lines)

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_list_length(to_inspect: List, expected_len: int, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected number of items.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param to_inspect: The list being inspected
        :param expected_len: The expected length of the list
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    found_len = len(to_inspect)
    if found_len != expected_len:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the actual length ({}) did not match expected length ({}):".format(
                msg_prefix, found_len, expected_len),
            "ITEMS:"
        ]

        for fitem in to_inspect:
            err_msg_lines.append("    {}".format(fitem))
        err_msg_lines.append("")

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_list_length_greater(to_inspect: List, boundary_len: int, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has more items than the specified expected
        number of items.  If the verification fails then an :class:`AssertionError` is created and returned,
        otherwise None is returned. It is the resposibility of the calling test to raise the returned error.

        :param to_inspect: The list being inspected
        :param boundary_len: The boundary that the list length should exceed.
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    found_len = len(to_inspect)
    if not found_len > boundary_len:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the actual length ({}) was not greater than the boundary length ({}):".format(
                msg_prefix, found_len, boundary_len),
            "ITEMS:"
        ]

        for fitem in to_inspect:
            err_msg_lines.append("    {}".format(fitem))
        err_msg_lines.append("")

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_list_length_less(to_inspect: List, boundary_len: int, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has less items than the specified expected
        number of items.  If the verification fails then an :class:`AssertionError` is created and returned,
        otherwise None is returned. It is the resposibility of the calling test to raise the returned error.

        :param to_inspect: The list being inspected
        :param boundary_len: The boundary the list length should not exceed
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """
    
    found_len = len(to_inspect)
    if not found_len < boundary_len:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)
        
        err_msg_lines = [
            "{} result verification failed because the actual length ({}) was not less than the boundary length ({}):".format(
                msg_prefix, found_len, boundary_len),
            "ITEMS:"
        ]

        for fitem in to_inspect:
            err_msg_lines.append("    {}".format(fitem))
        err_msg_lines.append("")

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def assert_not_equal(found: Any, not_expected: Any, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API does not have the specified not
        expected value. If the verification fails then an :class:`AssertionError` is created and returned,
        otherwise None is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to be compared
        :param not_expected: The value that is not expected to be found
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    if found == not_expected:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value matched the not_expected value:".format(msg_prefix)
        ]

        exp_format_lines = pformat(not_expected, indent=4).strip().splitlines()
        if len(exp_format_lines) == 1:
            err_msg_lines.append("NOT EXPECTED: {}".format(exp_format_lines[0]))
        elif len(exp_format_lines) > 1:
            err_msg_lines.append("NOT EXPECTED:")
            exp_format_lines = indent_lines_list(exp_format_lines, 1)
            err_msg_lines.extend(exp_format_lines)

        found_format_lines = pformat(found, indent=4).splitlines()
        if len(found_format_lines) == 1:
            err_msg_lines.append("FOUND: {}".format(found_format_lines[0]))
        elif len(found_format_lines) > 1:
            err_msg_lines.append("FOUND:")
            found_format_lines = indent_lines_list(found_format_lines, 1)
            err_msg_lines.extend(found_format_lines)

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return

def assert_type(found: Any, exp_type: Type, api: Optional[str] = None):
    """
        Verifies that the specified return result from the specified API has the specified expected value type.
        If the verification fails then an :class:`AssertionError` is created and returned, otherwise None
        is returned. It is the resposibility of the calling test to raise the returned error.

        :param found: The value to check the type of
        :param exp_type: The expected value type
        :param api: The name of the API that returned the result being inspected.
        
        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    found_type = type(found)
    if found_type != exp_type:

        msg_prefix = PREFIX_STD if api is None else PREFIX_API.format(api)

        err_msg_lines = [
            "{} verification failed because the found value did not the expected type={}.".format(msg_prefix, exp_type),
            "FOUND_TYPE: {}".format(found_type)
        ]

        errmsg = os.linesep.join(err_msg_lines)
        raise AssertionError(errmsg)

    return


def verify_dict_has_keys(to_inspect: dict, expected_keys: List[str], template: Optional[str]=None) -> List[str]:
    """
        Verifies that the expected keys are found in the dictionary provided.  Returns a list of
        any keys that are missing.

        :param to_inspect: The dictionary being inspected
        :param expected_keys: The list of expected keys
        :param template: Optional template used with missing key names to produce error messages.

        :returns: None
        :raises: :class:`AssertionError` if the verification fails.
    """

    missing_list = []

    if template is not None:
        for exkey in expected_keys:
            if exkey not in to_inspect:
                missing_list.append(template.format(exkey))
    else:
        for exkey in expected_keys:
            if exkey not in to_inspect:
                missing_list.append(exkey)

    return missing_list

def verify_dict_has_paths(to_inspect: dict, expected_paths: List[str], template: Optional[str]=None) -> List[str]:
    """
        Verifies that the expected paths are found in the dictionary provided.  Returns a list of
        any paths that are missing.

        A path is a slash-separated list of keys, such as ``"spec/template/metadata"``, that is
        followed down through nested dictionaries.  Leading and trailing slashes are ignored.  The
        path is found when the key named by its last segment exists, whatever the value of that
        key is.

        :param to_inspect: The dictionary being inspected
        :param expected_paths: The list of expected paths to leafs in a dictionary
        :param template: Optional template used with missing paths to produce error messages.

        :returns: A list of the missing paths, formatted with the template when one is provided.
    """

    missing_list = []

    for next_exp_path in expected_paths:
        search_path = next_exp_path.strip("/")

        leaf_parts = []
        found = _verify_dict_has_paths_descend(search_path, to_inspect, leaf_parts)

        if not found:
            if template is not None:
                missing_list.append(template.format(next_exp_path))
            else:
                missing_list.append(next_exp_path)

    return missing_list

def _verify_dict_has_paths_descend(search_path: str, cursor: dict, leaf_parts: List[str]) -> bool:
    """
        Searches the dictionary at ``cursor`` for ``search_path``, descending into nested dictionaries
        whose accumulated path is a prefix of ``search_path``.

        :param search_path: The slash-separated path being searched for, without leading or trailing slashes.
        :param cursor: The dictionary at the current level of the descent.
        :param leaf_parts: The keys that lead from the root dictionary to ``cursor``.

        :returns: True if the path was found at or below ``cursor``, otherwise False.
    """

    found = False

    cursor_path = "/".join(leaf_parts)

    for nxt_key in cursor.keys():
        nxt_key_str = str(nxt_key)

        if len(leaf_parts) > 0:
            nxt_path = cursor_path + "/" + nxt_key_str
        else:
            nxt_path = nxt_key_str

        if nxt_path == search_path:
            found = True
        elif search_path.startswith(nxt_path + "/"):
            nxt_val = cursor[nxt_key]
            if isinstance(nxt_val, dict):
                desc_leaf_parts = [lp for lp in leaf_parts]
                desc_leaf_parts.append(nxt_key_str)
                found = _verify_dict_has_paths_descend(search_path, nxt_val, desc_leaf_parts)

        if found:
            break

    return found


class RaisesContext:
    """
        The object bound by :func:`raises`, carrying the caught exception.

        The exception is available as :attr:`exception` only after the ``with``
        block exits, since that is when it has been raised and caught. Reading it
        inside the block is a mistake worth naming rather than returning ``None``
        for, so it raises :class:`SemanticError`.
    """

    def __init__(self, expected: Union[Type[BaseException], tuple],
                 match: Optional[Union[str, re.Pattern]] = None) -> None:
        """
            :param expected: The exception type, or tuple of types, to expect.
            :param match: Optional pattern the exception's text must contain.
        """
        self._expected = expected
        self._match = match
        self._exception = None
        self._complete = False
        return

    @property
    def exception(self) -> BaseException:
        """
            The exception that was caught.

            :returns: The caught exception.

            :raises SemanticError: If read before the ``with`` block has exited.
        """
        if self._complete is False:
            raise SemanticError(
                "The 'exception' of a 'raises' block is only available after "
                "the block exits, because that is when the exception has been "
                "raised and caught.")

        return self._exception

    @property
    def value(self) -> BaseException:
        """
            Alias of :attr:`exception`.

            :returns: The caught exception.
        """
        return self.exception

    def __enter__(self) -> "RaisesContext":
        """
            :returns: This context, to be bound by the ``as`` clause.
        """
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        """
            Accept the expected exception; let anything else propagate.

            :param exc_type: Type of the raised exception, or ``None``.
            :param exc_value: The raised exception, or ``None``.
            :param exc_traceback: The traceback, unused.

            :returns: ``True`` to suppress the expected exception.

            :raises AssertionError: If no exception was raised, or if one was
                raised whose text does not match the requested pattern.
        """
        self._complete = True

        if exc_type is None:
            expected_name = _describe_exception_types(self._expected)
            raise AssertionError(
                "Expected {} to be raised, but the block completed "
                "normally.".format(expected_name))

        if not issubclass(exc_type, self._expected):
            # Not what was asked for. Propagating beats reporting a failure
            # here, because the real exception and its traceback are more
            # useful than an assertion describing it second-hand.
            return False

        if self._match is not None:
            found = str(exc_value)
            if re.search(self._match, found) is None:
                raise AssertionError(
                    "Expected {} matching {!r} to be raised. A {} was raised, "
                    "but its text does not match:{}{}".format(
                        _describe_exception_types(self._expected),
                        self._match if isinstance(self._match, str)
                        else self._match.pattern,
                        exc_type.__name__, os.linesep,
                        indent_lines(found, 1)))

        self._exception = exc_value

        return True


def raises(expected: Union[Type[BaseException], tuple],
           match: Optional[Union[str, re.Pattern]] = None) -> RaisesContext:
    """
        Assert that the ``with`` block raises the expected exception.

        Unlike ``expect_exception``, which marks a whole test as expected to
        raise, this scopes the expectation to the statements in the block, so a
        test can go on to make assertions about the exception it caught and about
        anything else.

        A different exception type is not caught. It propagates with its own
        traceback intact, which says more than an assertion describing it
        second-hand would.

        Example::

            from ccai import testbase

            with testbase.raises(ValueError):
                int("not a number")

            with testbase.raises(SchemaSemanticError) as caught:
                validate(spec=spec)

            assert "inst-a" in str(caught.exception)

            # Or match the text directly, without binding the exception.
            with testbase.raises(ValueError, match="invalid literal"):
                int("not a number")

        :param expected: The exception type, or a tuple of types, to expect.
        :param match: Optional pattern searched for in the exception's text,
            as a string or compiled pattern.

        :returns: A context manager binding the caught exception.

        :raises AssertionError: If the block raises nothing, or raises an
            expected type whose text does not match ``match``.
    """
    return RaisesContext(expected, match=match)


def _describe_exception_types(expected: Union[Type[BaseException], tuple]) -> str:
    """
        Name an exception type, or a tuple of them, for a failure message.

        :param expected: The type or tuple of types.

        :returns: A readable description.
    """
    if isinstance(expected, tuple):
        return " or ".join([item.__name__ for item in expected])

    return expected.__name__
