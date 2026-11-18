# BusArrival AI - Design System & Tokens

**Theme Mode:** Light theme only  
**Aesthetic:** Clean, transit-themed, high-density dashboard with clear typographic hierarchy and semantic visual indicators.

---

## 1. Color Tokens

| Token | Hex Value | Semantic Usage |
|---|---|---|
| `bg-base` | `#F6F8FB` | Main application background |
| `surface` | `#FFFFFF` | Cards, sidebars, modals, top navigation bar |
| `bg-subtle` | `#EDF1F7` | Table headers, form input backgrounds, hover states |
| `border` | `#DCE3EE` | Borders, card outlines, table row dividers |
| `text-primary` | `#0F1E33` | Primary body copy, headers, active item text |
| `text-secondary` | `#4A5C75` | Secondary descriptions, column headers, metadata |
| `text-muted` | `#7C8CA3` | Placeholders, timestamps, disabled items, hints |
| `primary` (Transit Blue) | `#1D4ED8` | Primary action buttons, active navigation indicator |
| `primary-hover` | `#1E40AF` | Hover state for primary buttons and interactive accents |
| `primary-soft` | `#DBEAFE` | Soft badge backgrounds, selection highlights |
| `on-time` | Text: `#15803D`<br>Chart: `#22C55E`<br>Soft: `#DCFCE7` | Punctual arrivals, high model accuracy, positive metrics |
| `minor-delay` | Text: `#B45309`<br>Chart: `#F59E0B`<br>Soft: `#FEF3C7` | Moderate delays (1–5 min), warnings, cautionary status |
| `major-delay` | Text: `#B91C1C`<br>Chart: `#EF4444`<br>Soft: `#FEE2E2` | Severe delays (>5 min), errors, system alerts |
| `prediction` | Text: `#6D28D9`<br>Chart: `#8B5CF6`<br>Soft: `#EDE9FE` | Model forecasts, ETA confidence bands (P50–P90) |
| `teal` | `#0D9488` | Scheduled/timetabled reference baselines |

---

## 2. Route Color Palette

For distinguishing bus routes across map tracks, line diagrams, and charts:
- **Route 1:** `#2563EB` (Blue)
- **Route 2:** `#059669` (Emerald)
- **Route 3:** `#D97706` (Amber)
- **Route 4:** `#E11D48` (Rose)
- **Route 5:** `#7C3AED` (Violet)
- **Route 6:** `#0284C7` (Sky)
- **Route 7:** `#65A30D` (Lime)
- **Route 8:** `#EA580C` (Orange)

---

## 3. Typography & Spacing

- **Font Family:** Inter (`@fontsource/inter`), system sans-serif fallback.
- **Numbers:** Tabular figures (`font-variant-numeric: tabular-nums`) enabled across all data tables, KPI counters, and ETA readouts to prevent layout shifts.
- **Base Grid:** 8px spacing system (`8px`, `16px`, `24px`, `32px`, `48px`).
- **Corner Radii:**
  - Cards & Panels: `12px` (`rounded-xl`)
  - Inputs, Buttons & Badges: `8px` (`rounded-md`)
- **Shadows:** Soft diffuse shadows (e.g., `0 1px 3px rgba(15, 30, 51, 0.06), 0 1px 2px rgba(15, 30, 51, 0.04)`).
- **Transitions:** Snappy 150ms–200ms ease-out transitions, respecting `prefers-reduced-motion`.

---

## 4. Accessibility & UI Rules

1. **Never rely on color alone:** Always accompany color badges with text labels (e.g., "On Time", "Delayed +4m") and iconography.
2. **Contrast Standards:** All text pairings meet WCAG 2.1 AA standards (minimum 4.5:1 for body copy).
3. **Empty, Loading & Error States:** Every table, card, and chart includes skeleton placeholders during loading, intuitive empty states with action triggers, and retry-friendly error alerts.
