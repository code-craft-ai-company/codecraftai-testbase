# HTML Report Templates - Usage Examples

This directory contains example files demonstrating how to use and customize the HTML Report Templates system for displaying test execution results.

For comprehensive documentation, see the User Guide: `userguide/04-04-html-report-customization.rst`

## Contents

### Sample Test Result Data Files

The `sample_data/` directory contains example JSON and JSOS files that demonstrate the expected data formats:

| File | Description |
|------|-------------|
| `testrun_summary.json` | Test run summary with metrics and status |
| `testrun_results_stream.jsos` | Streaming test results in JSOS format |
| `catalog.json` | Directory catalog for file/folder navigation |
| `landscape-declared.json` | Landscape configuration with devices, services, and data profiles |
| `startup-configuration.json` | Startup configuration with command, environment, and packages |
| `import_errors.jsos` | Import error examples with tracebacks |

### Custom Branding Theme Example

The `custom_branding/` directory shows how to customize the report appearance:

| File | Description |
|------|-------------|
| `custom-branding-theme.css` | Complete custom CSS theme with organization branding |
| `README.md` | Instructions for applying custom branding |

Key customization areas:
- Result status colors (pass, fail, error, skip)
- Banner and section header colors
- Logo image
- Background colors

### Artifact Tab Page Example

The `custom_artifact_tab/` directory demonstrates creating custom artifact viewers:

| File | Description |
|------|-------------|
| `tab-logs.html` | Complete log file viewer with syntax highlighting and search |
| `chartsummary.json` | Time series chart configuration example |
| `README.md` | Instructions for creating custom artifact tabs |

## Quick Start

### 1. Customize Report Branding

```bash
# Copy the custom theme to your static files
cp custom_branding/custom-branding-theme.css /path/to/static/styles/

# Edit the CSS custom properties to match your branding
# Key properties: --color-banner-background-color, --image-logo
```

### 2. Create a Custom Artifact Tab

```bash
# Create artifact directory
mkdir -p results/artifacts/my-artifacts

# Create catalog.json listing your files
echo '{"files": ["data.json", "tab.html"], "folders": []}' > results/artifacts/my-artifacts/catalog.json

# Create tab.html (see custom_artifact_tab/tab-logs.html for example)
```

### 3. Use Sample Data for Testing

```bash
# Copy sample data to test your customizations
cp -r sample_data/* /path/to/test-output/
```

## Data File Formats

### testrun_summary.json

High-level test run summary:

```json
{
    "version": "2",
    "title": "Test Job",
    "runid": "unique-run-id",
    "start": "2024-01-15T10:30:00.000000",
    "stop": "2024-01-15T11:45:00.000000",
    "result": "PASSED",
    "apod": "automation-pod-name",
    "build": {
        "branch": "main",
        "build": "build-12345",
        "flavor": "release"
    },
    "detail": {
        "errors": 0,
        "failed": 2,
        "skipped": 5,
        "passed": 93,
        "total": 100
    }
}
```

### testrun_results_stream.jsos

JSOS (JSON Separated Object Stream) uses ASCII record separator (0x1E) between records:

```json
{"name": "package.module#test_function", "rtype": "TEST", "result": "PASSED", "start": "...", "stop": "...", "detail": {"errors": [], "failures": [], "warnings": []}}
{"name": "package.module#test_failure", "rtype": "TEST", "result": "FAILED", "detail": {"failures": [{"extype": "AssertionError", "exargs": ["..."], "trace": [...]}]}}
```

### catalog.json

Directory inventory:

```json
{
    "files": ["testrun_summary.json", "testrun_results_stream.jsos"],
    "folders": ["artifacts", "logs"]
}
```

### landscape-declared.json

Test environment topology:

```json
{
    "devices": {
        "group-name": [
            {"name": "device-01", "deviceType": "linux-server", "host": "192.168.1.100", "role": "web-server"}
        ]
    },
    "services": [
        {"name": "api-gateway", "serviceType": "http-api", "host": "https://api.example.com"}
    ],
    "dataprofiles": [
        {"name": "test-data", "profileType": "json-data", "host": "file:///data/fixtures"}
    ]
}
```

### startup-configuration.json

Test invocation details:

```json
{
    "command": "testbase run --testroot ./tests --output ./results",
    "environment": {
        "PYTHONPATH": "/app/src",
        "TEST_ENV": "staging"
    },
    "packages": {
        "automojo-testbase": "1.2.3",
        "pytest": "7.4.0"
    }
}
```

### import_errors.jsos

Import failures during test discovery:

```json
{"module": "tests.broken.test_missing", "extype": "ModuleNotFoundError", "exargs": ["No module named 'missing'"], "trace": [{"path": "/tests/broken/test_missing.py", "lineno": 1, "context": "import missing"}]}
```

## CSS Custom Properties Reference

| Property | Default | Description |
|----------|---------|-------------|
| `--color-error` | maroon | Error indicator |
| `--color-fail` | red | Failure indicator |
| `--color-pass` | green | Pass indicator |
| `--color-skip` | gray | Skip indicator |
| `--color-warn` | orange | Warning indicator |
| `--color-ghost` | #B0B0B0 | Zero count (ghosted) |
| `--color-banner-background-color` | #0e0e25 | Banner background |
| `--color-banner-color` | whitesmoke | Banner text |
| `--color-section-header-background-color` | #50526e | Section header background |
| `--image-logo` | url("/static/v2/images/...") | Banner logo |

## See Also

- `userguide/04-03-testresults-and-artifacts.rst` - Test result encoding overview
- `userguide/04-04-html-report-customization.rst` - Comprehensive customization guide
- `source/packages/automojo/testbase/templates/v2/` - Template source files
