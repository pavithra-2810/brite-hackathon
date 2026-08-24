"""
Core Policy Models and Data Structures
"""

from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    ANSWER = "ANSWER"
    REFUSE = "REFUSE"
    CONFLICT = "CONFLICT"


class Clause(BaseModel):
    clause_id: str  # e.g., "§6.4.1(a)" or "§4.3.2"
    part_id: str  # e.g., "Part 6 — Income"
    section_title: str  # e.g., "Disregards"
    text: str
    full_path: str
    document: str  # e.g., "policy-manual.md" or "Amendment No. 2026-01.md"
    policy_version: str  # e.g., "2025-12-31" or "2026-03-01"
    effective_from: str  # YYYY-MM-DD
    effective_to: Optional[str] = None  # YYYY-MM-DD or None if active
    parent_section: str  # e.g., "§6.4"
    referenced_sections: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QueryContext(BaseModel):
    question: str
    determination_date: str = "2026-01-15"  # ISO format YYYY-MM-DD
    event_date: Optional[str] = None  # ISO format YYYY-MM-DD
    household_size: Optional[int] = None
    adults_count: Optional[int] = None
    children_count: Optional[int] = None
    has_child_under_2: Optional[bool] = None
    adl_count: Optional[int] = None
    gross_earnings: Optional[float] = None
    care_allowance: Optional[float] = None
    housing_assistance: Optional[float] = None
    reporting_delay_days: Optional[int] = None


class SystemResponse(BaseModel):
    decision: DecisionType
    answer: str
    citations: List[str] = Field(default_factory=list)
    policy_proof: List[str] = Field(default_factory=list)
    retrieved_clauses: List[str] = Field(default_factory=list)
    conflicting_clauses: Optional[List[Dict[str, str]]] = None
    refusal_reason: Optional[str] = None
    debug_trace: Optional[Dict[str, Any]] = None
