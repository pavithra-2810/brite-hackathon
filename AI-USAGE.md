# AI Usage Declaration

**Project:** Calder County Household Support Program (HSP) Policy Engine  
**Event:** Brite Spark 2026 — Problem 1: The Grounded Answer  
**Document:** `AI-USAGE.md`

---

## 1. Summary of AI Tools Used

In accordance with the Brite Spark 2026 Participant Handbook and AI Usage Policy:
- **AI Coding Assistant:** Google Antigravity / Gemini 3.6 Flash.
- **Scope of AI Assistance:**
  - Parsing and structural breakdown of raw Markdown policy files.
  - Designing zero-dependency Python retrieval and deterministic calculation algorithms.
  - Generating test case structures in `tests/evaluation_cases.json`.
  - Writing documentation (`REQUIREMENTS.md`, `ARCHITECTURE.md`, `DECISIONS.md`, `DEMO.md`, `README.md`).

---

## 2. Human Verification & Control

- **Policy Inspection & Trap Identification:** All policy traps (the §4.3.2 vs §9.1.4 10-day vs 30-day reporting conflict and the §7.1.3 vs §5.4 student broken cross-reference) were explicitly verified against the source text (`policy-manual.md`).
- **Deterministic Math Safeguard:** Pure Python math calculation rules were manually checked against Part 6 and Part 7 tables to guarantee zero generative arithmetic errors.
- **Evaluation Integrity:** Test cases were constructed to probe real system boundaries, including 4 explicit refusal/conflict cases, ensuring honest evaluation metrics.
