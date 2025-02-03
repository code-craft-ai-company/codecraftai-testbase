__author__ = "Myron Walker"
__copyright__ = "Copyright 2025, Automation Mojo LLC"
__credits__ = []


from automojo.foundation.constants import URL_SEPARATOR


HELP_ROOT = "The root directory to use when scanning for tests."
HELP_EXCLUDES = "Add a test inclusion expression."
HELP_INCLUDES = "Add a test exclusion expression."
HELP_OUTPUT = "The output directory where results and artifacts are collected."
HELP_START = r"A time stamp to associate with the start of the run. Example: 2020-10-17T15:30:11.989120  Bash: date +%Y-%m-%dT%H:%M:%S.%N"
HELP_BRANCH = "The name of the branch to associate with the test run results."
HELP_BUILD = "The name of the build to associate with the test run results."
HELP_FLAVOR = "The name of the flavor to associate with the test run results."
HELP_JOB_ID = "A unique identifier for the job with respect to the job runner."
HELP_JOB_INITIATOR = "The name of the initiator of the job."
HELP_JOB_LABEL = "The label associated with the job."
HELP_JOB_NAME = "The name of the job."
HELP_JOB_OWNER = "The ownerid and possibly appended ';(display name)' of the test run result owner."
HELP_RUNID = "A uuid to use for the run id for the testrun."
HELP_CONSOLE_LOG_LEVEL = "The logging level for console output."
HELP_FILE_LOG_LEVEL = "The logging level for logfile output."
HELP_DEBUG = "Output debug information to the console."
HELP_DEBUGGER = "Debugger to active during the test run."
HELP_BREAKPOINT = "The breakpoint to activate for the test run."
HELP_TIMETRAVEL = "Enables tracing for Time-Travel-Debugging."
HELP_TIMEPORTAL = "The name of a time portal to open for Time-Travel-Debugging."
HELP_PRERUN_DIAGNOSTIC = "Flag indicating that a pre run diagnostic should be performed."
HELP_POSTRUN_DIAGNOSTIC = "Flag indicating that a post run diagnostic should be performed."
HELP_INCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will include a test."
HELP_EXCLUDE_MARKER_EXP = "Allows the specification of a marker expression that if matched will exclude a test."
