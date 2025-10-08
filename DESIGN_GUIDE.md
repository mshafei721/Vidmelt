# Vidmelt UI Depth & Elevation System (v2.0.0-alpha)

## 1. Base Palette & Shade Stack

Base color: fulvous-500 (#d78521), converted to HSL (H≈33°, S≈73%, L≈0.486).
Lightness adjustments (±0.10, +0.20) yield the following shades:
- Shade 1 (L=0.386) → #ab6a1a
- Shade 2 (L=0.486) → #d78521
- Shade 3 (L=0.586) → #e39d48
- Shade 4 (L=0.686) → #eab574

| Shade | Hex      | Usage                                            |
|-------|----------|--------------------------------------------------|
| 1     | #ab6a1a  | Page background, table canvas, low-emphasis zones|
| 2     | #d78521  | Cards, nav rails, dropdown shells                |
| 3     | #e39d48  | Buttons, inputs, active nav items                |
| 4     | #eab574  | Selected / hover states, focus rings             |

### Text & Icon Compensation
- Shade 3 surfaces: lighten text/icons by +0.10 lightness (use #000000) to keep ≥4.5:1 contrast.
- Shade 4 surfaces: lighten text/icons by +0.20 lightness and optionally add 0 1px 1px rgba(0,0,0,0.18) text shadow.
- Shade 1 text token suggestion: #f9f5ef; Shade 2 text: #fff4e2.

### Border Policy
- Remove borders on elements using Shade 3 or Shade 4.
- Allow subtle 1px borders on Shade 1/2 containers only when required: rgba(0,0,0,0.08) (light) or rgba(255,255,255,0.08) (dark).

## 2. Page Hierarchy & Element Recipes
- Page background → Shade 1
- Containers / cards / nav rails → Shade 2
- Interactive surfaces (buttons, tabs, inputs) → Shade 3
- Active / hover / selected → Shade 4

Tabs: track Shade 2; selected tab Shade 3; selected label lighten +0.10 L; no borders.
Cards: wrapper Shade 2; key inner block Shade 3; selected card Shade 3 plus medium shadow.
Dropdowns & buttons: default Shade 2; primary Shade 3 with premium gradient; focus ring Shade 4.
Radio/checkbox: container Shade 2; options Shade 2; selected fill Shade 3; focus outline Shade 4.
Tables: background Shade 1; header Shade 2; selected row Shade 3.
Navigation: base Shade 2; hovered/active item Shade 3; indicator strip Shade 4.

Emphasis guide: move to lighter shade (3→4) and larger shadow to emphasize; shift darker (3→2→1) and reduce shadow to de-emphasize.

## 3. Two-Layer Shadow & Gradient System

| Level  | Top (inset)                           | Bottom (outer)                           | Usage |
|--------|---------------------------------------|------------------------------------------|-------|
| Small  | inset 0 1px 0 rgba(255,255,255,0.10) | 0 1px 2px rgba(0,0,0,0.12)              | Nav items, subtle cards |
| Medium | inset 0 1px 0 rgba(255,255,255,0.15) | 0 3px 6px rgba(0,0,0,0.15)              | Cards, dropdowns, modals |
| Large  | inset 0 2px 0 rgba(255,255,255,0.20) | 0 6px 12px rgba(0,0,0,0.20)             | Hover/focus, spotlight modals |

Premium gradient recipe:
background: linear-gradient(to bottom, #f8b45d, #c6771d);
box-shadow: inset 0 1px 0 rgba(255,255,255,0.30), var(--shadow-medium);

Selection guide: profile cards/nav → small shadow; dashboard cards/dropdowns/modals → medium; hover/focus/premium → large.

Dark mode adaptation: use rich-black neutrals for base backgrounds, keep fulvous stack as accent. In dark mode, invert polarity of layers (outer shadow rgba(255,255,255,0.10), inset highlight rgba(0,0,0,0.25)) and reduce opacities by ~20%.

## 4. Token Export (CSS snippet)
:root {
  --color-depth-1: #ab6a1a;
  --color-depth-2: #d78521;
  --color-depth-3: #e39d48;
  --color-depth-4: #eab574;
  --text-on-depth-1: #f9f5ef;
  --text-on-depth-2: #fff4e2;
  --text-on-depth-3: #000000;
  --text-on-depth-4: #000000;
  --shadow-small: inset 0 1px 0 rgba(255,255,255,0.10), 0 1px 2px rgba(0,0,0,0.12);
  --shadow-medium: inset 0 1px 0 rgba(255,255,255,0.15), 0 3px 6px rgba(0,0,0,0.15);
  --shadow-large: inset 0 2px 0 rgba(255,255,255,0.20), 0 6px 12px rgba(0,0,0,0.20);
  --gradient-premium: linear-gradient(to bottom, #f8b45d, #c6771d);
}

[data-theme="dark"] {
  --shadow-small: inset 0 1px 0 rgba(0,0,0,0.20), 0 1px 2px rgba(255,255,255,0.08);
  --shadow-medium: inset 0 1px 0 rgba(0,0,0,0.24), 0 3px 6px rgba(255,255,255,0.10);
  --shadow-large: inset 0 2px 0 rgba(0,0,0,0.28), 0 6px 12px rgba(255,255,255,0.12);
  --gradient-premium: linear-gradient(to bottom, #b26c1a, #3a2609);
}

## 5. Implementation Notes
- Remove borders on Shade 3/4 elements; rely on shade contrast and shadows.
- Pair premium gradient with medium shadow for major CTAs.
- Apply tokens via Tailwind plugin or CSS variables for consistent layering across the app.
