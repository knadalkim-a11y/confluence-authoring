# Confluence HTML Macro Rules

These rules target environments where the Confluence HTML macro is enabled. Individual installations may still sanitize elements or CSS differently.

## Default fragment contract

A motion fragment should:
- contain style + content only;
- omit html, head, and body wrappers;
- avoid iframe;
- avoid external fonts, scripts, stylesheets, images, and CDN dependencies;
- avoid JavaScript by default;
- use inline SVG for charts and diagrams;
- remain readable if animation is disabled.

## Isolation

Every block must use a unique prefix.

Example:
- good: cx42-line, cx42-node-1, @keyframes cx42-reveal
- bad: card, chart, @keyframes reveal

The template token `{{PREFIX}}` must be replaced before publishing. One page may contain several motion blocks. Never reuse a prefix on the same page.

## Accessibility

Required:
- meaningful visible text outside animation-only layers;
- role/title or equivalent description for important SVG;
- color is not the only carrier of state;
- prefers-reduced-motion produces a usable static state;
- controls, when present, are keyboard reachable;
- print output does not depend on animation timing.

## Responsive behavior

- Use width:100% and max-width rather than fixed page width.
- Avoid horizontal scrolling for ordinary document widths.
- Collapse multi-column flows on narrow containers where possible.
- Text must remain readable without browser zoom.

## Data honesty

When values are synthetic, illustrative, simulated, or normalized, say so next to the visual. Do not let animation imply measured precision that the source does not provide.

## Runtime rule

CSS + SVG is the baseline because it minimizes dependencies and works in environments where JavaScript is restricted.

Use JavaScript only after the actual target Confluence environment has been verified to permit it and only when the required interaction cannot reasonably be achieved with HTML/CSS.

## Publication verification

After publish/update, verify separately:
1. the macro is present;
2. style was not stripped;
3. SVG is visible;
4. animation runs where expected;
5. reduced-motion/static state is understandable;
6. surrounding page content is unchanged;
7. the page still behaves acceptably when printed or exported.

Do not claim "Confluence verified" based only on local browser preview.
