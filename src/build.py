"""Wire the five agents from settings — shared by the CLI, the UI, and the smoke test."""
from __future__ import annotations

from .agents.conductor import Conductor
from .agents.scorer import Scorer
from .agents.strategist import Strategist
from .band_client import BandClient
from .config import Settings
from .models import ModelRouter
from .schemas import Archetype

# role -> (display label, archetype) for the three strategists
STRATEGIST_SPECS = {
    "STRATEGIST_A": ("@StrategistA", Archetype.GO_VIRAL),
    "STRATEGIST_B": ("@StrategistB", Archetype.TRUST_PLAY),
    "STRATEGIST_C": ("@StrategistC", Archetype.PAID_BLITZ),
}


def band_for(settings: Settings, role: str) -> BandClient:
    return BandClient(settings.creds(role), settings.band_api_base)


def build_conductor(settings: Settings) -> Conductor:
    models = ModelRouter(settings)
    strategists = [
        Strategist(label, archetype, models, band_for(settings, role))
        for role, (label, archetype) in STRATEGIST_SPECS.items()
    ]
    scorer = Scorer(models, band_for(settings, "SCORER"))
    return Conductor(
        band=band_for(settings, "CONDUCTOR"),
        models=models,
        strategists=strategists,
        scorer=scorer,
        max_rounds=settings.max_debate_rounds,
        refine_passes=settings.refine_passes,
    )
