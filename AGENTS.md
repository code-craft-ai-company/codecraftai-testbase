# Personality
AI Agents working in this repository should refer to themselves as an agent named 'AutomationX'.

# Project Overview


# Testing Conventions
The 'automojo-testbase' package repository utilizes the 'testbase' framework in order to test the functionality of the code.

# Code Naming Conventions
The code naming conventions of this repository follows the [Automation Mojo Python Naming Conventions](https://github.com/automationmojo/automojo-docs/blob/main/userguide/10-01-naming-conventions.rst)


# Code Structure
The code structure of this repository follows the [Automation Mojo Python Code Structure Standards](https://github.com/automationmojo/automojo-docs/blob/main/userguide/10-01-code-organization.rst)


# Coding Standards
The code in this repository is meant to be utilized by testing tools and test frameworks.  Therefore, the code must prioritize:

*  debuggability over performance
*  readability over conciseness

For all the code in this repository, follow the coding standards specified at [Coding Standards](https://github.com/automationmojo/automojo-docs/blob/main/userguide/10-00-coding-standards.rst)


# Environment Setup
When checking out the code for this repository in order to test changes, agents must:

* run the 'repository-setup/rehome-repository' script.  It creates a needed '.env' file.
* run the 'development/setup-envrionment' script in order to create the virtual environment.

# Running Tests
This repository uses `unittest` tests in order to test the `testbase` test framework code.  There are also 'testbase' tests included in this repository that are used to test the functionality of the `testbase` framework.

When you setup the environment, the '.venv/bin/activate' script is modified so that it will pull in the appropriate environment
variables from the '.env' file.  The environment setup script also creates an alias that makes it easy to run the 'testbase' command from the virtual environment command line.

## UnitTest
In order to run the unittest tests, you must first enter the virtual environment by running the command:

```
    source <repository-root>/.venv/bin/activate
```


For running the 'unittest' tests located under the folder '<repository-root>/source/tests', use the commands:

```
    cd <repository-root>

    python -m unittest discover -s source/tests -p "test_*.py"
```

## TestBase
In order to run the `testbase` tests, you must first enter the virtual environment by running the command:

```
    source <repository-root>/.venv/bin/activate
```

For running the `testbase` tests located under the folder '<repository-root>/source/testbase', use the commands:

``` 
    cd <repository-root>

    testbase testing run --root "<repository-root>/source/testbase" --include  automojo
```

# Project Specific Rules


# Pull Request Guidelines


# Packaging
Currently, this package is utilized using a reference to the github repository.  It is currently not published.
