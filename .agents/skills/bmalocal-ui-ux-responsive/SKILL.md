---
name: bmalocal-ui-ux-responsive
description: >-
  UI/UX design system and responsive layout rules for BMALocal — breakpoints,
  spacing scale, accessibility, and cross-device testing. Use for any new
  form, layout change, or component, and before shipping any client_code/
  change.
---

# BMALocal UI/UX & Responsive Design System

This skill defines the visual tokens, responsive layout rules, accessibility baselines, and cross-device validation standards for all client-side UI development in BMALocal.

---

## 1. Design Tokens & Visual Hierarchy

Always reuse existing design tokens from [theme/parameters.yaml](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/parameters.yaml) and [theme/assets/theme.css](file:///d:/BMAAutoAccessories/venv/Lib/site-packages/BMALocal/theme/assets/theme.css). Do not introduce ad-hoc colors or inline styling.

### 1.1 Color Palette
| Token / Name | Hex Code | Usage |
| :--- | :--- | :--- |
| **Primary 500** | `#2196F3` | Primary action buttons, active navigation links, focused borders |
| **Primary 700** | `#1976D2` | Button hover states, active headers |
| **Secondary 500** | `#FF9800` | Badges, warnings, pending workflow alerts |
| **Secondary 700** | `#F57C00` | Secondary button hover, active alert indicators |
| **White** | `#FFFFFF` | Form surfaces, card backgrounds (light mode), text (dark mode) |
| **Gray 50 - 100** | `#FAFAFA` - `#F5F5F5` | Main application background, table stripe backgrounds |
| **Gray 200 - 300** | `#EEEEEE` - `#E0E0E0` | Card borders, table dividers, input borders |
| **Gray 800 - 900** | `#424242` - `#212121` | Dark mode backgrounds, dark card surfaces, deep text |
| **Danger / Red** | `#F44336` | Delete/cancel buttons, error labels, defect indicators |
| **Success / Green** | `#4CAF50` | Completed job cards, payment success indicators |

### 1.2 Typography & Fonts
- **Headings & Titles**: `'Mozilla Headline', 'Outfit', sans-serif`
- **Body & Data Tables**: `'Inter', Roboto, Arial, sans-serif`
- **Technical & Monospace** (VIN, Part Numbers, License Plates): `'Courier New', Courier, monospace`

### 1.3 Spacing Scale (4px Grid)
- **None**: `0px` (`anvil-spacing-above-none`, `anvil-spacing-below-none`)
- **Small**: `4px` (`anvil-spacing-above-small`, `anvil-spacing-below-small`)
- **Medium**: `8px` (`anvil-spacing-above-medium`, `anvil-spacing-below-medium`)
- **Large**: `16px` (`anvil-spacing-above-large`, `anvil-spacing-below-large`)

---

## 2. Responsive Breakpoints

BMALocal is operated across workshop desktop PCs, office tablets, and technician mobile devices. All forms must adapt gracefully without horizontal scrollbars:

| Device Category | Viewport Width | Anvil Layout Strategy |
| :--- | :--- | :--- |
| **Mobile** | `< 600px` | Single-column stack (`col_widths: {}`), full-width action buttons, simplified card views (e.g. `ProgressTrackerMobileView`) |
| **Tablet** | `600px - 1024px` | 2-column grid, collapsible sidebar navigation, condensed table views |
| **Desktop** | `> 1024px` | Full multi-column layout, fixed side navigation, multi-column data grids |

### Responsive Implementation Rules
1. **Never Hardcode Pixel Widths**: Use percentage, fractional units, or Anvil's built-in column spans.
2. **Column Panel Wrapping**: Configure `ColumnPanel` components so fields wrap vertically on smaller screens.
3. **Data Grids & Tables**: Ensure repeating panels and table headers scroll internally or collapse to card views on mobile viewports.

---

## 3. Component Consistency & Roles

Use predefined Anvil component roles configured in `theme/parameters.yaml`:
- **`card` / `wide-card`**: Grouping form sections (e.g. Vehicle Details, Customer Information).
- **`primary-color`**: Main action button per screen (e.g. "Save Job Card", "Generate Invoice").
- **`secondary-color`**: Supporting actions (e.g. "Add Part", "Schedule Service").
- **`raised`**: Elevated interactive buttons.
- **`headline` / `subheading`**: Consistent hierarchy for section headings.

---

## 4. Accessibility & Interaction Feedback

- **WCAG AA Contrast**: Ensure text has at least a 4.5:1 contrast ratio against card and background surfaces.
- **Input Labels**: Every input (TextBox, DropDown, DatePicker) must have an associated visible Label or unambiguous placeholder.
- **Loading & In-Flight States**:
  - Disable submit buttons immediately upon click to prevent duplicate submissions.
  - Display an Anvil notification or spinner during asynchronous `anvil.server.call()` invocations.
  - Re-enable buttons in a `finally:` block.
- **Keyboard Operability**: Verify tab indexing across form fields and modal dialogs.

---

## 5. Pre-Merge Cross-Device Check

Before completing any client-side change, test across the required matrix:
1. **Desktop Viewport** (`1280x800` or higher)
2. **Tablet Viewport** (`768x1024`)
3. **Mobile Viewport** (`375x667`)
4. Verify both standard theme and dark mode contrast.
