"""Quick quality gate for the regenerated deliverables — banned phrases + likely-invented proof."""
import glob
import os
import re

from src.knowledge import lint_banned

SEALED = {"56a5f15f", "883cbd22", "a1f351a3"}


def rid(path: str) -> str:
    return os.path.basename(os.path.dirname(path))[:8]


files = [f for f in sorted(glob.glob("deliverables/*/*.md")) if rid(f) in SEALED]

print("=== BANNED PHRASE SWEEP ===")
bad = 0
for f in files:
    hits = lint_banned(open(f, encoding="utf-8").read())
    if hits:
        print(" HIT", f, hits)
        bad += len(hits)
print("banned_hits:", bad)

print("\n=== POSSIBLE INVENTED PROOF (specific people/result counts) ===")
pat = re.compile(
    r"\b(\d[\d,]{2,})\b[^.\n]{0,30}?(people|customers|users|members|others|quit|joined|reviews|clients)",
    re.I,
)
flagged = 0
for f in files:
    for m in pat.finditer(open(f, encoding="utf-8").read()):
        print("  ?", os.path.relpath(f), "->", m.group(0).strip()[:70])
        flagged += 1
print("possible_invented:", flagged)

print("\n=== HONEST PLACEHOLDERS KEPT ===")
total = 0
for f in files:
    c = open(f, encoding="utf-8").read().count("[INSERT REAL")
    if c:
        print(" ", os.path.relpath(f), c)
        total += c
print("insert_flags:", total)
