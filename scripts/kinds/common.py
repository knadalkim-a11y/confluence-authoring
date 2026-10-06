"""Shared by every kind: spec errors, field checks, number formatting, caption binding, the common header fields."""
from __future__ import annotations
import math
import re
from model import finite


KINDS = ('flow', 'trend', 'bars', 'share', 'timeline', 'diagram', 'distribution', 'concept', 'compose')
DATA_KINDS = {'measured': '측정값', 'estimate': '추정값', 'example': '예시 데이터'}
DIAGRAM_KINDS = {'current': '현재 구조', 'proposed': '제안안', 'example': '예시'}   # a diagram states a structure, not numbers
CIRCLED = '①②③④⑤⑥⑦⑧⑨⑩⑪⑫'
TONES = ('neutral', 'good', 'bad')
COLORS = ('blue', 'purple', 'green', 'red', 'amber', 'gray')


class SpecError(ValueError):
    pass


def need(cond, msg):
    if not cond:
        raise SpecError(msg)


def text(v, name, lo=1, hi=200):
    need(isinstance(v, str) and lo <= len(v.strip()) <= hi and '{{' not in v, f'{name}: text of {lo}-{hi} chars required')
    return v.strip()


def num(v, name, lo=-1e9, hi=1e9):
    try:
        return finite(v, name, lo, hi)
    except ValueError as e:
        raise SpecError(str(e))


def only(obj, allowed, name):
    need(isinstance(obj, dict), f'{name}: object required')
    extra = set(obj) - set(allowed)
    need(not extra, f'{name}: unknown keys {sorted(extra)} (allowed: {sorted(allowed)})')
    return obj


def fmt(v, decimals=None):
    """Readable number: thousands separators, decimals only where they carry information."""
    if decimals is None:
        decimals = 0 if abs(v) >= 100 or float(v).is_integer() else 1
    s = f'{v:,.{decimals}f}'
    return s


def decimals_of(values, cap=2):
    """Decimals the author actually used (12.8 -> 1), so shown values never round away information."""
    d = 0
    for v in values:
        s = repr(float(v))
        if 'e' not in s and '.' in s and not float(v).is_integer():
            d = max(d, len(s.split('.')[1].rstrip('0')))
    return min(d, cap)


def r1(x):
    """Round half up to 0.1, like the scenes' Math.round(x*10)/10 (Python's round() is half-even)."""
    return math.floor(x * 10 + 0.5) / 10


def fill(template, values, name):
    """Replace {key} placeholders with model values; unknown keys are errors, not blanks."""
    def rep(m):
        key = m[1]
        need(key in values, f'{name}: unknown placeholder {{{key}}}; available: {", ".join(sorted(values))}')
        return values[key]
    out = re.sub(r'\{([^{}\s]+)\}', rep, template)
    need('{' not in out and '}' not in out, f'{name}: unbalanced braces left in "{out}"')
    return out


def resolve_at(at, events, name):
    if isinstance(at, (int, float)) and not isinstance(at, bool):
        return float(at)
    need(isinstance(at, str), f'{name}: "at" must be a time or an event name')
    need(at in events, f'{name}: unknown event "{at}"; available: {", ".join(sorted(k for k, v in events.items() if v is not None))}')
    need(events[at] is not None, f'{name}: event "{at}" never happens in this model; choose another or change the data')
    return float(events[at])


def captions_from(spec, events, values, end, name='captions'):
    raw = spec.get('captions') or []
    need(isinstance(raw, list), f'{name}: list required')
    out = []
    for i, c in enumerate(raw):
        only(c, ('at', 'text'), f'{name}[{i}]')
        t = resolve_at(c.get('at', 0), events, f'{name}[{i}]')
        need(0 <= t <= end + 1e-9, f'{name}[{i}]: time {t:g} outside 0..{end:g}')
        out.append([round(t, 6), '', fill(text(c.get('text'), f'{name}[{i}].text', 2, 120), values, f'{name}[{i}].text')])
    out.sort(key=lambda c: c[0])
    for i, c in enumerate(out):
        c[1] = CIRCLED[i] if i < len(CIRCLED) else f'{i + 1}.'
    return out


def common(spec):
    kind = spec.get('kind')
    need(kind in KINDS, f'kind must be one of {KINDS}')
    title = text(spec.get('title'), 'title', 2, 120)
    claim = text(spec.get('claim'), 'claim', 2, 120)
    source = text(spec.get('source'), 'source (where the numbers come from)', 2, 400)
    data_kind = spec.get('data_kind')
    if kind in ('diagram', 'concept', 'compose'):
        need(data_kind in DIAGRAM_KINDS, f'data_kind must be one of {list(DIAGRAM_KINDS)} (say whether this is the current structure or a proposal)')
    else:
        need(data_kind in DATA_KINDS, f'data_kind must be one of {list(DATA_KINDS)} (say whether numbers are real)')
    motion = spec.get('motion', 'auto')
    need(motion in ('auto', 'play', 'none'), 'motion must be auto, play or none')
    return kind, title, claim, source, data_kind, motion
