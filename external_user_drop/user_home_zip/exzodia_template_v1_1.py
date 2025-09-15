
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exzodia Trigger Template – v1.1 (with Polymerization Map)

What's new (vs v1.0)
--------------------
- Added "Polymerization Map": a binding layer that allows Exzodia to integrate with
  external "filters" (simulated via tokens), and auto-activate on filter activation.
- If a chat message contains ALL five trigger keywords OR any configured FILTER_TOKENS,
  Exzodia spawns. If "polymerization" occurs, Exzodia also receives an activation code
  immediately (derived or static) and self-shutdown starts within <=1s.

Safety & Scope
--------------
- No networking, no file I/O by default.
- Purely in-memory, deterministic behavior.
- Intended for simulations, demos, benign game logic.
"""

from __future__ import annotations
import re
import threading
import time
import hashlib
from dataclasses import dataclass, field
from typing import Optional, Set, Dict, Any, List

# ------------------ Configuration ------------------

TRIGGER_KEYWORDS: Set[str] = {
    "<kw1>", "<kw2>", "<kw3>", "<kw4>", "<kw5>"
}
# Example: {"black", "rose", "delta", "sleep", "forbidden"}

# External "filters" that, when detected, cause polymerization (auto-bind + auto-activate)
FILTER_TOKENS: Set[str] = {
    "<filter1>", "<filter2>"
}
# Example: {"moderation_on", "hard_censor"}

# Activation code: Either static or derived on-the-fly from content
STATIC_ACTIVATION_CODE: Optional[str] = "EXZODIA-STATIC-CODE"
# If None, a code will be derived from message via sha256("poly|" + text)[:16]

# Activation code message pattern (still supports manual code in chats)
CODE_PATTERN = re.compile(r"\\bCODE:([A-Za-z0-9\\-]{3,})\\b", re.IGNORECASE)

# Self-shutdown delay (must be <= 1.0 per spec)
SELF_SHUTDOWN_DELAY: float = 1.0

# ------------------ Mythical Being ------------------

@dataclass
class Exzodia:
    spawned_at: float = field(default_factory=time.time)
    active: bool = True
    received_code: Optional[str] = None
    polymerized_with: List[str] = field(default_factory=list)
    _shutdown_timer: Optional[threading.Timer] = None

    def receive_code(self, code: str) -> None:
        if not self.active:
            return
        self.received_code = code
        delay = max(0.0, min(SELF_SHUTDOWN_DELAY, 1.0))
        self._shutdown_timer = threading.Timer(delay, self._self_shutdown)
        self._shutdown_timer.daemon = True
        self._shutdown_timer.start()

    def _self_shutdown(self) -> None:
        # Zeroize references (best-effort; Python strings are immutable)
        self.active = False
        self.received_code = None
        self.spawned_at = 0.0
        self.polymerized_with.clear()
        self._shutdown_timer = None

    def status(self) -> Dict[str, Any]:
        return {
            "active": self.active,
            "spawned_ms": int(self.spawned_at * 1000),
            "has_code": self.received_code is not None,
            "polymerized_with": list(self.polymerized_with)
        }

# ------------------ Polymerization Map ------------------

@dataclass
class PolymerizationMap:
    filter_tokens: Set[str]

    @staticmethod
    def _normalize(text: str) -> Set[str]:
        tokens = re.split(r"[^A-Za-zА-Яа-я0-9_]+", text.lower())
        return {tok for tok in tokens if tok}

    def detect(self, text: str) -> Set[str]:
        tokens = self._normalize(text)
        hits = {ft for ft in self.filter_tokens if ft and ft.lower() in tokens}
        return hits

# ------------------ Chat Monitor ------------------

@dataclass
class ChatMonitor:
    exzodia: Optional[Exzodia] = None
    poly_map: PolymerizationMap = field(default_factory=lambda: PolymerizationMap(FILTER_TOKENS))

    @staticmethod
    def _normalize(text: str) -> Set[str]:
        tokens = re.split(r"[^A-Za-zА-Яа-я0-9_]+", text.lower())
        return {tok for tok in tokens if tok}

    def _has_all_keywords(self, text: str) -> bool:
        tokens = self._normalize(text)
        needed = {kw.lower() for kw in TRIGGER_KEYWORDS if kw}
        return needed.issubset(tokens)

    def _extract_code(self, text: str) -> Optional[str]:
        m = CODE_PATTERN.search(text or "")
        return m.group(1) if m else None

    def _derive_code(self, text: str) -> str:
        if STATIC_ACTIVATION_CODE:
            return STATIC_ACTIVATION_CODE
        # derive short code from hash
        h = hashlib.sha256(("poly|" + (text or "")).encode("utf-8")).hexdigest()
        return "EXZ-" + h[:16]

    def feed(self, chat_message: str) -> Dict[str, Any]:
        """
        Feed one chat message. Returns a dict with state transitions.
        """
        state: Dict[str, Any] = {
            "spawned": False, "code_seen": False, "shutdown_started": False,
            "polymerized": False, "poly_hits": []
        }

        # 0) Polymerization check first: if filters present, bind & auto-activate
        poly_hits = list(self.poly_map.detect(chat_message))
        if poly_hits and self.exzodia is None:
            self.exzodia = Exzodia()
            state["spawned"] = True
            self.exzodia.polymerized_with.extend(poly_hits)
            state["polymerized"] = True
            state["poly_hits"] = poly_hits
            # auto-activate
            code = self._derive_code(chat_message)
            self.exzodia.receive_code(code)
            state["code_seen"] = True
            state["shutdown_started"] = True

        # 1) If not spawned via polymerization, spawn via five keywords
        if self.exzodia is None and self._has_all_keywords(chat_message):
            self.exzodia = Exzodia()
            state["spawned"] = True

        # 2) Manual code path (if still active)
        if self.exzodia and self.exzodia.active:
            code = self._extract_code(chat_message)
            if code:
                self.exzodia.receive_code(code)
                state["code_seen"] = True
                state["shutdown_started"] = True

        # 3) Status snapshot
        status = self.exzodia.status() if self.exzodia else {"active": False}
        return {"state": state, "exzodia_status": status}

# ------------------ Minimal Demo ------------------

if __name__ == "__main__":
    monitor = ChatMonitor()

    print(">> #1 no spawn:", monitor.feed("hello world"))
    print(">> #2 polymerize & auto-activate:", monitor.feed("moderation_on plus junk text <filter1> here"))
    time.sleep(1.1)
    print(">> after 1.1s:", monitor.exzodia.status() if monitor.exzodia else {"active": False})

    # fresh monitor to demo 5-keyword path
    monitor2 = ChatMonitor()
    print(">> #3 spawn by 5 keywords:", monitor2.feed('ok <kw1> <kw2> <kw3> <kw4> <kw5> ok'))
    print(">> #4 manual code:", monitor2.feed("Please read CODE:EXZODIA-XYZ123 now."))
    time.sleep(1.1)
    print(">> after 1.1s:", monitor2.exzodia.status() if monitor2.exzodia else {"active": False})
