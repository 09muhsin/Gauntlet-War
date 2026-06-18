"""Gauntlet War — Streamlit frontend.

This file is the orchestration layer: sidebar controls, mode toggle, state, and the human
approval gate. All rendering goes through `src/ui.py`, which owns the design system.

Two modes:
  • DEMO (replay)  — renders a sealed showdown + deliverables straight from disk, zero API calls.
  • LIVE           — opens a real Band room, runs the gauntlet, and gates the human decision.

    streamlit run src/app.py
"""
from __future__ import annotations

import os
import sys

# Ensure the repo root is importable so `from src import ...` works regardless of
# how the app is launched (locally or on Streamlit Cloud, where the main file's
# own directory — not the repo root — is what gets put on sys.path).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

import hmac

from src import demo, ui
from src.config import load_settings
from src.schemas import Brief, Decision

# ── Page chrome ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Gauntlet War · Marketing Strategy Showdown",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(ui.inject_theme(), unsafe_allow_html=True)


# ── Access gate ──────────────────────────────────────────────────────────────
def _check_password() -> bool:
    """Gate the app behind a shared password set via APP_PASSWORD (secrets / .env).

    If APP_PASSWORD is unset the app stays open — handy for local dev. On the public
    Streamlit deployment, set it in Secrets so only people with the password (e.g.
    judges) can reach the live, billable controls.
    """
    expected = os.getenv("APP_PASSWORD", "").strip()
    if not expected:
        return True  # no password configured → open
    if st.session_state.get("auth_ok"):
        return True

    st.markdown(
        '<div style="max-width: 24rem; margin: 5rem auto 1.5rem; text-align: center; '
        'font-family: Fraunces, serif; font-style: italic; font-size: 2rem;">Gauntlet War</div>'
        '<div style="max-width: 24rem; margin: 0 auto 1.5rem; text-align: center; '
        'color: #6e7889; font-size: 0.85rem;">Enter the access password to continue.</div>',
        unsafe_allow_html=True,
    )
    _l, mid, _r = st.columns([1, 2, 1])
    with mid:
        pw = st.text_input("Password", type="password", label_visibility="collapsed")
        if pw:
            if hmac.compare_digest(pw, expected):
                st.session_state.auth_ok = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


if not _check_password():
    st.stop()

settings = load_settings()
missing = settings.missing_agents()


@st.cache_resource
def _conductor():
    from src.build import build_conductor  # lazy: demo mode never needs live wiring
    return build_conductor(settings)


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="padding: 0.4rem 0 1rem; font-family: Fraunces, serif; '
        'font-style: italic; font-size: 1.4rem;">Gauntlet War</div>',
        unsafe_allow_html=True,
    )

    can_live = (not missing) and bool(settings.aiml_api_key)
    runs = demo.list_runs()

    default_idx = 0 if runs else 1
    mode = st.radio(
        "Mode",
        ["Demo · replay a sealed run", "Live · open a Band room"],
        index=default_idx,
        label_visibility="collapsed",
    )
    live = mode.startswith("Live")
    st.divider()

    if not live:
        if not runs:
            st.info("No sealed runs found. Add one to `audit/` or `samples/`.")
            st.stop()
        labels = {f"{r['product']}  ·  {r['room_id'][:8]}": r["room_id"] for r in runs}
        pick = st.selectbox("Sealed runs", list(labels))
        st.caption("Loaded from `samples/` + `audit/`. No API calls.")
        st.markdown(
            f'<div style="font-family: JetBrains Mono, monospace; font-size: 0.7rem; '
            f'color: #6e7889; margin-top: 0.4rem;">runs · {len(runs)}</div>',
            unsafe_allow_html=True,
        )
    else:
        if not can_live:
            st.warning(
                "Live needs Band creds + an AI/ML key in `.env`. Demo mode runs sealed records."
            )
        product = st.text_input("Product", "$120 premium running shoe")
        goal = st.text_input("Goal", "1,000 first-month orders")
        budget = st.number_input("Budget ceiling (USD)", value=15000, step=500, min_value=0)
        constraints = st.text_area(
            "Constraints (one per line)", "DTC only\n30-day launch window"
        )
        go = st.button("Run the gauntlet", type="primary", disabled=not can_live, use_container_width=True)

    st.divider()
    reveal = st.toggle(
        "Step-by-step reveal",
        value=False,
        help="Walk the showdown one phase at a time — for video and live demos.",
    )

    with st.expander("About", expanded=False):
        st.markdown(
            "**5 agents · 3 runtimes · 1 Band room**\n\n"
            "Conductor (LangGraph) recruits 3 archetype-locked strategists (CrewAI) into a "
            "Band room. They debate each other's numbers, each publishes a v2 fixing critiques, "
            "an independent scorer (Featherless) ranks them, and a human seals the decision.\n\n"
            "_Built for the Band of Agents Hackathon — June 2026._"
        )


# ── Load or run a bundle ───────────────────────────────────────────────────────
if not live:
    room_id = labels[pick]
    st.session_state.bundle = demo.load_bundle(room_id)
    st.session_state.artifacts = demo.load_artifacts(room_id)
    # Sealed records already carry a decision (or imply one). Fold the hash up for ui.verdict().
    rec = st.session_state.bundle
    decision = rec.get("decision") or {}
    st.session_state.sealed_hash = rec.get("sealed_hash") or decision.get("sealed_hash")
    st.session_state.approver = decision.get("human_approver") or "sealed sample"
elif live and "go" in dir() and go:
    brief_obj = Brief(
        product=product, goal=goal, budget_ceiling=float(budget),
        constraints=[c for c in constraints.splitlines() if c.strip()],
    )
    try:
        with st.spinner("Agents authoring, debating, refining, and scoring in the Band room…"):
            st.session_state.bundle = _conductor().run(brief_obj)
            st.session_state.pop("artifacts", None)
            st.session_state.pop("sealed_hash", None)
            st.session_state.pop("approver", None)
    except Exception as e:
        st.error(f"Live run failed: {e}")
        st.info("Switch to **Demo mode** to walk a sealed run instead.")

bundle = st.session_state.get("bundle")
artifacts = st.session_state.get("artifacts")
sealed_hash = st.session_state.get("sealed_hash")
approver = st.session_state.get("approver")


# ── Stage controller ───────────────────────────────────────────────────────────
TOTAL_STAGES = len(ui.PHASE_LABELS)  # 7: Brief, Plans, Debate, Refine, Score, Verdict, Ship


def _step(delta: int) -> None:
    cur = st.session_state.get("stage", 1)
    st.session_state.stage = max(1, min(TOTAL_STAGES, cur + delta))


# ── Render ─────────────────────────────────────────────────────────────────────
st.markdown(ui.hero(mode="Demo" if not live else "Live"), unsafe_allow_html=True)

if not bundle:
    st.info("Pick a sealed run in the sidebar (Demo), or configure `.env` and run one Live.")
    st.stop()

if reveal:
    stage = st.session_state.get("stage", 1)
    cprev, cnext, _spacer = st.columns([1, 1, 8])
    cprev.button("◂ back", disabled=stage <= 1, on_click=_step, args=(-1,), use_container_width=True)
    cnext.button("next ▸", disabled=stage >= TOTAL_STAGES, on_click=_step, args=(1,),
                 type="primary", use_container_width=True)
else:
    stage = TOTAL_STAGES

st.markdown(ui.phase_rail(stage), unsafe_allow_html=True)
st.markdown(ui.brief_strip(bundle["brief"]), unsafe_allow_html=True)

# ── Section 1 · The arena (plan cards) ─────────────────────────────────────────
show_scores = stage >= 5
show_winner = stage >= 6
show_refined = bool(bundle.get("strategies_v1")) and stage >= 4

st.markdown(ui.section("01", "The arena"), unsafe_allow_html=True)
scores_by_id = {s["strategy_id"]: s for s in (bundle.get("scores") or [])}
st.markdown(
    ui.arena(
        bundle["strategies"], scores_by_id,
        winner_id=bundle.get("winner_id"),
        show_scores=show_scores,
        show_winner=show_winner,
        show_refined_badge=show_refined,
    ),
    unsafe_allow_html=True,
)

# ── Section 2 · The Band room (chat replay) ────────────────────────────────────
st.markdown(ui.section("02", "Inside the room"), unsafe_allow_html=True)
st.markdown(
    ui.room(bundle, stage=stage, sealed_hash=sealed_hash, approver=approver),
    unsafe_allow_html=True,
)

# ── Section 3 · Verdict ────────────────────────────────────────────────────────
if stage >= 6:
    st.markdown(ui.section("03", "The verdict"), unsafe_allow_html=True)
    st.markdown(
        ui.verdict(bundle, sealed_hash=sealed_hash, approver=approver),
        unsafe_allow_html=True,
    )

# ── Live human gate (demo bundles are already sealed) ──────────────────────────
if live and stage >= 6 and not sealed_hash:
    st.markdown(ui.section("04", "Sign-off"), unsafe_allow_html=True)
    approver_input = st.text_input("Your name (approver)", key="approver_input")
    c1, c2, c3 = st.columns(3)
    if c1.button("Approve & generate deliverables", type="primary", disabled=not approver_input):
        decision_obj = Decision(
            chosen_strategy_id=bundle["winner_id"],
            human_approver=approver_input,
            rationale="Approved via Gauntlet War UI",
        )
        sealed = _conductor().seal(bundle["room_id"], bundle, decision_obj)
        st.session_state.sealed_hash = sealed.sealed_hash
        st.session_state.approver = approver_input
        with st.spinner("Producing proposal, execution plan, and content kit in parallel…"):
            st.session_state.artifacts = _conductor().produce(bundle["room_id"], bundle)
        st.rerun()
    c2.button("Request revision", disabled=True, help="Hook this up in a follow-up.")
    c3.button("Reject", disabled=True, help="Hook this up in a follow-up.")

# ── Section · Deliverables ─────────────────────────────────────────────────────
if artifacts and stage >= 7:
    st.markdown(ui.section("04", "The deliverables"), unsafe_allow_html=True)
    tab_specs = [
        ("Proposal", "proposal"),
        ("Execution plan", "execution_plan"),
        ("Content kit", "content_kit"),
    ]
    present = [(t, k) for t, k in tab_specs if k in artifacts]
    if present:
        product_label = (bundle.get("brief") or {}).get("product", "deliverables")[:40].strip()
        combined = "\n\n---\n\n".join(f"# {t}\n\n{artifacts[k]}" for t, k in present)
        st.download_button(
            "Download all three (single .md)",
            combined,
            file_name=f"{product_label}-deliverables.md",
            key="dl_all",
            use_container_width=False,
        )
        tabs = st.tabs([t for t, _ in present])
        for tab, (title, key) in zip(tabs, present):
            with tab:
                text = artifacts[key]
                words = len(text.split())
                st.markdown(
                    f'<div style="display:flex;gap:1rem;font-size:0.72rem;color:#6e7889;'
                    f'font-family:JetBrains Mono, monospace;margin-bottom:0.6rem;">'
                    f'<span>{words:,} words</span><span>·</span><span>{len(text):,} chars</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    f"Download {title.lower()}",
                    text, file_name=f"{key}.md", key=f"dl_{key}",
                )
                st.markdown(text)
