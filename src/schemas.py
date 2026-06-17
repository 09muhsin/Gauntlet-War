"""Data objects from PRD Section 10. These are the shared contracts passed through Band."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Archetype(str, Enum):
    GO_VIRAL = "Go Viral"
    TRUST_PLAY = "Trust Play"
    PAID_BLITZ = "Paid Blitz"


class Brief(BaseModel):
    product: str
    goal: str                       # e.g. "1,000 first-month orders"
    budget_ceiling: float           # USD
    constraints: list[str] = Field(default_factory=list)


class Strategy(BaseModel):
    strategy_id: str
    author: str                     # e.g. "@StrategistA"
    archetype: Archetype
    summary: str
    channel_mix: list[str]
    expected_outcome: str
    cost_estimate: float
    risks: list[str]
    # Substance fields — what makes the plan non-generic and the debate quantitative.
    budget_split: list[str] = []    # e.g. "Influencer seeding: $0 (affiliate rev-share)"
    funnel_math: str = ""           # reach -> leads -> conversions, with assumed CTR/CVR numbers
    projected_result: str = ""      # honest projection vs the goal (incl. shortfall if any)
    feasible: bool = True           # False if the archetype can't realistically work in this budget


class Critique(BaseModel):
    author: str                     # challenger agent
    target_strategy_id: str
    claim: str                      # the specific, grounded objection
    severity: int = Field(ge=1, le=5)


class DimensionScore(BaseModel):
    reach: int = Field(ge=1, le=10)
    cost_efficiency: int = Field(ge=1, le=10)
    speed: int = Field(ge=1, le=10)
    risk: int = Field(ge=1, le=10)          # higher = safer (inverted per PRD 5.4)
    durability: int = Field(ge=1, le=10)


# Weights from PRD Section 5.4 — kept visible so the human can challenge them.
SCORE_WEIGHTS = {
    "reach": 0.20,
    "cost_efficiency": 0.25,
    "speed": 0.20,
    "risk": 0.20,
    "durability": 0.15,
}


class Score(BaseModel):
    strategy_id: str
    dimensions: DimensionScore

    @property
    def weighted_total(self) -> float:
        d = self.dimensions
        return round(
            d.reach * SCORE_WEIGHTS["reach"]
            + d.cost_efficiency * SCORE_WEIGHTS["cost_efficiency"]
            + d.speed * SCORE_WEIGHTS["speed"]
            + d.risk * SCORE_WEIGHTS["risk"]
            + d.durability * SCORE_WEIGHTS["durability"],
            2,
        )


class Decision(BaseModel):
    chosen_strategy_id: str         # winner, or a synthesized hybrid id
    is_hybrid: bool = False
    rationale: str = ""
    human_approver: str = ""
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    sealed_hash: Optional[str] = None   # tamper-evident hash returned by Band on seal
