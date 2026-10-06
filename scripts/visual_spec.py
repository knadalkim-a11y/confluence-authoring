"""Spec-driven visuals for documents: a small JSON spec in, a validated Confluence macro out.

An author (person or AI) describes the situation and the data; this module validates the
spec, computes the model (queues, interpolation, events), binds captions to model events,
and returns scene data for the live JS scenes in visuals/live/scenes/ (flow, trend, bars,
timeline). Numbers shown in text come from the model through placeholders, never typed.
See references/visual-specs.md for the spec reference and selection rules.
"""
from __future__ import annotations
from kinds.common import KINDS, SpecError, need, decimals_of   # noqa: F401  (part of the public API)
from kinds.flow import flow_data, fluid_schedule                # noqa: F401
from kinds.trend import trend_data
from kinds.bars import bars_data
from kinds.share import share_data
from kinds.timeline import timeline_data
from kinds.diagram import diagram_data
from kinds.distribution import distribution_data
from kinds.compose import compose_data
from kinds.concept import concept_data

BUILDERS = dict(flow=flow_data, trend=trend_data, bars=bars_data, share=share_data, timeline=timeline_data, diagram=diagram_data, distribution=distribution_data, concept=concept_data, compose=compose_data)


def build(spec):
    need(isinstance(spec, dict), 'spec: JSON object required')
    kind = spec.get('kind'); need(kind in BUILDERS, f'kind must be one of {KINDS}')
    return BUILDERS[kind](spec)
