"""Tiny parallel-map helper for the gauntlet phases.

The Conductor's phases are embarrassingly parallel — 3 strategists authoring, 6 critique chains,
3 refines, 3 scores, 3 deliverables — and the bottleneck is the blocking LLM + Band HTTP call.
A ThreadPoolExecutor cuts a 90s gauntlet to ~30s without changing the token spend.

Order is preserved — the i-th result lines up with the i-th input — so the bundle's strategies,
debate log, and scores keep a deterministic shape for the UI to render.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
R = TypeVar("R")


def pmap(fn: Callable[[T], R], items: Iterable[T], *, workers: int = 6) -> list[R]:
    """Run `fn` over `items` concurrently; return results in the same order as `items`.

    Errors propagate from the first failing task (executor.map semantics) so a broken
    strategist surfaces cleanly instead of hiding behind a quiet retry loop.
    """
    items = list(items)
    if not items:
        return []
    # `max_workers=min(...)` keeps small batches from spinning unused threads.
    with ThreadPoolExecutor(max_workers=min(workers, len(items))) as pool:
        return list(pool.map(fn, items))
