"""Run Act 0 end to end from the CLI (the demo scenario, PRD §8).

    python run_act0.py

Wires the five agents, runs author -> debate -> score -> synthesize, prints the bundle,
and stops at the human gate (approval happens in the Streamlit app).
"""
from __future__ import annotations

import json
import sys

from src.build import build_conductor
from src.config import load_settings
from src.schemas import Brief

# PRD §8 demo brief — one product, end to end.
DEMO_BRIEF = Brief(
    product="$120 premium running shoe",
    goal="1,000 first-month orders",
    budget_ceiling=15000,
    constraints=["DTC only", "30-day launch window"],
)


def main() -> None:
    settings = load_settings()
    missing = settings.missing_agents()
    if missing:
        print(f"⚠️  Missing Band credentials for: {', '.join(missing)}")
        print("    Add them to .env before running the full debate. Aborting.")
        sys.exit(1)

    bundle = build_conductor(settings).run(DEMO_BRIEF)
    print(json.dumps(bundle, indent=2))


if __name__ == "__main__":
    main()
