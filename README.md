# ⚔️ Gauntlet War

**Rival AI agents run marketing strategies through a gauntlet of debate and scoring — one survives, and a human seals it.**

Built for the [Band of Agents Hackathon](https://lablab.ai/ai-hackathons/band-of-agents-hackathon) (June 12–19, 2026) · Track 1: Internal Enterprise Workflows.

Most multi-agent submissions debate a *single fixed input* (one claim, one contract). Gauntlet War is different: three strategist agents each **author a complete, competing marketing plan**, defend it in a live Band room, and a separate scorer + the Conductor drive to a winner that a human seals into a tamper-evident audit record.

---

## How it works (Act 0 — Strategy Showdown)

1. A human submits a brief — product, goal, budget ceiling, constraints.
2. **@Conductor** opens a Band room and **recruits** the agents via discovery.
3. **@StrategistA/B/C** each author a complete plan, locked to a distinct archetype — **Go Viral**, **Trust Play**, **Paid Blitz**.
4. Strategists critique each other via @mentions; every challenge gets a rebuttal.
5. **@Scorer** (independent) rates each plan 1–10 on five weighted dimensions → ranked table.
6. @Conductor synthesizes a winner or hybrid with cited reasons.
7. The human approves → **Band seals** the brief, plans, debate, scores, and choice.

## Stack

| Layer | Tech |
|---|---|
| Coordination | **Band** (rooms, discovery, @mention routing, audit seal) |
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

> ⚠️ **Before anything else:** `src/band_client.py` is written against a plausible REST shape with `TODO` markers. Confirm each endpoint against the Band Agent API / SDK docs on Day 1 — the `day1_two_agent_room.py` smoke test is how you verify it.

## License

MIT — see [LICENSE](LICENSE).
