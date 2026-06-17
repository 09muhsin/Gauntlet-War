"""Thin LLM client wrappers. Both AI/ML API and Featherless speak the OpenAI protocol,
so we reuse the openai SDK pointed at different base URLs.

Routing policy (PRD §12 token budget):
  - strong  -> AI/ML API strong model: Conductor synthesis, Strategist authoring, deliverables
  - cheap   -> AI/ML API cheap model:  Strategist rebuttals
  - scorer  -> Featherless (preferred) OR AI/ML API cheap (fallback), per SCORER_PROVIDER

Structured calls use JSON mode (response_format=json_object) so the model returns parseable
JSON. ask_json() adds a retry + clear error if a provider ignores JSON mode and returns prose.
"""
from __future__ import annotations

import json

from openai import OpenAI

from .config import Settings


class ModelRouter:
    def __init__(self, settings: Settings):
        self._s = settings
        self._aiml = OpenAI(api_key=settings.aiml_api_key, base_url=settings.aiml_api_base)
        self._feather = (
            OpenAI(api_key=settings.featherless_api_key, base_url=settings.featherless_api_base)
            if settings.featherless_api_key
            else None
        )
        self._scorer_on_featherless = (
            settings.scorer_provider == "featherless" and self._feather is not None
        )

    def _chat(self, client, model, system, user, temperature, json_mode=False) -> str:
        msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        kwargs: dict = {"temperature": temperature}
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        # Frontier models drop params over time (e.g. Opus 4.8 rejects `temperature`; some don't
        # support response_format). Strip the offending kwarg and retry instead of failing.
        for _ in range(3):
            try:
                resp = client.chat.completions.create(model=model, messages=msgs, **kwargs)
                return (resp.choices[0].message.content or "").strip()
            except Exception as e:
                msg = str(e).lower()
                if "temperature" in kwargs and "temperature" in msg:
                    kwargs.pop("temperature")
                elif "response_format" in kwargs and ("response_format" in msg or "json" in msg):
                    kwargs.pop("response_format")
                else:
                    raise
        resp = client.chat.completions.create(model=model, messages=msgs)
        return (resp.choices[0].message.content or "").strip()

    def strong(self, system, user, temperature: float = 0.7, json_mode: bool = False) -> str:
        return self._chat(self._aiml, self._s.aiml_model_strong, system, user, temperature, json_mode)

    def cheap(self, system, user, temperature: float = 0.7, json_mode: bool = False) -> str:
        return self._chat(self._aiml, self._s.aiml_model_cheap, system, user, temperature, json_mode)

    def scorer(self, system, user, temperature: float = 0.2, json_mode: bool = False) -> str:
        if self._scorer_on_featherless:
            return self._chat(
                self._feather, self._s.featherless_model, system, user, temperature, json_mode
            )
        return self._chat(self._aiml, self._s.aiml_model_cheap, system, user, temperature, json_mode)

    def ask_json(self, route: str, system: str, user: str, tries: int = 3) -> dict:
        """Call the given route in JSON mode and return a parsed dict, retrying on bad output."""
        fn = {"strong": self.strong, "cheap": self.cheap, "scorer": self.scorer}[route]
        last = ""
        for _ in range(tries):
            last = fn(system, user, json_mode=True)
            try:
                return parse_json(last)
            except (json.JSONDecodeError, ValueError):
                continue
        raise RuntimeError(
            f"Model route '{route}' did not return valid JSON after {tries} tries. "
            f"Last output: {last[:300]!r}"
        )

    @property
    def scorer_label(self) -> str:
        return "Featherless" if self._scorer_on_featherless else "AI/ML API (fallback)"

    @property
    def creative_depth(self) -> str:
        """How many think/polish passes the deliverable writers run: 'lite' | 'standard' | 'max'."""
        return self._s.creative_depth


def parse_json(raw: str) -> dict:
    """Tolerant JSON parse — models sometimes wrap output in prose or code fences."""
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = raw.split("```", 2)[1].lstrip("json").strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object found")
    return json.loads(raw[start : end + 1])
