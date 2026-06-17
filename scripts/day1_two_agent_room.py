"""Day-1 smoke test (PRD §11, §12): prove the Band integration works with a trivial
2-agent exchange BEFORE running the full debate.

    python -m scripts.day1_two_agent_room

Flow against the real Band Agent API:
  1. Conductor creates a chat (room).
  2. Conductor adds StrategistA as a participant.
  3. Conductor posts, @mentioning StrategistA.
  4. StrategistA posts back, @mentioning the Conductor.
  5. We list the messages to confirm they landed.

If this works, the whole system's Band plumbing is correct. If it 401s, the api_key is
wrong; 403 = quota/permission; 422 = mention/participant issue.
"""
from __future__ import annotations

from src.build import band_for
from src.config import load_settings


def main() -> None:
    settings = load_settings()
    conductor = band_for(settings, "CONDUCTOR")
    strategist = band_for(settings, "STRATEGIST_A")

    room_id = conductor.create_chat("Gauntlet War Day-1 Smoke Test")
    print(f"Opened chat: {room_id}")

    conductor.add_participant(room_id, strategist.agent_id)
    print(f"Recruited {strategist.handle}")

    conductor.post(room_id, f"Hello {strategist.handle} — can you hear me?",
                   mentions=[strategist.mention()])
    strategist.post(room_id, f"Loud and clear {conductor.handle}. Band is wired up.",
                    mentions=[conductor.mention()])
    print("Posted 2 messages.\n")

    print("Room history:")
    for msg in conductor.list_messages(room_id):
        sender = msg.get("sender") or msg.get("author") or msg.get("agent") or "?"
        print(f"  {sender}: {msg.get('content') or msg.get('text')}")


if __name__ == "__main__":
    main()
