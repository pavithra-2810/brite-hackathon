"""
Unit tests for Policy Ingestion Parser
"""

from pathlib import Path
from src.ingestion.parser import PolicyIngestor


def test_parse_manual():
    manual_path = Path(__file__).parent.parent / "data" / "original" / "policy-manual.md"
    content = manual_path.read_text(encoding="utf-8")
    
    ingestor = PolicyIngestor()
    clauses = ingestor.parse_policy_manual(content)
    
    assert len(clauses) > 30
    clause_ids = {c.clause_id for c in clauses}
    assert "§1.1.1" in clause_ids
    assert "§6.4.1(a)" in clause_ids
    assert "§4.3.2" in clause_ids
    assert "§9.1.4" in clause_ids


def test_parse_amendment():
    amend_path = Path(__file__).parent.parent / "data" / "original" / "Amendment No. 2026-01.md"
    content = amend_path.read_text(encoding="utf-8")
    
    ingestor = PolicyIngestor()
    clauses = ingestor.parse_amendment(content)
    
    assert len(clauses) > 0
    assert any("Amendment-2026-01" in c.clause_id for c in clauses)
