"""Scorer agent — independent of the Strategists (PRD §5.4, §5.5).

Its own Band identity; runs on Featherless (preferred) or the AI/ML API fallback, so no plan
grades its own homework. Rates each strategy 1-10 on five weighted dimensions; weighting is
computed in schemas.Score.
"""
from __future__ import annotations

from ..band_client import BandClient
from ..knowledge import MARKETING_DOCTRINE
from ..models import ModelRouter
from ..parallel import pmap
from ..schemas import DimensionScore, Score, Strategy

_SYSTEM = (
    "You are @Scorer, an impartial neuro-marketing analyst. You did NOT author any plan. Judge the "
    "actual FUNNEL MATH, persuasion quality, and budget feasibility — not the vibes. Rate each "
    "strategy 1-10 (10 = best) on five dimensions. For 'risk', higher means SAFER. If a plan is "
    "infeasible in the timeline or its funnel math doesn't credibly reach the goal, score "
    "cost_efficiency and reach harshly. Be consistent.\n\n" + MARKETING_DOCTRINE
)


class Scorer:
    def __init__(self, models: ModelRouter, band: BandClient):
        self.label = "@Scorer"
        self._models = models
        self.band = band

    @property
    def handle(self) -> str:
        return self.band.handle

    def score(self, strategy: Strategy) -> Score:
        prompt = (
            f"Strategy by {strategy.author} ({strategy.archetype.value}):\n"
            f" summary: {strategy.summary}\n channels: {strategy.channel_mix}\n"
            f" funnel_math: {strategy.funnel_math}\n projected_result: {strategy.projected_result}\n"
            f" feasible: {strategy.feasible}\n cost: {strategy.cost_estimate}\n"
            f" risks: {strategy.risks}\n\n"
            "Respond with STRICT JSON, integers 1-10:\n"
            '{"reach": int, "cost_efficiency": int, "speed": int, "risk": int, "durability": int}'
        )
        data = self._models.ask_json("scorer", _SYSTEM, prompt)
        return Score(strategy_id=strategy.strategy_id, dimensions=DimensionScore(**data))

    def ranked_table(self, strategies: list[Strategy]) -> list[Score]:
        scores = pmap(self.score, strategies)
        return sorted(scores, key=lambda s: s.weighted_total, reverse=True)
