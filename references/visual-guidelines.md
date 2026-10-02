# Visual Guidelines

## Default look

Use a restrained technical-document style:
- white/light background
- dark neutral text
- thin neutral borders
- one primary accent
- amber for attention/waiting
- red only for failure/critical conditions
- green only for verified success/completion

Do not rely on color alone.

## Typography

Prefer the page's native font stack. Keep chart labels compact but legible. Avoid oversized dashboard-style numbers unless the number is the point of the explanation.

## Motion timing

Typical cycle:
- 8–16 seconds for a complete explanatory sequence
- 2–5 meaningful stages
- short pause after the final state before repeating

Avoid constant pulsing, decorative bouncing, fast looping, and multiple unrelated animations competing at once.

## Motion density

Default:
- 0 motion blocks for ordinary status prose
- 1 motion block for a section that benefits from progression
- 2 only when they explain different concepts and are separated by text

## Captions

Every motion should explain what the viewer is seeing, what changes, why the change matters, and whether values are real or illustrative.

## Charts

Show units, label the axis or explain it in the title, do not animate a fabricated metric as if it were observed, and provide a static final frame that communicates the conclusion.

## Workflows

Clearly distinguish user action, automated execution, automated validation, human judgment/approval, and blocked/waiting state. Do not animate human approval as automatically completed unless that is factually true.
