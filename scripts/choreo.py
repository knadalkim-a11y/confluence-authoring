"""Choreography layer (docs/design/motion-concept-architecture.md, L2).

Kinds describe *how a state change looks* as cues: which element, which property, when (a model time),
how long and on which curve. Cues are resolved and validated here, in Python, next to the model and the
caption pacing; visuals/live/choreo.js only evaluates them at time T. Specs do not write cues (decision 1):
each kind builds its default choreography from the model.

Cue (resolved, as sent to the browser): [target, prop, t0, dur, curve, from, to], t0 and dur in model time.
Durations are written and validated in seconds on screen (at 1x) and converted through the case's rate map,
because model time runs at different speeds (paced captions, minutes or days per second).
"""
from __future__ import annotations

CURVES = ('linear', 'out', 'in', 'inOut')
# role of each property: how long its change may take (seconds of model time)
PROPS = {'level': 'state', 'act': 'state', 'on': 'state', 'opacity': 'state', 'pop': 'emph', 'reveal': 'progress'}
DUR = {'state': (0.15, 0.6), 'emph': (0.25, 0.6), 'progress': (0.2, 1.5)}   # seconds on screen at 1x
# overlap: the next segment starts when the previous one is this far through (design doc, section 4)
OVERLAP = 0.8
ENTER, EXIT = 0.3, 0.25   # state rising (out) / falling (in)


class ChoreoError(ValueError):
    pass


def rate_at(rate, t):
    r = 1.0
    for t0, v in (rate or [[0, 1]]):
        if t >= t0 - 1e-9:
            r = v
    return r


def cue(target, prop, t0, dur, frm, to, curve='out', rate=None):
    """dur: seconds on screen; stored as model time at t0 through the rate map."""
    if prop not in PROPS:
        raise ChoreoError(f'cue {target}.{prop}: unknown property (known: {", ".join(sorted(PROPS))})')
    if curve not in CURVES:
        raise ChoreoError(f'cue {target}.{prop}: unknown curve {curve!r}')
    lo, hi = DUR[PROPS[prop]]
    if not lo - 1e-9 <= dur <= hi + 1e-9:
        raise ChoreoError(f'cue {target}.{prop}: {dur:g}s outside {lo:g}-{hi:g}s for a {PROPS[prop]} change')
    return [target, prop, round(float(t0), 4), round(float(dur) * rate_at(rate, t0), 4), curve, frm, to]


def validate(cues, end):
    """No two cues on one target/property overlap in time; every cue ends by `end` (the final scene,
    which print, reduced motion and the no-JS fallback show, must be a settled state)."""
    by = {}
    for c in cues:
        by.setdefault((c[0], c[1]), []).append(c)
        if c[2] + c[3] > end + 1e-6:
            raise ChoreoError(f'cue {c[0]}.{c[1]} ends at {c[2] + c[3]:g}s, after the final scene ({end:g}s)')
    for (t, p), lst in by.items():
        lst.sort(key=lambda c: c[2])
        for a, b in zip(lst, lst[1:]):
            if b[2] < a[2] + a[3] - 1e-6:
                raise ChoreoError(f'cues on {t}.{p} overlap at {b[2]:g}s')
            if PROPS[p] != 'emph' and abs(b[5] - a[6]) > 1e-9:   # an emphasis is a pulse, each one starts at rest
                raise ChoreoError(f'cue {t}.{p} at {b[2]:g}s starts from {b[5]} but the previous one ended at {a[6]}')
    return sorted(cues, key=lambda c: (c[2], c[0], c[1]))


def switches(t, on, rate=None):
    """Times a boolean series changes and its new values, without flickers shorter than one rise plus
    one fall on screen (a state that would not finish entering is not shown)."""
    out, prev = [], False
    for x, v in zip(t, on):
        v = bool(v)
        if v == prev:
            continue
        if out and x - out[-1][0] < (ENTER + EXIT) * rate_at(rate, x):
            out.pop()                      # the previous change is undone too soon: drop both
        else:
            out.append([x, int(v)])
        prev = v
    return [x for x, _ in out], [v for _, v in out]


def levels(target, prop, seq, times, rate=None, rise=ENTER, fall=EXIT):
    """Cues for a discrete level that changes at `times[k]` to `seq[k]` (starting from 0).
    Falling changes start on the event; rising ones overlap the fall (start at OVERLAP of it),
    so the eye follows the old state out and the new one in."""
    out, prev = [], 0
    for t, v in zip(times, seq):
        if v == prev:
            continue
        if v > prev:
            t1 = t + fall * OVERLAP * rate_at(rate, t)
            out.append(cue(target, prop, t1, rise, prev, v, 'out', rate))
        else:
            out.append(cue(target, prop, t, fall, prev, v, 'in', rate))
        prev = v
    return out
