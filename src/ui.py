"""Gauntlet War — editorial UI for the Streamlit frontend (redesign).

A single, deliberate design system built for a hackathon stage:
  • Variable-axis typography (Fraunces display + Inter body + JetBrains Mono for data).
  • A near-black "midnight atelier" canvas with one accent per archetype and a warm gold
    for the winner/seal — no SaaS gradients, no shadcn defaults.
  • The Band room rendered as a real chat thread with role-coloured avatars and a staggered
    fade-in, so the agent-to-agent collaboration reads at a glance.
  • Motion only where it carries meaning — the progress rail fills, score bars grow, the
    winner card breathes, and the tamper-evident hash reveals.

Every public function returns a single string of HTML and is rendered via
`st.markdown(..., unsafe_allow_html=True)`. State and orchestration live in `app.py`; this
module is pure presentation, so it can be unit-tested by inspecting the returned strings.

The public surface (names, signatures, return types) is unchanged from the previous design,
so `app.py` keeps working untouched.
"""
from __future__ import annotations

import html
from typing import Iterable

# ── Design tokens ────────────────────────────────────────────────────────────────
# Single source of truth for the archetype accents. Change here, ripple everywhere.
ARCHETYPE_ACCENT: dict[str, str] = {
    "Go Viral":   "#ff4d6d",   # rose      — the high-risk play
    "Trust Play": "#5d8bff",   # cobalt    — the durable play
    "Paid Blitz": "#ffb454",   # amber     — the spend play
}
ARCHETYPE_GLYPH: dict[str, str] = {"Go Viral": "↯", "Trust Play": "◈", "Paid Blitz": "✦"}

PHASE_LABELS: tuple[str, ...] = (
    "Brief", "Plans", "Debate", "Refine", "Score", "Verdict", "Ship",
)

# ── Stylesheet (plain string — no f-string, so no brace-escaping) ────────────────
_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link href="https://fonts.googleapis.com/css2?'
    'family=Fraunces:ital,opsz,wght@0,9..144,300..900;1,9..144,300..900'
    '&family=Inter:wght@300;400;500;600;700;800'
    '&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">'
)

_CSS = """
:root{
  --bg-0:#070809; --bg-1:#0e1015; --bg-2:#15181f; --bg-3:#1f232d;
  --line:#272d39; --line-soft:#1b212c;
  --ink-0:#f4f6fb; --ink-1:#aab3c4; --ink-2:#717b8c; --ink-3:#3d4554;
  --gold:#f6c652; --gold-soft:#ffe7a6; --mint:#54e0b0;
  --shadow: 0 24px 60px -34px rgba(0,0,0,0.75);
}

/* ── Streamlit canvas overrides ─────────────────────────────────────────── */
.stApp{
  background:
    radial-gradient(60rem 40rem at 82% -8%, rgba(93,139,255,0.07), transparent 60%),
    radial-gradient(70rem 46rem at 12% -12%, rgba(246,198,82,0.06), transparent 55%),
    var(--bg-0) fixed;
}
.block-container{ padding-top:1.4rem !important; padding-bottom:5rem !important; max-width:1200px; }
html, body, [class^="st-"], [class*=" st-"], .stMarkdown, .stCaption, p, span, div, button, input, textarea{
  font-family:'Inter', system-ui, -apple-system, sans-serif !important;
  color:var(--ink-0); -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale;
}
h1,h2,h3,h4{ font-family:'Fraunces','Inter',serif !important; letter-spacing:-0.02em; color:var(--ink-0); }
::selection{ background:rgba(246,198,82,0.28); }
section[data-testid="stSidebar"]{ background:linear-gradient(180deg,#0b0e13,#080a0e); border-right:1px solid var(--line-soft); }
section[data-testid="stSidebar"] *{ font-family:'Inter',sans-serif !important; }
hr{ border-color:var(--line-soft) !important; }

/* ── Hero ──────────────────────────────────────────────────────────────── */
.gw-hero{ margin:0.2rem 0 1.9rem; padding:1.4rem 0 1.6rem; border-bottom:1px solid var(--line); position:relative; }
.gw-hero::after{
  content:""; position:absolute; left:0; bottom:-1px; height:2px; width:96px;
  background:linear-gradient(90deg,var(--gold),transparent); border-radius:2px;
}
.gw-eyebrow{
  text-transform:uppercase; letter-spacing:0.34em; font-size:0.66rem;
  color:var(--ink-2); font-weight:700; margin-bottom:0.8rem;
}
.gw-eyebrow .dot{
  display:inline-block; width:6px; height:6px; background:var(--mint); border-radius:999px;
  vertical-align:middle; margin:0 0.6em 2px 0; box-shadow:0 0 10px var(--mint);
  animation:gw-pulse 2s ease-in-out infinite;
}
@keyframes gw-pulse{ 0%,100%{ opacity:0.55; transform:scale(0.9);} 50%{ opacity:1; transform:scale(1);} }
.gw-title{
  font-family:'Fraunces',serif; font-weight:500; font-size:4rem; line-height:0.98;
  font-variation-settings:'opsz' 144; letter-spacing:-0.045em; margin:0 0 0.7rem;
}
.gw-title em{ font-style:italic; color:var(--gold); font-weight:400; }
.gw-tag{ color:var(--ink-1); font-size:1.04rem; max-width:720px; line-height:1.55; }
.gw-tag b{ color:var(--ink-0); font-weight:600; }
.gw-stats{ display:flex; flex-wrap:wrap; gap:0.5rem; margin-top:1.2rem; }
.gw-chip{
  display:inline-flex; align-items:center; gap:0.5rem; padding:0.36rem 0.8rem;
  border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,0.015);
  font-size:0.74rem; color:var(--ink-1); font-weight:500;
}
.gw-chip b{ color:var(--ink-0); font-weight:700; }
.gw-chip .led{ width:5px; height:5px; border-radius:999px; background:var(--gold); box-shadow:0 0 8px var(--gold); }

/* ── Phase rail (progress stepper) ─────────────────────────────────────── */
.gw-rail{
  position:sticky; top:0.4rem; z-index:50; margin-bottom:1.7rem;
  padding:0.95rem 1.3rem; border:1px solid var(--line); border-radius:16px;
  background:linear-gradient(180deg, rgba(20,24,32,0.92), rgba(13,16,22,0.92));
  backdrop-filter:blur(10px); box-shadow:var(--shadow);
}
.gw-track{ position:relative; display:flex; align-items:center; justify-content:space-between; }
.gw-track::before{
  content:""; position:absolute; left:11px; right:11px; top:11px; height:2px; background:var(--line);
}
.gw-track::after{
  content:""; position:absolute; left:11px; top:11px; height:2px; width:var(--progress,0%);
  background:linear-gradient(90deg,var(--mint),var(--gold)); border-radius:2px;
  transition:width 0.6s cubic-bezier(.2,.7,.2,1);
}
.gw-step{ position:relative; z-index:1; display:flex; flex-direction:column; align-items:center; gap:0.45rem; flex:1; }
.gw-step .num{
  display:inline-flex; align-items:center; justify-content:center; width:24px; height:24px;
  border-radius:999px; border:1px solid var(--line); background:var(--bg-0);
  font-size:0.72rem; font-weight:700; font-variant-numeric:tabular-nums; color:var(--ink-2);
  transition:all 0.3s ease;
}
.gw-step .lab{ font-size:0.72rem; font-weight:500; color:var(--ink-2); letter-spacing:0.01em; }
.gw-step.done .num{ background:var(--mint); color:#04221b; border-color:var(--mint); }
.gw-step.done .lab{ color:var(--ink-1); }
.gw-step.active .num{ background:var(--gold); color:#2a200a; border-color:var(--gold); box-shadow:0 0 0 5px rgba(246,198,82,0.14); }
.gw-step.active .lab{ color:var(--ink-0); font-weight:700; }

/* ── Brief strip ───────────────────────────────────────────────────────── */
.gw-brief{
  display:flex; flex-wrap:wrap; gap:0.7rem 2rem; align-items:center;
  padding:1.05rem 1.3rem; border:1px solid var(--line); border-left:3px solid var(--gold);
  border-radius:14px; background:linear-gradient(180deg,var(--bg-1),var(--bg-2)); margin-bottom:1.9rem;
  box-shadow:var(--shadow);
}
.gw-brief .field{ display:flex; flex-direction:column; gap:3px; }
.gw-brief .k{ font-size:0.62rem; text-transform:uppercase; letter-spacing:0.18em; color:var(--ink-2); font-weight:700; }
.gw-brief .v{ font-size:0.96rem; color:var(--ink-0); font-weight:500; }

/* ── Section header (editorial rules) ──────────────────────────────────── */
.gw-section{ margin:2.6rem 0 1.1rem; display:flex; align-items:baseline; gap:1rem; }
.gw-section .num{
  font-family:'JetBrains Mono',monospace; font-weight:500; font-size:0.8rem; color:var(--gold);
  font-variant-numeric:tabular-nums; letter-spacing:0.04em;
}
.gw-section h2{ margin:0; font-size:1.85rem; font-weight:500; font-style:italic; font-variation-settings:'opsz' 96; }
.gw-section .rule{ flex:1; height:1px; background:linear-gradient(90deg,var(--line),transparent); margin-top:14px; }

/* ── Plan cards (the arena) ────────────────────────────────────────────── */
.gw-arena{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; }
.gw-card{
  position:relative; border:1px solid var(--line); border-radius:18px; padding:1.3rem 1.3rem 1.1rem;
  background:linear-gradient(180deg,var(--bg-1),var(--bg-2));
  transition:transform 0.4s ease, box-shadow 0.4s ease, border-color 0.4s ease; overflow:hidden;
  box-shadow:var(--shadow);
}
.gw-card::before{ content:""; position:absolute; inset:0 0 auto 0; height:3px; background:var(--accent); opacity:0.9; }
.gw-card::after{
  content:""; position:absolute; inset:0; pointer-events:none; opacity:0.5;
  background:radial-gradient(40rem 12rem at 50% -8rem, color-mix(in srgb, var(--accent) 16%, transparent), transparent 70%);
}
.gw-card:hover{ transform:translateY(-4px); border-color:color-mix(in srgb, var(--accent) 32%, var(--line)); }
.gw-card.win{
  border-color:var(--gold);
  box-shadow:0 0 0 1px var(--gold), 0 0 70px -12px rgba(246,198,82,0.5), var(--shadow);
  animation:gw-crown 3.6s ease-in-out infinite;
}
.gw-card.win::before{ background:var(--gold); height:4px; }
@keyframes gw-crown{
  0%,100%{ box-shadow:0 0 0 1px var(--gold), 0 0 56px -14px rgba(246,198,82,0.4), var(--shadow); }
  50%{ box-shadow:0 0 0 1px var(--gold), 0 0 84px -8px rgba(246,198,82,0.62), var(--shadow); }
}
.gw-card .head{ display:flex; align-items:flex-start; justify-content:space-between; gap:10px; margin-bottom:0.8rem; }
.gw-card .arc{ display:inline-flex; align-items:center; gap:0.5rem; font-weight:700; font-size:1.04rem; color:var(--accent); letter-spacing:-0.01em; }
.gw-card .arc .glyph{ font-size:1.25rem; opacity:0.9; }
.gw-card .author{ font-size:0.72rem; color:var(--ink-2); font-family:'JetBrains Mono',monospace; margin-top:0.3rem; }
.gw-card .total{ font-family:'Fraunces',serif; font-size:1.7rem; font-weight:500; font-variation-settings:'opsz' 144; line-height:1; text-align:right; }
.gw-card .total .of{ color:var(--ink-3); font-size:0.82rem; margin-left:2px; }
.gw-card .summary{ color:var(--ink-1); font-size:0.9rem; line-height:1.55; min-height:4.6em; margin-bottom:0.85rem; }
.gw-card .meta{ font-size:0.73rem; color:var(--ink-2); margin-top:0.5rem; font-family:'JetBrains Mono',monospace; line-height:1.5; }

.gw-pill{
  display:inline-block; font-size:0.58rem; font-weight:800; padding:3px 9px; border-radius:999px;
  letter-spacing:0.1em; text-transform:uppercase; vertical-align:middle; margin-left:6px;
}
.gw-pill.win{ background:var(--gold); color:#1a1408; }
.gw-pill.bad{ background:rgba(255,80,90,0.12); color:#ff8a92; border:1px solid rgba(255,80,90,0.35); }
.gw-pill.refined{ background:rgba(84,224,176,0.12); color:var(--mint); border:1px solid rgba(84,224,176,0.35); }

/* ── Score bars (animated reveal) ──────────────────────────────────────── */
.gw-bars{ margin-top:0.7rem; display:flex; flex-direction:column; gap:0.5rem; }
.gw-bar{ display:flex; flex-direction:column; gap:5px; }
.gw-bar .row{ display:flex; justify-content:space-between; font-size:0.69rem; color:var(--ink-2); font-family:'JetBrains Mono',monospace; text-transform:uppercase; letter-spacing:0.06em; }
.gw-bar .track{ height:7px; background:var(--bg-3); border-radius:999px; overflow:hidden; }
.gw-bar .fill{
  height:100%; border-radius:999px; background:linear-gradient(90deg, color-mix(in srgb,var(--accent) 70%, #fff 0%), var(--accent));
  width:0; animation:gw-fill 1.1s cubic-bezier(.2,.7,.2,1) forwards; box-shadow:0 0 10px -2px var(--accent);
}
@keyframes gw-fill{ to{ width:var(--target); } }

/* ── The Band room (chat replay) ───────────────────────────────────────── */
.gw-room{ border:1px solid var(--line); border-radius:20px; background:linear-gradient(180deg,var(--bg-1),#0c0e13); padding:1.5rem 1.6rem 1.3rem; box-shadow:var(--shadow); }
.gw-room .roomhead{ display:flex; align-items:center; justify-content:space-between; padding-bottom:1rem; margin-bottom:1.1rem; border-bottom:1px dashed var(--line); }
.gw-room .roomtitle{ font-family:'Fraunces',serif; font-style:italic; font-size:1.1rem; color:var(--ink-1); }
.gw-room .roomtag{ font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:var(--ink-2); padding:0.25rem 0.6rem; border:1px solid var(--line); border-radius:999px; }

.gw-msg{ display:grid; grid-template-columns:38px 1fr; gap:0.9rem; margin:0.7rem 0; opacity:0; transform:translateY(8px); animation:gw-enter 0.5s ease-out forwards; }
@keyframes gw-enter{ to{ opacity:1; transform:translateY(0); } }
.gw-av{
  width:38px; height:38px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  font-family:'Fraunces',serif; font-style:italic; font-size:1.05rem; font-weight:600;
  background:var(--bg-3); color:var(--ink-0); border:1px solid var(--line);
}
.gw-av[data-role="A"]{ background:color-mix(in srgb,var(--r-go-viral) 18%, var(--bg-3)); border-color:color-mix(in srgb,var(--r-go-viral) 42%, var(--line)); color:var(--r-go-viral); }
.gw-av[data-role="B"]{ background:color-mix(in srgb,var(--r-trust-play) 18%, var(--bg-3)); border-color:color-mix(in srgb,var(--r-trust-play) 42%, var(--line)); color:var(--r-trust-play); }
.gw-av[data-role="C"]{ background:color-mix(in srgb,var(--r-paid-blitz) 18%, var(--bg-3)); border-color:color-mix(in srgb,var(--r-paid-blitz) 42%, var(--line)); color:var(--r-paid-blitz); }
.gw-av[data-role="K"]{ background:rgba(246,198,82,0.15); border-color:rgba(246,198,82,0.44); color:var(--gold); }
.gw-av[data-role="S"]{ background:rgba(84,224,176,0.15); border-color:rgba(84,224,176,0.42); color:var(--mint); }
.gw-bubble{ display:flex; flex-direction:column; gap:5px; min-width:0; }
.gw-who{ display:flex; align-items:center; gap:0.55rem; font-size:0.78rem; color:var(--ink-1); flex-wrap:wrap; }
.gw-who b{ font-weight:700; color:var(--ink-0); }
.gw-who .tag{ font-size:0.6rem; padding:2px 7px; border-radius:5px; background:var(--bg-3); color:var(--ink-2); letter-spacing:0.08em; text-transform:uppercase; font-family:'JetBrains Mono',monospace; }
.gw-who .target{ font-family:'JetBrains Mono',monospace; color:var(--ink-2); font-size:0.72rem; }
.gw-body{
  font-size:0.92rem; line-height:1.55; color:var(--ink-0);
  background:var(--bg-2); border:1px solid var(--line-soft); border-radius:14px;
  padding:0.75rem 1rem; white-space:pre-wrap; word-wrap:break-word;
}
.gw-msg[data-kind="critique"] .gw-body{ border-left:3px solid #ff6b75; }
.gw-msg[data-kind="rebuttal"] .gw-body{ border-left:3px solid var(--mint); background:linear-gradient(180deg,var(--bg-2),#111821); }
.gw-msg[data-kind="v2"] .gw-body{ border-left:3px solid var(--mint); }
.gw-msg[data-kind="verdict"] .gw-body{ border:1px solid rgba(246,198,82,0.4); background:linear-gradient(180deg,#1a1610,#0f0e08); }
.gw-msg[data-kind="seal"] .gw-body{ font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--mint); border:1px solid rgba(84,224,176,0.35); background:rgba(84,224,176,0.05); }

.gw-divider{ display:flex; align-items:center; gap:0.8rem; margin:1.5rem 0 1.1rem; text-transform:uppercase; letter-spacing:0.24em; font-size:0.64rem; color:var(--ink-2); font-weight:700; }
.gw-divider::before, .gw-divider::after{ content:""; flex:1; height:1px; background:var(--line); }

/* ── Verdict ───────────────────────────────────────────────────────────── */
.gw-verdict{ border:1px solid var(--line); border-radius:20px; padding:1.7rem 1.9rem; background:linear-gradient(135deg,var(--bg-1),var(--bg-2)); margin-top:1rem; position:relative; overflow:hidden; box-shadow:var(--shadow); }
.gw-verdict::after{ content:""; position:absolute; inset:0; pointer-events:none; background:radial-gradient(50rem 16rem at 100% 0, color-mix(in srgb,var(--accent) 12%, transparent), transparent 60%); }
.gw-verdict .who{ display:flex; align-items:baseline; gap:0.9rem; margin-bottom:0.7rem; position:relative; }
.gw-verdict .label{ font-size:0.64rem; text-transform:uppercase; letter-spacing:0.26em; color:var(--ink-2); font-weight:700; }
.gw-verdict .arc{ font-family:'Fraunces',serif; font-style:italic; font-weight:500; font-size:2.2rem; color:var(--accent); font-variation-settings:'opsz' 144; }
.gw-verdict .total{ font-family:'JetBrains Mono',monospace; font-size:0.85rem; color:var(--ink-1); margin-left:auto; }
.gw-verdict .total b{ color:var(--ink-0); font-size:1.5rem; font-weight:500; }
.gw-verdict .body{ color:var(--ink-1); font-size:0.97rem; line-height:1.6; white-space:pre-wrap; position:relative; }
.gw-verdict .hash{ margin-top:1.3rem; padding-top:1.1rem; border-top:1px dashed var(--line); display:flex; flex-direction:column; gap:0.35rem; position:relative; }
.gw-verdict .hash .k{ font-size:0.6rem; text-transform:uppercase; letter-spacing:0.22em; color:var(--ink-2); font-weight:700; }
.gw-verdict .hash .v{ font-family:'JetBrains Mono',monospace; font-size:0.78rem; color:var(--mint); word-break:break-all; line-height:1.5; }
.gw-verdict .hash .approver{ font-size:0.78rem; color:var(--ink-1); margin-top:0.25rem; }
.gw-verdict .hash .approver b{ color:var(--gold); }

/* ── Streamlit widget polish ───────────────────────────────────────────── */
.stButton > button{ border-radius:11px !important; font-weight:600 !important; transition:transform 0.15s ease, filter 0.15s ease !important; }
.stButton > button:hover:not(:disabled){ transform:translateY(-1px); filter:brightness(1.05); }
button[kind="primary"]{ background:linear-gradient(180deg,var(--gold-soft),var(--gold)) !important; color:#1a1408 !important; border:1px solid var(--gold) !important; font-weight:700 !important; box-shadow:0 8px 24px -12px rgba(246,198,82,0.6) !important; }
button[kind="primary"]:disabled{ background:var(--bg-2) !important; color:var(--ink-3) !important; border:1px dashed var(--line) !important; box-shadow:none !important; opacity:1 !important; }
button[kind="secondary"]{ background:var(--bg-2) !important; color:var(--ink-0) !important; border:1px solid var(--line) !important; }
.stTabs [data-baseweb="tab-list"]{ gap:0; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ background:transparent !important; padding:0.6rem 1.2rem !important; color:var(--ink-2) !important; }
.stTabs [aria-selected="true"]{ color:var(--ink-0) !important; border-bottom:2px solid var(--gold) !important; }
.stExpander{ border:1px solid var(--line-soft) !important; border-radius:14px !important; background:var(--bg-1) !important; }
.stTextInput input, .stNumberInput input, .stTextArea textarea{ background:var(--bg-2) !important; border:1px solid var(--line) !important; border-radius:10px !important; color:var(--ink-0) !important; }
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus{ border-color:var(--gold) !important; box-shadow:0 0 0 3px rgba(246,198,82,0.12) !important; }
"""


# ── Theme injection ──────────────────────────────────────────────────────────────
def inject_theme() -> str:
    """One-shot CSS + Google Fonts. Render once at the top of the page.

    All component styles live in `_CSS`; the three archetype accents are injected as
    CSS variables so the colour system stays sourced from `ARCHETYPE_ACCENT`.
    """
    accents = (
        ":root{"
        f"--r-go-viral:{ARCHETYPE_ACCENT['Go Viral']};"
        f"--r-trust-play:{ARCHETYPE_ACCENT['Trust Play']};"
        f"--r-paid-blitz:{ARCHETYPE_ACCENT['Paid Blitz']};"
        "}"
    )
    return f"{_FONTS}<style>{accents}{_CSS}</style>"


# ── Hero ────────────────────────────────────────────────────────────────────────
def hero(*, mode: str) -> str:
    chips = (
        '<div class="gw-stats">'
        '<span class="gw-chip"><span class="led"></span><b>5</b>&nbsp;agents</span>'
        '<span class="gw-chip"><b>3</b>&nbsp;runtimes</span>'
        '<span class="gw-chip"><b>1</b>&nbsp;Band room</span>'
        '<span class="gw-chip">human&nbsp;<b>sign-off</b></span>'
        '</div>'
    )
    return f"""
<div class="gw-hero">
  <div class="gw-eyebrow"><span class="dot"></span>{html.escape(mode)} · Band of Agents Hackathon</div>
  <h1 class="gw-title">Gauntlet <em>War</em></h1>
  <div class="gw-tag">Three strategist agents draft <b>competing marketing plans</b>, attack each other's numbers inside a Band room, and <b>publish a v2 that fixes the critiques</b>. An independent scorer ranks them, a human seals the verdict, and the winner drops out as ship-ready copy.</div>
  {chips}
</div>
"""


# ── Phase rail ──────────────────────────────────────────────────────────────────
def phase_rail(stage: int) -> str:
    n = len(PHASE_LABELS)
    # Fill the connecting line up to the current step.
    progress = 0.0 if n <= 1 else max(0.0, min(1.0, (stage - 1) / (n - 1))) * 100
    parts = []
    for i, label in enumerate(PHASE_LABELS, 1):
        cls = "done" if i < stage else ("active" if i == stage else "")
        parts.append(
            f'<div class="gw-step {cls}"><span class="num">{i}</span>'
            f'<span class="lab">{html.escape(label)}</span></div>'
        )
    return (
        f'<div class="gw-rail"><div class="gw-track" style="--progress:{progress:.1f}%">'
        f'{"".join(parts)}</div></div>'
    )


# ── Brief strip ─────────────────────────────────────────────────────────────────
def brief_strip(brief: dict) -> str:
    constraints = ", ".join(brief.get("constraints") or []) or "—"
    fields = [
        ("Product", brief.get("product", "—")),
        ("Goal", brief.get("goal", "—")),
        ("Budget", f"${(brief.get('budget_ceiling') or 0):,.0f}"),
        ("Constraints", constraints),
    ]
    body = "".join(
        f'<div class="field"><div class="k">{k}</div><div class="v">{html.escape(str(v))}</div></div>'
        for k, v in fields
    )
    return f'<div class="gw-brief">{body}</div>'


# ── Section header (editorial) ──────────────────────────────────────────────────
def section(num: str, title: str) -> str:
    return (
        f'<div class="gw-section"><div class="num">{html.escape(num)}</div>'
        f'<h2>{html.escape(title)}</h2><div class="rule"></div></div>'
    )


# ── The arena (plan cards) ─────────────────────────────────────────────────────
_DIM_LABELS = {
    "reach": "reach", "cost_efficiency": "cost", "speed": "speed",
    "risk": "risk", "durability": "durability",
}


def _score_bars(dims: dict, delay_base: float = 0.15) -> str:
    parts: list[str] = []
    for i, (k, v) in enumerate(dims.items()):
        label = _DIM_LABELS.get(k, k)
        pct = max(2, min(100, int(v) * 10))
        parts.append(
            f'<div class="gw-bar">'
            f'<div class="row"><span>{label}</span><span>{v}/10</span></div>'
            f'<div class="track"><div class="fill" style="--target:{pct}%; animation-delay:{delay_base + i*0.07:.2f}s"></div></div>'
            f'</div>'
        )
    return f'<div class="gw-bars">{"".join(parts)}</div>'


def arena(
    strategies: list[dict],
    scores_by_id: dict[str, dict],
    *,
    winner_id: str | None,
    show_scores: bool,
    show_winner: bool,
    show_refined_badge: bool,
) -> str:
    cards: list[str] = []
    for s in strategies:
        archetype = s["archetype"]
        accent = ARCHETYPE_ACCENT.get(archetype, "#888")
        glyph = ARCHETYPE_GLYPH.get(archetype, "·")
        is_win = show_winner and s["strategy_id"] == winner_id
        sc = scores_by_id.get(s["strategy_id"])
        pills = ""
        if is_win:
            pills += '<span class="gw-pill win">Winner</span>'
        if show_refined_badge:
            pills += '<span class="gw-pill refined">Refined v2</span>'
        if not s.get("feasible", True):
            pills += '<span class="gw-pill bad">Not feasible</span>'

        total_html = ""
        if sc and show_scores:
            total_html = (
                f'<div class="total">{sc["total"]:.2f}<span class="of">/10</span></div>'
            )

        bars_html = _score_bars(sc["dimensions"]) if (sc and show_scores) else ""

        meta_bits = []
        if s.get("funnel_math"):
            meta_bits.append(f"funnel · {html.escape(str(s['funnel_math']))}")
        if s.get("projected_result"):
            meta_bits.append(f"projection · {html.escape(str(s['projected_result']))}")
        meta_html = (
            f'<div class="meta">{"<br>".join(meta_bits)}</div>' if meta_bits else ""
        )

        cards.append(
            f'<div class="gw-card {"win" if is_win else ""}" style="--accent:{accent}">'
            f'  <div class="head">'
            f'    <div><div class="arc"><span class="glyph">{glyph}</span>{html.escape(archetype)}{pills}</div>'
            f'      <div class="author">{html.escape(s.get("author", ""))}</div>'
            f'    </div>'
            f'    {total_html}'
            f'  </div>'
            f'  <div class="summary">{html.escape(s.get("summary", ""))}</div>'
            f'  {bars_html}'
            f'  {meta_html}'
            f'</div>'
        )
    return f'<div class="gw-arena">{"".join(cards)}</div>'


# ── The Band room (chat replay) ────────────────────────────────────────────────
_ROLE_LETTER = {
    "@StrategistA": "A", "@StrategistB": "B", "@StrategistC": "C",
    "@Scorer": "S", "@Conductor": "K", "@Human": "H",
}


def _avatar(author: str) -> str:
    """Return the avatar tile for an author label."""
    role = _ROLE_LETTER.get(author, "·")
    initial = author.lstrip("@")[:1].upper() if author else "·"
    return f'<div class="gw-av" data-role="{role}">{html.escape(initial)}</div>'


def _msg(
    author: str,
    body: str,
    *,
    kind: str = "say",
    target: str | None = None,
    tag: str | None = None,
    delay: float = 0.0,
) -> str:
    target_html = f' <span class="target">→ {html.escape(target)}</span>' if target else ""
    tag_html = f' <span class="tag">{html.escape(tag)}</span>' if tag else ""
    return (
        f'<div class="gw-msg" data-kind="{kind}" style="animation-delay:{delay:.2f}s">'
        f'  {_avatar(author)}'
        f'  <div class="gw-bubble">'
        f'    <div class="gw-who"><b>{html.escape(author)}</b>{tag_html}{target_html}</div>'
        f'    <div class="gw-body">{html.escape(body)}</div>'
        f'  </div>'
        f'</div>'
    )


def _short_id(sid: str) -> str:
    return sid.split("-", 1)[1][:8] if "-" in sid else sid[:8]


def room(bundle: dict, *, stage: int, sealed_hash: str | None, approver: str | None) -> str:
    """Render the Band room as a chat thread. Each message fades in with a stagger.
    `stage` (1..7) controls how far through the playback we are."""
    brief = bundle.get("brief") or {}
    strategies = bundle.get("strategies") or []
    strategies_v1 = bundle.get("strategies_v1") or []  # may be empty for older runs
    debate = bundle.get("debate") or []
    recommendation = bundle.get("recommendation") or ""
    arch_of = {s["strategy_id"]: s["archetype"] for s in strategies}

    msgs: list[str] = []
    d = 0.0
    step = 0.10  # stagger between bubbles

    # 1. Brief
    msgs.append(_msg(
        "@Conductor",
        f"Brief posted. {brief.get('product','—')} · {brief.get('goal','—')} · "
        f"budget ceiling ${brief.get('budget_ceiling',0):,.0f}. Strategists, author your plans.",
        kind="say", tag="brief", delay=d,
    ))
    d += step

    # 2. v1 plans (if we have them; otherwise the bundle's current strategies are v2 only)
    if stage >= 2:
        source = strategies_v1 if strategies_v1 else strategies
        v1_label = "v1" if strategies_v1 else "plan"
        for s in source:
            msgs.append(_msg(
                s.get("author", ""),
                f"{s.get('archetype')} {v1_label} — {s.get('summary','')}",
                kind="say", tag=v1_label, delay=d,
            ))
            d += step

    # 3. Debate
    if stage >= 3 and debate:
        msgs.append(f'<div class="gw-divider">The debate · {len(debate)} cross-pair exchanges</div>')
        for entry in debate:
            c = entry["critique"]
            target_label = f"plan {_short_id(c['target_strategy_id'])}"
            sev = c.get("severity", 3)
            tag = f"critique · sev {sev}"
            msgs.append(_msg(
                c.get("author", ""), c.get("claim", ""),
                kind="critique", target=target_label, tag=tag, delay=d,
            ))
            d += step
            defender_label = next(
                (s["author"] for s in strategies if s["strategy_id"] == c["target_strategy_id"]),
                "@Defender",
            )
            msgs.append(_msg(
                defender_label, entry.get("rebuttal", ""),
                kind="rebuttal", target=c.get("author"), tag="rebuttal", delay=d,
            ))
            d += step

    # 4. v2 plans — show as refinement messages, only if v1 was captured (so v2 is a real delta)
    if stage >= 4 and strategies_v1:
        msgs.append('<div class="gw-divider">Self-improvement · v2 published</div>')
        for s in strategies:
            msgs.append(_msg(
                s.get("author", ""),
                f"Revised v2: {s.get('summary','')}",
                kind="v2", tag="refined", delay=d,
            ))
            d += step

    # 5. Scores
    if stage >= 5:
        scores = bundle.get("scores") or []
        if scores:
            ranked = sorted(scores, key=lambda x: -x["total"])
            lines = []
            for i, sc in enumerate(ranked, 1):
                arc = arch_of.get(sc["strategy_id"], "?")
                lines.append(f"{i}. {arc} — {sc['total']:.2f}")
            msgs.append(_msg(
                "@Scorer", "\n".join(lines),
                kind="say", tag="ranked", delay=d,
            ))
            d += step

    # 6. Verdict (Conductor synthesis)
    if stage >= 6 and recommendation:
        msgs.append(_msg(
            "@Conductor", recommendation,
            kind="verdict", tag="verdict", delay=d,
        ))
        d += step

    # 7. Seal
    if stage >= 6 and sealed_hash:
        seal_line = (
            f"DECISION SEALED" + (f" by {approver}" if approver else "")
            + f". Tamper-evident SHA-256: {sealed_hash}"
        )
        msgs.append(_msg("@Conductor", seal_line, kind="seal", tag="sealed", delay=d))

    room_id = bundle.get("room_id", "")
    return (
        f'<div class="gw-room">'
        f'  <div class="roomhead">'
        f'    <div class="roomtitle">Gauntlet War · the Band room</div>'
        f'    <div class="roomtag">room {html.escape(_short_id(room_id))}</div>'
        f'  </div>'
        + "".join(msgs)
        + '</div>'
    )


# ── Verdict block ──────────────────────────────────────────────────────────────
def verdict(bundle: dict, *, sealed_hash: str | None, approver: str | None) -> str:
    winner_id = bundle.get("winner_id")
    strategies = bundle.get("strategies") or []
    scores = {s["strategy_id"]: s for s in (bundle.get("scores") or [])}
    winner = next((s for s in strategies if s["strategy_id"] == winner_id), None)
    if not winner:
        return ""
    accent = ARCHETYPE_ACCENT.get(winner["archetype"], "#888")
    total = scores.get(winner_id, {}).get("total")
    rec = bundle.get("recommendation") or ""

    total_html = (
        f'<div class="total"><b>{total:.2f}</b> &nbsp;weighted</div>' if total is not None else ""
    )
    hash_html = ""
    if sealed_hash:
        approver_html = (
            f'<div class="approver">sealed by <b>{html.escape(approver or "—")}</b></div>'
            if approver else ""
        )
        hash_html = (
            f'<div class="hash"><div class="k">tamper-evident sha-256</div>'
            f'<div class="v">{html.escape(sealed_hash)}</div>{approver_html}</div>'
        )

    return (
        f'<div class="gw-verdict" style="--accent:{accent}">'
        f'  <div class="who">'
        f'    <div class="label">Winner</div>'
        f'    <div class="arc">{html.escape(winner["archetype"])}</div>'
        f'    {total_html}'
        f'  </div>'
        f'  <div class="body">{html.escape(rec)}</div>'
        f'  {hash_html}'
        f'</div>'
    )


# ── Helpers exported for app.py ────────────────────────────────────────────────
def archetype_for(strategy_id: str, strategies: Iterable[dict]) -> str:
    return next((s["archetype"] for s in strategies if s["strategy_id"] == strategy_id), "—")
