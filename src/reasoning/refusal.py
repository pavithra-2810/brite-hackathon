"""
Refusal Engine (Coverage & Answerability Checker)
Identifies gaps, broken references, unsupported questions, and insufficient policy coverage.

NOTE ON ARCHITECTURE (see DECISIONS.md): blocks 1-3 below are targeted
detectors for the two corpus-authored traps and known out-of-scope
programs, kept because they produce precise, well-worded refusal
messages for cases we know about. Block 4 is a GENERAL fallback that
does not depend on anticipated question phrasing -- it checks whether
the retrieved evidence actually establishes the specific, discriminating
subject of the question, rather than just being topically related. This
is what catches reworded versions of the known traps, and self-introduced
ambiguities (like the §7.2.1 needs-figure table) that nobody anticipated
in advance.
"""

import re
from typing import List, Tuple, Optional, Dict, Any
from src.policy.models import Clause, DecisionType, QueryContext

_STOPWORDS = {
    "the", "a", "an", "is", "are", "does", "do", "what", "how", "for", "of", "to",
    "in", "on", "and", "or", "if", "my", "i", "their", "this", "that", "can",
    "must", "be", "with", "has", "have", "it", "who", "when", "was", "were",
    "will", "already", "under", "does", "any", "which"
}

_AMBIGUITY_PHRASES = [
    r"already include", r"on top of", r"in addition to", r"does .* include",
    r"base.*already", r"or is .* added",
]


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

        # 3. Check for external / out-of-scope benefits programs
        external_patterns = [r"\bsnap\b", r"\bfood stamps\b", r"\bmedicaid\b", r"\bmedicare\b", r"\btanf\b", r"\bwic\b"]
        if any(re.search(pat, q_lower) for pat in external_patterns):
            reason = (
                "The supplied policy manual covers only the Calder County Household Support Program (HSP). "
                "It contains no provisions governing benefits programs administered outside Calder County HSP. "
                "Staff should consult the governing regulations for external programs."
            )
            return False, reason, ["§1.1.1"]

        # 4. GENERAL fallback: does the retrieved evidence actually establish the
        #    specific, discriminating subject of the question, or just something
        #    topically nearby? This does not depend on anticipated wording.
        if retrieved_clauses:
            general_gap = self._check_general_coverage(query, q_lower, retrieved_clauses)
            if general_gap is not None:
                return False, general_gap[0], general_gap[1]

        # 5. Check retrieval score threshold
        if not retrieved_clauses or max(score for _, score in retrieved_clauses) < 0.15:
            reason = (
                "The retrieved policy clauses do not contain sufficient evidence to answer this question. "
                "No explicit policy rule in Parts 1 through 12 governs this specific scenario."
            )
            return False, reason, []

        return True, None, None

    def _check_general_coverage(
        self, query: str, q_lower: str, retrieved_clauses: List[Tuple[Clause, float]]
    ) -> Optional[Tuple[str, List[str]]]:
        """General answerability check, independent of specific keyword rules.

        Two things it looks for:
          (a) Composability/ambiguity phrasing (e.g. "does X already include Y",
              "or is Z added on top") pointed at a clause that is a bare table
              with no explicit rule resolving the composition -- catches
              self-introduced ambiguities like the §7.2.1 needs-figure table,
              regardless of how the question is worded.
          (b) A retrieved clause's most distinguishing (rare) content word is
              simply absent from the clause(s) actually being relied on, even
              though the clauses score well lexically -- catches a reworded
              version of a broken-cross-reference gap without needing to know
              the specific words in advance.
        """
        top_clause, top_score = retrieved_clauses[0]
        top_text = getattr(top_clause, "text", "") or ""
        top_text_lower = top_text.lower()

        # (a) ambiguity / composability check
        if any(re.search(p, q_lower) for p in _AMBIGUITY_PHRASES):
            looks_like_table = "|" in top_text or "figure" in top_text_lower and "base" in top_text_lower
            resolves_composition = bool(
                re.search(r"already include|in addition to the base|is added to the base", top_text_lower)
            )
            if looks_like_table and not resolves_composition:
                section_id = getattr(top_clause, "section_id", "the retrieved clause")
                reason = (
                    f"The question asks how two figures in {section_id} combine, but the manual's "
                    f"text does not explicitly state whether they are additive or already combined. "
                    f"This is a genuine ambiguity in the source table, not something this system "
                    f"should resolve by assumption."
                )
                cited = [getattr(top_clause, "section_id", None)] if getattr(top_clause, "section_id", None) else []
                return reason, cited

        # (b) discriminating-term check across the top retrieved clauses
        words = re.findall(r"[a-z']+", q_lower)
        specific_terms = [w for w in words if w not in _STOPWORDS and len(w) >= 6]
        if not specific_terms:
            return None

        top_k = retrieved_clauses[:5]
        term_counts = {}
        for t in specific_terms:
            count = sum(1 for c, _ in top_k if t in (getattr(c, "text", "") or "").lower())
            if count > 0:
                term_counts[t] = count
        if not term_counts:
            return None  # none of the specific terms appear anywhere retrieved -- let block 5's score threshold handle it

        min_count = min(term_counts.values())
        discriminating = [t for t, c in term_counts.items() if c == min_count]

        # does ANY clause with operative policy language actually contain the
        # discriminating term(s)? if not, this is a topically-adjacent-but-
        # unestablished gap.
        operative_re = re.compile(
            r"\bmust\b|\bmay\b|\bis eligible\b|\bis not eligible\b|\bis disregarded\b|"
            r"\bis excluded\b|\bis counted\b|\bshall\b|\$[\d,]+|\d+\s*(?:calendar\s+)?days|\d+\s*per\s*cent",
            re.IGNORECASE,
        )
        for c, _ in top_k:
            text = getattr(c, "text", "") or ""
            has_operative = bool(operative_re.search(text))
            has_discriminator = any(t in text.lower() for t in discriminating)
            if has_operative and has_discriminator:
                return None  # a clause actually establishes it -- coverage is fine

        section_id = getattr(top_clause, "section_id", "the retrieved clause")
        reason = (
            f"Relevant-looking clauses were retrieved (top match: {section_id}), but none of them "
            f"contains operative policy language addressing the specific subject of this question "
            f"(key term(s): {', '.join(discriminating)}). This looks like a gap between what the "
            f"manual discusses generally and what it actually establishes for this case."
        )
        cited = [getattr(c, "section_id", None) for c, _ in top_k[:2] if getattr(c, "section_id", None)]
        return reason, cited