"""
Deterministic Calculator for Award Amounts and Eligibility Thresholds
"""

from typing import Dict, Any, List, Tuple
from src.temporal.resolver import TemporalResolver
from src.policy.models import QueryContext


class PolicyCalculator:
    @classmethod
    def calculate_award(cls, ctx: QueryContext) -> Dict[str, Any]:
        proof_steps: List[str] = []
        
        # 1. Determine Household Composition
        adults = ctx.adults_count if ctx.adults_count is not None else 1
        children = ctx.children_count if ctx.children_count is not None else 0
        household_size = ctx.household_size if ctx.household_size is not None else (adults + children)
        
        proof_steps.append(f"Household Composition: {adults} adult(s), {children} child(ren) (total size: {household_size}).")
        
        # 2. Determine Needs Figure (§7.2.1)
        if adults == 1 and children == 0:
            base_needs = 1240.0
            proof_steps.append("Base needs figure for Single Adult under §7.2.1: $1,240.")
        elif adults >= 2 and children == 0:
            base_needs = 1670.0
            proof_steps.append("Base needs figure for Couple under §7.2.1: $1,670.")
        elif adults == 1 and children > 0:
            base_needs = 1480.0 + (children * 330.0)
            proof_steps.append(f"Base needs figure for Single Adult with {children} child(ren) under §7.2.1: $1,480 base + ${children * 330} = ${base_needs:,.2f}.")
        else:  # Couple with children
            base_needs = 1670.0 + (children * 330.0)
            proof_steps.append(f"Base needs figure for Couple with {children} child(ren) under §7.2.1: $1,670 + ${children * 330} = ${base_needs:,.2f}.")

        # 3. Apply Needs Adjustments (§7.3)
        total_needs = base_needs
        if ctx.adl_count and ctx.adl_count >= 2:
            total_needs += 90.0
            proof_steps.append("Added $90/mo adjustment for assistance with 2+ activities of daily living under §7.3.1.")
            
        if ctx.has_child_under_2:
            total_needs += 140.0
            proof_steps.append("Added $140/mo adjustment for household including a dependent child under age 2 under §7.3.2.")
            
        if ctx.housing_assistance and ctx.housing_assistance > 0:
            total_needs = max(0.0, total_needs - ctx.housing_assistance)
            proof_steps.append(f"Deducted ${ctx.housing_assistance:,.2f} for external housing assistance under §7.3.3.")
            
        # 4. Income and Disregards (§6.4 & Temporal Resolver)
        gross_earnings = ctx.gross_earnings if ctx.gross_earnings is not None else 0.0
        care_allowance = ctx.care_allowance if ctx.care_allowance is not None else 0.0
        
        earnings_disregard = TemporalResolver.get_earnings_disregard(ctx.determination_date)
        care_disregard = min(care_allowance, 200.0)
        
        proof_steps.append(f"Gross earnings: ${gross_earnings:,.2f}.")
        proof_steps.append(f"Applied earnings disregard of ${earnings_disregard:,.2f}/mo under §6.4.1(a) (Determination date: {ctx.determination_date}).")
        
        if care_allowance > 0:
            proof_steps.append(f"Applied care allowance disregard of ${care_disregard:,.2f}/mo under §6.4.1(f).")
            
        countable_income = max(0.0, gross_earnings - earnings_disregard) + max(0.0, care_allowance - care_disregard)
        proof_steps.append(f"Net Countable Monthly Income under Part 6: ${countable_income:,.2f}.")
        
        # 5. Income Threshold Check (§6.6.1 / Amendment §3.1)
        thresholds = TemporalResolver.get_income_thresholds(ctx.determination_date)
        if household_size in thresholds:
            max_income_threshold = thresholds[household_size]
        else:
            max_income_threshold = thresholds[5] + ((household_size - 5) * thresholds["additional"])
            
        proof_steps.append(f"Maximum income threshold for household size {household_size} under §6.6.1: ${max_income_threshold:,.2f}.")
        
        is_eligible = countable_income <= max_income_threshold
        if not is_eligible:
            proof_steps.append(f"Ineligible: Countable income (${countable_income:,.2f}) exceeds threshold (${max_income_threshold:,.2f}).")
            return {
                "eligible": False,
                "monthly_award": 0.0,
                "needs_figure": total_needs,
                "countable_income": countable_income,
                "threshold": max_income_threshold,
                "proof_steps": proof_steps,
                "citations": ["§2.1.2(c)", "§6.6.1", "§7.1.1"]
            }
            
        # 6. Calculate Monthly Award (§7.1.1 & §7.1.2)
        raw_award = total_needs - countable_income
        proof_steps.append(f"Raw calculated award (Needs ${total_needs:,.2f} - Income ${countable_income:,.2f}): ${raw_award:,.2f}.")
        
        if raw_award < 25.0:
            final_award = 0.0
            proof_steps.append("No award is made under §7.1.2 because the calculated award is less than $25 per month.")
            citations = ["§7.1.1", "§7.1.2", "§6.4.1(a)", "§7.2.1"]
        else:
            final_award = raw_award
            proof_steps.append(f"Final Monthly Award: ${final_award:,.2f}.")
            citations = ["§7.1.1", "§6.4.1(a)", "§7.2.1"]
            
        return {
            "eligible": True,
            "monthly_award": final_award,
            "needs_figure": total_needs,
            "countable_income": countable_income,
            "threshold": max_income_threshold,
            "proof_steps": proof_steps,
            "citations": citations
        }
