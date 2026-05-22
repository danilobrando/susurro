"""Tests for the polish pipeline.

LLM calls are not exercised here — they require an API key + network. The
tests cover the deterministic layers: rules, triggers, mode behavior.
"""

from __future__ import annotations


def test_rules_remove_obvious_fillers() -> None:
    from susurro.polish.rules import apply_rules

    raw = "Hola, eh, ¿cómo estás? Mmm, bien."
    out = apply_rules(raw)
    assert "eh" not in out.lower().split()
    assert "mmm" not in out.lower()
    assert "Hola" in out
    assert "bien" in out


def test_rules_collapse_whitespace() -> None:
    from susurro.polish.rules import apply_rules

    raw = "Hola   mundo  .  Cómo  estás"
    out = apply_rules(raw)
    assert "  " not in out
    assert " ." not in out


def test_rules_preserve_meaningful_text() -> None:
    from susurro.polish.rules import apply_rules

    raw = "Hoy fui al banco y luego al supermercado."
    out = apply_rules(raw)
    # No filler in this sentence — output should be identical.
    assert out == raw


def test_triggers_ordinals_fire() -> None:
    from susurro.polish.triggers import should_invoke_llm

    assert should_invoke_llm("Primero, hacer A. Segundo, hacer B.")
    assert should_invoke_llm("First, do A. Second, do B.")
    assert should_invoke_llm("En primer lugar, esto. En segundo lugar, eso.")


def test_triggers_backtrack_fires() -> None:
    from susurro.polish.triggers import should_invoke_llm

    assert should_invoke_llm("Hablé con Pedro, en realidad con Pablo.")
    assert should_invoke_llm("Meet at 2 actually 3 PM.")


def test_triggers_short_simple_text_skips_llm() -> None:
    from susurro.polish.triggers import should_invoke_llm

    assert not should_invoke_llm("Hola, ¿cómo estás?")
    assert not should_invoke_llm("Hoy fui al cine y volví caminando.")


def test_triggers_long_text_fires() -> None:
    from susurro.polish.triggers import should_invoke_llm

    long_text = " ".join(["palabra"] * 45)
    assert should_invoke_llm(long_text)


def test_polisher_off_passes_through() -> None:
    from susurro.polish import Polisher

    p = Polisher(mode="off")
    out, meta = p.polish("Hola, eh, mundo.")
    assert out == "Hola, eh, mundo."
    assert meta["mode"] == "off"
    assert meta["llm_invoked"] is False


def test_polisher_rules_only_skips_llm() -> None:
    from susurro.polish import Polisher

    p = Polisher(mode="rules")
    out, meta = p.polish("Hola, eh, mundo.")
    assert "eh" not in out.lower().split()
    assert meta["llm_invoked"] is False


def test_polisher_smart_without_warmup_falls_back_to_rules() -> None:
    from susurro.polish import Polisher

    # mode=smart but no warmup → LLM stays None → falls back to rules cleanup.
    p = Polisher(mode="smart")
    out, meta = p.polish("Hola, eh, mundo.")
    assert "eh" not in out.lower().split()
    assert meta["llm_invoked"] is False
