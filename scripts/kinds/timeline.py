"""timeline: schedules by date, incident minutes by HH:MM."""
from __future__ import annotations
import datetime as dt
import math
import re
from kinds.common import DATA_KINDS, SpecError, common, need, num, only, text


CLOCK = re.compile(r'^([01]?\d|2[0-3]):([0-5]\d)$')


def as_day(v, name, origin, clock=None):
    """Days from a date origin, minutes for HH:MM clock times (after midnight wraps), or a number."""
    if isinstance(v, str) and clock is not None:
        m = CLOCK.match(v); need(m, f'{name}: HH:MM like the time range')
        x = int(m[1]) * 60 + int(m[2])
        return x + 1440 if x < clock else x
    if isinstance(v, str):
        try:
            d = dt.date.fromisoformat(v)
        except ValueError:
            raise SpecError(f'{name}: ISO date YYYY-MM-DD or a number')
        need(origin is not None, f'{name}: dates need time.start as a date')
        return (d - origin).days
    return num(v, name, -1e6, 1e6)


def timeline_data(spec):
    kind, title, claim, source, data_kind, motion = common(spec)
    only(spec, ('kind', 'title', 'claim', 'source', 'data_kind', 'motion', 'time', 'tracks', 'milestones', 'today', 'today_label', 'durations', 'legend', 'status_labels'), 'timeline spec')
    sl = only(spec.get('status_labels') or {}, ('done', 'active', 'planned', 'late', 'risk'), 'status_labels')
    tm = only(spec.get('time'), ('start', 'end', 'unit'), 'time')
    clock = None
    if isinstance(tm.get('start'), str) and CLOCK.match(tm['start']):
        m = CLOCK.match(tm['start']); clock = int(m[1]) * 60 + int(m[2])
    origin = dt.date.fromisoformat(tm['start']) if isinstance(tm.get('start'), str) and clock is None else None
    day = lambda v, n: as_day(v, n, origin, clock)
    t0 = clock if clock is not None else (as_day(tm.get('start'), 'time.start', origin) if origin is None else 0)
    t1 = day(tm.get('end'), 'time.end')
    need(t1 > t0, 'time.end after time.start')
    tracks = spec.get('tracks'); need(isinstance(tracks, list) and 1 <= len(tracks) <= 10, 'tracks: 1-10')
    out = []
    for i, tr in enumerate(tracks):
        only(tr, ('label', 'start', 'end', 'status', 'note'), f'tracks[{i}]')
        a, b = day(tr.get('start'), f'tracks[{i}].start'), day(tr.get('end'), f'tracks[{i}].end')
        need(t0 <= a < b <= t1, f'tracks[{i}]: start < end, inside the time range')
        st = tr.get('status', 'planned'); need(st in ('done', 'active', 'planned', 'late', 'risk'), f'tracks[{i}].status: done|active|planned|late|risk')
        out.append(dict(label=text(tr.get('label'), f'tracks[{i}].label', 1, 16), a=a, b=b, status=st, note=text(tr['note'], 'note', 1, 16) if tr.get('note') else ''))
    ms = []
    for i, m in enumerate(spec.get('milestones') or []):
        only(m, ('at', 'label'), f'milestones[{i}]')
        ms.append([day(m.get('at'), f'milestones[{i}].at'), text(m.get('label'), 'milestone label', 1, 14)])
    today = day(spec['today'], 'today') if spec.get('today') is not None else None
    ticks = []
    if clock is not None:
        span = t1 - t0; step = next(x for x in (5, 10, 15, 30, 60, 120, 240) if span / x <= 7)
        hm = lambda x: f'{int(x) // 60 % 24:02d}:{int(x) % 60:02d}'
        ticks = [[x, hm(x)] for x in range(int(math.ceil(t0 / step) * step), int(t1) + 1, step)]
        label_day = hm
        dur = lambda d: ' '.join(x for x in (f'{int(d) // 60}시간' if d >= 60 else '', f'{int(d) % 60}분' if d % 60 or d < 60 else '') if x)
    elif origin is not None:
        d = dt.date(origin.year, origin.month, 1)
        while (d - origin).days <= t1:
            if (d - origin).days >= t0:
                ticks.append([(d - origin).days, f'{d.month}월'])
            d = dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        label_day = lambda x: f'{(origin + dt.timedelta(days=round(x))).month}/{(origin + dt.timedelta(days=round(x))).day}'
        dur = lambda d: f'{d:g}일'
    else:
        unit = text(tm.get('unit', '주'), 'time.unit', 1, 4)
        step = max(1, round((t1 - t0) / 6))
        ticks = [[x, f'{x:g}{unit}'] for x in range(int(t0), int(t1) + 1, step)]
        label_day = lambda x: f'{x:g}{unit}'
        dur = lambda d: f'{d:g}{unit}'
    if spec.get('durations'):   # e.g. incident reviews: how long detection, response and recovery took
        for x in out:
            x['note'] = x['note'] or dur(x['b'] - x['a'])
    tl = text(spec.get('today_label', '오늘'), 'today_label', 1, 6)
    data = dict(scene='timeline', time=dict(unit='', end=1.0, start=t0, stop=t1), tracks=out, milestones=[[a, l, label_day(a)] for a, l in ms],
                today=[today, tl + ' ' + label_day(today)] if today is not None else None, ticks=ticks, legend=spec.get('legend', True),
                status_labels={k: text(v, f'status_labels.{k}', 1, 8) for k, v in sl.items()},
                captions=[[1.0, '', claim]], rate=[[0, 1]], labels=dict(data_kind=DATA_KINDS[data_kind]))
    head = ['항목', '시작', '끝', '상태']
    names = dict(done='완료', active='진행', planned='예정', late='지연', risk='위험')
    rows = [[x['label'], label_day(x['a']), label_day(x['b']), names[x['status']]] for x in out]
    checks = dict(end=1.0, samples=[1.0] * 6, annotations=[], expect=None, resize_at=0.5)
    return dict(data=data, aria=f'{title}. {claim}', notes=f'출처: {source} ({DATA_KINDS[data_kind]}).', table=(head, rows),
                checks=checks, live=False, numeric=dict(tracks=out), title=title)
