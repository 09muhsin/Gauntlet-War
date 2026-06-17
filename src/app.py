"""Gauntlet War — Streamlit frontend (PRD §10), redesigned.

Two modes:
  • DEMO (replay): renders a sealed showdown + its deliverables straight from disk — zero API calls,
    no credentials. This is what makes the app demoable for judges and on a spent key.
  • LIVE: opens a real Band room, runs the showdown, and gates the human decision + deliverables.

    streamlit run src/app.py
"""
from __future__ import annotations

import streamlit as st

from src import demo
from src.config import load_settings
from src.schemas import Brief, Decision

st.set_page_config(page_title="Gauntlet War", page_icon="⚔️", layout="wide")

# ---- Theme ------------------------------------------------------------------
ARCHETYPE_COLOR = {"Go Viral": "#ff4d6d", "Trust Play": "#4dabf7", "Paid Blitz": "#ffb703"}

st.markdown(
    """
    <style>
      .block-container { padding-top: 2.2rem; }
      .wr-hero { font-size: 2.1rem; font-weight: 800; letter-spacing:-.5px; }
      .wr-sub { color:#9aa4b2; margin-top:-.4rem; }
      .wr-card { border:1px solid #2b313b; border-radius:14px; padding:16px 18px; height:100%;
                 background:linear-gradient(180deg,#161a20,#11151a); }
      .wr-card.win { border:1px solid #ffd43b; box-shadow:0 0 0 1px #ffd43b33, 0 8px 30px #ffd43b1a; }
      .wr-arch { font-weight:700; font-size:1.05rem; }
      .wr-pill { display:inline-block; font-size:.7rem; font-weight:700; padding:2px 9px;
                 border-radius:999px; vertical-align:middle; margin-left:6px; }
      .wr-win-pill { background:#ffd43b; color:#1a1a1a; }
      .wr-bad-pill { background:#3a2326; color:#ff8787; border:1px solid #ff6b6b55; }
      .wr-label { color:#7d8694; font-size:.72rem; text-transform:uppercase; letter-spacing:.06em;
                  margin:.5rem 0 .15rem; }
      .wr-bar-track { background:#222831; border-radius:6px; height:9px; width:100%; }
      .wr-bar-fill { height:9px; border-radius:6px; }
      .wr-hash { font-family:ui-monospace,monospace; font-size:.72rem; color:#7d8694; word-break:break-all; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="wr-hero">⚔️ Gauntlet War — Marketing Strategy Showdown</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="wr-sub">Three strategist agents author competing marketing plans, fight to a scored '
    'winner, and a human seals it into a tamper-evident audit record.</div>',
    unsafe_allow_html=True,
)

with st.expander("How it works", expanded=False):
    st.markdown(
        "1. **Brief** — a human sets the product, goal, budget ceiling, and constraints.\n"
        "2. **Author** — `@StrategistA/B/C` each write a complete plan locked to a distinct archetype: "
        "**Go Viral**, **Trust Play**, **Paid Blitz** — with explicit funnel math.\n"
        "3. **Debate** — strategists attack each other's numbers; every challenge gets a rebuttal.\n"
        "4. **Refine** — each strategist revises its plan to answer the critiques.\n"
        "5. **Score** — an independent `@Scorer` rates all plans on five weighted dimensions.\n"
        "6. **Seal** — the human approves; the full decision is hashed (SHA-256) into an audit record.\n"
        "7. **Deliverables** — the winning plan becomes a proposal, execution plan, and content kit, "
        "authored by Claude through a neuro-marketing copy engine."
    )
st.write("")

settings = load_settings()
missing = settings.missing_agents()


@st.cache_resource
def get_conductor():
    from src.build import build_conductor  # imported lazily so DEMO mode needs no live wiring
    return build_conductor(settings)


# ---- Controls ---------------------------------------------------------------
with st.sidebar:
    st.header("Mode")
    can_live = not missing and bool(settings.aiml_api_key)
    default_mode = "🎬 Demo (replay a sealed run)" if demo.has_demo_data() else "⚡ Live run"
    mode = st.radio("How to run", ["🎬 Demo (replay a sealed run)", "⚡ Live run"],
                    index=0 if default_mode.startswith("🎬") else 1, label_visibility="collapsed")
    live = mode.startswith("⚡")
    st.divider()

    if not live:
        st.header("Sealed runs")
        runs = demo.list_runs()
        if not runs:
            st.info("No sealed runs found yet. Run one live, or add audit/*.json records.")
            st.stop()
        labels = {f"{r['product']}  ·  {r['room_id'][:8]}": r["room_id"] for r in runs}
        pick = st.selectbox("Replay", list(labels))
        st.caption("Loaded from `audit/` + `deliverables/` — no API calls.")
    else:
        st.header("Brief")
        if not can_live:
            st.warning("Live run needs Band creds + an AI/ML key in `.env`. "
                       "Use Demo mode to explore a finished run.")
        product = st.text_input("Product", "$120 premium running shoe")
        goal = st.text_input("Goal", "1,000 first-month orders")
        budget = st.number_input("Budget ceiling (USD)", value=15000, step=500)
        constraints = st.text_area("Constraints (one per line)", "DTC only\n30-day launch window")
        go = st.button("Run Strategy Showdown", type="primary", disabled=not can_live)

    st.divider()
    reveal = st.toggle("🎬 Reveal step-by-step", value=False,
                       help="Walk the showdown one phase at a time — great for a live demo or video.")


# ---- Load the bundle (demo: from disk · live: from a run) --------------------
if not live:
    room_id = labels[pick]
    bundle = demo.load_bundle(room_id)
    st.session_state.artifacts = demo.load_artifacts(room_id)
    st.session_state.bundle = bundle
elif go:
    brief = Brief(
        product=product, goal=goal, budget_ceiling=float(budget),
        constraints=[c for c in constraints.splitlines() if c.strip()],
    )
    try:
        with st.spinner("Agents authoring, debating, and scoring in the Band room…"):
            st.session_state.bundle = get_conductor().run(brief)
            st.session_state.pop("artifacts", None)
    except Exception as e:  # quota/credential/network failures shouldn't crash the demo
        st.error(f"Live run failed: {e}")
        st.info("Tip: switch to **Demo mode** to replay a sealed run with no API calls.")

bundle = st.session_state.get("bundle")


# ---- Render -----------------------------------------------------------------
def score_bar(label: str, value: int, color: str) -> str:
    pct = max(0, min(100, value * 10))
    return (
        f'<div class="wr-label">{label} · {value}/10</div>'
        f'<div class="wr-bar-track"><div class="wr-bar-fill" '
        f'style="width:{pct}%;background:{color}"></div></div>'
    )


PHASES = ["Competing plans", "The debate", "The scores", "The verdict", "The deliverables"]


def render(bundle: dict, stage: int) -> None:
    b = bundle["brief"]
    winner_id = bundle.get("winner_id")
    strategies = bundle["strategies"]
    scores_by_id = {s["strategy_id"]: s for s in bundle["scores"]}
    ranked = sorted(bundle["scores"], key=lambda s: -s["total"])
    arch_of = {s["strategy_id"]: s["archetype"] for s in strategies}

    st.markdown(
        f"**Brief** — {b['product']}  ·  🎯 {b['goal']}  ·  💰 ${b['budget_ceiling']:,.0f}"
        + (f"  ·  ⛓ {', '.join(b.get('constraints') or [])}" if b.get("constraints") else "")
    )

    # Verdict metrics — revealed once we reach the verdict phase.
    if stage >= 4 and ranked:
        win_sc = scores_by_id.get(winner_id) or ranked[0]
        margin = win_sc["total"] - (ranked[1]["total"] if len(ranked) > 1 else 0)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏆 Winner", arch_of.get(win_sc["strategy_id"], "—"))
        m2.metric("Weighted score", f"{win_sc['total']}")
        m3.metric("Margin over #2", f"+{margin:.1f}")
        m4.metric("Plans in the ring", len(strategies))
    st.write("")

    # Competing plans as cards. Scores light up at phase 3; the winner is crowned at phase 4.
    show_scores = stage >= 3
    show_winner = stage >= 4
    cols = st.columns(len(strategies))
    for col, s in zip(cols, strategies):
        is_win = show_winner and s["strategy_id"] == winner_id
        color = ARCHETYPE_COLOR.get(s["archetype"], "#868e96")
        sc = scores_by_id.get(s["strategy_id"])
        pills = '<span class="wr-pill wr-win-pill">WINNER</span>' if is_win else ""
        if not s.get("feasible", True):
            pills += '<span class="wr-pill wr-bad-pill">NOT FEASIBLE</span>'
        with col:
            st.markdown(
                f'<div class="wr-card {"win" if is_win else ""}">'
                f'<div class="wr-arch" style="color:{color}">{s["archetype"]}{pills}</div>'
                f'<div style="color:#9aa4b2;font-size:.8rem;margin-bottom:.4rem">{s["author"]}'
                + (f"  ·  ⭐ {sc['total']}" if sc and show_scores else "") + "</div>"
                f'<div style="font-size:.9rem">{s["summary"]}</div>',
                unsafe_allow_html=True,
            )
            if s.get("funnel_math"):
                st.caption(f"📊 {s['funnel_math']}")
            if s.get("projected_result"):
                st.caption(f"🎯 {s['projected_result']}")
            if sc and show_scores:
                st.markdown(
                    "".join(score_bar(k.replace("_", " "), v, color)
                            for k, v in sc["dimensions"].items()),
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

    st.write("")
    left, right = st.columns([3, 2])
    with left:
        if stage >= 2:
            st.subheader("⚔️ Debate")
            if not bundle["debate"]:
                st.caption("No debate recorded.")
            for d in bundle["debate"]:
                c = d["critique"]
                st.markdown(f"**{c['author']}** challenges `{c['target_strategy_id'][:13]}` "
                            f"· severity {c['severity']}")
                st.markdown(f"> {c['claim']}")
                st.markdown(f"🛡️ *{d['rebuttal']}*")
                st.divider()
    with right:
        if stage >= 4:
            st.subheader("🏆 Verdict")
            st.info(bundle["recommendation"])
            decision = bundle.get("decision") or {}
            if decision.get("human_approver"):
                st.success(f"Sealed by **{decision['human_approver']}**")
            if bundle.get("sealed_hash"):
                st.markdown("**Tamper-evident SHA-256**", help="Hash over the full decision bundle.")
                st.markdown(f'<div class="wr-hash">{bundle["sealed_hash"]}</div>',
                            unsafe_allow_html=True)

    # Live mode: the human gate (demo mode is already sealed).
    artifacts = st.session_state.get("artifacts")
    if live and stage >= 4 and not (bundle.get("decision") or {}).get("human_approver"):
        st.subheader("✋ Human decision gate")
        approver = st.text_input("Your name (approver)")
        c1, c2, c3 = st.columns(3)
        if c1.button("✅ Approve & generate deliverables", type="primary") and approver:
            decision = Decision(chosen_strategy_id=bundle["winner_id"], human_approver=approver,
                                rationale="Approved via Gauntlet War UI")
            sealed = get_conductor().seal(bundle["room_id"], bundle, decision)
            st.success(f"Sealed · SHA-256 {sealed.sealed_hash[:16]}…")
            with st.spinner("Producing execution plan, proposal, and content kit…"):
                st.session_state.artifacts = get_conductor().produce(bundle["room_id"], bundle)
            artifacts = st.session_state.artifacts
        c2.button("✏️ Request revision")
        c3.button("❌ Reject")

    if artifacts and stage >= 5:
        st.subheader("📦 Deliverables")
        tab_specs = [("Proposal", "proposal"), ("Execution plan", "execution_plan"),
                     ("Content kit", "content_kit")]
        present = [(t, k) for t, k in tab_specs if k in artifacts]
        combined = "\n\n---\n\n".join(
            f"# {t}\n\n{artifacts[k]}" for t, k in present
        )
        st.download_button("⬇ Download all deliverables (.md)", combined,
                           file_name=f"{b['product'][:30].strip()}-deliverables.md", key="dl_all")
        for tab, (title, key) in zip(st.tabs([t for t, _ in present]), present):
            with tab:
                st.download_button("⬇ Download this file", artifacts[key], file_name=f"{key}.md",
                                   key=f"dl_{key}")
                st.markdown(artifacts[key])


def _step(delta: int) -> None:
    cur = st.session_state.get("stage", 1)
    st.session_state.stage = max(1, min(len(PHASES), cur + delta))


if bundle:
    if reveal:
        stage = st.session_state.get("stage", 1)
        cprev, cnext, cbar = st.columns([1, 1, 6])
        cprev.button("◀ Back", disabled=stage <= 1, on_click=_step, args=(-1,),
                     use_container_width=True)
        cnext.button("Next ▶", disabled=stage >= len(PHASES), on_click=_step, args=(1,),
                     type="primary", use_container_width=True)
        cbar.progress(stage / len(PHASES), text=f"Phase {stage}/{len(PHASES)} — {PHASES[stage - 1]}")
    else:
        stage = len(PHASES)
    render(bundle, stage)
else:
    st.info("Pick a sealed run in the sidebar (Demo), or configure `.env` and run one Live.")
