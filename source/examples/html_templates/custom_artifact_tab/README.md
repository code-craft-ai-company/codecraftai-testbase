# Custom Artifact Tab Page Example

This directory demonstrates how to create custom artifact tab pages for the HTML Report Templates system.

## Overview

The TestBase HTML Report Templates support custom artifact viewers through embedded tab pages. When the report loads, it scans the `artifacts/` directory for subdirectories containing a `tab.html` file and creates a tab for each one.

## Directory Structure

```
test-output/
├── artifacts/
│   ├── catalog.json           # Lists artifact folders
│   ├── screenshots/
│   │   ├── catalog.json       # Lists files in this folder
│   │   └── tab.html           # Uses built-in tab-images.html
│   ├── logs/
│   │   ├── catalog.json
│   │   └── tab.html           # Custom log viewer (see tab-logs.html)
│   └── performance/
│       ├── catalog.json
│       ├── chartsummary.json  # Chart configuration
│       ├── series/            # Time series data
│       └── tab.html           # Uses built-in tab-timeseries.html
```

## Creating a Custom Tab

### Step 1: Create the Artifact Directory

Create a subdirectory under `artifacts/` for your artifact type:

```bash
mkdir -p artifacts/my-custom-artifacts
```

### Step 2: Create catalog.json

List the files in your artifact directory:

```json
{
    "files": ["file1.txt", "file2.txt", "data.json"],
    "folders": []
}
```

### Step 3: Create tab.html

Create an HTML file that displays your artifacts. The tab page is loaded in an iframe, so it should be a complete HTML document.

See `tab-logs.html` for a complete example of a custom log file viewer.

### Key Points

1. **Self-contained**: Tab pages are loaded in iframes, so include all necessary CSS and JavaScript
2. **Relative paths**: Use relative paths to access files in the same directory
3. **Helper functions**: You can use the shared helper functions from `/static/v2/javascript/testsummary-helpers.js`
4. **Catalog access**: Load `catalog.json` to get the list of files to display

## Example Files

### tab-logs.html

A custom log file viewer that:
- Loads text files from the catalog
- Displays log content with syntax highlighting
- Supports collapsible sections for large files
- Provides search/filter functionality

### chartsummary.json

Configuration for time series charts:
- Defines chart title and axis labels
- Specifies data series sources (JSOS files)
- Maps time and value fields

## Built-in Tab Types

The templates include built-in tab pages for common artifact types:

| Tab | File | Supported Extensions |
|-----|------|---------------------|
| Images | tab-images.html | .png, .jpg |
| Sounds | tab-sounds.html | .mp3, .wav |
| Time Series | tab-timeseries.html | .jsos (with chartsummary.json) |

## Tips

1. **Performance**: For large files, consider lazy loading or pagination
2. **Styling**: Match the main report's styling for a consistent look
3. **Error handling**: Handle missing files gracefully
4. **Accessibility**: Include appropriate ARIA labels and keyboard navigation
