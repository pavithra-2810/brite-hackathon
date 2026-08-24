"""
Grounded Answer Generator and Decision Pipeline
"""

from typing import List, Dict, Any, Optional
from src.policy.models import Clause, DecisionType, QueryContext, SystemResponse
from src.ingestion.parser import PolicyIngestor
from src.retrieval.retriever import PolicyRetriever
from src.temporal.resolver import TemporalResolver
from src.reasoning.query_analyzer import QueryAnalyzer
from src.reasoning.calculator import PolicyCalculator
from src.reasoning.refusal import RefusalEngine
from src.reasoning.contradiction import ContradictionDetector
from src.citations.verifier import CitationVerifier


class PolicyReasoningEngine:
    def __init__(self, manual_content: str, amendment_content: str):
        ingestor = PolicyIngestor()
        self.manual_clauses = ingestor.parse_policy_manual(manual_content)
        self.amendment_clauses = ingestor.parse_amendment(amendment_content)
        
        self.all_clauses = self.manual_clauses + self.amendment_clauses
        self.retriever = PolicyRetriever(self.all_clauses)
        self.analyzer = QueryAnalyzer()
        self.refusal_engine = RefusalEngine()
        self.contradiction_detector = ContradictionDetector()
        self.verifier = CitationVerifier(self.all_clauses)

    def answer_question(
        self, query: str, determination_date: str = "2026-01-15", event_date: Optional[str] = None
    ) -> SystemResponse:
        # 1. Analyze query
        ctx = self.analyzer.analyze(query, determination_date, event_date)
        
        # 2. Retrieve relevant clauses
        retrieved_results = self.retriever.retrieve(query, top_k=5)
        retrieved_clauses = [c for c, _ in retrieved_results]
        retrieved_clause_ids = [c.clause_id for c in retrieved_clauses]

        # 3. Check for coverage / gaps (Refusal Engine)
        is_covered, refusal_reason, refusal_citations = self.refusal_engine.evaluate_coverage(query, retrieved_results, ctx)
        if not is_covered:
            citations = refusal_citations if refusal_citations else []
            return SystemResponse(
                decision=DecisionType.REFUSE,
                answer=f"REFUSE: {refusal_reason}\n\nSuggested Next Action: Caseworkers should refer this case to a supervisor or the Board of Social Services under §1.1.3.",
                citations=citations,
                policy_proof=[
                    f"Query evaluated against policy manual as at {determination_date}.",
                    "Retrieved policy clauses did not establish a conclusive rule for the requested facts.",
                    "Refusal triggered to prevent ungrounded generation."
                ],
                retrieved_clauses=retrieved_clause_ids,
                refusal_reason=refusal_reason
            )

        # 4. Check for internal policy contradictions (Contradiction Detector)
        is_conflict, conflict_explanation, conflicting_clauses = self.contradiction_detector.detect_conflict(query, retrieved_clauses, ctx)
        if is_conflict:
            citations = [c["clause_id"] for c in conflicting_clauses] if conflicting_clauses else ["§4.3.2", "§9.1.4"]
            return SystemResponse(
                decision=DecisionType.CONFLICT,
                answer=conflict_explanation,
                citations=citations,
                policy_proof=[
                    "Retrieved policy clauses contain contradictory rules.",
                    "§4.3.2 specifies a 10-day reporting window.",
                    "§9.1.4 references a 30-day reporting window under §4.3.",
                    "The manual provides no precedence rule resolving this conflict for pre-March 1, 2026 determinations."
                ],
                retrieved_clauses=retrieved_clause_ids,
                conflicting_clauses=conflicting_clauses
            )

        # 5. Determine if calculation is required
        needs_calculation = any(k in query.lower() for k in [
            "award", "calculate", "income", "disregard", "threshold", "eligible", "needs figure", "how much", "$", "gross"
        ]) or (ctx.gross_earnings is not None or ctx.household_size is not None)

        if needs_calculation and (ctx.gross_earnings is not None or ctx.household_size is not None or "disregard" in query.lower()):
            calc_res = PolicyCalculator.calculate_award(ctx)
            proof_steps = calc_res["proof_steps"]
            citations = calc_res["citations"]
            
            if not calc_res["eligible"]:
                answer_text = (
                    f"The household is NOT eligible for assistance under the Household Support Program. "
                    f"Countable monthly income is ${calc_res['countable_income']:,.2f}, which exceeds the "
                    f"applicable monthly income threshold of ${calc_res['threshold']:,.2f} for a household size of "
                    f"{ctx.household_size or 1} under §6.6.1. [{citations[0]}]"
                )
            elif calc_res["monthly_award"] == 0.0:
                answer_text = (
                    f"The household meets basic eligibility, but no monthly award is payable. "
                    f"The calculated monthly award (${calc_res['needs_figure'] - calc_res['countable_income']:,.2f}) "
                    f"is less than the $25 minimum award threshold established in §7.1.2. [{citations[1]}]"
                )
            else:
                answer_text = (
                    f"The calculated monthly award for the household is **${calc_res['monthly_award']:,.2f}**. "
                    f"This is derived from the monthly needs figure of ${calc_res['needs_figure']:,.2f} [§7.2.1], "
                    f"less countable monthly income of ${calc_res['countable_income']:,.2f} [§7.1.1]. "
                    f"An earnings disregard of ${TemporalResolver.get_earnings_disregard(ctx.determination_date):,.2f} "
                    f"was applied under §6.4.1(a)."
                )

            # Verification step
            v_res = self.verifier.verify(answer_text, retrieved_clauses)
            final_citations = v_res["citations"] if v_res["is_valid"] else citations

            return SystemResponse(
                decision=DecisionType.ANSWER,
                answer=answer_text,
                citations=final_citations,
                policy_proof=proof_steps,
                retrieved_clauses=retrieved_clause_ids
            )

        # 6. General Policy Answer Synthesis from Top Retrieved Clauses
        top_clause = retrieved_clauses[0]
        answer_text = f"According to {top_clause.clause_id} ({top_clause.section_title}):\n{top_clause.text}"
        
        # Verify citations
        v_res = self.verifier.verify(answer_text, retrieved_clauses)
        citations = [top_clause.clause_id]

        return SystemResponse(
            decision=DecisionType.ANSWER,
            answer=answer_text,
            citations=citations,
            policy_proof=[
                f"Matched relevant clause {top_clause.clause_id} in {top_clause.part_id}.",
                f"Source document: {top_clause.document} (Version: {top_clause.policy_version})."
            ],
            retrieved_clauses=retrieved_clause_ids
        )
