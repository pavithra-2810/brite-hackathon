"""
Query Analyzer Module
Extracts policy features, entities, numerical inputs, and dates from user queries.
"""

import re
from typing import Dict, Any, Optional
from src.policy.models import QueryContext


class QueryAnalyzer:
    def analyze(self, query: str, determination_date: str = "2026-01-15", event_date: Optional[str] = None) -> QueryContext:
        q_lower = query.lower()
        
        ctx = QueryContext(
            question=query,
            determination_date=determination_date,
            event_date=event_date
        )
        
        # 1. Household size / adults / children extraction
        hh_match = re.search(r"household of (\d+)", q_lower)
        if hh_match:
            ctx.household_size = int(hh_match.group(1))
            
        adults_match = re.search(r"(\d+)\s*adult", q_lower) or re.search(r"single adult", q_lower)
        if adults_match:
            ctx.adults_count = 1 if "single adult" in q_lower else int(adults_match.group(1))
            
        children_match = re.search(r"(\d+)\s*(?:child|children|dependent)", q_lower)
        if children_match:
            ctx.children_count = int(children_match.group(1))
            
        if ctx.household_size is None and ctx.adults_count is not None and ctx.children_count is not None:
            ctx.household_size = ctx.adults_count + ctx.children_count
            
        # 2. Child under 2 check
        if "under 2" in q_lower or "under the age of 2" in q_lower or "infant" in q_lower or "baby" in q_lower:
            ctx.has_child_under_2 = True
        elif "child" in q_lower and "under" not in q_lower:
            ctx.has_child_under_2 = False
            
        # 3. ADL assistance count
        adl_match = re.search(r"(\d+)\s*activities of daily living", q_lower) or re.search(r"(\d+)\s*adls", q_lower)
        if adl_match:
            ctx.adl_count = int(adl_match.group(1))
        elif "assistance with two or more" in q_lower or "2 adl" in q_lower:
            ctx.adl_count = 2
            
        # 4. Monetary amounts (earnings, care allowance, housing assistance)
        earnings_match = re.search(r"(?:earning|earnings|income|earns|makes|paid)\s*(?:of)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", q_lower)
        if earnings_match:
            ctx.gross_earnings = float(earnings_match.group(1).replace(",", ""))
            
        care_match = re.search(r"care allowance\s*(?:of)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", q_lower)
        if care_match:
            ctx.care_allowance = float(care_match.group(1).replace(",", ""))
            
        housing_match = re.search(r"housing assistance\s*(?:of)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)", q_lower)
        if housing_match:
            ctx.housing_assistance = float(housing_match.group(1).replace(",", ""))
            
        # 5. Reporting delay days
        reporting_match = re.search(r"reported\s*(?:after|within|in)?\s*(\d+)\s*(?:calendar\s*)?days", q_lower)
        if reporting_match:
            ctx.reporting_delay_days = int(reporting_match.group(1))
            
        # 6. Date extraction in query text e.g. "determination on 2026-03-15" or "in April 2026"
        date_match = re.search(r"\b(202\d-\d{2}-\d{2})\b", query)
        if date_match:
            ctx.determination_date = date_match.group(1)
            
        return ctx
