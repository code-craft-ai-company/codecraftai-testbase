# Custom Branding Theme Example

This directory demonstrates how to customize the HTML Report Templates appearance for your organization's branding.

## Overview

The TestBase HTML Report Templates use CSS custom properties (CSS variables) for theming. You can override these properties to match your organization's branding without modifying the core template files.

## Usage

### Option 1: Override in a Custom CSS File

1. Create a custom CSS file (e.g., `my-organization-theme.css`)
2. Override the CSS custom properties as shown in `custom-branding-theme.css`
3. Include your custom CSS file after the default `branding-theme.css` in your HTML

```html
<link rel="stylesheet" href="/static/v2/styles/branding-theme.css">
<link rel="stylesheet" href="/path/to/my-organization-theme.css">
```

### Option 2: Replace the Default Theme

1. Copy `custom-branding-theme.css` to your static files directory
2. Rename it to `branding-theme.css`
3. Customize the values as needed

## Customizable Properties

### Result Status Colors

| Property | Default | Description |
|----------|---------|-------------|
| `--color-error` | maroon | Error indicator color |
| `--color-fail` | red | Failure indicator color |
| `--color-pass` | green | Pass indicator color |
| `--color-skip` | gray | Skip indicator color |
| `--color-warn` | orange | Warning indicator color |
| `--color-ghost` | #B0B0B0 | Zero count (ghosted) color |

### Background Colors

| Property | Default | Description |
|----------|---------|-------------|
| `--color-error-background` | rgb(252, 142, 142) | Error background |
| `--color-fail-background` | rgb(255, 171, 171) | Failure background |
| `--color-pass-background` | rgb(175, 231, 175) | Pass background |
| `--color-skip-background` | rgb(221, 199, 199) | Skip background |

### Banner and Section Colors

| Property | Default | Description |
|----------|---------|-------------|
| `--color-banner-background-color` | #0e0e25 | Banner background |
| `--color-banner-color` | whitesmoke | Banner text color |
| `--color-section-header-background-color` | #50526e | Section header background |
| `--color-section-header-color` | whitesmoke | Section header text |

### Logo Image

| Property | Default | Description |
|----------|---------|-------------|
| `--image-logo` | url("/static/v2/images/...") | Banner logo image |

## Example: Corporate Blue Theme

See `custom-branding-theme.css` for a complete example of a corporate blue theme that demonstrates:

- Custom banner colors matching corporate branding
- Modified result status colors for better accessibility
- Custom logo image path
- Adjusted section header styling

## Tips

1. **Accessibility**: Ensure sufficient contrast between text and background colors
2. **Consistency**: Use your organization's color palette for a cohesive look
3. **Logo Size**: The banner logo should be appropriately sized (recommended: 200x50px)
4. **Testing**: Preview your theme with various test result combinations (pass, fail, error, skip)
