"""
Post-Generation Citation Verifier
Validates that generated citations exist in the corpus and were present in retrieved evidence.
"""

import re
from typing import List, Set, Tuple, Dict, Any
from src.policy.models import Clause


class CitationVerifier:
    def __init__(self, all_clauses: List[Clause]):
        self.valid_clause_ids: Set[str] = {c.clause_id for c in all_clauses}
        # Also map base section numbers like §6.4 from §6.4.1(a)
        for c in all_clauses:
            if "." in c.clause_id:
                parts = c.clause_id.replace("§", "").split(".")
                if len(parts) >= 2:
                    self.valid_clause_ids.add(f"§{parts[0]}.{parts[1]}")
                    self.valid_clause_ids.add(f"§{parts[0]}")

    def extract_citations(self, text: str) -> List[str]:
        # Extract citations like [§6.4.1(a)] or §6.4.1
        raw_matches = re.findall(r"§\d+(?:\.\d+)+(?:\([a-z]\))?", text)
        citations = []
        for m in raw_matches:
            c = m if m.startswith("§") else f"§{m}"
            if c not in citations:
                citations.append(c)
        return citations

    def verify(self, answer_text: str, retrieved_clauses: List[Clause]) -> Dict[str, Any]:
        retrieved_ids = {c.clause_id for c in retrieved_clauses}
        # Add parent sections of retrieved clauses
        for c in retrieved_clauses:
            retrieved_ids.add(c.parent_section)
            if "(" in c.clause_id:
                base_id = c.clause_id.split("(")[0]
                retrieved_ids.add(base_id)

        cited_ids = self.extract_citations(answer_text)
        
        valid_citations = []
        invalid_citations = []
        unretrieved_citations = []

        for cid in cited_ids:
            if cid not in self.valid_clause_ids:
                invalid_citations.append(cid)
            elif cid not in retrieved_ids:
                # Check if base ID matches
                base_cid = cid.split("(")[0]
                if base_cid in retrieved_ids or any(r.startswith(base_cid) for r in retrieved_ids):
                    valid_citations.append(cid)
                else:
                    unretrieved_citations.append(cid)
            else:
                valid_citations.append(cid)

        is_valid = len(invalid_citations) == 0 and len(unretrieved_citations) == 0

        return {
            "is_valid": is_valid,
            "citations": valid_citations,
            "invalid_citations": invalid_citations,
            "unretrieved_citations": unretrieved_citations
        }
