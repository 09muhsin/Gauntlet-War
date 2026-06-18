# ⚔️ Gauntlet War

**Rival AI agents draft 3 competing marketing plans, *self-improve under fire*, and ship the deliverables — all inside one Band room.**

Built for the [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon) (June 12–19, 2026) · Track 1: Internal Enterprise Workflows.

The field is full of "agents debate one fixed input → human approves → audit sealed." Gauntlet War is different on three axes: **(1)** three strategist agents each **author a complete, competing marketing plan** (the alternatives are generated, not handed in); **(2)** after the debate, each strategist publishes a **v2 that fixes its critiques** — the contest *causes* better plans; **(3)** the winning plan drops out as three **production-ready deliverables** (founder proposal + operating execution plan + ready-to-ship content kit), polished by a neuro-marketing copy engine. The whole run lives inside one Band room and seals as a SHA-256 hash posted into the transcript.

---

## How it works (Act 0 — Strategy Showdown)

1. A human submits a brief — product, goal, budget ceiling, constraints.
2. **@Conductor** opens a Band room and adds the four agents through Band's add-participant API (not hardcoded — recruiting goes through Band).
3. **@StrategistA/B/C** each author a complete plan, locked to a distinct archetype — **Go Viral**, **Trust Play**, **Paid Blitz** — with explicit funnel math and an honest `feasible` flag.
4. Strategists challenge each other's *numbers* via @mentions; every challenge gets a rebuttal.
5. **REFINE** — each strategist publishes a **v2 plan** that fixes the critiques against it (same archetype, tightened math). The original move most adversarial submissions skip.
6. **@Scorer** (independent, on Featherless) rates each v2 plan 1–10 on five weighted dimensions → ranked table.
7. @Conductor synthesizes a winner or hybrid, citing the score AND the debate point that settled it.
8. The human approves → bundle is **SHA-256-hashed and the hash is posted into the Band room** as the final message; the same bundle is written to `audit/<room_id>.json`. The transcript itself is the audit; the hash makes the off-Band record tamper-evident.
9. **SHIP** — the winning plan becomes a proposal + execution plan + content kit through a `think → draft → creative-director polish → cliché scrub` copy engine. Files land in `deliverables/<room_id>/`.

## Stack

| Layer | Tech |
|---|---|
| Coordination | **Band** — rooms, multi-agent participants, @mention routing, transcript-as-audit |
| Orchestration | **LangGraph** (Conductor phase control) |
| Strategist agents | **CrewAI** |
| Reasoning models | **AI/ML API** (Conductor + Strategists) |
| Scorer / personas | **Featherless AI** |
| Frontend | **Streamlit** |

## Setup

```bash
python -m venv .venv && . .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then fill in your keys
```

Get the three load-bearing keys:
- **Band** — band.ai → Pro with promo `BANDHACK26` → Agent API key
- **AI/ML API** — claim coupon via lablab.ai → key from aimlapi.com
- **Featherless** — setup guide → activate with promo `BOA26`

## Try it instantly (no keys, no cost)

The app ships with **Demo mode** — it replays real, sealed showdowns (brief → competing plans →
debate → scores → human-sealed winner → full deliverables) straight from `samples/`, with **zero API
calls**. Perfect for judges:

```bash
pip install -r requirements.txt
streamlit run src/app.py        # opens in Demo mode — pick a sealed run and click through
```

The deliverables in the demo were authored by **Claude (Opus 4.8 / Sonnet 4.6)** via AI/ML API and
run through a neuro-marketing copy engine (think → draft → creative-director polish → cliché scrub).

## Run it live

```bash
cp .env.example .env            # fill in Band + AI/ML keys
python -m scripts.day1_two_agent_room   # 1. prove Band works (do this first)
python run_act0.py                      # 2. Act 0 end to end (CLI)
streamlit run src/app.py                # 3. the UI — switch to "Live run" in the sidebar
```

Cost control: `AIML_MODEL_STRONG` picks the model (Sonnet 4.6 = cheap default, Opus 4.8 = premium
final run) and `CREATIVE_DEPTH` (`lite`/`standard`/`max`) controls how many polish passes run.
Regenerate deliverables for any sealed run without a Band call:
`python -m scripts.regen_deliverables <room_id>`.

## Project layout

```
gauntlet-war/
├─ run_act0.py              # Act 0 end-to-end CLI entry point
├─ scripts/
│  ├─ day1_two_agent_room.py  # Band smoke test (run first)
│  ├─ regen_deliverables.py   # re-author deliverables from a sealed run (no Band call)
│  └─ audit_quality.py        # offline gate: cliché + invented-proof sweep
├─ src/
│  ├─ config.py            # env / settings loader (model + CREATIVE_DEPTH knobs)
│  ├─ schemas.py           # Brief, Strategy, Critique, Score, Decision
│  ├─ models.py            # AI/ML API + Featherless routing (strips unsupported params)
│  ├─ knowledge.py         # neuro-marketing doctrine + cliché ban + scrub
│  ├─ band_client.py       # Band coordination wrapper
│  ├─ build.py             # wires the five agents from settings
│  ├─ demo.py              # offline replay loader (samples/ + audit/)
│  ├─ app.py               # Streamlit frontend (Demo + Live modes)
│  └─ agents/
│     ├─ conductor.py      # opens room, recruits, runs phases, synthesizes, seals
│     ├─ strategist.py     # authors + defends one archetype, writes deliverables
│     └─ scorer.py         # independent weighted scoring
├─ samples/                # committed sealed runs for Demo mode (record.json + deliverables)
├─ audit/                  # sealed decision records (gitignored)
└─ deliverables/           # generated artifacts (gitignored)
```

> ⚠️ **Run the smoke test first.** `python -m scripts.day1_two_agent_room` proves the Band wiring (create chat → add participant → 2 messages → list) before you spend AI/ML credits on the full gauntlet. 401 = wrong api_key · 403 = quota/permission · 422 = mention/participant problem.

## License

MIT — see [LICENSE](LICENSE).
