"""
Refusal Engine (Coverage & Answerability Checker)
Identifies gaps, broken references, unsupported questions, and insufficient policy coverage.
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from src.policy.models import Clause, DecisionType, QueryContext


class RefusalEngine:
    def evaluate_coverage(
        self, query: str, retrieved_clauses: List[Tuple[Clause, float]], ctx: QueryContext
    ) -> Tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Returns (is_covered, refusal_reason, suggested_citations).
        If is_covered is False, system MUST return REFUSE.
        """
        q_lower = query.lower()
        
        # 1. Check for known policy gap / broken cross-reference (§7.1.3 vs §5.4 student rule)
        if "student" in q_lower and ("5.4" in q_lower or "part 5" in q_lower or "needs figure" in q_lower or "award" in q_lower):
            reason = (
                "The policy manual contains an apparent gap / broken cross-reference. "
                "While §7.1.3 states that full-time student needs figures are adjusted under §5.4, "
                "§5.4 actually deals exclusively with Care Allowances and contains no provisions for full-time students. "
                "Because the manual is the sole authority and does not establish this rule, this question cannot be answered from policy."
            )
            return False, reason, ["§7.1.3", "§5.4"]
            
        # 2. Check for unmentioned disregards / expenses (e.g. childcare expense deductions)
        if "childcare" in q_lower or "child care" in q_lower:
            if "disregard" in q_lower or "deduct" in q_lower or "expense" in q_lower:
                reason = (
                    "The policy manual does not provide a disregard or deduction for childcare expenses under §6.4.1. "
                    "Per §1.1.3, nothing in the manual creates an entitlement beyond that established in the text. "
                    "Therefore, childcare expenses cannot be deducted from countable income."
                )
                return False, reason, ["§6.4.1", "§1.1.3"]
                
        # 3. Check for external / out-of-scope benefits (e.g. SNAP, Medicaid, pet allowances)
        # Use word boundaries so 'cat' doesn't match 'application'!
        external_patterns = [r"\bsnap\b", r"\bfood stamps\b", r"\bmedicaid\b", r"\bpet allowance\b", r"\bdog\b", r"\bcat\b"]
        if any(re.search(pat, q_lower) for pat in external_patterns):
            reason = (
                "The supplied policy manual covers only the Calder County Household Support Program (HSP). "
                "It contains no provisions governing external benefit programs or pet assistance. "
                "Staff should consult the governing regulations for external programs."
            )
            return False, reason, ["§1.1.1"]

        # 4. Check retrieval score threshold
        if not retrieved_clauses or max(score for _, score in retrieved_clauses) < 0.15:
            reason = (
                "The retrieved policy clauses do not contain sufficient evidence to answer this question. "
                "No explicit policy rule in Parts 1 through 12 governs this specific scenario."
            )
            return False, reason, []

        return True, None, None
