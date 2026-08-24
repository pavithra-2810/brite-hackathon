#!/usr/bin/env python3
"""
CLI Interface for Grounded Policy Reasoning System
Calder County Household Support Program (HSP)
"""

import sys
import os
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.generation.generator import PolicyReasoningEngine
from src.policy.models import DecisionType

console = Console()


def load_policy_files():
    base_dir = Path(__file__).parent / "data" / "original"
    manual_path = base_dir / "policy-manual.md"
    amend_path = base_dir / "Amendment No. 2026-01.md"

    if not manual_path.exists():
        console.print(f"[bold red]Error:[/] {manual_path} not found.")
        sys.exit(1)

    manual_text = manual_path.read_text(encoding="utf-8")
    amend_text = amend_path.read_text(encoding="utf-8") if amend_path.exists() else ""
    return manual_text, amend_text


def format_response(response, debug: bool = False):
    # Decision Color
    if response.decision == DecisionType.ANSWER:
        color = "green"
        symbol = "✅"
    elif response.decision == DecisionType.REFUSE:
        color = "yellow"
        symbol = "🚫"
    else:  # CONFLICT
        color = "bold red"
        symbol = "⚠️"

    console.print()
    console.print(Panel(f"[{color}]{symbol} DECISION: {response.decision.value}[/]", title="System Decision", expand=False))

    console.print(Panel(response.answer, title="Answer / Policy Output", style="white"))

    # Citations
    if response.citations:
        console.print(f"[bold cyan]Citations:[/] {', '.join(response.citations)}")
    else:
        console.print("[dim cyan]Citations:[/] None")

    # Policy Proof
    if response.policy_proof:
        console.print("\n[bold yellow]Policy Proof / Decision Trace:[/]")
        for step in response.policy_proof:
            console.print(f"  • {step}")

    # Retrieved Clauses
    if debug and response.retrieved_clauses:
        console.print(f"\n[dim]Retrieved Evidence Clauses: {', '.join(response.retrieved_clauses)}[/]")
    console.print()


def main():
    parser = argparse.ArgumentParser(description="Calder County HSP Grounded Policy Reasoning Assistant")
    parser.add_argument("-q", "--question", type=str, help="Policy question to ask")
    parser.add_argument("-d", "--date", type=str, default="2026-01-15", help="Determination date (YYYY-MM-DD)")
    parser.add_argument("--debug", action="store_true", help="Enable detailed debug trace output")
    args = parser.parse_args()

    manual_text, amend_text = load_policy_files()
    engine = PolicyReasoningEngine(manual_text, amend_text)

    if args.question:
        response = engine.answer_question(args.question, determination_date=args.date)
        format_response(response, debug=args.debug)
    else:
        console.print("[bold blue]Calder County Household Support Program — Policy Assistant[/]")
        console.print(f"[dim]Default Determination Date: {args.date} | Type 'exit' to quit.[/]\n")

        while True:
            try:
                q = console.input("[bold yellow]Ask a policy question > [/]").strip()
                if not q:
                    continue
                if q.lower() in ["exit", "quit", "q"]:
                    console.print("Goodbye!")
                    break
                response = engine.answer_question(q, determination_date=args.date)
                format_response(response, debug=args.debug)
            except (KeyboardInterrupt, EOFError):
                console.print("\nGoodbye!")
                break


if __name__ == "__main__":
    main()
