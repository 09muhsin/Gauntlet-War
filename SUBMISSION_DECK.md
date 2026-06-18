# ⚔️ Gauntlet War — Submission Deck

> **Band of Agents Hackathon · Track 1 — Internal Enterprise Workflows**
> One slide per section. Each carries **on-slide text** (what a judge reads) and **speaker notes** (the video voiceover).
> **Copy rule** — every slide and the first 10 seconds of the video lead with *competing marketing plans · agents self-improve · production deliverables*. Never lead with "debate" or "audit trail" — that's the field's headline, not ours.

---

## Slide 1 — Title

**ON SLIDE**
# ⚔️ Gauntlet War
### Rival AI agents draft competing marketing plans, **self-improve under fire**, and ship the deliverables — a human seals it.
Band of Agents Hackathon · Track 1: Internal Enterprise Workflows

*Band · LangGraph · CrewAI · AI/ML API · Featherless AI · Streamlit*

**SPEAKER NOTES**
> Picking a marketing strategy shouldn't take three weeks of meetings where the loudest voice wins — and then another week to turn the choice into copy. Gauntlet War collapses both into 90 seconds of agents, plus a clean record of why.

---

## Slide 2 — The Problem

**ON SLIDE**
### Choosing a marketing strategy is slow, political, biased — and only half the work.
- Weeks of meetings between SEO, social, paid, and brand leads
- The **loudest voice or highest title** wins, not the strongest plan
- Only 1–2 options ever get seriously developed; alternatives die on the whiteboard
- **No written record** of *why* a direction was chosen → post-mortems are guesswork
- And the winning plan still has to be turned into actual copy — another week

**SPEAKER NOTES**
> Every channel lead pushes the approach that favors their own channel. Decisions get made on politics. Six months later nobody can explain why you went the way you did. And the strategy meeting is only half the work — turning the choice into copy is the other week.

---

## Slide 3 — What's Actually New (Originality)

**ON SLIDE**
### Everyone else debates *one fixed input.* We **author rival plans, refine them under fire, and ship the copy.**

| The rest of the field | Gauntlet War |
|---|---|
| Argues over **one** claim / contract / vendor / file | Agents **write 3 full rival game plans** |
| Stops at a verdict | Each strategist **publishes a v2 fixing its critiques** before the score |
| Compliance · claims · procurement (crowded) | **Marketing strategy** (uncontested domain) |
| Ends with a memo | Drops out **proposal + execution plan + content kit** — copy-paste ready |

**SPEAKER NOTES**
> Adversarial debate is the most common pattern in this hackathon — most submissions are some version of it. We're different on three axes nobody else owns at once. We **generate** the alternatives instead of grading a single fixed input. The debate **causes self-improvement** — every strategist publishes a v2 that answers its critiques, on the same archetype, so judges literally watch the plans get better. And the output isn't a memo — it's a founder proposal, an operating execution plan, and a starter content kit you could ship Monday morning. The argument is a supporting mechanic. Not the headline.

---

## Slide 4 — How It Works (Act 0: Strategy Showdown)

**ON SLIDE**
### A brief → a contested, scored, human-sealed decision → ready-to-ship copy.

1. Human submits a **brief** — product, goal, budget ceiling, constraints
2. **@Conductor** opens a Band room and adds the four agents through Band's API
3. **@Strategist A / B / C** each author a complete plan (locked archetype, explicit funnel math)
4. They challenge each other via **@mentions** — every challenge gets a rebuttal
5. **REFINE** — each strategist publishes a **v2** that fixes its critiques  ◄── *the original move*
6. **@Scorer** (independent, on Featherless) rates each v2 plan on 5 weighted dimensions
7. @Conductor synthesizes a **winner or hybrid** and cites the debate point that settled it
8. Human approves → **SHA-256 of the bundle is posted into the Band room** → audit record on disk
9. **SHIP** — winning plan becomes a proposal + execution plan + content kit, in one click

**SPEAKER NOTES**
> Five agents, three runtimes, one Band room. The Conductor doesn't hardcode its team — it adds participants through Band's API at runtime. The Scorer is on Featherless, so no plan grades its own homework. And we don't stop at the verdict: approval triggers a copy pipeline that turns the winning plan into three production-ready markdown files.

---

## Slide 5 — Three Plans, Built to Disagree

**ON SLIDE**
### Each strategist is locked to a distinct archetype — guaranteeing real alternatives.

| Archetype | Philosophy | Trade-off |
|---|---|---|
| 🚀 **Go Viral** | Win attention fast via creators & organic | Cheap & huge reach — but unpredictable |
| 🛡 **Trust Play** | Durable demand via SEO, long-form, email, PR | Compounds — but slow to ramp |
| 💸 **Paid Blitz** | Buy results now with aggressive paid | Fast & measurable — but stops when spend stops |

**SPEAKER NOTES**
> The archetype lock is the single most important design choice. Without it, three identically-trained LLMs converge to the same plan. With it, the alternatives are guaranteed to disagree — you get the high-risk play, the durable play, and the fast play, each defending its own logic with its own funnel math.

---

## Slide 6 — The Self-Improvement Loop (the original move)

**ON SLIDE**
### The debate *causes* better plans. Every strategist publishes a v2 that answers its critiques.

```
v1   →  cross-critique   →  REFINE  →  v2 (same archetype, tightened numbers)
      every @mention             ↑
      gets a rebuttal       fixes valid critiques,
                            patches the funnel math,
                            sharpens persuasion
```

- v1 plans are quantitative: explicit funnel math (reach → leads → conversions, named CTR/CVR), honest projection vs the goal, a `feasible` flag the Scorer punishes
- Critiques **attack numbers, not vibes** — challengers recompute the rival's funnel
- v2 plans **visibly answer** the debate — the UI shows the deltas

**SPEAKER NOTES**
> Every other adversarial submission stops at adjudication. Ours uses the debate as feedback. After the critiques land, each strategist re-authors its own plan — same archetype, tightened numbers, fixed math, sharper persuasion — and the Scorer rates the v2 versions, not the v1s. The contest produces a measurably better plan than any single agent would have written.

---

## Slide 7 — Live Demo: The $120 Running Shoe

**ON SLIDE**
### One product, followed end to end.
> **Brief:** New $120 running shoe · Goal: 1,000 first-month orders · Budget: $15,000

- **A** → creator-led viral push  ·  **B** → SEO + email + PR  ·  **C** → paid-search blitz
- They clash on the math: B attacks A's variance · A attacks C's CAC · C attacks B's 30-day timeline
- **REFINE** → each publishes a v2 fixing what got hit
- **Scorer** posts the ranked table → Conductor recommends a **hybrid**
- Human asks one question, gets an answer, **approves** → hash posted, deliverables drop

**SPEAKER NOTES**
> The Band room *is* the visualization — judges literally watch the plans appear, get attacked, get rewritten, get scored, and get chosen. End on the sealed hash and the deliverables panel.

---

## Slide 8 — Transparent Scoring

**ON SLIDE**
### Every refined plan rated 1–10 — weights are visible, the human can challenge them.

| Dimension | Measures | Weight |
|---|---|---|
| Cost-efficiency | Results per dollar within the budget | **25%** |
| Reach | Realistically reachable audience | 20% |
| Speed | Time to measurable results | 20% |
| Risk (inverted) | Underperformance / brand downside | 20% |
| Durability | Do results compound or vanish? | 15% |

- Scorer lives on **Featherless** — independent of the AI/ML API the strategists use
- Plans that mark themselves `feasible: false` are **harshly penalized** on reach + cost-efficiency, so honesty about a shortfall hurts

**SPEAKER NOTES**
> Nothing is a black box. The rubric is shared, weighted, and visible. The human can push back on the weights themselves before approving. And feasibility is real — a plan can't escape a hard math gap by hand-waving.

---

## Slide 9 — Production Deliverables (the second star)

**ON SLIDE**
### The winning plan drops out as three production-ready files — not a memo.

| File | Authored by | What's in it |
|---|---|---|
| **proposal.md** | `@Conductor` | The Big Bet (one line) · the customer + trigger moment · per-channel play · the score + the debate point that settled it · honest risks |
| **execution_plan.md** | Winning strategist | Day-by-day launch week · week-by-week calendar with every hook written out · per-channel playbook · funnel targets · KPI table |
| **content_kit.md** | Winning strategist | Landing hero + 3 alternate headlines (each tagged) · 10 SEO topics · 5-email nurture (fully written, one running character) · a 30-sec script shot-by-shot · 7 VAK-tagged hooks · objection handlers |

**THE COPY ENGINE** · think (creative brief) → draft → creative-director polish → cliché scrub
**THE DOCTRINE** · neuro-marketing (3 motivations × VAK processing) · banned-phrase linter · never invent proof

**SPEAKER NOTES**
> The Scorer turns the contest into a decision. The copy engine turns the decision into copy. Every line goes through a creative-director polish that hunts blandness as hard as clichés — any line that could run for any competitor gets rewritten until only THIS product could say it. Honest placeholders survive — Gauntlet War never invents proof.

---

## Slide 10 — How We Use Band (Application of Technology)

**ON SLIDE**
### Band is the spine, not a notification channel.

- **Shared room** — every authoring / debate / refine / score / synth / seal step is a message in one Band room
- **Multi-agent participants** — the Conductor adds the four agents through Band's add-participant API at runtime; agents never call each other directly
- **Per-agent Band identity** — five separate Agent API keys → five visible identities in the transcript
- **@mention routing** — Band requires every message to @mention a participant; we use it to drive every phase
- **Transcript-as-audit** — there's no `/seal` endpoint; the room *is* the immutable record, so we post a **SHA-256 of the canonical bundle into the room as the final message**
- **Cross-framework** — LangGraph (Conductor) + CrewAI (Strategists) + Featherless (Scorer) collaborate in one room

**SPEAKER NOTES**
> This is the heaviest judging criterion. Every collaboration physically happens through Band. Recruiting goes through Band's API, every message is routed by @mention, and the seal lives inside Band's transcript as a hash — so the off-Band audit record is tamper-evident *because* the hash is inside the chat. Take Band out and the product doesn't exist.

---

## Slide 11 — Architecture

**ON SLIDE**
### Five agents, three runtimes, one room.

| Layer | Tech |
|---|---|
| Coordination | **Band** — rooms, participants, @mention routing, transcript-as-audit |
| Phase control | **LangGraph-style** Conductor loop |
| Strategist persona | **CrewAI** — archetype-locked system prompt |
| Reasoning | **AI/ML API** — Claude Sonnet 4.6 default, Opus 4.8 for the premium recorded run |
| Independent scoring | **Featherless AI** — Meta-Llama-3.1-8B by default |
| Frontend | **Streamlit** — Demo + Live modes, step-by-step reveal |

**Cost discipline (live in `.env`)** — `CREATIVE_DEPTH={lite|standard|max}` · `MAX_DEBATE_ROUNDS` · `REFINE_PASSES` · `AIML_MODEL_STRONG` · `SCORER_PROVIDER`. `scripts/regen_deliverables.py` re-authors copy from any sealed run **without** burning Band credits.

**SPEAKER NOTES**
> Partner tech is load-bearing, not bolted on. Strategists reason through AI/ML API. The independent Scorer runs on Featherless — that's also what makes it eligible for the Featherless partner prize. Five knobs keep the gauntlet inside the credit budget, and we can re-author deliverables from a sealed record without spending a cent more on Band.

---

## Slide 12 — Business Value

**ON SLIDE**
### Weeks of meetings + a week of copywriting → 90 seconds of agents.
- ⏱️ **Weeks → minutes** for strategy selection
- ⚖️ **Evidence over seniority** — every plan scored, not shouted
- 🔁 **Every alternative fully developed** — and improved by the debate
- 📜 **Audit trail** — turn post-mortems from guesswork into review
- 📦 **Production deliverables** — proposal, execution plan, content kit, ship-ready
- 🏢 Every company that markets anything runs this process — badly

**SPEAKER NOTES**
> This is an internal enterprise workflow every company runs and runs badly. We make it fast, fair, reviewable — and we hand the operator the copy at the end, not a memo about what the copy *should* be.

---

## Slide 13 — Try It / Close

**ON SLIDE**
# ⚔️ Agents draft rival plans. Self-improve under fire. One ships.
- 🎬 **Demo mode** — replays real sealed showdowns + deliverables, **zero API keys, zero cost**
  `streamlit run src/app.py`
- 💻 Two pre-sealed sample runs committed in `samples/` — judges click through everything
- 🔗 **GitHub:** github.com/09muhsin/Gauntlet-War (MIT)
- 🧩 **Tags:** Band · AI/ML API · Featherless AI · LangGraph · CrewAI · Streamlit

*Built for the Band of Agents Hackathon — June 2026.*

**SPEAKER NOTES**
> Judges can run it instantly — Demo mode replays two real sealed showdowns end-to-end with no keys and no cost. Pick a sealed run, walk it through with the reveal toggle, watch the v2s answer the debate, watch the deliverables drop. Thanks for watching.

---

### Speaker timing (for a ~3-minute video)

| Slides | Time | Focus |
|---|---|---|
| 1–3 | 0:00–0:30 | Hook + the three originality moves (multi-plan + v2 + deliverables) |
| 4 + 5 | 0:30–0:50 | How it works + archetype lock |
| 6 + 7 | 0:50–1:40 | The self-improvement loop + live running-shoe showdown |
| 8 + 9 | 1:40–2:20 | Scoring + the deliverables drop |
| 10 + 11 | 2:20–2:40 | Band as the spine + stack |
| 12 + 13 | 2:40–3:00 | Value + "try it instantly" close |
