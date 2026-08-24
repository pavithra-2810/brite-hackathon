#!/usr/bin/env python3
"""
Automated Evaluation Script for Grounded Policy Reasoning Engine
Evaluates against 10 comprehensive test categories.
"""

import sys
import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

sys.path.insert(0, str(Path(__file__).parent))

from src.generation.generator import PolicyReasoningEngine
from src.policy.models import DecisionType

console = Console()


def run_evaluation():
    base_dir = Path(__file__).parent
    data_dir = base_dir / "data" / "original"
    cases_file = base_dir / "tests" / "evaluation_cases.json"

    manual_text = (data_dir / "policy-manual.md").read_text(encoding="utf-8")
    amend_text = (data_dir / "Amendment No. 2026-01.md").read_text(encoding="utf-8")

    engine = PolicyReasoningEngine(manual_text, amend_text)

    cases = json.loads(cases_file.read_text(encoding="utf-8"))

    results_table = Table(title="Policy RAG System Evaluation Results")
    results_table.add_column("ID", style="cyan")
    results_table.add_column("Category", style="magenta")
    results_table.add_column("Expected Decision", style="yellow")
    results_table.add_column("Actual Decision", style="blue")
    results_table.add_column("Citations Verified", style="green")
    results_table.add_column("Status", style="bold")

    total = len(cases)
    passed = 0
    decision_matches = 0
    citation_matches = 0

    for case in cases:
        cid = case["id"]
        cat = case["category"]
        question = case["question"]
        date_str = case.get("determination_date", "2026-01-15")
        exp_dec = case["expected_decision"]
        exp_secs = case.get("expected_sections", [])

        res = engine.answer_question(question, determination_date=date_str)

        dec_pass = res.decision.value == exp_dec
        if dec_pass:
            decision_matches += 1

        # Citation check
        cite_pass = any(sec in res.citations for sec in exp_secs) if exp_secs else True
        if cite_pass:
            citation_matches += 1

        case_passed = dec_pass and cite_pass
        if case_passed:
            passed += 1
            status = "[bold green]PASS[/]"
        else:
            status = "[bold red]FAIL[/]"

        cites_str = ", ".join(res.citations) if res.citations else "None"
        results_table.add_row(cid, cat, exp_dec, res.decision.value, cites_str, status)

    console.print()
    console.print(results_table)

    console.print(f"\n[bold title]EVALUATION SUMMARY REPORT[/]")
    console.print(f"Total Test Cases: [bold]{total}[/]")
    console.print(f"Passed: [bold green]{passed}[/] / {total} ({ (passed/total)*100:.1f}%)")
    console.print(f"Decision Accuracy: [bold blue]{ (decision_matches/total)*100:.1f}%[/]")
    console.print(f"Citation Accuracy: [bold green]{ (citation_matches/total)*100:.1f}%[/]")

    return passed == total


if __name__ == "__main__":
    success = run_evaluation()
    sys.exit(0 if success else 1)
