"""Polish pipeline — turn raw STT output into structured, WisprFlow-grade text.

Three modes (configured via `config.POLISH_MODE`):
    off    : pass-through, raw STT
    rules  : regex cleanup only (~5 ms, no network)
    smart  : rules + LLM polish when triggers fire (~300 ms over Groq)

The Polisher owns no AppKit / threading concerns — it's a pure transform that
can be called from any thread. The app wires it into the STT → paste pipeline.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import datetime

from .. import config
from ..backends import BackendError, BackendUnavailable, make_polish_llm
from .prompt import SYSTEM_PROMPT
from .rules import apply_rules
from .triggers import should_invoke_llm

logger = logging.getLogger(__name__)


class Polisher:
    def __init__(self, mode: str | None = None, backend: str | None = None) -> None:
        self.mode = (mode or config.POLISH_MODE).lower()
        self.backend_name = backend or config.POLISH_BACKEND
        self._llm = None
        self._llm_warmup_failed = False

    def warmup(self) -> None:
        if self.mode != "smart":
            return
        try:
            self._llm = make_polish_llm(self.backend_name)
            self._llm.warmup()
        except (BackendUnavailable, BackendError, ValueError) as e:
            logger.warning("polish LLM warmup failed (%s); falling back to rules-only", e)
            self._llm_warmup_failed = True
            self._llm = None

    def polish(self, raw: str) -> tuple[str, dict]:
        """Return (polished_text, metadata).

        Metadata fields:
            mode:        the mode actually used (after fallbacks)
            llm_invoked: whether the LLM ran
            elapsed_s:   total polish time
            raw:         the input (for logging)
        """
        t0 = time.perf_counter()
        meta = {"mode": self.mode, "llm_invoked": False, "elapsed_s": 0.0, "raw": raw}
        if not raw or self.mode == "off":
            meta["elapsed_s"] = time.perf_counter() - t0
            return raw, meta

        # Tier 1 — rules always run when mode != off.
        cleaned = apply_rules(raw)
        if self.mode == "rules":
            meta["elapsed_s"] = time.perf_counter() - t0
            return cleaned, meta

        # Tier 2 — LLM only when the trigger fires and warmup succeeded.
        if self._llm is None or not should_invoke_llm(cleaned):
            meta["elapsed_s"] = time.perf_counter() - t0
            return cleaned, meta
        try:
            polished = self._llm.polish(cleaned, system_prompt=SYSTEM_PROMPT)
            meta["llm_invoked"] = True
        except BackendError as e:
            logger.warning("LLM polish failed (%s); returning rules-only output", e)
            polished = cleaned

        meta["elapsed_s"] = time.perf_counter() - t0
        return polished, meta


def append_to_log(raw: str, polished: str, meta: dict) -> None:
    """Append one polish event to the local JSONL log for later tuning."""
    try:
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "mode": meta.get("mode"),
            "llm_invoked": meta.get("llm_invoked"),
            "elapsed_s": round(meta.get("elapsed_s", 0.0), 3),
            "raw": raw,
            "polished": polished,
            "changed": raw.strip() != polished.strip(),
        }
        with open(config.POLISH_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        logger.debug("polish log write failed", exc_info=True)
