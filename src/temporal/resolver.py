"""
Temporal & Policy Version Resolver
Applies amendment rules dynamically based on determination date and event date.
"""

from datetime import datetime
from typing import Dict, Any, Optional


class TemporalResolver:
    AMENDMENT_DATE = "2026-03-01"

    @classmethod
    def is_post_amendment(cls, date_str: str) -> bool:
        if not date_str:
            return False
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            amend_dt = datetime.strptime(cls.AMENDMENT_DATE, "%Y-%m-%d")
            return dt >= amend_dt
        except ValueError:
            return False

    @classmethod
    def get_earnings_disregard(cls, determination_date: str) -> float:
        """Paragraph 1.1 / §5.1: $120 before 2026-03-01, $175 on or after."""
        if cls.is_post_amendment(determination_date):
            return 175.0
        return 120.0

    @classmethod
    def get_income_thresholds(cls, determination_date: str) -> Dict[str, Any]:
        """Paragraph 3.1 / §5.1: Income thresholds."""
        if cls.is_post_amendment(determination_date):
            return {
                1: 1225.0,
                2: 1650.0,
                3: 2075.0,
                4: 2500.0,
                5: 2925.0,
                "additional": 425.0
            }
        return {
            1: 1180.0,
            2: 1590.0,
            3: 2000.0,
            4: 2410.0,
            5: 2820.0,
            "additional": 410.0
        }

    @classmethod
    def get_sanction_percentage(cls, determination_date: str) -> float:
        """Paragraph 4.1 / §5.1: 20% before 2026-03-01, 15% on or after."""
        if cls.is_post_amendment(determination_date):
            return 0.15
        return 0.20

    @classmethod
    def get_reporting_window_days(cls, determination_date: str, event_date: Optional[str] = None) -> int:
        """
        Paragraph 2.1 / §5.2:
        Applies ONLY if change of circumstances occurred on or after 1 March 2026.
        If event occurred before 1 March 2026, reporting window was 10 days (§4.3.2).
        On or after 1 March 2026, reporting window is 14 days.
        """
        eval_date = event_date if event_date else determination_date
        if cls.is_post_amendment(eval_date):
            return 14
        return 10  # Pre-amendment baseline window in §4.3.2
