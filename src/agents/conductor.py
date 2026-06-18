"""Conductor — opens the room, recruits agents, runs the phases, writes the recommendation,
requests human sign-off, and seals the decision (PRD §5.1, §5.2).

Each agent posts to Band AS ITSELF (its own BandClient). Band requires every message to
@mention at least one participant, so the Conductor threads mentions through every phase.

There is no Band "/seal" endpoint — in Band the transcript IS the audit trail. So we seal by
hashing the full decision bundle (SHA-256) and writing a local tamper-evident audit record,
then posting the hash into the room so it lives in the immutable transcript too.

This plain pipeline lifts cleanly into a LangGraph StateGraph on Day 3-4.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from ..band_client import BandClient, Mention
from ..knowledge import (
    CLICHE_BAN,
    COPY_CRAFT,
    CREATIVE_BAR,
    HUMAN_VOICE,
    MARKETING_DOCTRINE,
    scrub_banned,
)
from ..models import ModelRouter
from ..parallel import pmap
from ..schemas import Brief, Decision, Score, Strategy
from .scorer import Scorer
from .strategist import Strategist

AUDIT_DIR = Path(__file__).resolve().parents[2] / "audit"
DELIVERABLES_DIR = Path(__file__).resolve().parents[2] / "deliverables"


class Conductor:
    def __init__(
        self,
        band: BandClient,
        models: ModelRouter,
        strategists: list[Strategist],
        scorer: Scorer,
        max_rounds: int = 2,
        refine_passes: int = 1,
    ):
        self.band = band
        self.label = "@Conductor"
        self._models = models
        self._strategists = strategists
        self._scorer = scorer
        self._max_rounds = max_rounds
        self._refine_passes = refine_passes

    def run(self, brief: Brief) -> dict:
        # Phase 0 — open room + recruit participants (Band's add-participant API).
        room_id = self.band.create_chat(title=f"Gauntlet War: {brief.product}")
        for member in self._members():
            self.band.add_participant(room_id, member.band.agent_id)
        everyone = [m.band.mention() for m in self._members()]
        self.band.post(
            room_id,
            f"Brief posted. Product: {brief.product} | Goal: {brief.goal} | "
            f"Budget: ${brief.budget_ceiling:,.0f} | Constraints: {brief.constraints}. "
            "Strategists, author your competing plans.",
            mentions=everyone,
        )

        # Phase 1 — AUTHOR (3 strategists in parallel; each posts AS ITSELF).
        def _author(s: Strategist) -> Strategy:
            plan = s.author(brief)
            feas = "" if plan.feasible else " ⚠️ NOT feasible in this budget"
            s.band.post(
                room_id,
                f"My plan ({plan.archetype.value}){feas}: {plan.summary}\n"
                f"Funnel: {plan.funnel_math}\n"
                f"Projection: {plan.projected_result} | Est. cost: ${plan.cost_estimate:,.0f}",
                mentions=[self.band.mention()],
            )
            return plan

        strategies: list[Strategy] = pmap(_author, self._strategists)
        plan_of: dict[str, Strategist] = {
            p.strategy_id: s for p, s in zip(strategies, self._strategists)
        }
        my_plan: dict[str, Strategy] = {s.label: p for p, s in zip(strategies, self._strategists)}

        # Phase 2 — DEBATE (every cross-pair runs concurrently; each chain stays critique→rebuttal).
        debate_log: list[dict] = []
        crits_against: dict[str, list] = {p.strategy_id: [] for p in strategies}

        def _chain(args: tuple[Strategist, Strategist, Strategy]) -> dict:
            challenger, defender, rival_plan = args
            mine = my_plan[challenger.label]
            crit = challenger.critique(brief, mine, rival_plan)
            challenger.band.post(room_id, crit.claim, mentions=[defender.band.mention()])
            rebuttal = defender.rebut(brief, rival_plan, crit)
            defender.band.post(room_id, rebuttal, mentions=[challenger.band.mention()])
            return {"critique": crit, "rebuttal": rebuttal}

        for _ in range(self._max_rounds):
            pairs = [
                (challenger, plan_of[rival.strategy_id], rival)
                for challenger in self._strategists
                for rival in strategies
                if rival.author != challenger.label
            ]
            results = pmap(_chain, pairs)
            for r in results:
                crit = r["critique"]
                crits_against[crit.target_strategy_id].append(crit)
                debate_log.append({"critique": crit.model_dump(), "rebuttal": r["rebuttal"]})

        # Snapshot v1 BEFORE refinement so the UI can show the v1→v2 progression.
        plans_v1 = [my_plan[s.label] for s in self._strategists]

        # Phase 2.5 — REFINE (3 strategists self-improving in parallel; v2 visibly answers debate).
        def _refine(s: Strategist) -> Strategy:
            plan = my_plan[s.label]
            improved = s.refine(brief, plan, crits_against.get(plan.strategy_id, []))
            feas = "" if improved.feasible else " ⚠️ still not feasible"
            s.band.post(
                room_id,
                f"Revised plan v2 ({improved.archetype.value}){feas}: {improved.summary}\n"
                f"Funnel: {improved.funnel_math}\nProjection: {improved.projected_result}",
                mentions=[self.band.mention()],
            )
            return improved

        for _ in range(self._refine_passes):
            refined = pmap(_refine, self._strategists)
            for s, plan in zip(self._strategists, refined):
                my_plan[s.label] = plan
            strategies = [my_plan[s.label] for s in self._strategists]

        # Phase 3 — SCORE the refined plans (scorer parallelizes internally).
        ranked: list[Score] = self._scorer.ranked_table(strategies)
        self._scorer.band.post(
            room_id, _format_table(ranked, strategies), mentions=[self.band.mention()]
        )

        # Phase 4 — synthesize recommendation + open the human gate.
        recommendation = self._synthesize(strategies, ranked, debate_log)
        self.band.post(room_id, recommendation, mentions=everyone)
        self.band.post(
            room_id,
            "Human review requested. Approve, reject, or request a revision.",
            mentions=everyone,
        )

        return {
            "room_id": room_id,
            "brief": brief.model_dump(),
            "strategies": [s.model_dump() for s in strategies],
            "strategies_v1": [s.model_dump() for s in plans_v1],
            "debate": debate_log,
            "scores": [{"strategy_id": s.strategy_id, "total": s.weighted_total,
                        "dimensions": s.dimensions.model_dump()} for s in ranked],
            "recommendation": recommendation,
            "winner_id": ranked[0].strategy_id if ranked else None,
        }

    def seal(self, room_id: str, bundle: dict, decision: Decision) -> Decision:
        """Seal the decision: SHA-256 over the canonical bundle, write a local audit record,
        and post the hash into the room so it lives in the immutable transcript."""
        record = {
            "room_id": room_id,
            "brief": bundle["brief"],
            "strategies": bundle["strategies"],
            "debate": bundle["debate"],
            "scores": bundle["scores"],
            "recommendation": bundle["recommendation"],
            "decision": decision.model_dump(exclude={"sealed_hash"}),
            "sealed_at": datetime.now(timezone.utc).isoformat(),
        }
        canonical = json.dumps(record, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        record["sealed_hash"] = digest

        AUDIT_DIR.mkdir(exist_ok=True)
        (AUDIT_DIR / f"{room_id}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")

        self.band.post(
            room_id,
            f"DECISION SEALED by {decision.human_approver}. Winner: {decision.chosen_strategy_id}. "
            f"Tamper-evident SHA-256: {digest}",
            mentions=self._everyone(),
        )
        return decision.model_copy(update={"sealed_hash": digest})

    def produce(self, room_id: str, bundle: dict) -> dict:
        """Deliverables stage: turn the approved winner into usable artifacts —
        execution plan + content kit (by the winning Strategist) and a proposal (Conductor).
        Saves them as markdown files and posts a notice into the Band room."""
        winner_dict = next(
            s for s in bundle["strategies"] if s["strategy_id"] == bundle["winner_id"]
        )
        winner = Strategy(**winner_dict)
        strategist = next(s for s in self._strategists if s.label == winner.author)
        brief = Brief(**bundle["brief"])

        # Three deliverables run concurrently — each is ~6 LLM calls (think + draft + polish + scrub),
        # so this cuts the post-approval wait from ~90s to ~30s without changing the token spend.
        jobs = [
            ("execution_plan", lambda: strategist.execution_plan(brief, winner)),
            ("content_kit",    lambda: strategist.content_kit(brief, winner)),
            ("proposal",       lambda: self._proposal(brief, winner, bundle)),
        ]
        results = pmap(lambda j: j[1](), jobs)
        artifacts = dict(zip([j[0] for j in jobs], results))

        out_dir = DELIVERABLES_DIR / room_id
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, text in artifacts.items():
            (out_dir / f"{name}.md").write_text(text, encoding="utf-8")

        self.band.post(
            room_id,
            f"Deliverables generated for {winner.author}'s {winner.archetype.value} plan: "
            "execution plan, shareable proposal, and starter content kit.",
            mentions=[strategist.band.mention()],
        )
        artifacts["dir"] = str(out_dir)
        return artifacts

    def _proposal(self, brief: Brief, winner: Strategy, bundle: dict) -> str:
        system = (
            "You are @Conductor, a head of growth presenting to the founder who will fund this. Write a "
            "sharp, client-ready MARKETING STRATEGY PROPOSAL in markdown with these sections: The Big Bet "
            "(one bold line — the single idea this whole plan rides on), Executive Summary, The Customer "
            "We're Betting On (one tight paragraph on who buys and the moment that triggers them), "
            "Recommended Approach (per-channel, with the actual play for each), Why This Won (cite the "
            "actual scores AND the specific debate point that settled it), The Funnel Math (the real "
            "numbers, not vibes), Timeline, KPIs, The Risks (honest — 2-3 real ones and the fallback), "
            "Next Steps. Open with the result the founder gets, not background. Use the plan's real "
            "numbers throughout; respect the budget exactly. A confident point of view, not a committee "
            "memo — write like a real operator talking to the founder, and make them WANT to fund it.\n\n"
            f"{MARKETING_DOCTRINE}\n\n{CREATIVE_BAR}\n\n{HUMAN_VOICE}\n\n{CLICHE_BAN}"
        )
        payload = {
            "brief": bundle["brief"],
            "winner": {"archetype": winner.archetype.value, "summary": winner.summary,
                       "channels": winner.channel_mix, "cost_estimate": winner.cost_estimate,
                       "funnel_math": winner.funnel_math, "projected_result": winner.projected_result,
                       "risks": winner.risks},
            "scores": bundle["scores"],
            "recommendation": bundle["recommendation"],
        }
        text = self._models.strong(system, json.dumps(payload, indent=2), temperature=0.85)
        # Polish passes scale with the spend knob: 0 (lite), 1 (standard), 2 (max).
        passes = {"lite": 0, "standard": 1, "max": 2}.get(self._models.creative_depth, 1)
        for _ in range(passes):
            polish = (
                "Red-pen this proposal as a creative director: kill every cliche AND every line that's "
                "merely correct-but-forgettable, sharpen The Big Bet so it's genuinely compelling, keep "
                "all the real numbers and the funnel math, lead with the founder's payoff. One confident "
                f"voice. Output ONLY the finished markdown.\n\n{COPY_CRAFT}\n\nDRAFT:\n{text}"
            )
            text = self._models.strong(system, polish, temperature=0.75)

        def _scrub(hits, text):
            fix = (
                "These banned phrases survived: " + ", ".join(f'"{h}"' for h in hits)
                + ". Replace each with a concrete, specific alternative; change nothing else. "
                f"Output ONLY the corrected markdown.\n\nCOPY:\n{text}"
            )
            return self._models.strong(system, fix, temperature=0.6)

        return scrub_banned(text, _scrub)

    def _members(self):
        return [*self._strategists, self._scorer]

    def _everyone(self) -> list:
        """Mentions for all participants except the Conductor (Band forbids self-mention)."""
        return [m.band.mention() for m in self._members()]

    def _synthesize(self, strategies, ranked, debate_log) -> str:
        system = (
            "You are @Conductor, the head of growth. Synthesize the funnel math, debate, and scores "
            "into a decisive recommendation: a single winner OR a specific hybrid. Cite real numbers "
            "from the plans and name the debate point that settled it. Reject any plan that is "
            "infeasible in the budget. End with the single most important reason. Be sharp, not generic."
        )
        payload = {
            "scores": [{"id": s.strategy_id, "total": s.weighted_total} for s in ranked],
            "strategies": [{"id": s.strategy_id, "archetype": s.archetype.value,
                            "summary": s.summary, "funnel_math": s.funnel_math,
                            "projected_result": s.projected_result, "feasible": s.feasible}
                           for s in strategies],
            "debate_highlights": debate_log[:8],
        }
        return self._models.strong(system, json.dumps(payload, indent=2))


def _format_table(ranked: list[Score], strategies: list[Strategy]) -> str:
    name = {s.strategy_id: f"{s.author} ({s.archetype.value})" for s in strategies}
    lines = ["Ranked strategies (weighted total):"]
    for i, sc in enumerate(ranked, 1):
        lines.append(f"  {i}. {name.get(sc.strategy_id, sc.strategy_id)} — {sc.weighted_total}")
    return "\n".join(lines)
