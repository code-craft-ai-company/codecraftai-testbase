HTML Report Templates Customization Guide
==========================================

Audience
--------

QA engineers and developers who want to customize the appearance and functionality of TestBase HTML test reports.


Overview
--------

The TestBase HTML Report Templates system provides a client-side web application for rendering test execution results. This guide covers three key customization areas:

1. **Theming Customization** - Customize colors, branding, and visual appearance
2. **Custom Artifact Tabs** - Create specialized viewers for test artifacts
3. **Data File Formats** - Understand the JSON/JSOS data structures consumed by the templates


1. Theming Customization
------------------------

The HTML Report Templates use CSS custom properties (CSS variables) for theming. You can override these properties to match your organization's branding without modifying the core template files.

CSS Custom Properties Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Result Status Colors
^^^^^^^^^^^^^^^^^^^^

These colors are used for test result indicators (pass, fail, error, etc.):

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Property
     - Default
     - Description
   * - ``--color-error``
     - maroon
     - Error indicator color (test errors)
   * - ``--color-fail``
     - red
     - Failure indicator color (assertion failures)
   * - ``--color-pass``
     - green
     - Pass indicator color (successful tests)
   * - ``--color-skip``
     - gray
     - Skip indicator color (skipped tests)
   * - ``--color-warn``
     - orange
     - Warning indicator color
   * - ``--color-ghost``
     - #B0B0B0
     - Zero count (ghosted) color for visual de-emphasis

Result Background Colors
^^^^^^^^^^^^^^^^^^^^^^^^

Background colors for result status indicators (lighter versions of status colors):

.. list-table::
   :header-rows: 1
   :widths: 30 30 40

   * - Property
     - Default
     - Description
   * - ``--color-error-background``
     - rgb(252, 142, 142)
     - Error background
   * - ``--color-fail-background``
     - rgb(255, 171, 171)
     - Failure background
   * - ``--color-pass-background``
     - rgb(175, 231, 175)
     - Pass background
   * - ``--color-skip-background``
     - rgb(221, 199, 199)
     - Skip background
   * - ``--color-warn-background``
     - rgb(204, 170, 108)
     - Warning background
   * - ``--color-ghost-background``
     - #d6d4d4
     - Ghost background

Banner and Section Colors
^^^^^^^^^^^^^^^^^^^^^^^^^

Colors for the report header banner and section headers:

.. list-table::
   :header-rows: 1
   :widths: 40 20 40

   * - Property
     - Default
     - Description
   * - ``--color-banner-background-color``
     - #0e0e25
     - Banner background color
   * - ``--color-banner-color``
     - whitesmoke
     - Banner text color
   * - ``--color-section-header-background-color``
     - #50526e
     - Section header background
   * - ``--color-section-header-color``
     - whitesmoke
     - Section header text
   * - ``--color-subsection-header-background-color``
     - #50526e
     - Subsection header background
   * - ``--color-subsection-header-color``
     - whitesmoke
     - Subsection header text

Logo Image
^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Property
     - Default
     - Description
   * - ``--image-logo``
     - url("/static/v2/images/test-report-banner-background-image.png")
     - Banner logo image URL

Creating a Custom Theme
~~~~~~~~~~~~~~~~~~~~~~~

Option 1: Override in a Custom CSS File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a custom CSS file that overrides the default properties:

.. code-block:: css

   /* my-organization-theme.css */
   
   @property --color-banner-background-color {
       syntax: "<color>";
       inherits: false;
       initial-value: #1E3A5F;  /* Corporate dark blue */
   }
   
   @property --color-banner-color {
       syntax: "<color>";
       inherits: false;
       initial-value: #FFFFFF;
   }
   
   @property --color-section-header-background-color {
       syntax: "<color>";
       inherits: false;
       initial-value: #2E5A8F;  /* Corporate medium blue */
   }
   
   @property --image-logo {
       syntax: "<url>";
       inherits: false;
       initial-value: url("/path/to/my-organization-logo.png");
   }

Include your custom CSS file after the default ``branding-theme.css``:

.. code-block:: html

   <link rel="stylesheet" href="/static/v2/styles/branding-theme.css">
   <link rel="stylesheet" href="/path/to/my-organization-theme.css">

Option 2: Replace the Default Theme
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Copy the default ``branding-theme.css`` to your static files directory
2. Modify the CSS custom property values to match your branding
3. Deploy the modified file as ``branding-theme.css``

Theming Best Practices
~~~~~~~~~~~~~~~~~~~~~~

1. **Accessibility**: Ensure sufficient contrast between text and background colors (WCAG 2.1 AA requires 4.5:1 for normal text)
2. **Consistency**: Use your organization's color palette for a cohesive look
3. **Logo Size**: The banner logo should be appropriately sized (recommended: 200x50 pixels)
4. **Testing**: Preview your theme with various test result combinations (pass, fail, error, skip)

Example Theme
~~~~~~~~~~~~~

See ``source/examples/html_templates/custom_branding/`` for a complete corporate blue theme example.


2. Custom Artifact Tab Creation
-------------------------------

The HTML Report Templates support custom artifact viewers through embedded tab pages. When the report loads, it scans the ``artifacts/`` directory for subdirectories containing a ``tab.html`` file and creates a tab for each one.

Artifact Directory Structure
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

   test-output/
   ├── artifacts/
   │   ├── catalog.json           # Lists artifact folders
   │   ├── screenshots/
   │   │   ├── catalog.json       # Lists files in this folder
   │   │   └── tab.html           # Tab page (built-in or custom)
   │   ├── logs/
   │   │   ├── catalog.json
   │   │   └── tab.html           # Custom log viewer
   │   └── performance/
   │       ├── catalog.json
   │       ├── chartsummary.json  # Chart configuration
   │       ├── series/            # Time series data files
   │       └── tab.html           # Time series chart viewer

Creating a Custom Tab
~~~~~~~~~~~~~~~~~~~~~

Step 1: Create the Artifact Directory
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a subdirectory under ``artifacts/`` for your artifact type:

.. code-block:: bash

   mkdir -p artifacts/my-custom-artifacts

Step 2: Create catalog.json
^^^^^^^^^^^^^^^^^^^^^^^^^^^

List the files in your artifact directory:

.. code-block:: json

   {
       "files": ["file1.txt", "file2.txt", "data.json", "tab.html"],
       "folders": []
   }

Step 3: Create tab.html
^^^^^^^^^^^^^^^^^^^^^^^

Create an HTML file that displays your artifacts. The tab page is loaded in an iframe, so it should be a complete HTML document.

Basic tab.html template:

.. code-block:: html

   <!DOCTYPE html>
   <html lang="en">
   <head>
       <title>My Custom Artifacts</title>
       <script src="/static/v2/javascript/testsummary-helpers.js"></script>
       <style>
           body {
               margin: 0;
               padding: 10px;
               font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           }
           .artifact-container {
               margin-bottom: 15px;
               border: 1px solid #ddd;
               border-radius: 4px;
               padding: 10px;
           }
       </style>
       <script>
           async function loadArtifacts() {
               const catalog = await fetch_json("catalog.json");
               if (!catalog || !catalog.files) return;
               
               const container = document.getElementById('artifacts');
               for (const filename of catalog.files) {
                   if (filename === 'tab.html' || filename === 'catalog.json') continue;
                   
                   const div = document.createElement('div');
                   div.className = 'artifact-container';
                   div.innerHTML = `<h4>${filename}</h4>`;
                   // Add your custom rendering logic here
                   container.appendChild(div);
               }
           }
           document.addEventListener('DOMContentLoaded', loadArtifacts);
       </script>
   </head>
   <body>
       <h3>My Custom Artifacts</h3>
       <div id="artifacts"></div>
   </body>
   </html>

Built-in Tab Types
~~~~~~~~~~~~~~~~~~

The templates include built-in tab pages for common artifact types:

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Tab Type
     - File
     - Supported Extensions
   * - Images
     - tab-images.html
     - .png, .jpg
   * - Sounds
     - tab-sounds.html
     - .mp3, .wav
   * - Videos
     - tab-videos.html
     - .mp4, .webm, .ogg, .mov, .avi
   * - Log Files
     - tab-logs.html
     - .log, .txt, .out
   * - Data Files
     - tab-data.html
     - .json, .xml, .jsos
   * - Time Series
     - tab-timeseries.html
     - .jsos (with chartsummary.json)

Video Artifact Viewer
~~~~~~~~~~~~~~~~~~~~~

The video artifact viewer (``tab-videos.html``) provides:

- HTML5 video playback with standard controls
- Fullscreen mode toggle
- Video metadata display (duration, resolution)
- Download functionality

Supported video formats: MP4, WebM, OGG, MOV, AVI

Log File Viewer
~~~~~~~~~~~~~~~

The log file viewer (``tab-logs.html``) provides:

- Syntax highlighting for log levels (ERROR, WARN, INFO, DEBUG)
- Real-time search with match highlighting
- Log level filtering buttons
- Line numbers for easy reference
- Collapsible log file sections
- Download functionality

Supported log formats: .log, .txt, .out

Data File Viewer
~~~~~~~~~~~~~~~~

The data file viewer (``tab-data.html``) provides:

- JSON syntax highlighting with color-coded keys, values, and brackets
- XML syntax highlighting with tag and attribute coloring
- JSOS (JSON Stream) support with record separation
- Tree view mode for JSON files (collapsible/expandable nodes)
- Search functionality with highlighting
- Copy to clipboard functionality
- Download functionality

Supported data formats: .json, .xml, .jsos

Time Series Chart Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For time series charts, create a ``chartsummary.json`` file:

.. code-block:: json

   {
       "title": "Performance Metrics",
       "xlabel": "Time",
       "ylabel": "Value",
       "series": [
           {
               "name": "CPU Usage",
               "file": "series/cpu.jsos",
               "timeField": "timestamp",
               "valueField": "value",
               "color": "#2196F3"
           },
           {
               "name": "Memory Usage",
               "file": "series/memory.jsos",
               "timeField": "timestamp",
               "valueField": "value",
               "color": "#4CAF50"
           }
       ]
   }

Custom Tab Best Practices
~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Self-contained**: Tab pages are loaded in iframes, so include all necessary CSS and JavaScript
2. **Relative paths**: Use relative paths to access files in the same directory
3. **Helper functions**: Use shared helpers from ``/static/v2/javascript/testsummary-helpers.js``
4. **Error handling**: Handle missing files gracefully
5. **Performance**: For large files, consider lazy loading or pagination
6. **Accessibility**: Include appropriate ARIA labels and keyboard navigation

Example Custom Tab
~~~~~~~~~~~~~~~~~~

See ``source/examples/html_templates/custom_artifact_tab/tab-logs.html`` for a complete log file viewer example.


3. Data File Formats
--------------------

The HTML Report Templates consume several JSON and JSOS data files generated by the TestBase framework.

testrun_summary.json
~~~~~~~~~~~~~~~~~~~~

High-level test run summary with metrics and status.

.. code-block:: json

   {
       "version": "2",
       "title": "Example Test Suite",
       "runid": "unique-run-identifier",
       "start": "2024-01-15T10:30:00.000000",
       "stop": "2024-01-15T11:45:30.500000",
       "result": "PASSED",
       "apod": "automation-pod-name",
       "build": {
           "branch": "main",
           "build": "build-12345",
           "flavor": "release"
       },
       "totals": null,
       "running": {},
       "detail": {
           "errors": 1,
           "failed": 2,
           "skipped": 5,
           "passed": 92,
           "total": 100
       }
   }

Field descriptions:

.. list-table::
   :header-rows: 1
   :widths: 20 15 65

   * - Field
     - Type
     - Description
   * - ``version``
     - string
     - Schema version (currently "2")
   * - ``title``
     - string
     - Test run title
   * - ``runid``
     - string
     - Unique identifier for this test run
   * - ``start``
     - string
     - ISO 8601 timestamp when test run started
   * - ``stop``
     - string
     - ISO 8601 timestamp when test run completed
   * - ``result``
     - string
     - Overall result: PASSED, FAILED, ERRORED
   * - ``apod``
     - string
     - Automation pod name
   * - ``build``
     - object
     - Build information (branch, build number, flavor)
   * - ``detail``
     - object
     - Result counts (errors, failed, skipped, passed, total)

testrun_results_stream.jsos
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Streaming test results in JSOS (JSON Separated Object Stream) format. Each record is a JSON object separated by the ASCII record separator character (``0x1E``).

Test Result Record
^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "name": "package.module#test_function",
       "monikers": [],
       "pivots": {},
       "instance": "uuid-for-this-test-instance",
       "parent": "uuid-of-parent-container",
       "rtype": "TEST",
       "result": "PASSED",
       "start": "2024-01-15T10:30:05.000000",
       "stop": "2024-01-15T10:30:05.150000",
       "detail": {
           "errors": [],
           "failures": [],
           "warnings": []
       }
   }

Field descriptions:

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Field
     - Type
     - Description
   * - ``name``
     - string
     - Full test name (package.module#test_function)
   * - ``monikers``
     - array
     - Test monikers/tags
   * - ``pivots``
     - object
     - Pivot parameters for parameterized tests
   * - ``instance``
     - string
     - UUID for this test instance
   * - ``parent``
     - string
     - UUID of parent container
   * - ``rtype``
     - string
     - Record type: TEST, TASKING_GROUP, TASKING
   * - ``result``
     - string
     - Result code: PASSED, FAILED, ERRORED, SKIPPED, UNSET
   * - ``start``
     - string
     - ISO 8601 start timestamp
   * - ``stop``
     - string
     - ISO 8601 stop timestamp
   * - ``detail``
     - object
     - Detailed results (errors, failures, warnings arrays)

Failed Test Example
^^^^^^^^^^^^^^^^^^^

.. code-block:: json

   {
       "name": "example.tests.test_api#test_delete_user",
       "instance": "c9d0e1f2-a3b4-5678-cdef-901234567890",
       "parent": "root-parent-id-002",
       "rtype": "TEST",
       "result": "FAILED",
       "start": "2024-01-15T10:31:06.000000",
       "stop": "2024-01-15T10:31:08.100000",
       "detail": {
           "errors": [],
           "failures": [
               {
                   "extype": "AssertionError",
                   "exargs": ["Expected status 204 but got 403"],
                   "trace": [
                       {
                           "path": "/tests/integration/test_api.py",
                           "lineno": 78,
                           "context": "assert response.status_code == 204"
                       }
                   ]
               }
           ],
           "warnings": []
       }
   }

catalog.json
~~~~~~~~~~~~

Directory inventory for file/folder navigation.

.. code-block:: json

   {
       "files": [
           "testrun_summary.json",
           "testrun_results_stream.jsos",
           "landscape-declared.json",
           "startup-configuration.json"
       ],
       "folders": [
           "artifacts",
           "logs"
       ]
   }

landscape-declared.json
~~~~~~~~~~~~~~~~~~~~~~~

Test landscape configuration describing devices, services, and data profiles.

.. code-block:: json

   {
       "devices": {
           "primary-group": [
               {
                   "name": "web-server-01",
                   "deviceType": "linux-server",
                   "host": "192.168.1.100",
                   "role": "web-server",
                   "credentials": "ssh-key-web",
                   "features": ["nginx", "ssl"],
                   "skip": false
               }
           ]
       },
       "services": [
           {
               "name": "api-gateway",
               "serviceType": "http-api",
               "host": "https://api.example.com",
               "credentials": "api-key-gateway"
           }
       ],
       "dataprofiles": [
           {
               "name": "test-data-profile",
               "profileType": "json-data",
               "host": "file:///data/test-fixtures",
               "credentials": null
           }
       ]
   }

startup-configuration.json
~~~~~~~~~~~~~~~~~~~~~~~~~~

Test invocation command, environment variables, and installed packages.

.. code-block:: json

   {
       "command": "testbase run --testroot ./tests --output ./results",
       "environment": {
           "PYTHONPATH": "/app/src:/app/tests",
           "TEST_ENV": "staging",
           "LOG_LEVEL": "DEBUG"
       },
       "packages": {
           "codecraftai-testbase": "1.2.3",
           "pytest": "7.4.0",
           "requests": "2.31.0"
       }
   }

import_errors.jsos
~~~~~~~~~~~~~~~~~~

Import errors encountered during test discovery (JSOS format).

.. code-block:: json

   {
       "module": "example.tests.broken.test_missing_dependency",
       "trace": [
           {
               "path": "/tests/broken/test_missing_dependency.py",
               "lineno": 1,
               "context": "import nonexistent_package"
           }
       ],
       "extype": "ModuleNotFoundError",
       "exargs": ["No module named 'nonexistent_package'"]
   }


Example Files
-------------

Complete example files are available in the repository:

- ``source/examples/html_templates/sample_data/`` - Sample JSON/JSOS data files
- ``source/examples/html_templates/custom_branding/`` - Custom theme example
- ``source/examples/html_templates/custom_artifact_tab/`` - Custom artifact tab example


4. Result Comparison and Trend Analysis
---------------------------------------

The HTML Report Templates include built-in components for comparing test results between runs and analyzing trends over time.

Result Comparison
~~~~~~~~~~~~~~~~~

The Result Comparison component allows you to compare the current test run against a baseline run to identify:

- **New Failures**: Tests that passed in the baseline but failed in the current run
- **Fixes**: Tests that failed in the baseline but passed in the current run
- **New Tests**: Tests that exist in the current run but not in the baseline
- **Removed Tests**: Tests that existed in the baseline but not in the current run

Using Result Comparison
^^^^^^^^^^^^^^^^^^^^^^^

1. In the test report, locate the "Result Comparison" section
2. Enter the URL or path to a baseline test run's ``testrun_summary.json`` file
3. Click "Load Baseline" to load and compare the results
4. Use the filter buttons to focus on specific change types (New Failures, Fixes, etc.)

Example baseline URL formats:

- Relative path: ``../previous-run/testrun_summary.json``
- Absolute URL: ``https://ci.example.com/results/build-123/testrun_summary.json``

Trend Analysis
~~~~~~~~~~~~~~

The Trend Analysis component allows you to analyze test results across multiple historical runs to identify:

- **Pass Rate Trends**: How the overall pass rate has changed over time
- **Flaky Tests**: Tests that intermittently pass and fail across runs
- **Consistent Failures**: Tests that have failed in every analyzed run

Using Trend Analysis
^^^^^^^^^^^^^^^^^^^^

1. In the test report, locate the "Trend Analysis" section
2. Enter comma-separated URLs to historical test run directories
3. Click "Analyze Trends" to load and analyze the historical data
4. Review the pass rate chart and identified flaky/failing tests

Example input:

.. code-block:: text

   ../run-001, ../run-002, ../run-003, ../run-004

Trend Analysis Metrics
^^^^^^^^^^^^^^^^^^^^^^

The trend analysis provides:

- **Pass Rate Over Time**: A table showing pass rate, passed/failed/error counts for each run
- **Flaky Tests**: Tests with inconsistent results (both passes and failures across runs)
- **Consistent Failures**: Tests that have failed in every analyzed run

Best Practices for Comparison and Trends
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Consistent Test Names**: Ensure test names are consistent across runs for accurate comparison
2. **Baseline Selection**: Choose a known-good baseline for meaningful comparison
3. **Historical Data**: Include enough historical runs (5-10) for meaningful trend analysis
4. **Regular Analysis**: Run trend analysis regularly to catch flaky tests early


See Also
--------

- :doc:`04-03-testresults-and-artifacts` - Test result encoding and report rendering overview
- ``source/packages/ccai/testbase/templates/v2/`` - Template source files
