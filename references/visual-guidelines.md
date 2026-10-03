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

## Composition (explanatory figures)

These rules come from the v0.4.0 thread-pool rebuild and apply to both tiers:

- The main figure carries the core state; supporting charts must not be the only place
  a key quantity (queue length, which work is slow) is visible.
- One claim per scene. The caption states it and appears when the model event that makes
  it true has happened, not at a fixed fraction of the clip.
- Show a number once, where the eye already is. Prefer one live causal line over KPI
  cards that repeat the chart.
- Never show future values (peaks, maxima) before the clock reaches them.
- Keep assumptions, provenance and raw tables in one collapsed section below the figure.
- Height budget: about 520 px at a 715 px container and 600 px at 360 px.
- Stack metrics that must be read together on one shared time axis, not side by side.
- Moving tokens stand for real units in the model and travel on drawn routes.

## Visual language (live tier, v0.6.0)

Target: the look, feel and finish of the kciter.so article demos, not their content.
Derived by measuring the recorded originals (palette sampled from pixels, sizes at a
673 px column) and applied once in `visuals/live/kit.js`, `shell.html` and the grammars,
so every live case inherits it.

- **Palette:** Open Color. Busy/flow = blue `#228be6`; waiting = yellow dots `#fab005`;
  alarm = pink fill `#fff5f5` + red border `#fa5252`; healthy = green border `#40c057`;
  P99/latency = violet `#845ef7`; text greys `#495057` / `#868e96` / `#adb5bd`. Small text
  uses the darker variants (`redText`, `amberText`, `greenText`, `blueText`) for contrast.
- **Chrome is quiet:** no card border; one centred status line ("label **value**" joined by
  " · ", value blue or red when alarming); centred small grey caption with ①②③; text-only
  controls and the collapsed notes on one low row.
- **Things, not abstractions:** waiting requests are dots in a grid or cells in a buffer;
  stages are white boxes with a thick gauge and a bold % below; plain-language pills
  ("여유(한가함)", "한도 도달", "수용분 대기 80ms") sit on the element they describe and
  appear only when true.
- **Charts only when the prose needs them.** Light panel (`#f8f9fa`), soft area fill, 2 px
  line, value labelled at the cursor dot. Drop a panel the surrounding text never reads.
- **Compact:** aim for the main figure plus status and caption; time panels are the
  exception that must earn their height.

## Readability rules enforced by the gates (v0.6.1+)

- Captions: 25–45 chars, one claim each, bound to model events; playback slows so each stays
  on screen max(2.5 s, chars ÷ 12) at the default speed; captions too close to read both are
  a build error (merge them).
- Text contrast ≥ 4.5:1 (including chips); the faint grey is for rails and grids only.
- Labels over lines, areas or dots use the white halo; no text may be painted over by a
  later shape; value labels avoid each other and event labels.
- No in-flight tokens in the final/static scene; a phone-width static scene is shown when
  scripts do not run.
- Decimals follow the author's data; a change within the stated flat band reads "≈ 그대로".
