"""Offline demo data — replay a sealed showdown with ZERO API calls.

A sealed run holds the full bundle (brief, competing strategies, debate, scores, recommendation,
human decision) plus its deliverable markdown. Together that's everything the UI needs to render a
complete, real run — so judges (and you, on a dead key) can click through the whole experience for
free, with no credentials or quota.

Two sources, merged (samples win on id collision):
  • samples/<room>/   — committed, self-contained demo runs (record.json + *.md). Survive a clone.
  • audit/<room>.json + deliverables/<room>/  — runs you generate locally (gitignored).
"""
from __future__ import annotations

import json
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = _ROOT / "audit"
DELIVERABLES_DIR = _ROOT / "deliverables"
SAMPLES_DIR = _ROOT / "samples"

_DELIVERABLE_FILES = {
    "execution_plan": "execution_plan.md",
    "proposal": "proposal.md",
    "content_kit": "content_kit.md",
}


def winner_id(record: dict) -> str | None:
    """The human-chosen winner, falling back to the top-scored plan."""
    decision = record.get("decision") or {}
    if decision.get("chosen_strategy_id"):
        return decision["chosen_strategy_id"]
    scores = record.get("scores") or []
    if scores:
        return max(scores, key=lambda s: s.get("total", 0))["strategy_id"]
    strategies = record.get("strategies") or []
    return strategies[0]["strategy_id"] if strategies else None


def _sources() -> dict[str, tuple[Path, Path]]:
    """room_id -> (record.json path, deliverables dir). Samples take precedence."""
    out: dict[str, tuple[Path, Path]] = {}
    for j in AUDIT_DIR.glob("*.json"):
        out[j.stem] = (j, DELIVERABLES_DIR / j.stem)
    if SAMPLES_DIR.exists():
        for d in SAMPLES_DIR.iterdir():
            rec = d / "record.json"
            if d.is_dir() and rec.exists():
                out[d.name] = (rec, d)  # samples override live audit on the same id
    return out


def list_runs() -> list[dict]:
    """Every replayable run, newest first: {room_id, product, sealed_at}."""
    runs = []
    for room_id, (rec_path, _) in _sources().items():
        try:
            rec = json.loads(rec_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        runs.append({
            "room_id": rec.get("room_id", room_id),
            "product": (rec.get("brief") or {}).get("product", room_id),
            "sealed_at": rec.get("sealed_at", ""),
        })
    return sorted(runs, key=lambda r: r["sealed_at"], reverse=True)


def load_bundle(room_id: str) -> dict:
    """Load a sealed record as a UI bundle (same shape conductor.run() returns), with winner_id."""
    rec_path, _ = _sources()[room_id]
    rec = json.loads(rec_path.read_text(encoding="utf-8"))
    rec["winner_id"] = winner_id(rec)
    return rec


def load_artifacts(room_id: str) -> dict:
    """Read the generated deliverable markdown for a run, if present. Missing files are skipped."""
    _, out_dir = _sources()[room_id]
    artifacts: dict = {}
    for key, fname in _DELIVERABLE_FILES.items():
        f = out_dir / fname
        if f.exists():
            artifacts[key] = f.read_text(encoding="utf-8")
    if artifacts:
        artifacts["dir"] = str(out_dir)
    return artifacts


def has_demo_data() -> bool:
    return bool(_sources())
