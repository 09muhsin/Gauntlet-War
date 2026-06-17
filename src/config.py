"""Central config — loads .env and exposes typed settings.

Each Band remote agent authenticates with its OWN api_key, so credentials are stored
per-agent (keyed by role) rather than as a single key.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

# Roles -> the env var prefix used for that agent's BAND_* credentials.
AGENT_ROLES = ["CONDUCTOR", "STRATEGIST_A", "STRATEGIST_B", "STRATEGIST_C", "SCORER"]


@dataclass(frozen=True)
class AgentCreds:
    role: str          # e.g. "STRATEGIST_A"
    agent_id: str
    api_key: str
    handle: str        # full Band handle, e.g. "@muhsinabdulkader09/strategista"

    @property
    def configured(self) -> bool:
        return bool(self.agent_id and self.api_key)


@dataclass(frozen=True)
class Settings:
    band_api_base: str
    agents: dict[str, AgentCreds]      # keyed by role

    aiml_api_key: str
    aiml_api_base: str
    aiml_model_strong: str
    aiml_model_cheap: str

    featherless_api_key: str
    featherless_api_base: str
    featherless_model: str

    # Where the Scorer runs: "featherless" (preferred) or "aiml" (fallback if no Featherless key).
    scorer_provider: str
    max_debate_rounds: int
    refine_passes: int
    # Deliverable pipeline spend: "lite" | "standard" | "max" (see .env). Controls think/polish passes.
    creative_depth: str

    def creds(self, role: str) -> AgentCreds:
        return self.agents[role]

    def missing_agents(self) -> list[str]:
        return [r for r, c in self.agents.items() if not c.configured]


def _agent(role: str) -> AgentCreds:
    return AgentCreds(
        role=role,
        agent_id=os.getenv(f"BAND_{role}_ID", "").strip(),
        api_key=os.getenv(f"BAND_{role}_KEY", "").strip(),
        handle=os.getenv(f"BAND_{role}_HANDLE", "").strip(),
    )


def load_settings() -> Settings:
    return Settings(
        band_api_base=os.getenv("BAND_API_BASE", "https://app.band.ai/api/v1/agent"),
        agents={role: _agent(role) for role in AGENT_ROLES},
        aiml_api_key=os.getenv("AIML_API_KEY", "").strip(),
        aiml_api_base=os.getenv("AIML_API_BASE", "https://api.aimlapi.com/v1"),
        aiml_model_strong=os.getenv("AIML_MODEL_STRONG", "gpt-4o"),
        aiml_model_cheap=os.getenv("AIML_MODEL_CHEAP", "gpt-4o-mini"),
        featherless_api_key=os.getenv("FEATHERLESS_API_KEY", "").strip(),
        featherless_api_base=os.getenv("FEATHERLESS_API_BASE", "https://api.featherless.ai/v1"),
        featherless_model=os.getenv("FEATHERLESS_MODEL", "meta-llama/Meta-Llama-3.1-8B-Instruct"),
        scorer_provider=os.getenv("SCORER_PROVIDER", "featherless").strip().lower(),
        max_debate_rounds=int(os.getenv("MAX_DEBATE_ROUNDS", "1")),
        refine_passes=int(os.getenv("REFINE_PASSES", "1")),
        creative_depth=os.getenv("CREATIVE_DEPTH", "standard").strip().lower(),
    )
