"""
Unit tests for Policy Reasoning, Refusal, Calculation, and Contradictions
"""

from pathlib import Path
from src.generation.generator import PolicyReasoningEngine
from src.policy.models import DecisionType


def get_engine():
    data_dir = Path(__file__).parent.parent / "data" / "original"
    manual = (data_dir / "policy-manual.md").read_text(encoding="utf-8")
    amend = (data_dir / "Amendment No. 2026-01.md").read_text(encoding="utf-8")
    return PolicyReasoningEngine(manual, amend)


def test_calculation_award():
    engine = get_engine()
    res = engine.answer_question(
        "Calculate the monthly award for a single adult with 1 child earning $1,000 per month.",
        determination_date="2026-01-15"
    )
    assert res.decision == DecisionType.ANSWER
    assert "$930.00" in res.answer
    assert "§7.2.1" in res.citations


def test_refusal_gap():
    engine = get_engine()
    res = engine.answer_question(
        "What is the needs figure adjustment rule for full-time students under §5.4?",
        determination_date="2026-01-15"
    )
    assert res.decision == DecisionType.REFUSE
    assert "REFUSE" in res.answer


def test_conflict_detection():
    engine = get_engine()
    res = engine.answer_question(
        "If a recipient reported a change of income after 20 days on February 10, 2026, can an overpayment be established under §4.3.2 and §9.1.4?",
        determination_date="2026-02-10"
    )
    assert res.decision == DecisionType.CONFLICT
    assert "§4.3.2" in res.citations
    assert "§9.1.4" in res.citations


def test_day2_amendment_disregard():
    engine = get_engine()
    # Before March 1 2026 -> $120
    res_pre = engine.answer_question("What is the earnings disregard?", determination_date="2026-01-15")
    assert "$120.00" in res_pre.answer

    # On or after March 1 2026 -> $175
    res_post = engine.answer_question("What is the earnings disregard?", determination_date="2026-03-15")
    assert "$175.00" in res_post.answer
