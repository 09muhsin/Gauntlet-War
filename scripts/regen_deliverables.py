"""Regenerate deliverables for an already-sealed decision — no Band run required.

The audit record holds the full bundle (brief, the competing strategies, scores, the human's
decision). That's everything the deliverable writers need, so we can re-render the proposal,
execution plan, and content kit with the upgraded copy engine and overwrite the markdown files.

Usage:
    python -m scripts.regen_deliverables <room_id|audit_file>     # regenerate one
    python -m scripts.regen_deliverables --all                    # every sealed record
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from src.agents.conductor import DELIVERABLES_DIR
from src.build import build_conductor
from src.config import load_settings
from src.schemas import Brief, Strategy

AUDIT_DIR = Path(__file__).resolve().parents[1] / "audit"


def _winner_id(record: dict) -> str:
    decision = record.get("decision") or {}
    if decision.get("chosen_strategy_id"):
        return decision["chosen_strategy_id"]
    scores = record.get("scores") or []
    if scores:  # fall back to the top-scored plan
        return max(scores, key=lambda s: s.get("total", 0))["strategy_id"]
    return record["strategies"][0]["strategy_id"]


def regen_one(audit_path: Path, conductor) -> Path:
    record = json.loads(audit_path.read_text(encoding="utf-8"))
    room_id = record["room_id"]
    brief = Brief(**record["brief"])
    winner_id = _winner_id(record)
    winner = Strategy(**next(s for s in record["strategies"] if s["strategy_id"] == winner_id))
    strategist = next(s for s in conductor._strategists if s.label == winner.author)
    bundle = {**record, "winner_id": winner_id}

    print(f"[{room_id}] {winner.author} / {winner.archetype.value} — regenerating...")
    artifacts = {
        "proposal": conductor._proposal(brief, winner, bundle),
        "execution_plan": strategist.execution_plan(brief, winner),
        "content_kit": strategist.content_kit(brief, winner),
    }

    out_dir = DELIVERABLES_DIR / room_id
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, text in artifacts.items():
        (out_dir / f"{name}.md").write_text(text, encoding="utf-8")
        print(f"    wrote {name}.md ({len(text):,} chars)")
    return out_dir


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    conductor = build_conductor(load_settings())

    if argv[0] == "--all":
        records = sorted(AUDIT_DIR.glob("*.json"))
    else:
        arg = argv[0]
        p = Path(arg)
        records = [p if p.exists() else AUDIT_DIR / f"{arg}.json"]

    for path in records:
        if not path.exists():
            print(f"!! no audit record at {path}")
            continue
        regen_one(path, conductor)
    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
