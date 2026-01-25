# Automation Mojo TestBase

Automation Mojo TestBase is a Python testing framework designed for automation testing with an emphasis on debuggability, readability, and resource-managed test execution. The framework provides structured discovery, dependency injection, sequencing, and results recording capabilities so complex test suites can remain isolated, extensible, and easy to troubleshoot.【F:specs/requirements.md†L1-L129】【F:specs/design.md†L1-L120】

## Highlights

- Test discovery and filtering with include/exclude expressions and metadata support.【F:specs/requirements.md†L18-L55】
- Dependency injection with session/package/test lifecycles and centralized resource management.【F:specs/requirements.md†L56-L93】
- Structured execution sequencing with diagnostics and result recording.【F:specs/requirements.md†L94-L150】
- JSON result recording plus result browsing support.【F:specs/requirements.md†L151-L194】
- Click-based CLI for running and managing tests.【F:specs/requirements.md†L195-L223】

## Repository Structure

- `development/` - Runtime environment scripts.
- `repository-setup/` - Repository homing and setup scripts.
- `source/packages/` - Package source code.
- `source/tests/` - `unittest`-based tests.
- `source/testbase/` - TestBase framework tests.
- `specs/` - Requirements, design, and task documentation.
- `userguide/` - Standards, conventions, and documentation.

## Environment Setup

When working in a Codex container, use the setup script below:

```bash
./development/setup-agent-container
```

For local development environments, run the repository homing and virtual environment setup scripts:

```bash
./repository-setup/rehome-repository
./development/setup-envrionment
```

## Running Tests

Activate the virtual environment first:

```bash
source .venv/bin/activate
```

Run `unittest` tests:

```bash
python -m unittest discover -s source/tests -p "test_*.py"
```

Run TestBase tests:

```bash
testbase testing run --root "source/testbase" --include automojo
```

## Standards and Conventions

- Naming conventions: `userguide/10-02-naming-conventions.rst`
- Code organization: `userguide/10-01-code-organization.rst`
- Coding standards: `userguide/10-00-coding-standards.rst`

## Additional Resources

- User guide entry point: `userguide/userguide.rst`
- Design documentation: `specs/design.md`
- Requirements: `specs/requirements.md`
