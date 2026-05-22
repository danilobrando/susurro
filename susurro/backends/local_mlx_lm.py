"""Local LLM polish via Apple's mlx-lm.

Used when Susurro Local wants to be genuinely offline: no API keys, no
network. Default model is Llama 3.2 3B 4-bit, which runs at ~40-60 tok/s
on an M3 Pro and is good enough for the polish task (structure changes,
no generative creativity needed).
"""

from __future__ import annotations

import logging
import time

from .. import config
from .base import BackendError, BackendUnavailable

logger = logging.getLogger(__name__)


class LocalMLXPolishLLM:
    name = "local"

    def __init__(self, model: str | None = None) -> None:
        self.model_repo = model or config.LOCAL_POLISH_MODEL
        self._model = None
        self._tokenizer = None

    def warmup(self) -> None:
        if self._model is not None:
            return
        try:
            from mlx_lm import load
        except ImportError as e:
            raise BackendUnavailable(
                "mlx-lm not installed — pip install mlx-lm or use POLISH_BACKEND='groq'"
            ) from e
        try:
            self._model, self._tokenizer = load(self.model_repo)
        except Exception as e:
            raise BackendError(f"Failed to load {self.model_repo}: {e}") from e
        logger.info("local polish LLM ready: %s", self.model_repo)

    def polish(self, raw: str, *, system_prompt: str) -> str:
        if not raw:
            return raw
        if self._model is None:
            self.warmup()
        try:
            from mlx_lm import generate
        except ImportError as e:
            raise BackendUnavailable("mlx-lm not installed") from e

        # Build the chat-style prompt using the model's tokenizer template.
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": raw},
        ]
        prompt = self._tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        t0 = time.perf_counter()
        try:
            text = generate(
                self._model,
                self._tokenizer,
                prompt=prompt,
                max_tokens=min(2048, len(raw) * 4),
                verbose=False,
            )
        except Exception as e:
            logger.exception("local polish generation failed")
            raise BackendError(f"local polish: {e}") from e
        elapsed = time.perf_counter() - t0
        # mlx-lm's generate returns the full output; strip any leading assistant turn.
        polished = (text or "").strip()
        logger.info("[local-polish] %d→%d chars in %.2fs", len(raw), len(polished), elapsed)
        return polished
