# Stockanalysis Design System

## 1. Atmosphere & Identity

Stockanalysis is a quiet Korean investment research desk: dense enough for serious analysis, but ordered so one decision remains dominant on each screen. Its signature is the `decision line`, a restrained horizontal path that connects market condition, evidence, security, recommendation, and portfolio impact without exposing internal processing terminology.

## 2. Color

### Palette

| Role | Token | Light | Usage |
| --- | --- | --- | --- |
| Canvas | `--surface-canvas` | `#f2f3f5` | Page background |
| Primary surface | `--surface-primary` | `#fbfbfa` | Main reading surface |
| Secondary surface | `--surface-secondary` | `#e8ebef` | Grouped analysis |
| Raised surface | `--surface-raised` | `#ffffff` | Menus and focused panels |
| Inverse surface | `--surface-inverse` | `#111923` | High-priority conclusion |
| Text primary | `--ink-primary` | `#111923` | Headings and body |
| Text secondary | `--ink-secondary` | `#4d5968` | Supporting analysis |
| Text muted | `--ink-muted` | `#465160` | Metadata |
| Divider | `--line-subtle` | `#d5dae0` | Structural separators |
| Divider strong | `--line-strong` | `#aeb7c2` | Focused separators |
| Analytical accent | `--accent-analysis` | `#155c8a` | Links and selected data |
| Positive | `--signal-positive` | `#176b4d` | Supportive evidence |
| Caution | `--signal-caution` | `#7a4c00` | Observation required |
| Risk | `--signal-risk` | `#a33b35` | Risk and blocked states |
| Neutral | `--signal-neutral` | `#52606f` | Unknown or not applicable |

### Rules

- Accent color indicates interaction or analytical selection, never decoration.
- Positive and risk colors never communicate price movement without a label.
- Investor pages use tonal surfaces and dividers. Shadows are reserved for floating navigation.
- New colors must be added here before use.

## 3. Typography

### Scale

| Level | Token | Size | Weight | Line height | Usage |
| --- | --- | --- | --- | --- | --- |
| Display | `--type-display` | `clamp(2.5rem, 6vw, 5.5rem)` | 760 | 0.98 | Daily conclusion |
| H1 | `--type-h1` | `clamp(2rem, 4vw, 3.5rem)` | 740 | 1.05 | Page title |
| H2 | `--type-h2` | `clamp(1.45rem, 2.4vw, 2.2rem)` | 700 | 1.15 | Major section |
| H3 | `--type-h3` | `1.15rem` | 700 | 1.3 | Analysis item |
| Lead | `--type-lead` | `1.05rem` | 480 | 1.7 | Decision summary |
| Body | `--type-body` | `0.95rem` | 450 | 1.65 | Default text |
| Small | `--type-small` | `0.82rem` | 500 | 1.5 | Supporting text |
| Caption | `--type-caption` | `0.72rem` | 650 | 1.4 | Metadata |

### Font Stack

- Primary: `"Pretendard Variable", Pretendard, "Noto Sans KR", "Apple SD Gothic Neo", sans-serif`
- Numeric/mono: `"SFMono-Regular", "Roboto Mono", Consolas, monospace`

### Rules

- Korean text uses `word-break: keep-all` and `text-wrap: pretty`.
- Financial values use tabular numerals.
- Body text never drops below 14px on a 375px viewport.
- Headings are conclusions or nouns, not operating instructions.

## 4. Spacing & Layout

### Base Unit

All spacing is based on 4px.

| Token | Value | Usage |
| --- | --- | --- |
| `--space-1` | `4px` | Tight inline gap |
| `--space-2` | `8px` | Compact row |
| `--space-3` | `12px` | Label group |
| `--space-4` | `16px` | Standard inner spacing |
| `--space-5` | `20px` | Compact panel |
| `--space-6` | `24px` | Default panel |
| `--space-8` | `32px` | Analysis group |
| `--space-10` | `40px` | Section break |
| `--space-12` | `48px` | Major section break |
| `--space-16` | `64px` | Page rhythm |
| `--space-20` | `80px` | Hero rhythm |

### Grid

- Maximum width: 1480px.
- Investor pages: 12-column grid, 24px desktop gutter.
- Reading columns: 720px maximum prose width.
- Breakpoints: 640px, 768px, 1024px, 1280px.
- Mobile edge: 16px; desktop edge: clamp from 24px to 64px.

### Rules

- A screen has one dominant conclusion area.
- Tables and charts may use full width; prose may not.
- Cards are used only when a boundary has semantic meaning.
- Secondary details use progressive disclosure instead of additional grids.

## 5. Components

### Workspace shell

- Structure: skip link, brand, primary navigation, utility navigation, main.
- Variants: desktop horizontal, mobile disclosure menu.
- States: current route, hover, focus, pressed.
- Accessibility: semantic navigation labels and visible focus.

### Decision summary

- Structure: eyebrow, conclusion, supporting sentence, status, primary actions.
- Variants: neutral, supportive, caution, risk.
- Usage: exactly once near the top of every primary investor route.

### Decision line

- Structure: market, evidence, security, decision, portfolio stages.
- Variants: complete, partial, blocked.
- Usage: trace impact, not internal execution steps.

### Status badge

- Variants: ready, watch, stale, source-limited, blocked, not-applicable, empty, error.
- Accessibility: status meaning is always written; color is secondary.

### Metric strip

- Structure: label, value, context.
- Usage: two to five comparable metrics, never a generic feature-card grid.

### Research section

- Structure: section heading, concise implication, optional detail body.
- Usage: major analytical layers in stock and recommendation reports.

### Data visualization

- Structure: title, visual, textual takeaway, accessible data table.
- Variants: trend, range, heatmap, hierarchy, exposure.

### Empty and error states

- Structure: factual title, cause, impact on investment judgment, recovery destination.
- Never instruct the user to run an internal command.

## 6. Motion & Interaction

| Type | Duration | Easing | Usage |
| --- | --- | --- | --- |
| Micro | 120ms | ease-out | Press and focus |
| Standard | 220ms | ease-in-out | Menu and disclosure |
| Emphasis | 440ms | cubic-bezier(0.16, 1, 0.3, 1) | Page entry |

### Rules

- Animate only transform, opacity, and filter.
- Respect `prefers-reduced-motion`.
- Every interactive element has hover, active, and focus-visible states.
- Motion clarifies hierarchy and never delays access to data.

## 7. Depth & Surface

The depth strategy is `tonal-shift with restrained dividers`.

- Primary hierarchy comes from background tone and spacing.
- Dividers separate datasets and reading phases.
- Borders do not wrap every item.
- Shadows appear only on floating navigation or menus.
- Border radii stay between 2px and 12px; pill shapes are reserved for compact status labels.
