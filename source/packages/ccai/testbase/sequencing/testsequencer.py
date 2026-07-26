"""
    .. module:: ccai.testbase.sequencing.testsequencer
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module for testsequencer.

    .. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""



__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Code Craft AI LLC"
__credits__ = []


from typing import Any, Dict, List, OrderedDict, Optional, Sequence, Tuple, Type, Union


import asyncio
import collections
import json
import os
import sys
import uuid

from io import TextIOWrapper
from types import TracebackType

from ccai.errors.exceptions import SemanticError

from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger
from ccai.xmodules.ximport import import_file
from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR
from ccai.xmodules.debugging import debugger_wellknown_breakpoint_code_append

from ccai.testbase import environment
from ccai.testbase.output.outputcontext import IOutputContext, SimpleOutputContext

from ccai.testbase.injection.injectionregistry import injection_registry
from ccai.testbase.origins.resourceorigin import ResourceOrigin

from ccai.testbase.coupling.configurationcoupling import ConfigurationCoupling
from ccai.testbase.coupling.integrationcoupling import IntegrationCoupling

from ccai.testbase.diagnostics import DiagnosticLabel, DiagnosticLabelRegistry, DiagnosticFilter
from ccai.testbase.markers import MetaFilter


from ccai.testbase.results.model.jobcontainer import JobContainer
from ccai.testbase.results.model.taskinggroup import TaskingGroup
from ccai.testbase.results.model.taskingresult import TaskingResult
from ccai.testbase.results.model.testcontainer import TestContainer
from ccai.testbase.results.model.testresult import TestResult

from ccai.testbase.results.recorders.resultrecorder import ResultRecorder

# Well-known result/diagnostic paths are resolved via the injected IOutputContext (see __init__).

from ccai.testbase.breakpoints import WELLKNOWN_BREAKPOINTS
from ccai.testbase.testcollector import TestCollector
from ccai.testbase.testgroup import TestGroup
from ccai.testbase.testref import TestRef

from ccai.testbase.sequencing.sequencersessionscope import SequencerSessionScope
from ccai.testbase.sequencing.sequencermodulescope import SequencerModuleScope
from ccai.testbase.sequencing.sequencertestscope import SequencerTestScope
from ccai.testbase.sequencing.sequencertestsetupscope import SequencerTestSetupScope

from ccai.testbase.constraints import ConstraintsCatalog

constraints_catalog = ConstraintsCatalog()

logger = getEnhancedLogger()


CONSTRAINT_IMPORT_INSERTION_POINT = "# ------- INSERT CONSTRAINT IMPORTS HERE -------"

FACTORY_IMPORT_INSERTION_POINT = "# ------- INSERT FACTORY IMPORTS HERE -------"


TEMPLATE_TESTRUN_SEQUENCE_MODULE = '''"""
    ======================================= CODE GENERATED - DO NOT EDIT =======================================
    This is a code generated execution sequence document, do not manually edit this document.  The 'testbase'
    test framework generates this document in order to layout the test run scopes, parameter creations, and
    test calls in a user ledgible way which is easy to read and also to debug.
"""

__traceback_format_policy__ = "Brief"

import logging

from ccai.xmodules.xlogging.enhancedloggers import getEnhancedLogger

from ccai.testbase.constraints import ConstraintsCatalog

logger = getEnhancedLogger()

constraints_catalog = ConstraintsCatalog()

{}

{}

'''.format(CONSTRAINT_IMPORT_INSERTION_POINT, FACTORY_IMPORT_INSERTION_POINT)


class TEST_SEQUENCER_PHASES:
    """
        Indicates the current state of the sequencer.
    """
    Initial = 0
    Discovery = 1
    Collection = 2
    Graph = 3
    Traversal = 4


class TestSequencer:
    """
        The :class:`TestSequencer` is a state machine that orchestrates the flow of a test run through
        distinct phases: Initial, Discovery, Collection, Graph, and Traversal. It ensures that the steps
        of the test flow are consistent between runs.

        Phase Transitions:
            The sequencer progresses through the following phases:

            1. **Initial** (Phase 0): Sequencer created, not yet started. This is the state after
               construction but before any discovery or execution methods are called.

            2. **Discovery** (Phase 1): Test modules are being discovered and imported. Entered when
               :meth:`discover` is called. The sequencer uses a :class:`TestCollector` to process
               include/exclude expressions and find test references.

            3. **Collection** (Phase 2): Test references are being collected and organized. The
               :class:`TestCollector` gathers test function references and applies metadata filters.

            4. **Graph** (Phase 3): Test tree structure is being built. The hierarchical test tree
               (:class:`TestGroup` and :class:`TestRef` nodes) is constructed from collected references.

            5. **Traversal** (Phase 4): Tests are being executed via the sequence document. Entered when
               :meth:`execute_tests` is called. The generated sequence document is imported and executed.

        Scope Stack Management:
            The sequencer maintains a scope stack (``_scope_stack``) that tracks the current execution
            context hierarchy. The stack contains tuples of ``(scope_name, scope_id)`` representing
            the nested scope contexts during test execution.

            Scope Stack Operations:
                - :meth:`scope_id_create`: Creates a new scope ID (UUID) and pushes it onto the stack.
                  Returns a tuple of ``(parent_id, scope_id)`` for result hierarchy tracking.
                - :meth:`scope_id_push`: Manually pushes a scope entry onto the stack.
                - :meth:`scope_id_pop`: Removes the top scope from the stack. Raises ``RuntimeError``
                  if the scope name doesn't match the expected name (detects scope imbalance).
                - :meth:`get_top_scope_id`: Returns the scope ID at the top of the stack without
                  modifying the stack.

            Scope Hierarchy Example::

                Session Scope (root)
                ├── Module Scope (package.module)
                │   ├── Test Setup Scope (setup:test_name)
                │   │   └── Test Scope (test_name)
                │   └── Test Setup Scope (setup:test_name_2)
                │       └── Test Scope (test_name_2)
                └── Module Scope (package.module_2)
                    └── ...

        Usage Example::

            # Create and use a TestSequencer within a TestJob
            with TestSequencer(jobtitle, root, includes, excludes, metafilters) as sequencer:
                # Phase 1-3: Discovery and collection
                test_count = sequencer.discover()

                if test_count > 0:
                    # Integration setup
                    sequencer.attach_to_framework()
                    sequencer.attach_to_environment()

                    # Generate sequence document (Phase 3 -> 4 transition)
                    sequencer.generate_testrun_sequence_document(output_file)

                    # Execute tests (Phase 4: Traversal)
                    sequencer.execute_tests(runid, recorder)

        See Also:
            - :class:`TEST_SEQUENCER_PHASES`: Enumeration of sequencer phases
            - :class:`TestJob`: High-level orchestrator that uses TestSequencer
            - :class:`SequencerSessionScope`: Session-level scope context manager
            - :class:`SequencerModuleScope`: Module-level scope context manager
            - :class:`SequencerTestScope`: Test-level scope context manager
    """

    def __init__(self, jobtitle: str, root: str, includes: Sequence[str], excludes: Sequence[str], metafilters: List[MetaFilter], job_seed: int = None, output_context: Optional[IOutputContext] = None):
        """
            Creates a :class:`TestSequencer` object which is used to discover tests and control the
            flow of a test run through its various phases.

            :param jobtitle: The name of the test job. Used for identification in results and logs.
            :param root: The path to the root folder that is the base of the tests. All test discovery
                starts from this directory.
            :param includes: List of expressions used to determine which tests to include. Expression
                format: ``(scope):(package).(package)@(module)#(testname)``
            :param excludes: List of expressions used to determine which tests to exclude from the
                included tests. Uses the same format as includes.
            :param metafilters: List of :class:`MetaFilter` expressions used to filter tests by
                metadata attributes such as priority, feature tags, etc.

            Instance Attributes:
                After construction, the sequencer initializes the following internal state:

                - ``_jobtitle``: The job title for identification
                - ``_root``: Root path for test discovery
                - ``_includes``: Include expressions for test filtering
                - ``_excludes``: Exclude expressions for test filtering
                - ``_metafilters``: Metadata filter expressions
                - ``_integrations``: Dictionary of :class:`IntegrationCoupling` instances
                - ``_configurations``: Dictionary of :class:`ConfigurationCoupling` instances
                - ``_references``: List of discovered :class:`TestRef` objects
                - ``_scope_roots``: List of scope root nodes
                - ``_import_errors``: Dictionary of import errors encountered during discovery
                - ``_testtree``: The hierarchical :class:`TestGroup` tree structure
                - ``_sequence_document``: Path to the generated sequence document
                - ``_recorder``: The :class:`ResultRecorder` for recording test results
                - ``_root_result``: The root :class:`JobContainer` result node
                - ``_scope_stack``: Stack of ``(scope_name, scope_id)`` tuples for context tracking

            Example::

                from ccai.testbase.sequencing.testsequencer import TestSequencer
                from ccai.testbase.markers import MetaFilter

                # Create a sequencer for a specific test package
                sequencer = TestSequencer(
                    jobtitle="My Test Suite",
                    root="/path/to/tests",
                    includes=["ccai.tests@*"],
                    excludes=["ccai.tests@test_slow_*"],
                    metafilters=[MetaFilter("priority", "high")]
                )
        """
        super().__init__()

        self._jobtitle = jobtitle
        self._root = root
        self._includes = includes
        self._excludes = excludes
        self._metafilters = metafilters
        self._integrations: Dict[str, IntegrationCoupling] = {}
        self._configurations: Dict[str, ConfigurationCoupling] = {}
        self._references = []
        self._scope_roots = []
        self._import_errors = {}
        self._testtree = None
        self._sequence_document = None
        self._recorder = None
        self._root_result = None
        self._scope_stack = []
        self._job_seed = job_seed

        self._output_context = output_context if output_context is not None else SimpleOutputContext()

        return

    @property
    def output_context(self) -> IOutputContext:
        """
            The :class:`IOutputContext` used to resolve where this sequencer writes run artefacts.
        """
        return self._output_context

    def __enter__(self):
        """
            Provides 'with' statement scope semantics for the :class:`TestSequencer`
        """
        return self

    def __exit__(self, ex_type: Type, ex_inst: BaseException, ex_tb: TracebackType) -> bool:
        """
            Provides 'with' statement scope semantics for the :class:`TestSequencer`
        """
        return False

    @property
    def import_errors(self):
        """
            A list of import errors that were encountered during the sequencing of the test run.
        """
        return self._import_errors

    @property
    def references(self):
        """
            A list of :class:`TestRef` objects that are included in the test run.
        """
        return self._references

    @property
    def testnodes(self):
        """
            Returns the root-level test nodes from the test tree.

            This property extracts the top-level nodes from the test tree structure, which represent
            the root packages or modules containing tests.

            :returns: A list of root-level test nodes (:class:`TestGroup` or :class:`TestRef` objects).

            Note:
                This property should only be accessed after :meth:`discover` has been called and
                the test tree has been built.
        """
        root_nodes = [tnode for _, tnode in self._testtree]
        return root_nodes

    @property
    def testtree(self):
        """
            Returns the hierarchical test tree structure.

            The test tree is a :class:`TestGroup` object that contains the complete hierarchy of
            discovered tests organized by package and module. The tree is built during the
            discovery phase.

            :returns: The root :class:`TestGroup` node of the test tree, or ``None`` if discovery
                has not been performed.

            Tree Structure:
                The test tree follows this hierarchy::

                    TestGroup (root)
                    ├── TestGroup (package)
                    │   ├── TestGroup (module)
                    │   │   ├── TestRef (test_function_1)
                    │   │   └── TestRef (test_function_2)
                    │   └── TestGroup (another_module)
                    │       └── TestRef (test_function_3)
                    └── TestGroup (another_package)
                        └── ...

            Note:
                This property should only be accessed after :meth:`discover` has been called.
        """
        return self._testtree

    def attach_to_environment(self, **kwargs):
        """
            Invokes the ``attach_to_environment`` lifecycle method on all registered integrations
            and configurations, allowing them to validate and connect to the test environment.

            This method is called during the integration phase of test execution, after
            :meth:`attach_to_framework` but before test execution begins. It performs the following:

            1. Creates a password-masked copy of the environment variables
            2. Collects information about loaded Python packages
            3. Writes startup configuration to ``startup-configuration.json``
            4. Calls ``attach_to_environment`` on each registered :class:`IntegrationCoupling`
            5. Calls ``attach_to_environment`` on each registered :class:`ConfigurationCoupling`

            :param kwargs: Additional keyword arguments passed to each coupling's
                ``attach_to_environment`` method.

            :returns: None

            Output Files:
                Creates ``startup-configuration.json`` in the test results directory containing:

                - ``command``: The command line used to invoke the test run
                - ``environment``: Environment variables (with passwords masked)
                - ``packages``: Dictionary of loaded Python packages and their file paths

            Phase Context:
                This method should be called after :meth:`discover` and :meth:`attach_to_framework`
                but before :meth:`generate_testrun_sequence_document`.

            Example::

                # Typical usage within TestJob.execute()
                sequencer.attach_to_framework()
                sequencer.attach_to_environment()  # Called here
                sequencer.generate_testrun_sequence_document(output_file)

            See Also:
                - :meth:`attach_to_framework`: Called before this method
                - :meth:`establish_presence`: Called after environment attachment
                - :meth:`create_password_masked_environment`: Creates masked environment copy
        """

        results_dir = self._output_context.get_test_results_dir()

        environment_dict = self.create_password_masked_environment()

        package_dict = collections.OrderedDict()

        package_names = [k for k in sys.modules.keys()]
        package_names.sort()
        for pname in package_names:
            nxtmod = sys.modules[pname]
            if pname.find(".") == -1 and hasattr(nxtmod, "__file__"):
                package_dict[pname] = nxtmod.__file__

        startup_dict = collections.OrderedDict([
            ("command", " ".join(sys.argv)),
            ("environment", environment_dict),
            ("packages", package_dict)
        ])

        startup_full = os.path.join(results_dir, "startup-configuration.json")
        with open(startup_full, 'w') as suf:
            json.dump(startup_dict, suf, indent=True)

        integ_type: IntegrationCoupling

        for _, integ_type in self._integrations.items():
            integ_type.attach_to_environment(**kwargs)

        config_type: ConfigurationCoupling

        for _, config_type in self._configurations.items():
            config_type.attach_to_environment(**kwargs)

        return

    def attach_to_framework(self, **kwargs):
        """
            Invokes the ``attach_to_framework`` lifecycle method on all registered integrations,
            allowing them to register with the test framework.

            This method is called during the integration phase of test execution, after
            :meth:`discover` but before :meth:`attach_to_environment`. It iterates over all
            registered :class:`IntegrationCoupling` instances and calls their
            ``attach_to_framework`` method.

            :param kwargs: Additional keyword arguments passed to each integration's
                ``attach_to_framework`` method.

            :returns: None

            Phase Context:
                This method should be called after :meth:`discover` has completed successfully
                and before :meth:`attach_to_environment`.

            Integration Lifecycle Order:
                1. ``attach_to_framework`` (this method) - Register with test framework
                2. ``attach_to_environment`` - Validate configuration
                3. ``collect_resources`` - Acquire external resources
                4. ``establish_presence`` - Verify resource availability

            Example::

                # Typical usage within TestJob.execute()
                test_count = sequencer.discover()
                if test_count > 0:
                    sequencer.attach_to_framework()  # Called here
                    sequencer.attach_to_environment()

            See Also:
                - :meth:`attach_to_environment`: Called after this method
                - :class:`IntegrationCoupling`: Base class for integrations
        """

        integ_type: IntegrationCoupling

        for _, integ_type in self._integrations.items():
            integ_type.attach_to_framework(**kwargs)

        return

    def collect_resources(self):
        """
            Invokes the ``collect_resources`` lifecycle method on all registered integrations,
            allowing them to acquire shared resources required for testing.

            This method is called during the integration phase of test execution, after
            :meth:`attach_to_environment` but before :meth:`establish_presence`. It iterates
            over all registered :class:`IntegrationCoupling` instances and calls their
            ``collect_resources`` method.

            :returns: None

            Phase Context:
                This method should be called after :meth:`attach_to_environment` has completed
                and before :meth:`establish_presence`.

            Integration Lifecycle Order:
                1. ``attach_to_framework`` - Register with test framework
                2. ``attach_to_environment`` - Validate configuration
                3. ``collect_resources`` (this method) - Acquire external resources
                4. ``establish_presence`` - Verify resource availability

            Example::

                # Typical usage within TestJob.execute()
                sequencer.attach_to_framework()
                sequencer.attach_to_environment()
                sequencer.collect_resources()  # Called here
                sequencer.establish_presence()

            See Also:
                - :meth:`attach_to_environment`: Called before this method
                - :meth:`establish_presence`: Called after this method
                - :class:`IntegrationCoupling`: Base class for integrations
        """

        integ_type: IntegrationCoupling

        for _, integ_type in self._integrations.items():
            integ_type.collect_resources()

        return

    def create_job_result_container(self, scope_id: str, scope_name: str) -> JobContainer:
        """
            Factory method for creating a :class:`JobContainer` result container.

            Creates a new :class:`JobContainer` instance that serves as the root result node
            for a test job. This container holds the aggregated results of all tests executed
            within the job.

            :param scope_id: The unique identifier (UUID) for this scope. Typically the run ID
                for the root job container.
            :param scope_name: The name of the scope, typically ``"<session>"`` for the root
                job container.

            :returns: A new :class:`JobContainer` instance.

            Scope Stack Context:
                The job container is created at the session level and represents the root of
                the result hierarchy. Its scope_id becomes the parent_id for all module-level
                containers.

            Example::

                # Create the root result container for a test run
                root_result = sequencer.create_job_result_container(runid, "<session>")
                recorder.record(root_result)

            See Also:
                - :meth:`create_test_result_container`: Creates module-level containers
                - :meth:`create_test_result_node`: Creates individual test results
                - :class:`JobContainer`: The result container class
        """
        rcontainer = JobContainer(scope_id, scope_name)
        return rcontainer

    def create_password_masked_environment(self) -> OrderedDict[str, str]:
        """
            Creates copy of the environment for writing to a file with the passwords masked.
        """
        environment_dict = collections.OrderedDict()

        env_keys = [k for k in os.environ.keys()]
        env_keys.sort()
        for ek in env_keys:
            environment_dict[ek] = os.environ[ek]

        for key in environment_dict.keys():
            if key.find("PASSWORD") > -1:
                environment_dict[key] = "(hidden)"
        
        return environment_dict

    def create_tasking_group(self, scope_id: str, name: str, parent_inst: str) -> TaskingGroup:
        """
            Factory method for creating a :class:`TaskingGroup` result group.

            Creates a new :class:`TaskingGroup` instance that groups related tasking results
            together within the result hierarchy.

            :param scope_id: The unique identifier (UUID) for this tasking group.
            :param name: The name of the tasking group.
            :param parent_inst: The scope ID of the parent result node.

            :returns: A new :class:`TaskingGroup` instance.

            See Also:
                - :meth:`create_tasking_result`: Creates individual tasking results
                - :class:`TaskingGroup`: The tasking group class
        """
        tgrp = TaskingGroup(scope_id, name, parent_inst)
        return tgrp
    
    def create_tasking_result(self, scope_id: str, name: str, parent_inst: str) -> TaskingResult:
        """
            Factory method for creating a :class:`TaskingResult` result node.

            Creates a new :class:`TaskingResult` instance that represents the result of
            an individual tasking operation within the result hierarchy.

            :param scope_id: The unique identifier (UUID) for this tasking result.
            :param name: The name of the tasking result.
            :param parent_inst: The scope ID of the parent result node.

            :returns: A new :class:`TaskingResult` instance.

            See Also:
                - :meth:`create_tasking_group`: Creates tasking groups
                - :class:`TaskingResult`: The tasking result class
        """
        tresult = TaskingResult(scope_id, name, parent_inst) 
        return tresult

    def create_test_result_container(self, scope_id: str, scope_name: str, parent_inst: str) -> TestContainer:
        """
            Factory method for creating a :class:`TestContainer` result container.

            Creates a new :class:`TestContainer` instance that serves as a container for
            test results at the module level. This container groups all test results from
            a single test module.

            :param scope_id: The unique identifier (UUID) for this scope.
            :param scope_name: The name of the scope, typically the module name
                (e.g., ``"package.module"``).
            :param parent_inst: The scope ID of the parent result node (typically the
                session or parent module container).

            :returns: A new :class:`TestContainer` instance.

            Scope Stack Context:
                Test containers are created when entering a module scope via
                :class:`SequencerModuleScope`. The container's scope_id becomes the
                parent_id for all test results within that module.

            Example::

                # Created internally by SequencerModuleScope.__enter__
                parent_id, scope_id = sequencer.scope_id_create("package.module")
                container = sequencer.create_test_result_container(
                    scope_id, "package.module", parent_id
                )
                recorder.record(container)

            See Also:
                - :meth:`create_job_result_container`: Creates the root job container
                - :meth:`create_test_result_node`: Creates individual test results
                - :class:`TestContainer`: The test container class
                - :class:`SequencerModuleScope`: Uses this method to create containers
        """
        rcontainer = TestContainer(scope_id, scope_name, parent_inst)
        return rcontainer
    
    def create_test_result_node(self, scope_id: str, name: str, monikers: List[str], pivots: OrderedDict[str, Any], parent_inst: str) -> TestResult:
        """
            Factory method for creating a :class:`TestResult` result node.

            Creates a new :class:`TestResult` instance that represents the result of an
            individual test function execution. This is the leaf node in the result hierarchy.

            :param scope_id: The unique identifier (UUID) for this test result.
            :param name: The name of the test function.
            :param monikers: List of string identifiers for parameterized test instances.
                These are extracted from the ``notables`` parameter values and used to
                distinguish different parameter combinations.
            :param pivots: Ordered dictionary of pivot values for parameterized tests.
                Contains the actual parameter values used for this test instance.
            :param parent_inst: The scope ID of the parent result node (typically the
                module container).

            :returns: A new :class:`TestResult` instance.

            Scope Stack Context:
                Test results are created when entering a test scope via
                :class:`SequencerTestScope`. The result is previewed with the recorder
                on entry and recorded on exit.

            Example::

                # Created internally by SequencerTestScope.__enter__
                parent_id, scope_id = sequencer.scope_id_create("test_function")
                result = sequencer.create_test_result_node(
                    scope_id, "test_function", monikers, pivots, parent_id
                )
                recorder.preview(result)
                # ... test execution ...
                result.mark_passed()
                recorder.record(result)

            See Also:
                - :meth:`create_test_result_container`: Creates module-level containers
                - :class:`TestResult`: The test result class
                - :class:`SequencerTestScope`: Uses this method to create results
        """
        rnode = TestResult(scope_id, name, parent_inst, monikers, pivots)
        return rnode

    def diagnostic_capture_pre_testrun(self, level: int=9):
        """
        Captures diagnostic information from all registered integrations before test execution.

        This method is called during the pre-run phase of test execution to collect diagnostic
        information about the initial state of the test environment. It iterates over all
        registered integration couplings and invokes their ``diagnostic`` method with the
        pre-run diagnostic label.

        The diagnostic capture only occurs if pre-run diagnostics are enabled via the
        ``AM_DIAGNOSTICS_PRERUN`` runtime variable (typically set by the ``--prerun-diagnostic``
        CLI option).

        :param level: The maximum diagnostic level to capture (1-9). Higher levels indicate
            more detailed diagnostic information. Defaults to 9 (maximum detail).

            * Levels 1-3: Basic diagnostic information (quick status checks)
            * Levels 4-6: Standard diagnostic information (normal debugging)
            * Levels 7-9: Detailed diagnostic information (deep investigation)

        :returns: None. Diagnostic files are written to the diagnostic output folder.

        Diagnostic Output:
            When enabled, diagnostics are written to::

                <test_results_dir>/diagnostics/prerun-diagnostic/

            Each integration coupling creates its own subfolder within this directory.

        Example Usage::

            # Called internally by TestJob during test execution
            sequencer.diagnostic_capture_pre_testrun(level=9)

            # With custom diagnostic level for basic diagnostics only
            sequencer.diagnostic_capture_pre_testrun(level=3)

        Note:
            This method is typically called by :meth:`TestJob.fire_diagnostic_capture_pre_testrun`
            rather than being invoked directly. The method silently returns without action if
            pre-run diagnostics are not enabled.

        See Also:
            - :meth:`diagnostic_capture_post_testrun`: Captures post-run diagnostics
            - :class:`ccai.testbase.diagnostics.DiagnosticLabel`: Diagnostic stage labels
            - :meth:`ccai.testbase.coupling.integrationcoupling.IntegrationCoupling.diagnostic`:
              Integration method called for each registered coupling
        """
        
        # ============================================================================
        # DIAGNOSTIC CAPTURE FLOW - PRE-RUN PHASE
        # ============================================================================
        # This method implements the pre-run diagnostic capture as part of the test
        # execution lifecycle. The flow is:
        #
        # 1. Check if pre-run diagnostics are enabled via runtime variable
        # 2. If enabled, determine the diagnostic label (prerun-diagnostic)
        # 3. Create/get the diagnostic output folder path
        # 4. Iterate over all registered integration couplings
        # 5. Call each integration's diagnostic() method to capture data
        #
        # The diagnostic capture occurs AFTER integration setup but BEFORE test
        # execution begins, allowing capture of the initial test environment state.
        # ============================================================================
        
        # Step 1: Check if pre-run diagnostics are enabled
        # The AM_DIAGNOSTICS_PRERUN runtime variable is set by the --prerun-diagnostic
        # CLI option. If not set or False, we skip the entire capture process.
        prerun_info = environment.diagnostics_prerun_enabled()

        if prerun_info is not None and prerun_info == True:
            # Step 2: Use the well-known pre-run diagnostic label
            # This label identifies the diagnostic stage and is used for folder naming
            label = DiagnosticLabel.PRERUN_DIAGNOSTIC
            
            # Check if this label should be captured based on filter settings
            if not DiagnosticFilter.should_capture_label(label):
                return
            
            # Step 3: Create the diagnostic folder structure
            # output_context.get_diagnostics_dir() creates: <test_results_dir>/diagnostics/<label>/
            # The folder is created automatically if it doesn't exist
            diagnostic_root = self._output_context.get_diagnostics_dir(label)

            # Step 4-5: Iterate over all registered integrations and capture diagnostics
            # Each integration coupling implements its own diagnostic() method to capture
            # integration-specific diagnostic information (logs, status, configuration, etc.)
            # Apply diagnostic filtering to determine which integrations should be captured
            for integ_name, integ_type in self._integrations.items():
                # Check if this integration should be captured based on filter settings
                if DiagnosticFilter.should_capture_integration(integ_name):
                    integ_type.diagnostic(label, level, diagnostic_root)

        return

    def diagnostic_capture_post_testrun(self, level: int=9):
        """
        Captures diagnostic information from all registered integrations after test execution.

        This method is called during the post-run phase of test execution to collect diagnostic
        information about the final state of the test environment. It iterates over all
        registered integration couplings and invokes their ``diagnostic`` method with the
        post-run diagnostic label.

        The diagnostic capture only occurs if post-run diagnostics are enabled via the
        ``AM_DIAGNOSTICS_POSTRUN`` runtime variable (typically set by the ``--postrun-diagnostic``
        CLI option).

        :param level: The maximum diagnostic level to capture (1-9). Higher levels indicate
            more detailed diagnostic information. Defaults to 9 (maximum detail).

            * Levels 1-3: Basic diagnostic information (quick status checks)
            * Levels 4-6: Standard diagnostic information (normal debugging)
            * Levels 7-9: Detailed diagnostic information (deep investigation)

        :returns: None. Diagnostic files are written to the diagnostic output folder.

        Diagnostic Output:
            When enabled, diagnostics are written to::

                <test_results_dir>/diagnostics/postrun-diagnostic/

            Each integration coupling creates its own subfolder within this directory.

        Example Usage::

            # Called internally by TestJob during test execution
            sequencer.diagnostic_capture_post_testrun(level=9)

            # With custom diagnostic level for standard diagnostics
            sequencer.diagnostic_capture_post_testrun(level=5)

        Note:
            This method is typically called by :meth:`TestJob.fire_diagnostic_capture_post_testrun`
            rather than being invoked directly. The method silently returns without action if
            post-run diagnostics are not enabled.

        See Also:
            - :meth:`diagnostic_capture_pre_testrun`: Captures pre-run diagnostics
            - :class:`ccai.testbase.diagnostics.DiagnosticLabel`: Diagnostic stage labels
            - :meth:`ccai.testbase.coupling.integrationcoupling.IntegrationCoupling.diagnostic`:
              Integration method called for each registered coupling
        """
        # ============================================================================
        # DIAGNOSTIC CAPTURE FLOW - POST-RUN PHASE
        # ============================================================================
        # This method implements the post-run diagnostic capture as part of the test
        # execution lifecycle. The flow mirrors the pre-run capture:
        #
        # 1. Check if post-run diagnostics are enabled via runtime variable
        # 2. If enabled, determine the diagnostic label (postrun-diagnostic)
        # 3. Create/get the diagnostic output folder path
        # 4. Iterate over all registered integration couplings
        # 5. Call each integration's diagnostic() method to capture data
        #
        # The diagnostic capture occurs AFTER test execution completes but BEFORE
        # finalization, allowing capture of the final test environment state including
        # any changes that occurred during testing.
        # ============================================================================
        
        # Step 1: Check if post-run diagnostics are enabled
        # The AM_DIAGNOSTICS_POSTRUN runtime variable is set by the --postrun-diagnostic
        # CLI option. If not set or False, we skip the entire capture process.
        postrun_info = environment.diagnostics_postrun_enabled()

        if postrun_info is not None and postrun_info == True:

            # Step 2: Use the well-known post-run diagnostic label
            # This label identifies the diagnostic stage and is used for folder naming
            label = DiagnosticLabel.POSTRUN_DIAGNOSTIC
            
            # Check if this label should be captured based on filter settings
            if not DiagnosticFilter.should_capture_label(label):
                return
            
            # Step 3: Create the diagnostic folder structure
            # output_context.get_diagnostics_dir() creates: <test_results_dir>/diagnostics/<label>/
            # The folder is created automatically if it doesn't exist
            diagnostic_root = self._output_context.get_diagnostics_dir(label)

            # Step 4-5: Iterate over all registered integrations and capture diagnostics
            # Each integration coupling implements its own diagnostic() method to capture
            # integration-specific diagnostic information (logs, status, configuration, etc.)
            # Apply diagnostic filtering to determine which integrations should be captured
            for integ_name, integ_type in self._integrations.items():
                # Check if this integration should be captured based on filter settings
                if DiagnosticFilter.should_capture_integration(integ_name):
                    integ_type.diagnostic(label, level, diagnostic_root)

        return

    def diagnostic_capture_custom(self, label: str, level: int=9):
        """
        Captures diagnostic information from all registered integrations using a custom label.

        This method enables diagnostic capture at custom-defined points during test execution,
        beyond the standard pre-run and post-run stages. It allows integration couplings to
        collect diagnostic data at specialized checkpoints defined by the user.

        Unlike the pre-run and post-run methods, this method does not check runtime variables
        for enablement - it captures diagnostics immediately when called. The caller is
        responsible for determining when custom diagnostic capture should occur.

        :param label: The custom diagnostic label identifying this capture point. Should be
            a registered label from :class:`DiagnosticLabelRegistry` or a custom string
            following the naming convention of lowercase words separated by hyphens
            (e.g., "checkpoint-diagnostic", "mid-test-diagnostic").
        :param level: The maximum diagnostic level to capture (1-9). Higher levels indicate
            more detailed diagnostic information. Defaults to 9 (maximum detail).

            * Levels 1-3: Basic diagnostic information (quick status checks)
            * Levels 4-6: Standard diagnostic information (normal debugging)
            * Levels 7-9: Detailed diagnostic information (deep investigation)

        :returns: None. Diagnostic files are written to the diagnostic output folder.

        Diagnostic Output:
            Diagnostics are written to::

                <test_results_dir>/diagnostics/<label>/

            Each integration coupling creates its own subfolder within this directory.

        Example Usage::

            from ccai.testbase.diagnostics import DiagnosticLabelRegistry

            # Register a custom diagnostic label
            DiagnosticLabelRegistry.register("checkpoint-diagnostic", "Test checkpoint")

            # Capture diagnostics at the custom checkpoint
            sequencer.diagnostic_capture_custom("checkpoint-diagnostic", level=5)

            # Capture with maximum detail
            sequencer.diagnostic_capture_custom("mid-test-diagnostic", level=9)

        Note:
            This method captures diagnostics immediately without checking runtime variables.
            For conditional capture based on configuration, the caller should check the
            appropriate conditions before calling this method.

        See Also:
            - :meth:`diagnostic_capture_pre_testrun`: Captures pre-run diagnostics
            - :meth:`diagnostic_capture_post_testrun`: Captures post-run diagnostics
            - :class:`ccai.testbase.diagnostics.DiagnosticLabelRegistry`: Registry for
              custom diagnostic labels
            - :meth:`ccai.testbase.coupling.integrationcoupling.IntegrationCoupling.diagnostic`:
              Integration method called for each registered coupling
        """
        # ============================================================================
        # DIAGNOSTIC CAPTURE FLOW - CUSTOM LABEL
        # ============================================================================
        # This method implements custom diagnostic capture for user-defined stages.
        # Unlike pre-run and post-run, this method:
        #
        # 1. Does NOT check runtime variables - captures immediately when called
        # 2. Uses the provided custom label for folder naming
        # 3. Creates the diagnostic output folder path
        # 4. Iterates over all registered integration couplings
        # 5. Calls each integration's diagnostic() method to capture data
        #
        # The caller is responsible for determining when to call this method and
        # whether capture should occur based on their own conditions.
        # ============================================================================

        # Check if this label should be captured based on filter settings
        if not DiagnosticFilter.should_capture_label(label):
            return

        # Create the diagnostic folder structure using the custom label
        # output_context.get_diagnostics_dir() creates: <test_results_dir>/diagnostics/<label>/
        # The folder is created automatically if it doesn't exist
        diagnostic_root = self._output_context.get_diagnostics_dir(label)

        # Iterate over all registered integrations and capture diagnostics
        # Each integration coupling implements its own diagnostic() method to capture
        # integration-specific diagnostic information (logs, status, configuration, etc.)
        # Apply diagnostic filtering to determine which integrations should be captured
        for integ_name, integ_type in self._integrations.items():
            # Check if this integration should be captured based on filter settings
            if DiagnosticFilter.should_capture_integration(integ_name):
                integ_type.diagnostic(label, level, diagnostic_root)

        return

    def discover(self, test_module=None, include_integrations: bool=True) -> int:
        """
            Initiates the discovery phase of the test run, transitioning the sequencer from
            the Initial phase through Discovery, Collection, and Graph phases.

            This method creates a :class:`TestCollector` and uses it to discover test functions
            based on the configured include/exclude expressions and metadata filters. The
            discovered tests are organized into a hierarchical test tree structure.

            :param test_module: Optional module object to limit discovery to a single module.
                When provided, discovery is restricted to tests within this module only.
                Defaults to ``None`` for full discovery.
            :param include_integrations: Whether to collect integration and configuration
                couplings after discovering tests. Defaults to ``True``. Set to ``False``
                for query-only operations that don't need integration setup.

            :returns: The count of discovered tests. Returns 0 if no tests match the
                include/exclude criteria.

            Phase Transitions:
                This method transitions the sequencer through multiple phases:

                1. **Initial → Discovery**: Begins when this method is called
                2. **Discovery → Collection**: After ``collect_references`` completes
                3. **Collection → Graph**: After ``finalize_collection`` builds the test tree

            Side Effects:
                After successful discovery, the following instance attributes are populated:

                - ``_testtree``: The hierarchical :class:`TestGroup` tree structure
                - ``_references``: List of discovered :class:`TestRef` objects
                - ``_integrations``: Dictionary of :class:`IntegrationCoupling` instances
                  (if ``include_integrations=True``)
                - ``_configurations``: Dictionary of :class:`ConfigurationCoupling` instances
                  (if ``include_integrations=True``)
                - ``_import_errors``: Dictionary of any import errors encountered

            Example::

                # Full discovery with integrations
                sequencer = TestSequencer(jobtitle, root, includes, excludes, metafilters)
                test_count = sequencer.discover()
                if test_count > 0:
                    # Proceed with test execution
                    pass

                # Query-only discovery (no integration setup)
                test_count = sequencer.discover(include_integrations=False)

                # Single module discovery
                import my_test_module
                test_count = sequencer.discover(test_module=my_test_module)

            See Also:
                - :class:`TestCollector`: Performs the actual test discovery
                - :meth:`attach_to_framework`: Called after discovery for integration setup
                - :class:`TestGroup`: The test tree node type
                - :class:`TestRef`: Individual test reference type
        """
        collector = TestCollector(self._root, excludes=self._excludes, metafilters=self._metafilters, test_module=test_module)

        # Discover the tests, integration points, and scopes.  If test modules is not None then
        # we are running tests from an individual module and we can limit discovery to the test module
        for inc_item in self._includes:
            collector.collect_references(inc_item)

        collector.finalize_collection()

        self._testtree = collector.test_tree
        self._references = collector.references

        testcount = len(self._references)
        if testcount > 0:
            if include_integrations:
                self._integrations, self._configurations = collector.collect_integrations_and_configurations()
            self._import_errors = collector.import_errors

        return testcount

    def enter_module_scope_context(self, scope_name) -> SequencerModuleScope:
        """
            Creates and returns a :class:`SequencerModuleScope` context manager for entering
            a module-level scope during test execution.

            This method is called by the generated sequence document when entering a new
            module scope. The returned context manager handles scope ID management, result
            container creation, and exception handling for the module scope.

            :param scope_name: The fully qualified name of the module scope, typically in
                the format ``"package.module"``.

            :returns: A :class:`SequencerModuleScope` context manager instance.

            Scope Stack Management:
                When the returned context manager is entered (``__enter__``):

                1. A new scope ID is created via :meth:`scope_id_create`
                2. A :class:`TestContainer` is created and recorded
                3. The scope is pushed onto the scope stack

                When exited (``__exit__``):

                1. Any exceptions are handled (SkipError marks descendants as skipped,
                   other exceptions mark descendants as errored)
                2. The scope is finalized and popped from the stack

            Example::

                # Used in generated sequence document
                with sequencer.enter_module_scope_context("package.module") as msc:
                    # Module-level setup and test execution
                    for param in create_module_resource():
                        with sequencer.enter_test_scope_context("test_func") as tsc:
                            test_func(param)

            See Also:
                - :class:`SequencerModuleScope`: The context manager class
                - :meth:`enter_session_scope_context`: Creates session-level scope
                - :meth:`enter_test_scope_context`: Creates test-level scope
                - :meth:`scope_id_create`: Creates scope IDs for the stack
        """
        context = SequencerModuleScope(self, self._recorder, scope_name)
        return context

    def enter_session_scope_context(self) -> SequencerSessionScope:
        """
            Creates and returns a :class:`SequencerSessionScope` context manager for entering
            the root session scope during test execution.

            This method is called by the generated sequence document's ``session()`` function
            to establish the root scope for the entire test run. The returned context manager
            handles scope ID management and exception handling for the session scope.

            :returns: A :class:`SequencerSessionScope` context manager instance.

            Scope Stack Management:
                When the returned context manager is entered (``__enter__``):

                1. The session scope ID is pushed onto the scope stack
                2. The root result container is associated with the scope

                When exited (``__exit__``):

                1. Any exceptions are handled (SkipError marks all tests as skipped,
                   other exceptions mark all tests as errored)
                2. The session scope is finalized and popped from the stack

            Example::

                # Used in generated sequence document's session() function
                def session(sequencer):
                    with sequencer.enter_session_scope_context() as ssc:
                        # Session-level setup
                        for session_param in create_session_resource():
                            scope_package_module(sequencer, session_param)

            See Also:
                - :class:`SequencerSessionScope`: The context manager class
                - :meth:`enter_module_scope_context`: Creates module-level scope
                - :meth:`enter_test_scope_context`: Creates test-level scope
        """
        context = SequencerSessionScope(self, self._recorder, self._root_result)
        return context

    def enter_test_scope_context(self, test_name, notables: Optional[Sequence] = None,
                                     expected_failure: dict = None) -> SequencerTestScope:
        """
            Creates and returns a :class:`SequencerTestScope` context manager for entering
            a test-level scope during test execution.

            This method is called by the generated sequence document when executing an
            individual test function. The returned context manager handles scope ID management,
            result creation, exception handling, and result recording for the test.

            :param test_name: The name of the test function being executed.
            :param notables: Optional sequence of notable parameter values for parameterized
                tests. These values are used to generate monikers (string identifiers) and
                pivots (actual values) that distinguish different parameter combinations.
                Defaults to ``None`` (empty list).
            :param expected_failure: Optional dictionary from the ``@expect_exception`` decorator
                containing ``exception_type`` and ``reason``. When provided, the scope exit
                will mark the test as PASSED if the expected exception is raised, or FAILED
                if no exception occurs.

            :returns: A :class:`SequencerTestScope` context manager instance.

            Scope Stack Management:
                When the returned context manager is entered (``__enter__``):

                1. A new scope ID is created via :meth:`scope_id_create`
                2. Monikers and pivots are extracted from notables
                3. A :class:`TestResult` is created and previewed with the recorder
                4. The scope is pushed onto the scope stack

                When exited (``__exit__``):

                1. The test result is marked based on the exit condition:
                   - No exception: ``mark_passed()``
                   - SkipError: ``mark_skip()``
                   - AssertionError: ``add_failure()``
                   - Other exception: ``add_error()``
                   - Expected exception (via ``@expect_exception``): ``mark_passed()``
                2. The result is finalized and recorded
                3. The scope is popped from the stack

            Example::

                # Used in generated sequence document
                with sequencer.enter_test_setup_context(test_scope_name) as tsetup:
                    for test_param in create_test_resource():
                        notables = {'test_param': test_param}
                        with sequencer.enter_test_scope_context(test_scope_name, notables=notables) as tscope:
                            from package.module import test_function
                            test_function(test_param)

            See Also:
                - :class:`SequencerTestScope`: The context manager class
                - :meth:`enter_test_setup_context`: Creates test setup scope
                - :meth:`enter_module_scope_context`: Creates module-level scope
                - :meth:`scope_id_create`: Creates scope IDs for the stack
        """

        if notables is None:
            notables = []

        context = SequencerTestScope(self, self._recorder, test_name, notables=notables,
                                     expected_failure=expected_failure)
        return context

    def enter_test_setup_context(self, test_name) -> SequencerTestSetupScope:
        """
            Creates and returns a :class:`SequencerTestSetupScope` context manager for entering
            a test setup scope during test execution.

            This method is called by the generated sequence document before executing a test
            function that requires test-local parameter creation. The setup scope provides
            a context for creating parameters that are scoped to a single test execution.

            :param test_name: The name of the test function being set up.

            :returns: A :class:`SequencerTestSetupScope` context manager instance.

            Scope Stack Management:
                The test setup scope is a lightweight scope that prepares for test-local
                parameter creation. It does not create its own scope ID but prepares the
                context for the nested test scope.

            Example::

                # Used in generated sequence document for parameterized tests
                with sequencer.enter_test_setup_context(test_scope_name) as tsetup:
                    # Create test-local parameters
                    for test_param in create_test_resource():
                        notables = {'test_param': test_param}
                        with sequencer.enter_test_scope_context(test_scope_name, notables=notables) as tscope:
                            test_function(test_param)

            See Also:
                - :class:`SequencerTestSetupScope`: The context manager class
                - :meth:`enter_test_scope_context`: Creates the actual test scope
                - :meth:`enter_module_scope_context`: Creates module-level scope
        """
        context = SequencerTestSetupScope(self, self._recorder, test_name)
        return context

    def establish_integration_order(self):
        """
            Re-orders the registered integrations based on any declared precedences.

            This method iterates over all registered :class:`IntegrationCoupling` instances
            and calls their ``establish_integration_order`` method, allowing integrations
            to declare dependencies on other integrations and establish a proper initialization
            order.

            :returns: None

            Note:
                This method is typically called during the integration setup phase to ensure
                that integrations are initialized in the correct order based on their
                dependencies.

            See Also:
                - :class:`IntegrationCoupling`: Base class for integrations
                - :meth:`establish_presence`: Called after integration ordering
        """

        integ_type: IntegrationCoupling

        for _, integ_type in self._integrations.items():
            integ_type.establish_integration_order()

        return

    def establish_presence(self):
        """
            Invokes the ``establish_presence`` lifecycle method on all registered integrations,
            allowing them to establish persistent services or connections with test resources.

            This method is called during the integration phase of test execution, after
            :meth:`collect_resources`. It iterates over all registered :class:`IntegrationCoupling`
            instances and calls their ``establish_presence`` method.

            :returns: None

            Phase Context:
                This method should be called after :meth:`collect_resources` has completed
                and before test execution begins.

            Integration Lifecycle Order:
                1. ``attach_to_framework`` - Register with test framework
                2. ``attach_to_environment`` - Validate configuration
                3. ``collect_resources`` - Acquire external resources
                4. ``establish_presence`` (this method) - Verify resource availability

            Example::

                # Typical usage within TestJob.execute()
                sequencer.attach_to_framework()
                sequencer.attach_to_environment()
                sequencer.collect_resources()
                sequencer.establish_presence()  # Called here

            See Also:
                - :meth:`collect_resources`: Called before this method
                - :class:`IntegrationCoupling`: Base class for integrations
        """

        integ_type: IntegrationCoupling

        for _, integ_type in self._integrations.items():
            integ_type.establish_presence()

        return

    def execute_tests(self, runid: str, recorder: ResultRecorder):
        """
            Executes the tests by importing and running the generated sequence document,
            transitioning the sequencer to the Traversal phase.

            This method imports the previously generated sequence document as a Python module
            and calls its ``session()`` function to begin test execution. The sequence document
            orchestrates the creation of scopes, parameter provisioning, and test function calls.

            :param runid: The unique identifier for this test run. Used as the scope ID for
                the root :class:`JobContainer` result.
            :param recorder: The :class:`ResultRecorder` instance to use for recording test
                results during execution.

            :raises SemanticError: If called before :meth:`generate_testrun_sequence_document`
                has been called to create the sequence document.

            Phase Transition:
                This method transitions the sequencer from the Graph phase to the Traversal
                phase. The Traversal phase continues until all tests have been executed.

            Execution Flow:
                1. Store the recorder reference for use by scope context managers
                2. Create the root :class:`JobContainer` result and record it
                3. Import the sequence document as a Python module
                4. Call the sequence document's ``session(sequencer)`` function
                5. The session function creates scopes and executes tests

            Example::

                # Typical usage within TestJob.execute()
                sequencer.generate_testrun_sequence_document(output_file)

                with recorder:
                    sequencer.execute_tests(runid, recorder)

            See Also:
                - :meth:`generate_testrun_sequence_document`: Must be called first
                - :meth:`enter_session_scope_context`: Called by the sequence document
                - :class:`ResultRecorder`: Records test results
        """

        res_name = "<session>"

        self._recorder = recorder

        self._root_result = self.create_job_result_container(runid, res_name)
        recorder.record(self._root_result)

        if self._sequence_document is None:
            errmsg = "The 'execute_tests' method should not be called without first generating the test sequence document."
            raise SemanticError(errmsg) from None

        # Import the test sequence document
        sequence_mod = import_file("sequence_document", self._sequence_document)
        sequence_mod.session(self)

        return

    def expand_test_tree_based_on_query(self):
        """
            Expands the test tree by resolving parameter queries and generating test instances.

            This method walks the test tree and expands parameterized tests based on their
            parameter factory queries. This allows the test tree to reflect the actual test
            instances that will be executed.

            :returns: None

            Note:
                This method is currently a placeholder for future functionality. The actual
                parameter expansion occurs during sequence document execution.

            See Also:
                - :meth:`generate_testrun_sequence_document`: Generates the execution sequence
                - :attr:`testtree`: The test tree to be expanded
        """

        context_locals = {}

        # Walk the test tree and expand the parameters
        # self._testtree

        return

    def find_test_scope(self) -> SequencerTestScope:
        """
            Searches the scope stack to find the current :class:`SequencerTestScope` instance.

            This method iterates through the scope stack from bottom to top and returns the
            most recent (innermost) :class:`SequencerTestScope` instance. This is useful for
            components that need to interact with the current test scope but only have a
            reference to the sequencer.

            :returns: The current :class:`SequencerTestScope` instance if one exists on the
                stack, or ``None`` if no test scope is currently active.

            Scope Stack Context:
                The scope stack may contain multiple scope types (session, module, test setup,
                test). This method specifically searches for :class:`SequencerTestScope`
                instances, which represent active test executions.

            Example::

                # Used internally by mark_activity to find the current test scope
                test_scope = sequencer.find_test_scope()
                if test_scope is not None:
                    test_scope.mark_activity("operation", target="resource")

            See Also:
                - :meth:`find_treenode_for_scope`: Finds tree nodes by scope name
                - :meth:`mark_activity`: Uses this method to delegate activity marking
                - :class:`SequencerTestScope`: The test scope class
        """

        test_scope = None
        for next_scope in self._scope_stack:
            if isinstance(next_scope, SequencerTestScope):
                test_scope = next_scope

        return test_scope

    def find_treenode_for_scope(self, scope_name, cursor=None):
        """
            Recursively searches the test tree to find a node matching the given scope name.

            This method performs a depth-first search of the test tree starting from the
            specified cursor (or the root if no cursor is provided) to locate a
            :class:`TestGroup` or :class:`TestRef` node with a matching scope name.

            :param scope_name: The scope name to search for. This should match the
                ``scope_name`` attribute of a tree node.
            :param cursor: Optional starting node for the search. If ``None``, the search
                starts from the root of the test tree (``_testtree``).

            :returns: The :class:`TestGroup` or :class:`TestRef` node with the matching
                scope name, or ``None`` if no matching node is found.

            Search Algorithm:
                1. Check if the cursor's scope_name matches the target
                2. If the cursor is a :class:`TestGroup`, recursively search its children
                3. Return the first matching node found, or ``None`` if no match

            Example::

                # Find a specific module node in the test tree
                module_node = sequencer.find_treenode_for_scope("package.module")
                if module_node is not None:
                    # Process the module node
                    for child in module_node.children.values():
                        print(child.name)

            See Also:
                - :meth:`find_test_scope`: Finds test scope in the scope stack
                - :class:`TestGroup`: Container node type in the test tree
                - :class:`TestRef`: Leaf node type in the test tree
        """
        found = None

        if cursor is None:
            cursor = self._testtree

        if cursor.scope_name == scope_name:
            found = cursor
        elif isinstance(cursor, TestGroup):
            for child in cursor.children.values():
                found = self.find_treenode_for_scope(scope_name, cursor=child)
                if found is not None:
                    break

        return found

    def generate_testrun_sequence_document(self, outputfilename: str, indent_space="    "):
        """
            Generates a Python sequence document that encodes the test execution order and
            parameter provisioning for the test run.

            This method creates a Python module file that, when imported and executed, will
            orchestrate the test run by creating scopes, provisioning parameters, and calling
            test functions in the correct order. The generated document is human-readable and
            can be used for debugging test execution flow.

            :param outputfilename: The absolute or relative path where the sequence document
                should be written. The file will be a valid Python module that can be imported.
                The path should have a ``.py`` extension. A temporary file with ``.tmp`` extension
                will be created during generation and removed upon completion.

            :param indent_space: The string to use for indentation in the generated code.
                Defaults to four spaces (``"    "``). This parameter allows customization of
                the indentation style in the generated document. Common values include:

                - ``"    "`` (four spaces) - PEP 8 recommended, default
                - ``"  "`` (two spaces) - More compact output
                - ``"\\t"`` (tab) - Tab-based indentation

            :returns: None. The method stores the output filename in the ``_sequence_document``
                attribute for later use by :meth:`execute_tests`.

            :raises OSError: If the output file cannot be created or written to due to
                permission issues or invalid path.
            :raises RuntimeError: If a constraint lookup fails during generation because
                the constraint key is not found in the :class:`ConstraintsCatalog`.

            Prerequisites:
                Before calling this method, the following must be completed:

                1. :meth:`discover` must have been called to build the test tree
                2. :meth:`attach_to_framework` should have been called for integrations
                3. :meth:`attach_to_environment` should have been called for environment setup

            Phase Transition:
                This method should be called after discovery and integration setup are complete,
                but before :meth:`execute_tests`. It prepares the sequencer for the Traversal
                phase. After this method completes, the ``_sequence_document`` attribute will
                contain the path to the generated document.

            Generated Document Structure:
                The sequence document contains:

                1. **Module header**: Imports, logger setup, and constraints catalog
                2. **Constraint imports**: Import statements for constraint classes
                3. **Factory imports**: Import statements for parameter factory functions
                4. **session() function**: Entry point that creates the session scope and
                   calls module scope functions
                5. **scope_*() functions**: One function per module that creates module scopes,
                   provisions parameters, and executes tests

            Two-Pass Generation Process:
                The document is generated using a two-pass approach to handle forward-referenced
                imports:

                **Pass 1 (Code Generation)**:
                    1. Write the module template with placeholder insertion points to a temp file
                    2. Generate the ``session()`` function via :meth:`_generate_session_method`
                    3. Generate scope functions via :meth:`_generate_scope_method` for each module
                       using breadth-first traversal of the test tree
                    4. Collect factory imports and constraint imports into sets during generation

                **Pass 2 (Import Insertion)**:
                    1. Read the temporary file line by line
                    2. Insert collected constraint imports at ``CONSTRAINT_IMPORT_INSERTION_POINT``
                    3. Insert collected factory imports at ``FACTORY_IMPORT_INSERTION_POINT``
                    4. Write the final document to the output path
                    5. Remove the temporary file

            Scope Function Naming:
                Scope functions are named using the pattern ``scope_{module_name}`` where dots
                in the module name are replaced with underscores. For example:

                - Module ``tests.unit.test_example`` becomes ``scope_tests_unit_test_example``
                - Module ``package.subpackage.module`` becomes ``scope_package_subpackage_module``

            Parameter Handling:
                The generated document handles parameters at three scope levels:

                - **Session-scoped**: Parameters created once per test run, passed to all modules
                - **Module-scoped**: Parameters created once per module, passed to all tests in module
                - **Test-local**: Parameters created for each test instance, used for parameterization

            Debugger Integration:
                When the ``AM_DEBUG_DEBUGGER`` and ``AM_DEBUG_BREAKPOINTS`` runtime variables are
                configured, the generated document will include breakpoint code at the configured
                locations (e.g., ``TESTRUN_START``).

            Example Generated Code::

                def session(sequencer):
                    \"\"\"
                    This is the entry point for the test run sequence document.
                    \"\"\"
                    with sequencer.enter_session_scope_context() as ssc:
                        from package.factories import create_session_resource
                        for session_param in create_session_resource():
                            scope_package_module(sequencer, session_param)
                    return

                def scope_package_module(sequencer, session_param):
                    \"\"\"
                    This is the entry point for the 'package.module' test scope.
                    \"\"\"
                    with sequencer.enter_module_scope_context("package.module") as msc:
                        # ================ Test Scope: test_function ================
                        test_scope_name = "test_function"
                        with sequencer.enter_test_scope_context(test_scope_name) as tscope:
                            from package.module import test_function
                            test_function(session_param)
                    return

            Example Usage::

                from ccai.testbase.sequencing.testsequencer import TestSequencer
                import os

                # Create and configure the sequencer
                with TestSequencer(jobtitle, root, includes, excludes, metafilters) as sequencer:
                    # Phase 1-3: Discovery and collection
                    test_count = sequencer.discover()

                    if test_count > 0:
                        # Integration setup
                        sequencer.attach_to_framework()
                        sequencer.attach_to_environment()

                        # Generate the sequence document
                        results_dir = sequencer.output_context.get_test_results_dir()
                        output_file = os.path.join(results_dir, "testrun_sequence.py")
                        sequencer.generate_testrun_sequence_document(output_file)

                        # Optionally use custom indentation
                        # sequencer.generate_testrun_sequence_document(output_file, indent_space="  ")

                        # Later, execute the tests
                        sequencer.execute_tests(runid, recorder)

            Example with Validators::

                # When tests have validators, the generated code includes try/finally blocks:
                #
                # with sequencer.enter_test_scope_context(test_scope_name) as tscope:
                #     try:
                #         validator = create_validator(constraints=constraints_catalog.lookup_constraints('key'))
                #         validator.attach_to_test(tscope, 'suffix')
                #         from package.module import test_function
                #         test_function(param1, param2)
                #     finally:
                #         validator.finalize()

            See Also:
                - :meth:`execute_tests`: Imports and executes the generated document
                - :meth:`_generate_session_method`: Generates the session function
                - :meth:`_generate_scope_method`: Generates module scope functions
                - :meth:`record_import_errors`: Records import errors encountered during discovery
                - :attr:`_sequence_document`: Stores the path to the generated document
                - :class:`ConstraintsCatalog`: Used for constraint lookups in generated code
        """

        # ============================================================================
        # SEQUENCE DOCUMENT GENERATION - OVERVIEW
        # ============================================================================
        # The sequence document is a generated Python module that orchestrates test
        # execution. It contains:
        #   1. Module header with imports and global setup
        #   2. Constraint imports (inserted at CONSTRAINT_IMPORT_INSERTION_POINT)
        #   3. Factory imports (inserted at FACTORY_IMPORT_INSERTION_POINT)
        #   4. session() function - the entry point for test execution
        #   5. scope_*() functions - one per module containing tests
        #
        # The generation process uses a two-pass approach:
        #   Pass 1: Generate code to a temp file, collecting import statements
        #   Pass 2: Insert collected imports at their designated insertion points
        # ============================================================================

        # ============================================================================
        # TWO-PASS GENERATION PATTERN - RATIONALE
        # ============================================================================
        # Why two passes? The challenge is that import statements must appear at the
        # top of the generated Python file, but we don't know which imports are needed
        # until we've traversed the entire test tree and generated all scope functions.
        #
        # The solution is a two-pass approach:
        #
        # PASS 1 (Code Generation):
        #   - Write the module template with placeholder insertion points to a temp file
        #   - Generate session() and all scope_*() functions
        #   - As we generate code, collect required imports into sets (no duplicates)
        #   - The insertion point markers remain in the temp file as placeholders
        #
        # PASS 2 (Import Insertion):
        #   - Read the temp file line by line
        #   - When we encounter an insertion point marker, write the collected imports
        #   - All other lines are copied unchanged to the final output
        #   - Delete the temp file after successful completion
        #
        # This pattern ensures:
        #   - All imports appear at the top of the file (valid Python module structure)
        #   - No duplicate imports (using sets for collection)
        #   - Constraint imports appear before factory imports (proper dependency order)
        #   - The final document is a valid, executable Python module
        # ============================================================================

        # ============================================================================
        # IMPORT COLLECTION STRATEGY
        # ============================================================================
        # Imports are collected into sets during code generation to ensure:
        #   1. No duplicate imports (sets automatically deduplicate)
        #   2. Proper categorization (constraints vs factories)
        #   3. Correct ordering in the final document
        #
        # Import sources:
        #   - constraint_imports: Populated when constraint lookups are generated
        #   - factory_imports: Populated from multiple sources:
        #       * Session-scoped parameter factories (_generate_session_method)
        #       * Module-scoped parameter factories (_generate_scope_method)
        #       * Test-local parameter factories (_generate_scope_method)
        #       * Validator factories (_generate_scope_method)
        #
        # Import format: "from {module} import {function}"
        # Example: "from mypackage.factories import create_database_connection"
        # ============================================================================
        constraint_imports = set()  # Constraint class imports (e.g., from package import MyConstraint)
        factory_imports = set()     # Parameter factory imports (e.g., from package import create_resource)
        test_imports = set()        # Test function imports (currently unused, reserved for future)

        # ============================================================================
        # PASS 1: GENERATE CODE TO TEMPORARY FILE
        # ============================================================================
        # Write the sequence document to a temporary file first. During this pass,
        # we collect all the import statements that are needed. The imports cannot
        # be written immediately because they need to appear at the top of the file,
        # but we don't know what imports are needed until we've processed all scopes.
        # ============================================================================
        temp_outputfile = outputfilename + ".tmp"

        with open(temp_outputfile, 'w') as sdf:

            # --------------------------------------------------------------------
            # TEMPLATE STRUCTURE
            # --------------------------------------------------------------------
            # Write the module template which includes:
            #   - Module docstring (CODE GENERATED - DO NOT EDIT warning)
            #   - __traceback_format_policy__ = "Brief" for cleaner error output
            #   - Standard imports (logging, EnhancedLogger, ConstraintsCatalog)
            #   - Logger and constraints_catalog global instances
            #   - Placeholder comments for constraint and factory imports
            # --------------------------------------------------------------------
            sdf.write(TEMPLATE_TESTRUN_SEQUENCE_MODULE)

            # --------------------------------------------------------------------
            # SESSION METHOD GENERATION
            # --------------------------------------------------------------------
            # Generate the session() function which is the entry point for test
            # execution. This function:
            #   - Creates the session scope context
            #   - Imports and creates session-scoped parameters
            #   - Calls child module scope functions
            #
            # Returns a list of child scopes that need to be generated next.
            # Each item is a tuple: (scope_module, scope_name, scope_node, scope_call_args)
            # --------------------------------------------------------------------
            scopes_called = self._generate_session_method(sdf, self._testtree, factory_imports, constraint_imports, indent_space)

            # --------------------------------------------------------------------
            # SCOPE METHOD GENERATION (BREADTH-FIRST TRAVERSAL)
            # --------------------------------------------------------------------
            # The test tree is traversed using breadth-first order (BFS) to generate
            # scope functions. This ensures that parent scopes are defined before
            # their children in the generated document, which is important for:
            #   1. Readability - the document flows from top-level to nested scopes
            #   2. Debugging - execution order matches document order
            #   3. Determinism - consistent output across runs
            #
            # BREADTH-FIRST TRAVERSAL ALGORITHM:
            # ===================================
            # The scopes_called list acts as a FIFO queue:
            #   1. Initialize queue with child scopes from session method
            #   2. While queue is not empty:
            #      a. Dequeue (pop from front) the next scope to process
            #      b. Generate the scope function, which may discover child scopes
            #      c. Enqueue (append to end) any newly discovered child scopes
            #   3. Continue until all scopes have been processed
            #
            # Example traversal order for a test tree:
            #   Root
            #   ├── package_a (processed 1st)
            #   │   ├── module_a1 (processed 3rd)
            #   │   └── module_a2 (processed 4th)
            #   └── package_b (processed 2nd)
            #       └── module_b1 (processed 5th)
            #
            # This produces scope functions in the order:
            #   scope_package_a, scope_package_b, scope_package_a_module_a1,
            #   scope_package_a_module_a2, scope_package_b_module_b1
            #
            # Queue state at each iteration:
            #   Initial: [package_a, package_b]
            #   After processing package_a: [package_b, module_a1, module_a2]
            #   After processing package_b: [module_a1, module_a2, module_b1]
            #   After processing module_a1: [module_a2, module_b1]
            #   After processing module_a2: [module_b1]
            #   After processing module_b1: [] (done)
            # --------------------------------------------------------------------
            while len(scopes_called) > 0:
                sdf.write(os.linesep)
                
                # Dequeue the next scope to process (FIFO - pop from front)
                # Each scope entry is a tuple: (scope_module, scope_name, scope_node, scope_call_args)
                #   - scope_module: Fully qualified module name (e.g., "package.module")
                #   - scope_name: Function-safe name with underscores (e.g., "package_module")
                #   - scope_node: The TestGroup node from the test tree
                #   - scope_call_args: List of parameter names to pass to this scope
                scope_module, scope_name, scope_node, scope_call_args = scopes_called.pop(0)
                
                # Generate the scope function and get any child scopes discovered
                # The child scopes are returned as a list of tuples in the same format
                child_scopes_called = self._generate_scope_method(sdf, scope_module, scope_name, scope_node, scope_call_args, 
                                                                  factory_imports, constraint_imports, indent_space)
                
                # Enqueue newly discovered child scopes (append to end for BFS order)
                # We extend child_scopes_called with the remaining scopes_called to maintain
                # the correct order: new children go to the end of the queue
                child_scopes_called.extend(scopes_called)
                scopes_called = child_scopes_called

        linesep = os.linesep

        # ============================================================================
        # PASS 2: INSERT COLLECTED IMPORTS AT INSERTION POINTS
        # ============================================================================
        # Now that we've generated all the code and collected all the imports,
        # we read the temporary file and write the final output, inserting the
        # collected imports at their designated insertion points.
        #
        # The insertion points are marked by special comment lines:
        #   - CONSTRAINT_IMPORT_INSERTION_POINT: Where constraint imports go
        #   - FACTORY_IMPORT_INSERTION_POINT: Where factory imports go
        #
        # This two-pass approach ensures imports appear at the top of the file
        # even though we don't know what imports are needed until we've processed
        # all the scopes.
        # ============================================================================
        with open(temp_outputfile, 'r') as tmpf:

            with open(outputfilename, 'w') as sdf:

                while True:
                    nxtline = tmpf.readline()
                    if len(nxtline) == 0:
                        break
                    
                    # ------------------------------------------------------------
                    # CONSTRAINT IMPORT INSERTION
                    # ------------------------------------------------------------
                    # When we encounter the constraint import insertion point,
                    # write all collected constraint imports. These are imports
                    # for constraint classes used by parameter factories.
                    # ------------------------------------------------------------
                    if nxtline.startswith(CONSTRAINT_IMPORT_INSERTION_POINT):
                        for cimp in constraint_imports:
                            sdf.write(cimp)
                            sdf.write(linesep)

                    # ------------------------------------------------------------
                    # FACTORY IMPORT INSERTION
                    # ------------------------------------------------------------
                    # When we encounter the factory import insertion point,
                    # write all collected factory imports. These are imports
                    # for parameter factory functions used to create test
                    # parameters at various scope levels.
                    # ------------------------------------------------------------
                    elif nxtline.startswith(FACTORY_IMPORT_INSERTION_POINT):
                        for fimp in factory_imports:
                            sdf.write(fimp)
                            sdf.write(linesep)

                    else:
                        # Pass through all other lines unchanged
                        sdf.write(nxtline)

        # Clean up the temporary file
        os.remove(temp_outputfile)

        # Store the sequence document path for later use by execute_tests()
        self._sequence_document = outputfilename

        return

    def get_recorder(self) -> str:
        """
            Returns the current :class:`ResultRecorder` instance.

            :returns: The :class:`ResultRecorder` being used for this test run, or ``None``
                if :meth:`execute_tests` has not been called yet.

            Note:
                The recorder is set when :meth:`execute_tests` is called and remains
                available throughout the test execution.
        """
        return self._recorder

    @property
    def job_seed(self) -> str:
        """
            Returns the job-level seed for reproducible property testing.

            The seed is set by the :class:`TestJob` that creates this sequencer.
            If no seed was provided, a random UUID is generated on first access.

            :returns: A string seed value (UUID).
        """
        if self._job_seed is None:
            import uuid
            self._job_seed = str(uuid.uuid4())
        return self._job_seed

    def run_property_test(self, test_func: 'Callable', test_name: str,
                          recorder: 'Any', parent_inst: str,
                          injected_args: 'Dict[str, Any]') -> 'Dict[str, Any]':
        """
            Runs a property test function using the :class:`PropertyRunner`.

            This method encapsulates the full property test execution lifecycle:
            extracting metadata from the ``@given`` decorator, separating strategy
            parameters from injected parameters, constructing a :class:`PropertyRunner`,
            and invoking it.

            :param test_func: The ``@given``-decorated test function to run.
            :param test_name: The fully qualified test name (e.g., ``"pkg.module#test_func"``).
            :param recorder: The result recorder for writing check results.
            :param parent_inst: The instance ID of the parent test result.
            :param injected_args: Dictionary of all injection-resolved parameter values.
                Strategy-generated parameters are automatically filtered out.
            :returns: A dictionary containing property test metadata from the runner.
        """
        from ccai.testbase.properties.propertyrunner import PropertyRunner

        prop_meta = test_func._property_
        strategies = prop_meta['strategies']
        constraints = prop_meta.get('constraints', {})

        # Filter out strategy params from injected args
        filtered_injected = {k: v for k, v in injected_args.items() if k not in strategies}

        runner = PropertyRunner(
            constraints=constraints,
            job_seed=self.job_seed,
            test_name=test_name,
            recorder=recorder,
            parent_inst=parent_inst
        )

        return runner.run(test_func, strategies, filtered_injected)

    def run_async_test(self, test_func: 'Callable', injected_args: 'Dict[str, Any]') -> 'Any':
        """
            Runs an async test function and re-raises any exception from the coroutine so
            the surrounding test scope can mark the result correctly.

            :param test_func: The async test function to invoke.
            :param injected_args: Dictionary of injection-resolved parameter values.
            :returns: The result returned by the async test coroutine.
        """
        coroutine = test_func(**injected_args)
        return asyncio.run(coroutine)

    def get_top_scope_id(self) -> str:
        """
            Returns the scope ID at the top of the scope stack without modifying the stack.

            This method provides read-only access to the current (innermost) scope ID,
            which is useful for creating result nodes that need to reference their parent
            scope.

            :returns: The scope ID (UUID string) at the top of the stack, or ``None`` if
                the scope stack is empty.

            Scope Stack Context:
                The scope stack contains tuples of ``(scope_name, scope_id)``. This method
                returns only the scope_id component of the top entry.

            Example::

                # Get the current scope ID for creating a child result
                parent_id = sequencer.get_top_scope_id()
                if parent_id is not None:
                    # Create a result with this parent
                    pass

            See Also:
                - :meth:`scope_id_create`: Creates and pushes a new scope ID
                - :meth:`scope_id_push`: Manually pushes a scope entry
                - :meth:`scope_id_pop`: Removes the top scope entry
        """

        top_id = None
        if len(self._scope_stack) > 0:
            top_id = self._scope_stack[-1][1]
        
        return top_id
    
    def mark_activity(self, activity_name: str, target: str="NA", detail: Optional[dict] = None):
        """
            Marks an activity in the current test scope, allowing components with sequencer
            access to record timing and operational information.

            This is a convenience method that delegates to the current :class:`SequencerTestScope`'s
            :meth:`mark_activity` method. It allows components that have a reference to the
            sequencer (but not the test scope) to record activities during test execution.

            :param activity_name: The name of the activity being recorded (e.g., "ssh_command",
                "http_request", "file_operation").
            :param target: The target of the activity (e.g., hostname, URL, filename).
                Defaults to ``"NA"``.
            :param detail: Optional dictionary containing additional details about the activity.
                Defaults to ``None``.

            :returns: None

            Behavior:
                - If a test scope is currently active on the scope stack, the activity is
                  recorded in that scope's activity stream.
                - If no test scope is active (e.g., during session or module setup), the
                  method silently returns without recording anything.

            Example::

                # Record an activity from a component with sequencer access
                sequencer.mark_activity(
                    "database_query",
                    target="users_table",
                    detail={"query": "SELECT * FROM users", "rows": 100}
                )

            See Also:
                - :meth:`find_test_scope`: Locates the current test scope
                - :class:`SequencerTestScope`: Contains the actual activity recording logic
                - :meth:`SequencerTestScope.mark_activity`: The delegated method
                - :meth:`SequencerTestScope.begin_activity`: For activities with duration
        """

        test_scope = self.find_test_scope()
        if test_scope is not None:
            test_scope.mark_activity(activity_name, target=target, detail=detail)
        
        return

    def scope_id_create(self, scope_name: str) -> Tuple[str, str]:
        """
            Creates a new scope ID (UUID) and pushes it onto the scope stack.

            This method generates a unique identifier for a new scope, retrieves the parent
            scope ID from the current top of the stack, and pushes the new scope entry onto
            the stack. This is the primary method for entering a new scope during test
            execution.

            :param scope_name: The name of the scope being created. This is used for
                identification and for validation when the scope is popped.

            :returns: A tuple of ``(parent_id, scope_id)`` where:
                - ``parent_id``: The scope ID of the parent scope (from the previous top of
                  stack), or ``None`` if this is the first scope on the stack.
                - ``scope_id``: The newly generated UUID string for this scope.

            Scope Stack Management:
                This method performs two operations atomically:

                1. Retrieves the current top scope ID as the parent_id
                2. Generates a new UUID and pushes ``(scope_name, scope_id)`` onto the stack

                The returned parent_id is used to establish the parent-child relationship
                in the result hierarchy.

            Example::

                # Create a new scope and get parent reference
                parent_id, scope_id = sequencer.scope_id_create("package.module")

                # Create a result container with proper hierarchy
                container = sequencer.create_test_result_container(
                    scope_id, "package.module", parent_id
                )

            See Also:
                - :meth:`scope_id_push`: Manually pushes a scope entry
                - :meth:`scope_id_pop`: Removes a scope from the stack
                - :meth:`get_top_scope_id`: Gets the current top scope ID
        """

        parent_id = None
        if len(self._scope_stack) > 0:
            parent_id = self._scope_stack[-1][1]

        scope_id = str(uuid.uuid4())
        self._scope_stack.append((scope_name, scope_id))

        return parent_id, scope_id

    def scope_id_pop(self, scope_name: str):
        """
            Removes the top scope entry from the scope stack with validation.

            This method pops the top entry from the scope stack and validates that the
            scope name matches the expected name. This validation helps detect scope
            imbalance issues where scopes are not properly nested.

            :param scope_name: The expected name of the scope being popped. Must match
                the name of the scope at the top of the stack.

            :raises RuntimeError: If the scope name at the top of the stack does not match
                the expected ``scope_name``. This indicates a scope imbalance bug.

            :returns: None

            Scope Stack Management:
                This method should be called when exiting a scope context. The validation
                ensures that scopes are properly nested and that no scope entries are
                orphaned or skipped.

            Example::

                # Properly nested scope management
                parent_id, scope_id = sequencer.scope_id_create("package.module")
                try:
                    # ... scope operations ...
                    pass
                finally:
                    sequencer.scope_id_pop("package.module")  # Must match create name

            See Also:
                - :meth:`scope_id_create`: Creates and pushes a new scope
                - :meth:`scope_id_push`: Manually pushes a scope entry
                - :meth:`get_top_scope_id`: Gets the current top scope ID
        """

        top_entry_name, _ = self._scope_stack.pop()
        if top_entry_name != scope_name:
            errmsg = "Attempting to pop '{}' from the scope stack but encountered '{}'.".format(scope_name, top_entry_name)
            raise RuntimeError(errmsg) from None

        return

    def scope_id_push(self, scope_name: str, scope_id: str):
        """
            Manually pushes a scope entry onto the scope stack.

            This method allows direct manipulation of the scope stack by pushing a
            pre-existing scope entry. This is useful when a scope ID has already been
            created elsewhere (e.g., the session scope which uses the run ID).

            :param scope_name: The name of the scope being pushed.
            :param scope_id: The scope ID (UUID string) to associate with this scope.

            :returns: None

            Scope Stack Management:
                Unlike :meth:`scope_id_create`, this method does not generate a new UUID.
                It simply pushes the provided ``(scope_name, scope_id)`` tuple onto the
                stack. The caller is responsible for ensuring the scope_id is valid.

            Example::

                # Push an existing scope ID (e.g., session scope with run ID)
                sequencer.scope_id_push("<session>", runid)

            See Also:
                - :meth:`scope_id_create`: Creates a new scope ID and pushes it
                - :meth:`scope_id_pop`: Removes a scope from the stack
                - :meth:`get_top_scope_id`: Gets the current top scope ID
        """
        self._scope_stack.append((scope_name, scope_id))
        return

    def _generate_session_method(self, outf: TextIOWrapper, root_node: TestGroup, factory_imports: set,
                                 constraint_imports: set, indent_space: str):
        """
            Generates the ``session()`` entry point function for the test run sequence document.

            This method creates the root function that serves as the entry point for test
            execution. The session function establishes the session scope context, imports
            session-scoped parameter factories, creates session-scoped parameters, and calls
            the child module scope functions.

            :param outf: The output file handle to write the generated code to.
            :param root_node: The root :class:`TestGroup` node of the test tree.
            :param factory_imports: A set that will be populated with factory import statements
                needed by the generated code.
            :param constraint_imports: A set that will be populated with constraint import
                statements needed by the generated code.
            :param indent_space: The string to use for indentation.

            :returns: A list of tuples representing child scopes that need to be generated.
                Each tuple contains ``(scope_module, scope_name, scope_node, scope_call_args)``.

            Generated Code Structure:
                The session function follows this structure::

                    def session(sequencer):
                        # Optional debugger breakpoint
                        with sequencer.enter_session_scope_context() as ssc:
                            # Import session-scoped parameter factories
                            from package.factories import create_session_resource

                            # Create session-scoped parameters and call child scopes
                            for session_param in create_session_resource():
                                scope_package_module(sequencer, session_param)
                        return

            See Also:
                - :meth:`generate_testrun_sequence_document`: Calls this method
                - :meth:`_generate_scope_method`: Generates child scope functions
        """
        # ============================================================================
        # SESSION METHOD GENERATION
        # ============================================================================
        # This method generates the session() function which serves as the entry
        # point for test execution. The session function:
        #   1. Optionally inserts debugger breakpoint code
        #   2. Creates the session scope context
        #   3. Imports session-scoped parameter factory functions
        #   4. Creates nested loops for session-scoped parameters
        #   5. Calls child module scope functions with the created parameters
        # ============================================================================
        
        # List to track child scopes that need to be generated after this method
        scopes_called = []

        current_indent = indent_space

        # --------------------------------------------------------------------
        # FUNCTION SIGNATURE AND DOCSTRING
        # --------------------------------------------------------------------
        # Generate the function definition and docstring for the session function.
        # The session function takes a single 'sequencer' parameter which provides
        # access to scope context managers and result recording.
        # --------------------------------------------------------------------
        method_lines: List[str] = [
            'def session(sequencer):',
            '{}"""'.format(current_indent),
            '{}This is the entry point for the test run sequence document.'.format(indent_space),
            '{}"""'.format(current_indent)
        ]

        # --------------------------------------------------------------------
        # DEBUGGER BREAKPOINT INSERTION
        # --------------------------------------------------------------------
        # If debugging is enabled via AM_DEBUG_DEBUGGER and AM_DEBUG_BREAKPOINTS
        # runtime variables, insert breakpoint code at TESTRUN_START. This allows
        # developers to pause execution at the start of the test run for debugging.
        # --------------------------------------------------------------------
        debugger_name = environment.get_debugger_name()
        configured_breakpoints = environment.get_debug_breakpoints()

        if debugger_name is not None and configured_breakpoints is not None:
            debugger_wellknown_breakpoint_code_append(debugger_name, WELLKNOWN_BREAKPOINTS.TESTRUN_START, method_lines, current_indent, configured_breakpoints)

        method_lines.append('')
        
        # --------------------------------------------------------------------
        # SESSION SCOPE CONTEXT
        # --------------------------------------------------------------------
        # Create the session scope context using a 'with' statement. This ensures
        # proper setup and teardown of the session scope, including:
        #   - Pushing the session scope onto the scope stack
        #   - Creating the root result container
        #   - Handling exceptions and marking results appropriately
        # --------------------------------------------------------------------
        method_lines.append('{}with sequencer.enter_session_scope_context() as ssc:'.format(current_indent))
        method_lines.append('')

        current_indent = current_indent + indent_space

        # Get the resource scope for the session level to access parameter originations
        this_scope = root_node.get_resource_scope()
        this_parameter_originations = this_scope.parameter_originations if this_scope is not None else {}

        # --------------------------------------------------------------------
        # SESSION-SCOPED PARAMETER FACTORY IMPORTS
        # --------------------------------------------------------------------
        # Import all parameter factory functions that are used at the session scope.
        # These are functions that create session-scoped resources (e.g., database
        # connections, API clients) that are shared across all tests in the session.
        #
        # We skip 'implied' parameters (like 'sequencer') which are provided by
        # the framework rather than created by factory functions.
        # --------------------------------------------------------------------
        for _, porigin in this_parameter_originations.items():
            if not porigin.implied:
                method_lines.append('{}from {} import {}'.format(current_indent, porigin.source_module_name, porigin.source_function.__name__))
        method_lines.append('')

        # Initialize the list of arguments that will be passed to child scope functions.
        # Always starts with 'sequencer' which is needed by all scope functions.
        child_call_args = ['sequencer']

        # --------------------------------------------------------------------
        # SESSION-SCOPED PARAMETER LOOP GENERATION
        # --------------------------------------------------------------------
        # Generate nested for loops for each session-scoped parameter. Each
        # parameter factory function is called and its results are iterated.
        # This creates the parameter instances that will be passed to child scopes.
        #
        # Example generated code:
        #   for session_db in create_database_connection():
        #       for session_api in create_api_client():
        #           scope_package_module(sequencer, session_db, session_api)
        #
        # Each parameter is added to child_call_args so it can be passed to
        # child scope functions.
        # --------------------------------------------------------------------
        for pname, porigin in this_parameter_originations.items():
            if not porigin.implied:
                # Generate the factory function call (may include constraints)
                source_func_call = porigin.generate_call()
                
                # Create the for loop that iterates over factory results
                method_lines.append('{}for {} in {}:'.format(current_indent, pname, source_func_call))
                
                # Add this parameter to the list of arguments for child scopes
                child_call_args.append(pname)
                
                # Increase indent for the next nested loop or child scope calls
                current_indent = current_indent + indent_space

        # --------------------------------------------------------------------
        # CHILD SCOPE FUNCTION CALLS
        # --------------------------------------------------------------------
        # Generate calls to child module scope functions. Each child of the root
        # node represents a top-level package or module containing tests.
        #
        # The child scope functions are named scope_<module_name> where dots in
        # the module name are replaced with underscores.
        #
        # Each child scope is added to scopes_called so it will be generated
        # by the caller after this method returns.
        # --------------------------------------------------------------------
        child_name_list = [cnk for cnk in root_node.children.keys()]
        child_name_list.sort()  # Sort for deterministic output

        for child_name in child_name_list:

            # This code is assuming that all the children of the root node are of type
            # `TestGroup` which might not be a valid assumption to make all the time.
            # TODO: Add support for root level TestRef nodes.
            child_node: Union[TestRef, TestGroup] = root_node.children[child_name]

            # Build the fully qualified module name
            scope_module = child_name
            if child_node.package:
                scope_module = child_node.package + "." + child_name
            
            # Convert module name to a valid Python function name (replace dots with underscores)
            scope_name = scope_module.replace(".", "_")
            
            # Generate the function call with all accumulated parameters
            call_line = '{}scope_{}({})'.format(current_indent, scope_name, ", ".join(child_call_args))
            method_lines.append(call_line)
            
            # Queue this scope for generation
            scopes_called.append((scope_module, scope_name, child_node, child_call_args))

        # --------------------------------------------------------------------
        # FUNCTION RETURN
        # --------------------------------------------------------------------
        method_lines.append('')
        method_lines.append('{}return'.format(indent_space))
        method_lines.append('')

        # Write the complete method to the output file
        method_content = os.linesep.join(method_lines)
        outf.write(method_content)

        return scopes_called

    def _generate_scope_method(self, outf: TextIOWrapper, scope_module: str, scope_name: str, scope_node: TestGroup,
                               scope_call_args: List[str], factory_imports: set, constraint_imports: set,
                               indent_space: str):
        """
            Generates a module scope function for the test run sequence document.

            This method creates a function that represents a module-level scope in the test
            hierarchy. The generated function establishes the module scope context, imports
            and creates module-scoped parameters, and either executes tests directly or calls
            child scope functions.

            :param outf: The output file handle to write the generated code to.
            :param scope_module: The fully qualified module name (e.g., ``"package.module"``).
            :param scope_name: The function-safe scope name (dots replaced with underscores).
            :param scope_node: The :class:`TestGroup` node representing this module scope.
            :param scope_call_args: List of argument names that this function receives from
                its parent scope.
            :param factory_imports: A set that will be populated with factory import statements
                needed by the generated code.
            :param constraint_imports: A set that will be populated with constraint import
                statements needed by the generated code.
            :param indent_space: The string to use for indentation.

            :returns: A list of tuples representing child scopes that need to be generated.
                Each tuple contains ``(scope_module, scope_name, scope_node, scope_call_args)``.

            Generated Code Structure:
                For modules containing tests::

                    def scope_package_module(sequencer, session_param):
                        with sequencer.enter_module_scope_context("package.module") as msc:
                            # Module-scoped parameter creation
                            for module_param in create_module_resource():

                                # Test execution
                                test_scope_name = "test_function"
                                with sequencer.enter_test_setup_context(test_scope_name) as tsetup:
                                    for test_param in create_test_resource():
                                        notables = {'test_param': test_param}
                                        with sequencer.enter_test_scope_context(test_scope_name, notables=notables) as tscope:
                                            from package.module import test_function
                                            test_function(session_param, module_param, test_param)
                        return

            See Also:
                - :meth:`generate_testrun_sequence_document`: Calls this method
                - :meth:`_generate_session_method`: Generates the session function
        """
        # ============================================================================
        # MODULE SCOPE METHOD GENERATION
        # ============================================================================
        # This method generates a scope_*() function for a module in the test tree.
        # The generated function:
        #   1. Creates the module scope context
        #   2. Imports and creates module-scoped parameters
        #   3. For each child:
        #      - If TestRef: generates test setup, test scope, and test call
        #      - If TestGroup: generates call to child scope function
        # ============================================================================
        
        # List to track child scopes that need to be generated after this method
        scopes_called = []

        current_indent = "    "

        # --------------------------------------------------------------------
        # FUNCTION SIGNATURE AND DOCSTRING
        # --------------------------------------------------------------------
        # Generate the function definition with all parameters received from
        # parent scopes. The function name is scope_<module_name> where dots
        # are replaced with underscores.
        # --------------------------------------------------------------------
        method_lines = [
            'def scope_{}({}):'.format(scope_name, ", ".join(scope_call_args)),
            '{}"""'.format(current_indent),
            "{}This is the entry point for the '{}' test scope.".format(current_indent, scope_name),
            '{}"""'.format(current_indent),
            '',
            # Create the module scope context for result recording and scope tracking
            '{}with sequencer.enter_module_scope_context("{}") as msc:'.format(current_indent, scope_module)
        ]

        current_indent = current_indent + indent_space

        # Copy the parent scope arguments - these will be extended with module-scoped parameters
        child_call_args = [arg for arg in scope_call_args]

        # Get the resource scope for this module to access parameter originations
        resource_scope = scope_node.get_resource_scope()
        resource_parameter_originations = resource_scope.parameter_originations if resource_scope is not None else {}

        # --------------------------------------------------------------------
        # MODULE-SCOPED FACTORY IMPORT COLLECTION
        # --------------------------------------------------------------------
        # Collect all factory imports needed for module-scoped parameters.
        # These imports are added to the factory_imports set and will be
        # inserted at the FACTORY_IMPORT_INSERTION_POINT in the final document.
        #
        # IMPORT COLLECTION STRATEGY FOR MODULE SCOPE:
        # =============================================
        # 1. Iterate over all parameter originations in the resource scope
        # 2. For each parameter, extract the source module and function name
        # 3. Add the import statement to the factory_imports set
        # 4. The set automatically deduplicates (same import won't appear twice)
        #
        # Why collect imports here instead of writing them inline?
        #   - Python requires imports at the top of the module
        #   - We don't know all imports until we've processed all scopes
        #   - Using a set prevents duplicate imports
        #   - The two-pass generation pattern handles the actual insertion
        #
        # Import format: "from {source_module_name} import {source_function_name}"
        # Example: "from mypackage.factories import create_database_connection"
        # --------------------------------------------------------------------
        for _, porigin in resource_parameter_originations.items():
            factory_imports.add('from {} import {}'.format(porigin.source_module_name, porigin.source_function.__name__))

        # --------------------------------------------------------------------
        # MODULE-SCOPED PARAMETER LOOP GENERATION
        # --------------------------------------------------------------------
        # Generate nested for loops for each module-scoped parameter. Each
        # parameter factory function is called and its results are iterated.
        #
        # If a factory function accepts a 'constraints' parameter, we look up
        # the constraints from the ConstraintsCatalog and pass them to the
        # factory function.
        #
        # Example generated code:
        #   constraints=constraints_catalog.lookup_constraints('my_constraints')
        #   for module_param in create_module_resource(constraints=constraints):
        #       # ... test execution code ...
        # --------------------------------------------------------------------
        for pname, porigin in resource_parameter_originations.items():

            # A parameter this scope already RECEIVES from an ancestor scope is
            # satisfied -- re-originating it here would both shadow the inherited
            # value with a fresh one and emit a duplicate argument name into
            # descendant scope signatures, which is a SyntaxError in the
            # generated sequence document.
            if pname in scope_call_args:
                continue

            # Get the parameter names from the factory function signature
            sp_parameter_names = [pn for pn in porigin.source_signature.parameters.keys()]
            sp_constraints = None

            # ------------------------------------------------------------
            # CONSTRAINT PARAMETER HANDLING
            # ------------------------------------------------------------
            # If the factory function accepts a 'constraints' parameter,
            # look up the constraints from the catalog and generate code
            # to pass them to the factory function.
            # ------------------------------------------------------------
            if 'constraints' in sp_parameter_names:
                constraints_key = porigin.constraints_key
                if constraints_key is not None:
                    sp_constraints = constraints_catalog.lookup_constraints(constraints_key)
                    if sp_constraints is None:
                        raise RuntimeError(f"Constraint required but not found for contraints_key={constraints_key}")
                    # Generate the constraints lookup code
                    method_lines.append('{}constraints=constraints_catalog.lookup_constraints({})'.format(current_indent, repr(constraints_key)))
                else:
                    # No constraints key specified, remove constraints from parameter list
                    sp_parameter_names.remove('constraints')

            # Generate the factory function call (may include constraints)
            source_func_call = porigin.generate_call(constraints=sp_constraints)
            
            # Create the for loop that iterates over factory results
            method_lines.append('{}for {} in {}:'.format(current_indent, pname, source_func_call))
            
            # Add this parameter to the list of arguments for child scopes/tests
            child_call_args.append(pname)
            
            # Increase indent for the next nested loop or child processing
            current_indent = current_indent + indent_space

        # --------------------------------------------------------------------
        # CHILD NODE PROCESSING
        # --------------------------------------------------------------------
        # Process each child node in sorted order for deterministic output.
        # Children can be either:
        #   - TestRef: Individual test functions that need test scope generation
        #   - TestGroup: Sub-modules that need scope function calls
        # --------------------------------------------------------------------
        child_name_list = [cnk for cnk in scope_node.children.keys()]
        child_name_list.sort()  # Sort for deterministic output

        for child_name in child_name_list:
            child_node: Union[TestRef, TestGroup] = scope_node.children[child_name]

            if isinstance(child_node, TestRef):
                # ============================================================
                # TEST REFERENCE PROCESSING
                # ============================================================
                # Generate code to execute an individual test function. This
                # includes:
                #   1. Test setup scope (if test has local parameters)
                #   2. Test-local parameter loops
                #   3. Notables dictionary for parameterized tests
                #   4. Test scope context
                #   5. Validator setup (if any)
                #   6. Test function import and call
                #   7. Validator finalization
                # ============================================================

                # Save the current indent to restore after test scope generation
                pre_test_scope_indent = current_indent

                # Get test metadata from the injection registry
                test_scope_name = child_node.name
                test_scope = injection_registry.lookup_resource_scope(test_scope_name)

                # Get the list of parameters the test function expects
                test_parameters = child_node.function_parameters

                # ------------------------------------------------------------
                # TEST-LOCAL PARAMETER IDENTIFICATION
                # ------------------------------------------------------------
                # Identify parameters that are created at test scope (not
                # inherited from parent scopes). These need factory imports
                # and for loops to create them.
                # ------------------------------------------------------------
                test_local_args = []

                for param_name in test_parameters:
                    # If the test parameter is of test_scope origin
                    # then we need to add it to test_local_args so we
                    # can create an import for it.
                    if test_scope is not None and param_name in test_scope.parameter_originations:
                        param_obj = test_scope.parameter_originations[param_name]
                        test_local_args.append((param_name, param_obj))

                # Variables for building the notables dictionary (used for parameterized tests)
                notables_map = ""
                notables_args = ""

                # Generate a visual separator comment for this test in the sequence document
                method_lines.append("{}# ================ Test Scope: {} ================".format(current_indent, test_scope_name))
                method_lines.append('')

                # Store the test name in a variable for use in scope context calls
                method_lines.append('{}test_scope_name = "{}"'.format(current_indent, test_scope_name))
                method_lines.append('')

                constraints = None

                # ------------------------------------------------------------
                # TEST SETUP SCOPE AND LOCAL PARAMETER GENERATION
                # ------------------------------------------------------------
                # If the test has local parameters, generate:
                #   1. Test setup scope context
                #   2. Factory imports for local parameters
                #   3. For loops to create local parameters
                #   4. Notables dictionary for parameterized test identification
                # ------------------------------------------------------------
                if len(test_local_args) > 0:
                    method_lines.append('{}with sequencer.enter_test_setup_context(test_scope_name) as tsetup:'.format(current_indent))
                    current_indent += indent_space

                    # Track parameter names for building the notables dictionary
                    notables_map_names = []

                    # Collect factory imports for test-local parameters
                    param_name: str
                    param_obj: ResourceOrigin

                    for param_name, param_obj in test_local_args:
                        fmodname = param_obj.source_module_name
                        ffuncname = param_obj.source_function_name
                        # Add to factory_imports set for insertion at the top of the document
                        factory_imports.add("from {} import {}".format(fmodname, ffuncname))

                    method_lines.append('')

                    # ------------------------------------------------------------
                    # TEST-LOCAL PARAMETER LOOP GENERATION
                    # ------------------------------------------------------------
                    # Generate for loops for each test-local parameter. Similar
                    # to module-scoped parameters, but these are created fresh
                    # for each test execution.
                    # ------------------------------------------------------------
                    for param_name, param_obj in test_local_args:
                        ffuncname = param_obj.source_function_name
                        ffuncsig = param_obj.source_signature
                        ffuncargs = [pn for pn in ffuncsig.parameters]

                        # Handle constraints parameter for test-local factories
                        if 'constraints' in ffuncargs:
                            constraints_key = param_obj.constraints_key
                            if constraints_key is not None:
                                if constraints_catalog.lookup_constraints(constraints_key) is None:
                                    raise RuntimeError(f"Constraint required but not found for contraints_key={constraints_key}")
                                method_lines.append('{}constraints=constraints_catalog.lookup_constraints({})'.format(current_indent, repr(constraints_key)))
                            else:
                                ffuncargs.remove('constraints')

                        # Generate the for loop for this parameter
                        ffuncargs_str = " ,".join(ffuncargs)
                        method_lines.append("{}for {} in {}({}):".format(current_indent, param_name, ffuncname, ffuncargs_str))
                        
                        # Track this parameter for the notables dictionary
                        notables_map_names.append(param_name)
                        current_indent += indent_space
                
                    # ------------------------------------------------------------
                    # NOTABLES DICTIONARY GENERATION
                    # ------------------------------------------------------------
                    # Build the notables dictionary which maps parameter names to
                    # their values. This is used by the test scope to identify
                    # parameterized test instances (monikers) and record pivot values.
                    #
                    # Example: notables = { 'param1': param1, 'param2': param2, }
                    # ------------------------------------------------------------
                    notables_map = ", ".join(map(lambda arg: "'{}': {}".format(arg, arg), notables_map_names))
                    if len(notables_map_names) == 1:
                        # Add trailing comma for single-item dict to ensure valid Python syntax
                        notables_map += ","

                    # Add notables argument to the test scope context call
                    notables_args = ", notables=notables"

                    method_lines.append('')

                # Write the notables dictionary if we have parameterized values
                if len(notables_map) > 0:
                    method_lines.append('{}notables'.format(current_indent) + " = { " + notables_map + " }")

                # ------------------------------------------------------------
                # TEST SCOPE CONTEXT
                # ------------------------------------------------------------
                # Create the test scope context which:
                #   - Creates a unique scope ID for this test execution
                #   - Creates a TestResult node for recording
                #   - Handles exceptions and marks results appropriately
                #   - Records the final result on exit
                # ------------------------------------------------------------
                # Detect @expect_exception at code-gen time and build the expected_failure arg
                expect_exception_meta = getattr(child_node._inj_function, '_expect_exception_', None)
                expected_failure_args = ""
                if expect_exception_meta is not None:
                    ex_type = expect_exception_meta['exception_type']
                    ex_reason = expect_exception_meta.get('reason', '')
                    # Import the exception class into the generated code
                    ex_module = ex_type.__module__
                    ex_name = ex_type.__qualname__
                    if ex_module != 'builtins':
                        factory_imports.add("from {} import {}".format(ex_module, ex_name))
                    expected_failure_args = ", expected_failure={{'exception_type': {}, 'reason': {}}}".format(ex_name, repr(ex_reason))

                method_lines.append('{}with sequencer.enter_test_scope_context(test_scope_name{}{}) as tscope:'.format(current_indent, notables_args, expected_failure_args))
                current_indent += indent_space

                # ------------------------------------------------------------
                # VALIDATOR SETUP (VALIDATOR LIFECYCLE - PHASE 1: CONSTRUCTION)
                # ------------------------------------------------------------
                # Validators are assertion helpers that can perform setup before
                # a test runs and verification after it completes. The validator
                # lifecycle has three phases:
                #
                # VALIDATOR LIFECYCLE OVERVIEW:
                # =============================
                # Phase 1 - Construction: Create validator instances from factories
                # Phase 2 - Attachment: Attach validators to the test scope
                # Phase 3 - Finalization: Call finalize() for cleanup and assertions
                #
                # The generated code wraps test execution in try/finally to ensure
                # finalize() is always called, even if the test raises an exception.
                #
                # Generated code structure:
                #   try:
                #       # Phase 1: Construction
                #       validator = create_validator(constraints=...)
                #       # Phase 2: Attachment
                #       validator.attach_to_test(tscope, 'suffix')
                #       
                #       # Test execution
                #       from module import test_function
                #       test_function(params...)
                #   finally:
                #       # Phase 3: Finalization (always runs)
                #       validator.finalize()
                #
                # Why try/finally?
                #   - Ensures validators can perform cleanup regardless of test outcome
                #   - Allows validators to record additional failures during finalize()
                #   - Prevents resource leaks from validators that hold external resources
                #
                # Validator ordering:
                #   - Construction: Validators are created in reverse order
                #   - Finalization: Validators are finalized in original order
                #   - This ensures proper nesting for validators that depend on each other
                # ------------------------------------------------------------
                validator_originations = [vo for vo in test_scope.validator_originations.values()] if test_scope is not None else []

                val_indent = ""
                # Write the validator construction calls (Phase 1 & 2)
                if len(validator_originations) > 0:
                    val_indent = "    "  # Extra indent for try block content
                    validator_originations.reverse()  # Process in reverse order for proper nesting
                    method_lines.append("")
                    method_lines.append(f"{current_indent}try:")
                    
                    # VALIDATOR LIFECYCLE - PHASE 1: CONSTRUCTION
                    # Create each validator instance from its factory function
                    for vorigin in validator_originations:
                        # Add validator factory import to the imports set
                        factory_imports.add("from {} import {}".format(vorigin.source_module_name, vorigin.source_function_name))

                        # Handle constraints for validator factories (same pattern as parameter factories)
                        val_parameter_names = [pn for pn in vorigin.source_signature.parameters.keys()]
                        val_constraints = None

                        if 'constraints' in val_parameter_names:
                            constraints_key = vorigin.constraints_key
                            if constraints_key is not None:
                                val_constraints = constraints_catalog.lookup_constraints(constraints_key)
                                if val_constraints is None:
                                    raise RuntimeError(f"Constraint required but not found for contraints_key={constraints_key}")
                                method_lines.append('{}{}constraints=constraints_catalog.lookup_constraints({})'.format(current_indent, val_indent, repr(constraints_key)))
                            else:
                                val_parameter_names.remove('constraints')
                        
                        # Generate validator construction: validator = create_validator(...)
                        method_lines.append("{}{}{} = {}".format(current_indent, val_indent, vorigin.identifier, vorigin.generate_call(constraints=val_constraints)))
                        
                        # VALIDATOR LIFECYCLE - PHASE 2: ATTACHMENT
                        # Attach the validator to the test scope so it can:
                        #   - Access test metadata and results
                        #   - Record failures and warnings
                        #   - Interact with the test execution context
                        method_lines.append("{}{}{}.attach_to_test(tscope, '{}')".format(current_indent, val_indent, vorigin.identifier, vorigin.suffix))
                    method_lines.append("")

                # ------------------------------------------------------------
                # TEST FUNCTION IMPORT AND CALL
                # ------------------------------------------------------------
                # Import the test function from its module and call it with
                # all the accumulated parameters (session, module, and test-local).
                #
                # PROPERTY TEST DETECTION (compile-time):
                # At code-gen time, the test function is already available via
                # child_node._inj_function (imported during discovery). If the
                # function has a _property_ attribute (set by the @given
                # decorator), we generate PropertyRunner invocation code.
                # Otherwise we generate a direct function call.
                # ------------------------------------------------------------
                test_args = []
                for param_name in test_parameters:
                    test_args.append(param_name)

                # Import the test function (done inside the scope for lazy loading)
                method_lines.append("{}{}from {} import {}".format(current_indent, val_indent, child_node.module_name, child_node.base_name))
                method_lines.append('')

                # Detect property tests at code-gen time
                is_property_test = hasattr(child_node._inj_function, '_property_')

                if is_property_test:
                    # PROPERTY TEST: delegate to sequencer.run_property_test()
                    prop_indent = current_indent + val_indent
                    test_qualified_name = "{}#{}".format(child_node.module_name, child_node.base_name)
                    method_lines.append('{}test_case_name = "{}"'.format(prop_indent, test_qualified_name))
                    method_lines.append('')

                    # Exclude strategy params — they don't exist as variables in the
                    # generated scope; PropertyRunner generates them at runtime.
                    strategy_names = set(child_node._inj_function._property_['strategies'].keys())
                    injected_only = [a for a in test_args if a not in strategy_names]

                    if len(injected_only) > 0:
                        args_dict = ", ".join(["'{}': {}".format(a, a) for a in injected_only])
                        method_lines.append("{}sequencer.run_property_test({}, test_case_name, tscope.recorder, tscope.scope_id, {{{}}})".format(
                            prop_indent, child_node.base_name, args_dict))
                    else:
                        method_lines.append("{}sequencer.run_property_test({}, test_case_name, tscope.recorder, tscope.scope_id, {{}})".format(
                            prop_indent, child_node.base_name))
                elif child_node.is_async:
                    async_indent = current_indent + val_indent

                    if len(test_args) > 0:
                        args_dict = ", ".join(["'{}': {}".format(a, a) for a in test_args])
                        method_lines.append("{}sequencer.run_async_test({}, {{{}}})".format(
                            async_indent, child_node.base_name, args_dict))
                    else:
                        method_lines.append("{}sequencer.run_async_test({}, {{}})".format(
                            async_indent, child_node.base_name))
                else:
                    # REGULAR TEST: direct function call (existing behavior)
                    call_line = '{}{}{}({})'.format(current_indent, val_indent, child_node.base_name, ", ".join(test_args))
                    method_lines.append(call_line)

                method_lines.append('')

                # ------------------------------------------------------------
                # VALIDATOR FINALIZATION (VALIDATOR LIFECYCLE - PHASE 3)
                # ------------------------------------------------------------
                # Generate the finally block to ensure finalize() is called on
                # each validator regardless of test outcome. This is critical for:
                #
                # 1. Cleanup: Release resources held by validators
                # 2. Final assertions: Validators can check accumulated state
                # 3. Result recording: Validators can add failures/warnings
                #
                # Finalization order:
                #   - Validators are finalized in the ORIGINAL order (not reversed)
                #   - This is the opposite of construction order
                #   - Ensures proper unwinding of nested validator dependencies
                #
                # Example with multiple validators:
                #   try:
                #       validator_a = create_validator_a()  # Created first
                #       validator_b = create_validator_b()  # Created second
                #       test_function()
                #   finally:
                #       validator_a.finalize()  # Finalized first (original order)
                #       validator_b.finalize()  # Finalized second
                #
                # The finalize() method typically:
                #   - Verifies expected conditions were met during the test
                #   - Releases external resources (connections, files, etc.)
                #   - Records any deferred failures or warnings
                #   - Performs cleanup that must happen regardless of test result
                # ------------------------------------------------------------
                if len(validator_originations) > 0:
                    validator_originations.reverse()  # Reverse back to original order for finalization
                    method_lines.append("")
                    method_lines.append(f"{current_indent}finally:")
                    for vorigin in validator_originations:
                        method_lines.append("{}{}{}.finalize()".format(current_indent, val_indent, vorigin.identifier))

                # Restore the indent to before the test scope
                current_indent = pre_test_scope_indent

            else:
                # ============================================================
                # CHILD SCOPE FUNCTION CALL
                # ============================================================
                # For TestGroup children (sub-modules), generate a call to
                # the child's scope function. The child scope will be generated
                # separately and added to the scopes_called list.
                # ============================================================
                scope_module = child_name

                # Build the fully qualified module name
                if child_node.package:
                    scope_module = child_node.package + "." + child_name
                
                # Convert module name to a valid Python function name
                scope_name = scope_module.replace(".", "_")
                
                # Generate the function call with all accumulated parameters
                call_line = '{}scope_{}({})'.format(current_indent, scope_name, ", ".join(child_call_args))
                method_lines.append(call_line)
                
                # Queue this scope for generation
                scopes_called.append((scope_module, scope_name, child_node, child_call_args))

        # --------------------------------------------------------------------
        # FUNCTION RETURN
        # --------------------------------------------------------------------
        method_lines.append('')
        method_lines.append('{}return'.format(indent_space))
        method_lines.append('')

        # Write the complete method to the output file
        method_content = os.linesep.join(method_lines)
        outf.write(method_content)

        return scopes_called

    def record_import_errors(self, outputfilename: str):
        """
            Writes import errors encountered during discovery to a file in JSOS format.

            This method serializes all import errors that were collected during the discovery
            phase to a file. The file uses JSOS (JSON Separated Object Stream) format, where
            each error record is separated by a record separator character. This format allows
            for efficient streaming and parsing of error records.

            :param outputfilename: The absolute or relative path to the file where import errors
                should be written. The file will be created if it does not exist, or overwritten
                if it already exists. The recommended file extension is ``.jsos`` to indicate
                the JSOS format.

            :returns: None. The method writes directly to the specified file.

            :raises OSError: If the output file cannot be created or written to due to
                permission issues or invalid path.
            :raises IOError: If there is an error during file write operations.

            Prerequisites:
                This method should be called after :meth:`discover` has been executed, as the
                import errors are collected during the discovery phase. If called before
                discovery, the output file will be empty.

            JSOS Format:
                JSOS (JSON Separated Object Stream) is a format where multiple JSON objects
                are stored in a single file, separated by the ASCII record separator character
                (``\\x1e``). This format is useful for:

                - Streaming large numbers of records without loading all into memory
                - Appending new records without rewriting the entire file
                - Efficient parsing of individual records

            Output Format:
                Each import error is written as a JSON object with the following fields:

                - ``module`` (str): The fully qualified name of the module that failed to import
                  (e.g., ``"package.subpackage.module"``)
                - ``filename`` (str): The absolute path to the file that failed to import
                  (e.g., ``"/path/to/module.py"``)
                - ``trace`` (List[str]): A list of strings containing the error traceback lines,
                  split by newlines for easier processing

                Records are separated by the JSOS record separator character (``CHAR_RECORD_SEPERATOR``).

            Example Output File Content::

                <RS>{"module": "package.module", "filename": "/path/to/module.py", "trace": [
                    "Traceback (most recent call last):",
                    "  File \\"/path/to/module.py\\", line 1, in <module>",
                    "    import nonexistent_module",
                    "ImportError: No module named 'nonexistent_module'"
                ]}
                <RS>{"module": "package.other", "filename": "/path/to/other.py", "trace": [
                    "Traceback (most recent call last):",
                    "  File \\"/path/to/other.py\\", line 5",
                    "    def broken_function(",
                    "SyntaxError: unexpected EOF while parsing"
                ]}

            Common Import Error Types:
                The import errors captured during discovery typically include:

                - **ImportError**: Missing dependencies or modules
                - **SyntaxError**: Python syntax errors in the module
                - **ModuleNotFoundError**: Module not found in the Python path
                - **AttributeError**: Errors accessing module attributes during import
                - **TypeError**: Type-related errors during module initialization

            Example Usage::

                from ccai.testbase.sequencing.testsequencer import TestSequencer
                import os

                # Create and configure the sequencer
                with TestSequencer(jobtitle, root, includes, excludes, metafilters) as sequencer:
                    # Discover tests (import errors are collected here)
                    test_count = sequencer.discover()

                    # Check if there were any import errors
                    if len(sequencer.import_errors) > 0:
                        # Record import errors to a file for later analysis
                        results_dir = sequencer.output_context.get_test_results_dir()
                        error_file = os.path.join(results_dir, "import-errors.jsos")
                        sequencer.record_import_errors(error_file)

                        # Log a warning about the import errors
                        logger.warning(f"Encountered {len(sequencer.import_errors)} import errors")

            Example Parsing JSOS Output::

                import json
                from ccai.xmodules.jsos import CHAR_RECORD_SEPERATOR

                def parse_import_errors(filepath):
                    \"\"\"Parse import errors from a JSOS file.\"\"\"
                    errors = []
                    with open(filepath, 'r') as f:
                        content = f.read()
                        # Split by record separator and filter empty strings
                        records = [r for r in content.split(CHAR_RECORD_SEPERATOR) if r.strip()]
                        for record in records:
                            error = json.loads(record)
                            errors.append(error)
                    return errors

                # Usage
                errors = parse_import_errors("import-errors.jsos")
                for error in errors:
                    print(f"Module: {error['module']}")
                    print(f"File: {error['filename']}")
                    print("Traceback:")
                    for line in error['trace']:
                        print(f"  {line}")

            Integration with Test Reporting:
                Import errors are typically recorded as part of the test run setup phase and
                can be included in test reports to help diagnose why certain tests were not
                discovered or executed. The JSOS format allows test reporting tools to
                efficiently process and display these errors.

            See Also:
                - :attr:`import_errors`: The dictionary of import errors collected during discovery
                - :meth:`discover`: Populates the import_errors during the discovery phase
                - :meth:`generate_testrun_sequence_document`: Generates the test execution document
                - :const:`CHAR_RECORD_SEPERATOR`: The JSOS record separator character
        """
        with open(outputfilename, 'w') as ief:

            modname: str
            filename: str
            errmsg: str
            
            for modname, filename, errmsg in self._import_errors.values():
                ief.write(CHAR_RECORD_SEPERATOR)
                ieitem = {
                    "module": modname,
                    "filename": filename,
                    "trace": errmsg.splitlines(False)
                }
                json.dump(ieitem, ief, indent=4)

        return
