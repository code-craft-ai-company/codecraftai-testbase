=======================
Code Craft AI TestBase
=======================

Code Craft AI TestBase is a Python testing framework designed for automation testing with an emphasis on debuggability, readability, and resource-managed test execution. The framework provides structured discovery, dependency injection, sequencing, and results recording capabilities so complex test suites can remain isolated, extensible, and easy to troubleshoot.

Highlights
==========

- Test discovery and filtering with include/exclude expressions and metadata support.
- Dependency injection with session/package/test lifecycles and centralized resource management.
- Structured execution sequencing with diagnostics and result recording.
- JSON result recording plus result browsing support.
- Click-based CLI for running and managing tests.

Repository Structure
====================

- ``development/`` - Runtime environment scripts.
- ``repository-setup/`` - Repository homing and setup scripts.
- ``source/packages/`` - Package source code.
- ``source/tests/`` - ``unittest``-based tests.
- ``source/testbase/`` - TestBase framework tests.
- ``specs/`` - Requirements, design, and task documentation.
- ``userguide/`` - Standards, conventions, and documentation.

Environment Setup
=================

When working in a Codex container, use the setup script below:

.. code-block:: bash

   ./development/setup-agent-container

For local development environments, run the repository homing and virtual environment setup scripts:

.. code-block:: bash

   ./repository-setup/rehome-repository
   ./development/setup-envrionment

Running Tests
=============

Activate the virtual environment first:

.. code-block:: bash

   source .venv/bin/activate

Run ``unittest`` tests:

.. code-block:: bash

   python -m unittest discover -s source/tests -p "test_*.py"

Run TestBase tests:

.. code-block:: bash

   testbase testing run --root "source/testbase" --include ccai

Standards and Conventions
=========================

- Naming conventions: ``userguide/10-02-naming-conventions.rst``
- Code organization: ``userguide/10-01-code-organization.rst``
- Coding standards: ``userguide/10-00-coding-standards.rst``

Additional Resources
====================

- User guide entry point: ``userguide/userguide.rst``
- Design documentation: ``specs/design.md``
- Requirements: ``specs/requirements.md``
