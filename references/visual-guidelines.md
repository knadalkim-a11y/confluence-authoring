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

## Motion and wiring parts (v0.11.0, enforced)

Every scene and kind draws moving things and connectors with the shared kit parts, so a pace or
routing rule is fixed once for all visuals instead of case by case:

- Connectors: `K.wire(K.ortho(points))`. Straight when the two boxes face each other, otherwise
  one elbow; never a diagonal. The `diagram` kind routes this way (a fan-out shares one spine).
- Moving dots: `K.token(x, y, id, ...)`; travel at `K.M.speed` (150 px per model second), circle
  at `K.M.turn` (0.45 revolutions per second), use `K.at(points, distance)` along a wire. A new
  trip is a new id. Appearances and state changes ease with `K.ease(T, t0)` (0.35 s).
- Markers that ride on data (a line's head) use `K.follow(...)`: they may jump when the data
  jumps; the data, not the animation, sets their pace.

The browser gate (`visual_gates.MOTION_JS`, 30 frames per wall second, playback rate included,
715 and 360 px) fails a visual when a token moves faster than 480 px/s, a wire has a diagonal
segment, or a dot moves without being a token. 480 px/s is a chosen limit, not one measured
on readers; the pre-v0.10.1 event loop (about 3,000 px/s) fails it, the current cases pass.
Not gated: "instant change" (a large area switching in one frame). Measured on the article
demos with the same pixel metric, they switch as abruptly as ours, so the metric did not
separate good from bad motion; smooth transitions stay a review item.

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

### Focus rules from the v0.9.1 side-by-side review

A same-scale comparison with the article demos showed where ours read worse, and why:

- **One mechanism per picture.** The demos show only the mechanism; ours stacked a second and
  third claim (history strip, two charts under the thread pool) and became 2-3x taller with
  no focal point. Secondary measures go to the status line, the caption or the table.
- **Type scale:** box names 15 px bold, values and secondary text 13 px, notes 12 px on wide
  screens (one step smaller on phones). 11 px is the floor for tertiary text only.
- **State is a fill, not an outline.** Busy slots are solid blue; the bottleneck is a red
  box with red waiting dots right in front of it; a pill must not repeat what the red box
  already says.
- **No meta text in the picture** beyond the data kind (dot scales, encodings go to notes).
- Fonts: the demos use Pretendard; we list it first but cannot ship it (no font files, no
  external requests). Readers without it see Apple SD Gothic Neo, Malgun Gothic or Noto Sans
  KR; metrics differ slightly, which the gates check under two fonts.

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
