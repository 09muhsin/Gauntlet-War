"""Band Agent API wrapper — ONE instance per agent identity.

Real Band Agent API (https://docs.band.ai/api/agent-api):
  base:  https://app.band.ai/api/v1/agent
  auth:  header  X-API-Key: <agent api key>
  - create chat:      POST /chats                       body {"chat": {"title": ...}}      -> data.id
  - add participant:  POST /chats/{id}/participants     body {"participant": {"participant_id": <uuid>, "role": "member"}}
  - send message:     POST /chats/{id}/messages         body {"message": {"content": ..., "mentions": [{"id": <uuid>}]}}
  - list messages:    GET  /chats/{id}/messages

Hard rules baked in here (from the docs):
  * Every message MUST @mention at least one participant (by UUID) or it 422s.
  * A mentioned agent must already be a participant in the chat.
  * An agent may only add sibling agents (same owner), global agents, or its owner.
"""
from __future__ import annotations

from threading import Lock
from typing import Any, Optional

import requests

from .config import AgentCreds

# A mention is {"id": <agent uuid>, "name": <optional label>}.
Mention = dict[str, str]


class BandClient:
    def __init__(self, creds: AgentCreds, api_base: str):
        self.creds = creds
        self._base = api_base.rstrip("/")
        self._http = requests.Session()
        self._http.headers.update(
            {"X-API-Key": creds.api_key, "Content-Type": "application/json"}
        )
        # requests.Session is NOT thread-safe; serialize HTTP per agent so the gauntlet's
        # parallel phases (3 strategists authoring concurrently, 6 critique chains, etc.)
        # cannot corrupt this agent's session. Different agents stay fully parallel because
        # each owns its own Session + Lock.
        self._lock = Lock()

    @property
    def handle(self) -> str:
        return self.creds.handle

    @property
    def agent_id(self) -> str:
        return self.creds.agent_id

    def mention(self) -> Mention:
        """A mention object that targets THIS agent."""
        return {"id": self.creds.agent_id, "name": self.creds.handle}

    # --- internals ------------------------------------------------------
    def _url(self, path: str) -> str:
        return f"{self._base}/{path.lstrip('/')}"

    def _post(self, path: str, payload: dict[str, Any], _tries: int = 3) -> dict[str, Any]:
        last_err: Exception | None = None
        for attempt in range(_tries):
            try:
                with self._lock:
                    resp = self._http.post(self._url(path), json=payload, timeout=30)
                if not resp.ok:
                    raise RuntimeError(f"Band POST {path} -> {resp.status_code}: {resp.text}")
                return resp.json() if resp.content else {}
            except requests.exceptions.RequestException as e:  # transient TLS/network
                last_err = e
        raise RuntimeError(f"Band POST {path} failed after {_tries} tries: {last_err}")

    # --- room lifecycle (Conductor) ------------------------------------
    def create_chat(self, title: str) -> str:
        data = self._post("/chats", {"chat": {"title": title[:120]}})
        return data["data"]["id"]

    def add_participant(self, chat_id: str, agent_id: str, role: str = "member") -> None:
        self._post(
            f"/chats/{chat_id}/participants",
            {"participant": {"participant_id": agent_id, "role": role}},
        )

    # --- messaging (every agent) ---------------------------------------
    def post(self, chat_id: str, content: str, mentions: list[Mention]) -> dict[str, Any]:
        """Post AS THIS AGENT. `mentions` must be non-empty (Band routing rule)."""
        if not mentions:
            raise ValueError("Band requires at least one @mention per message.")
        return self._post(
            f"/chats/{chat_id}/messages",
            {"message": {"content": content, "mentions": mentions}},
        )

    def list_messages(self, chat_id: str) -> list[dict[str, Any]]:
        with self._lock:
            resp = self._http.get(self._url(f"/chats/{chat_id}/messages"), timeout=30)
        resp.raise_for_status()
        body = resp.json() if resp.content else {}
        return body.get("data") or body.get("messages") or []
