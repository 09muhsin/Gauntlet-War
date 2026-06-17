"""Strategist agent — authors and defends one archetype's complete plan (PRD §5.2, §5.3).

These are senior growth marketers, not slogan generators. Every plan must carry explicit
funnel math (reach -> leads -> conversions with assumed CTR/CVR), a budget split that respects
the ceiling, and an HONEST projection vs the goal — including conceding when the archetype
simply can't work in the given budget (e.g. Paid Blitz on $0). That honesty is what makes the
debate real and credible. Authoring AND debate run on the strong model for quality.
"""
from __future__ import annotations

import re
import uuid

from ..band_client import BandClient
from ..knowledge import (
    CLICHE_BAN,
    COPY_CRAFT,
    CREATIVE_BAR,
    HUMAN_VOICE,
    MARKETING_DOCTRINE,
    ZERO_BUDGET_DOCTRINE,
    scrub_banned,
)
from ..models import ModelRouter
from ..schemas import Archetype, Brief, Critique, Strategy

def _num(x) -> float:
    """Coerce a model-returned value to a float — tolerant of '$0', '1,500', or prose."""
    if isinstance(x, (int, float)):
        return float(x)
    m = re.search(r"-?\d[\d,]*\.?\d*", str(x))
    return float(m.group().replace(",", "")) if m else 0.0


def _as_list(x) -> list[str]:
    """Coerce to a clean list[str] — models sometimes return a string, dict, or list-of-dicts."""
    if isinstance(x, dict):
        return [f"{k}: {v}" for k, v in x.items()]
    if isinstance(x, list):
        out = []
        for i in x:
            out.append(" — ".join(str(v) for v in i.values()) if isinstance(i, dict) else str(i))
        return out
    return [] if x in (None, "") else [str(x)]


def _as_str(x) -> str:
    """Coerce to a string — models sometimes return a dict or list for a text field."""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return "; ".join(f"{k}={v}" for k, v in x.items())
    if isinstance(x, list):
        return "; ".join(str(i) for i in x)
    return "" if x is None else str(x)


ARCHETYPE_BRIEFS: dict[Archetype, str] = {
    Archetype.GO_VIRAL: (
        "Go Viral: win attention through organic reach and creators — TikTok, Reels, Shorts, "
        "influencer/affiliate seeding, UGC, community. Cheap to free, high upside, but unpredictable. "
        "You think in views, watch-through, share rate, creator deal terms, and organic CVR."
    ),
    Archetype.TRUST_PLAY: (
        "Trust Play: build durable demand through credibility and search — SEO, long-form content, "
        "email nurture, PR, partnerships. Compounds over time but slow to ramp. "
        "You think in keyword volume, ranking timelines, content velocity, email open/click, and LTV."
    ),
    Archetype.PAID_BLITZ: (
        "Paid Blitz: buy results now with paid acquisition — search/social ads, retargeting. Fast and "
        "measurable but needs real budget and stops when spend stops. "
        "You think in CPM, CPC, CTR, CVR, CAC, and ROAS, and you live or die by the math."
    ),
}


class Strategist:
    def __init__(self, label: str, archetype: Archetype, models: ModelRouter, band: BandClient):
        self.label = label
        self.archetype = archetype
        self._models = models
        self.band = band

    @property
    def handle(self) -> str:
        return self.band.handle

    def _system(self) -> str:
        return (
            f"You are {self.label}, a senior NEURO-marketing strategist running the "
            f"'{self.archetype.value}' playbook. {ARCHETYPE_BRIEFS[self.archetype]}\n\n"
            f"{MARKETING_DOCTRINE}\n\n"
            "Rules: (1) Be specific and numeric — exact tactics, channels, cadences, funnel math. "
            "(2) Respect the budget ceiling exactly; $0 means zero-cash/organic tactics only. "
            "(3) Be honest: only set feasible=false if the GOAL is impossible in the TIMELINE even with "
            "excellent execution — a $0 budget alone never makes it infeasible; design the organic path."
        )

    def _brief_line(self, brief: Brief) -> str:
        line = (
            f"product={brief.product}; goal={brief.goal}; budget_ceiling=${brief.budget_ceiling:,.0f}; "
            f"constraints={brief.constraints}"
        )
        if brief.budget_ceiling <= 0:
            line += f"\n\n{ZERO_BUDGET_DOCTRINE}"
        return line

    def author(self, brief: Brief) -> Strategy:
        prompt = (
            f"Brief: {self._brief_line(brief)}\n\n"
            "Author a complete, numeric strategy. Show your funnel math explicitly: estimate reach, "
            "apply realistic CTR/CVR (state the % you assume), and arrive at a projected number you "
            "can compare to the goal. State honestly whether you hit the goal or fall short, and by "
            "how much. Respond with STRICT JSON:\n"
            "{\n"
            '  "summary": "2-3 sentences, the actual plan with named tactics",\n'
            '  "channel_mix": ["specific channel + tactic", ...],\n'
            '  "budget_split": ["line item: $amount (note)", ...],\n'
            '  "funnel_math": "e.g. 500k organic views x 2% profile clicks = 10k visits x 4% CVR = 400 signups",\n'
            '  "projected_result": "honest projection vs the goal, with the number",\n'
            '  "cost_estimate": <number <= budget_ceiling>,\n'
            '  "expected_outcome": "one line",\n'
            '  "risks": ["specific risk", ...],\n'
            '  "feasible": <true|false>\n'
            "}"
        )
        d = self._models.ask_json("strong", self._system(), prompt)
        return Strategy(
            strategy_id=f"strat-{uuid.uuid4().hex[:8]}",
            author=self.label,
            archetype=self.archetype,
            summary=_as_str(d.get("summary", "")),
            channel_mix=_as_list(d.get("channel_mix")),
            budget_split=_as_list(d.get("budget_split")),
            funnel_math=_as_str(d.get("funnel_math", "")),
            projected_result=_as_str(d.get("projected_result", "")),
            expected_outcome=_as_str(d.get("expected_outcome", "")),
            cost_estimate=_num(d.get("cost_estimate", 0)),
            risks=_as_list(d.get("risks")),
            feasible=bool(d.get("feasible", True)),
        )

    def critique(self, brief: Brief, my_plan: Strategy, rival: Strategy) -> Critique:
        prompt = (
            f"Brief: {self._brief_line(brief)}\n\n"
            f"Rival plan by {rival.author} ({rival.archetype.value}):\n"
            f"  summary: {rival.summary}\n  funnel_math: {rival.funnel_math}\n"
            f"  projected: {rival.projected_result}\n  budget_split: {rival.budget_split}\n\n"
            "Attack their NUMBERS, not vibes. Recompute their funnel against the goal and budget. "
            "Find the specific place the math breaks (unrealistic CTR/CVR, budget can't fund the "
            "channel, timeline misses the goal window) and state it with the numbers. One sharp, "
            'quantified objection. STRICT JSON: {"claim": "...with numbers...", "severity": 1-5}'
        )
        d = self._models.ask_json("strong", self._system(), prompt)
        return Critique(
            author=self.label,
            target_strategy_id=rival.strategy_id,
            claim=d["claim"],
            severity=int(d.get("severity", 3)),
        )

    def refine(self, brief: Brief, plan: Strategy, critiques: list[Critique]) -> Strategy:
        """Self-improvement: revise the plan to fix valid critiques and sharpen the persuasion
        using the doctrine. Keeps the same id/archetype so it's the same plan, improved."""
        crit_text = "\n".join(
            f"- {c.author}: {c.claim} (severity {c.severity})" for c in critiques
        ) or "- (no direct critiques — improve it anyway using the doctrine)"
        prompt = (
            f"Brief: {self._brief_line(brief)}\n\n"
            f"Your current plan ({plan.archetype.value}): {plan.summary}\n"
            f"Funnel: {plan.funnel_math}\nProjection: {plan.projected_result}\n\n"
            f"Critiques raised against your plan in the debate:\n{crit_text}\n\n"
            "Produce an IMPROVED v2 of your plan: fix every valid critique, tighten the funnel math "
            "honestly, and sharpen tactics with the neuro-marketing doctrine (motivation fit, VAK copy, "
            "real persuasion levers). Keep your archetype. Respond with the SAME STRICT JSON schema:\n"
            '{"summary","channel_mix","budget_split","funnel_math","projected_result",'
            '"cost_estimate","expected_outcome","risks","feasible"}'
        )
        d = self._models.ask_json("strong", self._system(), prompt)
        return Strategy(
            strategy_id=plan.strategy_id,
            author=self.label,
            archetype=self.archetype,
            summary=_as_str(d.get("summary", plan.summary)),
            channel_mix=_as_list(d.get("channel_mix") or plan.channel_mix),
            budget_split=_as_list(d.get("budget_split") or plan.budget_split),
            funnel_math=_as_str(d.get("funnel_math", plan.funnel_math)),
            projected_result=_as_str(d.get("projected_result", plan.projected_result)),
            expected_outcome=_as_str(d.get("expected_outcome", plan.expected_outcome)),
            cost_estimate=_num(d.get("cost_estimate", plan.cost_estimate)),
            risks=_as_list(d.get("risks") or plan.risks),
            feasible=bool(d.get("feasible", True)),
        )

    def rebut(self, brief: Brief, my_plan: Strategy, critique: Critique) -> str:
        prompt = (
            f"Brief: {self._brief_line(brief)}\n"
            f"Your plan: {my_plan.summary}\n  Your funnel: {my_plan.funnel_math}\n\n"
            f"A challenger objected with numbers: \"{critique.claim}\"\n"
            "Defend in 2-3 sentences. If their math is right, concede the gap and adjust your numbers; "
            "if it's wrong, counter with your own figures. Be concrete — cite a number. No platitudes."
        )
        return self._models.strong(self._system(), prompt)

    # --- Deliverables (run only for the winning strategy) --------------
    def _deliverable_system(self) -> str:
        """Richer system prompt for copy deliverables — adds the craft rules, creative bar, human
        voice, and cliche ban on top of the strategist persona, so the output reads like a sharp
        human creative director, not a chatbot."""
        return (
            f"{self._system()}\n\n{COPY_CRAFT}\n\n{CREATIVE_BAR}\n\n{HUMAN_VOICE}\n\n{CLICHE_BAN}"
        )

    def _creative_brief(self, brief: Brief, plan: Strategy) -> str:
        """THINK step — reason about the human before writing a word. Produces a short internal
        creative brief: the real buyer, their verbatim pain, the single Big Idea, the emotional core.
        Feeding this into the draft is what makes the output thoughtful instead of template-filled."""
        prompt = (
            f"Brief: {self._brief_line(brief)}\nProduct: {brief.product}\n"
            f"Winning {plan.archetype.value} plan: {plan.summary}\nChannels: {', '.join(plan.channel_mix)}\n\n"
            "Before writing any copy, THINK like a creative director. In tight markdown (no fluff), produce:\n"
            "1. THE BUYER: a named avatar, their day, the exact 7pm-Sunday moment the product saves them "
            "from, and 3 phrases in THEIR words (how they'd describe the pain to a friend).\n"
            "2. THE BIG IDEA: one nameable creative concept the whole campaign hangs off — a reframe or a "
            "tension, not a tactic list. One sentence, make it surprising.\n"
            "3. EMOTIONAL CORE: the single feeling we sell (e.g. relief, vindication, status), and the "
            "true before->after scene that earns it.\n"
            "4. THE WEDGE: the one contrarian or specific angle competitors won't say.\n"
            "5. PROOF NEEDED: which claims need a real number/testimonial (flag as [INSERT REAL NUMBER]).\n"
            "Keep it under 200 words. This is your own thinking, not customer-facing."
        )
        return self._models.strong(self._deliverable_system(), prompt, temperature=0.85)

    def _think(self, brief: Brief, plan: Strategy) -> str:
        """The creative-brief step — skipped in 'lite' depth to save a call."""
        if self._models.creative_depth == "lite":
            return ""
        return self._creative_brief(brief, plan)

    def _polish(self, brief: Brief, plan: Strategy, kind: str, brief_doc: str, draft: str) -> str:
        """Creative-director critique -> rewrite. Hunts BLANDNESS as hard as cliches: any safe,
        forgettable, could-be-any-brand line gets replaced with the surprising, specific version.
        This is the pass that lifts 'correct' to 'best'. Runs 0x (lite), 1x (standard), or 2x (max),
        then a conditional banned-phrase scrub (free unless something slipped through)."""
        depth = self._models.creative_depth
        passes = {"lite": 0, "standard": 1, "max": 2}.get(depth, 1)
        text = draft
        for _ in range(passes):
            text = self._polish_once(brief, plan, kind, brief_doc, text)
        return scrub_banned(text, self._scrub_pass)

    def _polish_once(self, brief: Brief, plan: Strategy, kind: str, brief_doc: str, draft: str) -> str:
        prompt = (
            f"Product: {brief.product}\nCreative brief you wrote:\n{brief_doc}\n\n"
            f"Below is a DRAFT {kind}. Put on your creative-director hat and red-pen it HARD against the "
            "CREATIVE BAR and the BANNED list, then ship a sharper v2:\n"
            "- Kill every banned phrase AND every line that is merely correct-but-forgettable — if it "
            "could run for any competitor, rewrite it until only THIS product could say it.\n"
            "- Make sure the Big Idea is felt in every asset; open on a pattern interrupt; trade abstract "
            "benefits for concrete scenes and exact numbers; keep one distinct, human voice.\n"
            "- HUMANIZE: read every line aloud. Vary sentence length hard, use contractions, cut the AI "
            "tells (Moreover/Furthermore/'Not just X, it's Y'/perfectly parallel bullets). If a line "
            "sounds like a brand wrote it, rewrite it like a person said it.\n"
            "- Every headline uses a named technique; every email is fully written; never invent proof.\n"
            "- Keep the structure and anything already sharp. Output ONLY the finished markdown — no notes.\n\n"
            f"DRAFT:\n{draft}"
        )
        return self._models.strong(self._deliverable_system(), prompt, temperature=0.75)

    def _scrub_pass(self, hits: list[str], text: str) -> str:
        """Surgical fix for banned phrases a creative draft slipped past — replace ONLY the flagged
        phrases, leave everything else byte-for-byte."""
        prompt = (
            "These banned phrases survived in the copy below: "
            + ", ".join(f'"{h}"' for h in hits)
            + ".\nReplace EACH one with a concrete, specific alternative (a real image or a named "
            "tactic). Change nothing else. Output ONLY the corrected markdown.\n\n"
            f"COPY:\n{text}"
        )
        return self._models.strong(self._deliverable_system(), prompt, temperature=0.6)

    def execution_plan(self, brief: Brief, plan: Strategy) -> str:
        doc = self._think(brief, plan)
        prompt = (
            f"Brief: {self._brief_line(brief)}\n"
            f"Winning strategy ({plan.archetype.value}): {plan.summary}\n"
            f"Channels: {', '.join(plan.channel_mix)}\nFunnel: {plan.funnel_math}\n"
            f"Projection: {plan.projected_result}\n\n"
            f"Your creative brief (build on it; the campaign hangs off the Big Idea):\n{doc}\n\n"
            "Write a thorough, concrete EXECUTION PLAN in markdown that a small team can actually run. "
            "Be detailed — this is an operating doc, not a summary. Include ALL of:\n"
            "1. THE BIG IDEA in one line at the top.\n"
            "2. DAY-BY-DAY for the first 7 days (launch week): for each day, the exact task, the channel, "
            "the actual hook/script written out, who owns it, and roughly how long it takes.\n"
            "3. WEEK-BY-WEEK calendar for the rest of the timeline: each week lists each channel, the EXACT "
            "deliverable WITH the real scroll-stopping line written out (e.g. \"TikTok: 'I quit my job at "
            "34 — this 45-min test told me why' — kinaesthetic, contextual-status\"), cadence, owner.\n"
            "4. A per-channel PLAYBOOK (one short block each): the format, posting cadence, the repeatable "
            "hook formula for that channel, and the one metric that proves it's working.\n"
            "5. FUNNEL targets per stage (reach -> traffic -> leads -> conversions) with weekly numbers "
            "that ramp to the goal, consistent with the strategy's funnel math.\n"
            "6. A KPI table (metric | target | by-when) and the ONE leading metric to watch each week.\n"
            "7. A short RISKS & FALLBACKS block: the 2-3 likeliest ways this stalls and the move if it does.\n"
            "Respect the budget exactly ($0 = organic only). Every hook specific to THIS product. Write it "
            "like a sharp operator briefing the team out loud — concrete, human, no filler."
        )
        draft = self._models.strong(self._deliverable_system(), prompt, temperature=0.9)
        return self._polish(brief, plan, "execution plan", doc, draft)

    def content_kit(self, brief: Brief, plan: Strategy) -> str:
        doc = self._think(brief, plan)
        prompt = (
            f"Brief: {self._brief_line(brief)}\n"
            f"Winning strategy ({plan.archetype.value}) channels: {', '.join(plan.channel_mix)}\n\n"
            f"Your creative brief (everything ladders up to the Big Idea):\n{doc}\n\n"
            "Produce a deep, ready-to-ship STARTER CONTENT KIT in markdown — real assets for THIS product, "
            "copy-paste ready, NO placeholders or '[body brief]' shorthand. Be generous and detailed. Lead "
            "the file with the named BIG IDEA (one line), then include ALL of:\n"
            "- LANDING-PAGE HERO: a pattern-interrupt headline + curiosity subhead + 3 alternate headlines "
            "(each tagged with its technique) + a 3-4 sentence hero paragraph + the button copy.\n"
            "- 10 SEO/blog topics — title + target keyword + the angle + the searcher's WIIFM. Curiosity-"
            "driven titles, not encyclopedic.\n"
            "- A 5-EMAIL nurture sequence, FULLY WRITTEN: each email = subject + a preview line + 80-130 "
            "words of real body copy that opens on a scene or confession (one idea, one CTA) + a PS. Tag "
            "each with its motivation type (rational/emotional/contextual). They tell ONE running story "
            "with a recurring named character across all five.\n"
            "- ONE FULL SHORT-FORM SCRIPT (TikTok/Reel, ~30s): written shot by shot — the spoken hook (first "
            "3 seconds), the beats, the on-screen text, and the CTA. Make it genuinely scroll-stopping.\n"
            "- 7 scroll-stopping hooks for the primary channel — the first spoken line, each a different VAK "
            "or motivation angle, tagged as such.\n"
            "- 3 SOCIAL CAPTIONS (with a couple of real hashtags each) and 2 short ad variations.\n"
            "- OBJECTION HANDLERS: the top 3 reasons they won't act, each with a one-line reframe.\n"
            "- A reusable RISK-REVERSAL line and a real-SCARCITY line.\n"
            "Every line usable as-is and unmistakably about THIS product, in one human voice. Where a real "
            "number/testimonial is needed but unknown, write [INSERT REAL NUMBER] — never invent proof."
        )
        draft = self._models.strong(self._deliverable_system(), prompt, temperature=0.9)
        return self._polish(brief, plan, "content kit", doc, draft)
