"""
    .. module:: automojo.testbase.expressions
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for expressions.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from typing import Optional
from types import ModuleType

def parse_test_include_expression(expression: str, testmodule: Optional[ModuleType], method_prefix: str = "test"):
    """
        Parses a test include expression and returns its component parts for test discovery and filtering.

        This function supports two distinct workflows:

        1. **CLI Workflow** (testmodule is None): Parses full expressions from command-line arguments
           in the format ``(package).(module)@(testclass)#(testname)``.

        2. **Module Workflow** (testmodule is provided): Parses simplified expressions when debugging
           or running a test module directly. The package and module are extracted from the testmodule
           object, and the expression specifies only the testclass and/or testname.

        :param expression: A test include expression string. The format depends on the workflow:

            **CLI Workflow formats:**
                - ``pkg.mod`` - Package and module only
                - ``pkg.mod@TestClass`` - With test class
                - ``pkg.mod@TestClass#test_demo`` - Full specification
                - ``pkg.mod@#test_demo`` - Test name without class
                - ``pkg.subpkg.mod`` - Nested packages
                - ``mod`` - Module only (no package)

            **Module Workflow formats:**
                - ``*`` - Wildcard to match all tests in the module
                - ``TestClass`` - Test class only
                - ``TestClass#test_method`` - Test class and method
                - ``#test_method`` - Test method only (no class filter)

        :type expression: str

        :param testmodule: A Python module object containing tests. When provided, the function
            operates in Module Workflow mode, extracting package and module information from
            the module's ``__name__`` attribute. When ``None``, the function operates in CLI
            Workflow mode and parses the full expression.

        :type testmodule: Optional[ModuleType]

        :param method_prefix: The string prefix that identifies test methods. Test names extracted
            from expressions must start with this prefix. Defaults to ``"test"``.

        :type method_prefix: str

        :returns: A tuple of four optional strings representing the parsed expression components:

            - **expr_package** (Optional[str]): The package path (e.g., ``"pkg.subpkg"``).
              Set to ``None`` if no package is specified, or ``"*"`` for ``__main__`` modules.

            - **expr_module** (Optional[str]): The module name (e.g., ``"mod"``).
              Set to ``"*"`` for ``__main__`` modules.

            - **expr_testclass** (Optional[str]): The test class name (e.g., ``"TestClass"``).
              Set to ``None`` if no test class is specified or if empty (e.g., ``@#test_demo``).

            - **expr_testname** (Optional[str]): The test method name (e.g., ``"test_demo"``).
              Set to ``None`` if no test name is specified.

        :rtype: tuple[Optional[str], Optional[str], Optional[str], Optional[str]]

        :raises ValueError: Raised in the following conditions:

            - **Module Workflow with invalid characters**: When ``testmodule`` is provided and
              the expression contains ``.``, ``@``, or ``:`` characters. Module workflow
              expressions should only specify test class and/or test method.

              Error message: ``"parse_test_include_expression: The include expression for test
              module runs should only have a test class and test method."``

            - **Invalid test name prefix**: When a test name is extracted but does not start
              with the ``method_prefix``.

              Error message: ``"parse_test_include_expression: The testname component of the
              expression must start with the method_prefix='{prefix}'. expression'{expr}'"``

        **CLI Workflow Examples:**

        .. code-block:: python

            from automojo.testbase.expressions import parse_test_include_expression

            # Full expression with all components
            pkg, mod, cls, name = parse_test_include_expression(
                "mypackage.mymodule@TestClass#test_example",
                testmodule=None
            )
            # Returns: ("mypackage", "mymodule", "TestClass", "test_example")

            # Package and module only
            pkg, mod, cls, name = parse_test_include_expression(
                "mypackage.mymodule",
                testmodule=None
            )
            # Returns: ("mypackage", "mymodule", None, None)

            # Nested package
            pkg, mod, cls, name = parse_test_include_expression(
                "pkg.subpkg.mod@TestClass",
                testmodule=None
            )
            # Returns: ("pkg.subpkg", "mod", "TestClass", None)

            # Module only (no package)
            pkg, mod, cls, name = parse_test_include_expression(
                "mymodule",
                testmodule=None
            )
            # Returns: (None, "mymodule", None, None)

            # Test name without class (empty testclass)
            pkg, mod, cls, name = parse_test_include_expression(
                "pkg.mod@#test_demo",
                testmodule=None
            )
            # Returns: ("pkg", "mod", None, "test_demo")

        **Module Workflow Examples:**

        .. code-block:: python

            import sys
            from automojo.testbase.expressions import parse_test_include_expression

            # Assume we have a test module loaded
            test_module = sys.modules["mypackage.mymodule"]

            # Wildcard to match all tests
            pkg, mod, cls, name = parse_test_include_expression(
                "*",
                testmodule=test_module
            )
            # Returns: ("mypackage", "mymodule", None, None)

            # Specific test class
            pkg, mod, cls, name = parse_test_include_expression(
                "TestClass",
                testmodule=test_module
            )
            # Returns: ("mypackage", "mymodule", "TestClass", None)

            # Test class and method
            pkg, mod, cls, name = parse_test_include_expression(
                "TestClass#test_example",
                testmodule=test_module
            )
            # Returns: ("mypackage", "mymodule", "TestClass", "test_example")

            # Custom method prefix
            pkg, mod, cls, name = parse_test_include_expression(
                "TestClass#check_validation",
                testmodule=test_module,
                method_prefix="check"
            )
            # Returns: ("mypackage", "mymodule", "TestClass", "check_validation")

        **__main__ Module Handling:**

        When a test module is run directly (e.g., ``python test_module.py``), its ``__name__``
        is ``"__main__"``. In this case, the function returns wildcards for package and module
        to enable test discovery without exact path matching:

        .. code-block:: python

            # When testmodule.__name__ == "__main__"
            pkg, mod, cls, name = parse_test_include_expression(
                "*",
                testmodule=main_module  # where main_module.__name__ == "__main__"
            )
            # Returns: ("*", "*", None, None)

        .. seealso::

            - :class:`automojo.testbase.testcollector.TestCollector` - Uses parsed expressions
              for test discovery and filtering.
            - :func:`automojo.testbase.testcollector.find_included_modules_under_root` - Uses
              ``expr_package`` and ``expr_module`` for module discovery.
    """

    expr_package = None
    expr_module = None
    expr_testclass = None
    expr_testname = None

    # ==================================================================================
    # MODULE WORKFLOW (testmodule is not None)
    # ==================================================================================
    # When a testmodule is provided, we are running in debug/script mode where a test
    # module is executed directly (e.g., `python test_module.py` or via IDE debugger).
    # In this workflow, the package and module are derived from the testmodule object,
    # and the expression only specifies the testclass and/or testname.
    #
    # This workflow uses simplified expressions to avoid redundancy since the module
    # context is already known from the testmodule parameter.
    # ==================================================================================
    if testmodule is not None:

        # -----------------------------------------------------------------------------
        # MODULE WORKFLOW RESTRICTIONS
        # -----------------------------------------------------------------------------
        # In module workflow, expressions must NOT contain:
        #   - '.' (dot): Would indicate package/module path, which is redundant since
        #                we already have the module from testmodule parameter
        #   - '@' (at): Would indicate testclass separator in CLI format, but module
        #               workflow uses a simpler format without this delimiter
        #   - ':' (colon): Reserved delimiter that could cause parsing ambiguity
        #
        # These restrictions prevent ambiguous expressions and ensure clear separation
        # between CLI workflow (full expressions) and module workflow (simplified).
        # Valid module workflow expressions: "*", "TestClass", "TestClass#test_method"
        # -----------------------------------------------------------------------------
        if expression.find(".") > -1 or expression.find("@") > -1 or expression.find(":") > -1:
            raise ValueError("parse_test_include_expression: The include expression for test module runs should only have a " \
                             "test class and test method.")

        testmodule_name = testmodule.__name__

        # -----------------------------------------------------------------------------
        # __main__ HANDLING RATIONALE
        # -----------------------------------------------------------------------------
        # When a Python module is executed directly (e.g., `python test_module.py`),
        # its __name__ attribute is set to "__main__" instead of its actual module path.
        # This creates a challenge for test discovery because we cannot determine the
        # exact package/module path from the module object.
        #
        # Solution: Use wildcard values ("*") for both expr_package and expr_module.
        # This signals to the TestCollector that it should:
        #   1. Scan all available test roots for matching tests
        #   2. Not filter by package or module path
        #   3. Rely on testclass/testname filtering if specified
        #
        # This approach enables debugging tests by running the module directly while
        # still supporting test filtering by class and method name.
        #
        # Default to wildcards first, then override with exact values if we have
        # a proper module path (non-__main__ case).
        # -----------------------------------------------------------------------------
        expr_package = "*"
        expr_module = "*"

        # If the full path to the module was set correctly by the generic entry point,
        # then replace the package and module expressions with exact expressions so we
        # don't load code that does not need to be loaded when we are scanning for tests.
        # This optimization avoids unnecessary module imports during test discovery.
        if testmodule_name != "__main__":
            tm_name_parts = testmodule_name.split('.')
            if len(tm_name_parts) > 1:
                # Multi-component module name: "pkg.subpkg.mod" -> package="pkg.subpkg", module="mod"
                expr_package = '.'.join(tm_name_parts[:-1])
                expr_module = tm_name_parts[-1]
            # Note: Single-component module names keep the wildcard defaults since
            # there's no package component to extract.

        # Extract testname if present (indicated by '#' delimiter)
        if expression.find("#") > -1:
            expression, expr_testname = expression.split("#")
            if not expr_testname.startswith(method_prefix):
                raise ValueError("parse_test_include_expression: The testname component of the expression must start with the " \
                                "method_prefix=%r. expression%r" % (method_prefix, expression))

        # Handle wildcard expression "*" which matches all tests in the module
        if expression == "*":
            expr_testclass = None
        else:
            # Remaining expression (after removing testname) is the testclass
            # Empty string becomes None for consistency
            expr_testclass = expression if expression else None

    # ==================================================================================
    # CLI WORKFLOW (testmodule is None)
    # ==================================================================================
    # When testmodule is None, we are performing a command-line run where test
    # expressions are passed via CLI arguments (e.g., `testbase pkg.mod@TestClass#test_demo`).
    # The full expression must be parsed to extract all components.
    # ==================================================================================
    else:
        # -----------------------------------------------------------------------------
        # DELIMITER PRECEDENCE PARSING (Right-to-Left)
        # -----------------------------------------------------------------------------
        # The expression is parsed from RIGHT to LEFT using the following delimiter
        # precedence order:
        #
        #   1. '#' (hash) - HIGHEST PRIORITY - Separates testname from the rest
        #      Example: "pkg.mod@TestClass#test_demo" -> testname="test_demo"
        #
        #   2. '@' (at) - MEDIUM PRIORITY - Separates testclass from package.module
        #      Example: "pkg.mod@TestClass" -> testclass="TestClass"
        #
        #   3. '.' (dot) - LOWEST PRIORITY - Separates package components and module
        #      Example: "pkg.subpkg.mod" -> package="pkg.subpkg", module="mod"
        #
        # This right-to-left parsing ensures that:
        #   - Test names containing dots (unlikely but possible) are handled correctly
        #   - The most specific component (testname) is extracted first
        #   - Package paths with multiple dots are correctly split from the module
        #
        # The delimiter precedence matches the expression grammar:
        #   expression := package_module_expr ["@" testclass_expr] ["#" testname_expr]
        # -----------------------------------------------------------------------------

        # STEP 1: Extract testname (highest precedence delimiter '#')
        # Split on '#' first to isolate the testname component before processing
        # other delimiters. This prevents '#' in testnames from interfering with
        # package/module/class parsing.
        if expression.find("#") > -1:
            expression, expr_testname = expression.split("#")
            # Validate that testname starts with the required method prefix
            if not expr_testname.startswith(method_prefix):
                raise ValueError("parse_test_include_expression: The testname component of the expression must " \
                                "start with the method_prefix=%r. expression%r" % (method_prefix, expression))

        # STEP 2: Extract testclass (medium precedence delimiter '@')
        # After removing testname, split on '@' to isolate the testclass component.
        # The '@' delimiter separates the testclass from the package.module portion.
        if expression.find("@") > -1:
            expression, expr_testclass = expression.split("@")

        # Handle empty testclass case (e.g., "pkg.mod@#test_demo")
        # An empty string after '@' means no testclass filter, represented as None
        if expr_testclass == "":
            expr_testclass = None

        # STEP 3: Extract package and module (lowest precedence delimiter '.')
        # After removing testname and testclass, the remaining expression contains
        # the package.module path. Split on '.' to separate package from module.
        # Convention: All components except the last form the package path,
        #             the last component is the module name.
        comb_expr_comp = expression.split(".")
        if len(comb_expr_comp) > 1:
            # Multi-component path: "pkg.subpkg.mod" -> package="pkg.subpkg", module="mod"
            expr_package = ".".join(comb_expr_comp[:-1])
            expr_module = comb_expr_comp[-1]
        else:
            # Single component: "mod" -> package=None, module="mod"
            # No package specified, only module name
            expr_package = None
            expr_module = expression

    return expr_package, expr_module, expr_testclass, expr_testname
