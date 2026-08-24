# Grounded Policy Reasoning System — Calder County Household Support Program

**Event:** Brite Spark 2026 — Problem 1: The Grounded Answer  
**Status:** Floor Completed & Day 2 Amendment Ready (100% Evaluation Score)

---

## Project Overview

The **Grounded Policy Reasoning System** is an AI policy assistant built for caseworkers administering the Calder County Household Support Program (HSP). Unlike generic generative chatbots that hallucinate plausible answers, this system acts as a deterministic policy reasoning engine: every substantive claim is strictly grounded in exact policy clauses, unsupported questions trigger explicit refusals, policy self-contradictions are surfaced rather than hidden, and mathematical award calculations are computed deterministically.

---

## Problem & Challenge Scenario

Front-line caseworkers at Calder County field ~200 questions a week from a 12-Part policy manual that has grown by accretion over years. The manual contains deliberate real-world flaws:
1. **Internal Contradictions:** §4.3.2 requires reporting changes within **10 days**, while §9.1.4 references *"the 30 calendar days required under §4.3"*.
2. **Apparent Gaps / Broken References:** §7.1.3 directs caseworkers to §5.4 for student needs figures, but §5.4 covers Care Allowances and omits students.
3. **Temporal Policy Amendments (Day 2):** Amendment No. 2026-01 takes effect on March 1, 2026, altering earnings disregards ($120 to $175), reporting windows (14 days), income thresholds, and sanction percentages.

---

## Solution & Architecture

Our architecture decouples retrieval, policy versioning, coverage analysis, contradiction detection, arithmetic computation, and citation verification:

```text
                           USER QUESTION
                    (+ determination/event date)
                                 │
                                 ▼
                       Query Feature Extractor
                                 │
                      Temporal Version Resolver
                                 │
                          Hybrid Retrieval
                       (BM25 + TF-IDF Vector)
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
           Coverage Check  Conflict Check  Calculation Engine
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                          Decision Engine
                                 │
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
               ANSWER          REFUSE        CONFLICT
                  │              │              │
                  └──────────────┼──────────────┘
                                 ▼
                        Citation Verifier
                                 │
                                 ▼
                    Final Structured Response
```

---

## Key Differentiators

1. **Strict Policy Grounding & Citation:** Every claim cites exact clause identifiers (`[§6.4.1(a)]`).
2. **Actionable Refusal Engine (`REFUSE`):** Explicitly declines questions where policy text is missing or out-of-scope, providing supervisory referral advice under §1.1.3.
3. **Contradiction Surfacing (`CONFLICT`):** Identifies internal policy conflicts and outputs both opposing clauses instead of silently making unauthorized administrative choices.
4. **Deterministic Calculation Engine:** All numerical calculations (needs figures, income disregards, net awards, minimum $25 thresholds under §7.1.2) are calculated via code.
5. **Day-2 Amendment Readiness:** Pass determination dates dynamically to evaluate pre-amendment vs post-amendment (March 1, 2026) rules.
6. **Transparent Policy Proof:** Provides step-by-step evidence traces for every calculation and decision.
7. **Post-Generation Citation Verifier:** Validates that generated citations exist in the ingested manual and were retrieved in the candidate evidence set.

---

## Repository Structure

```text
policy-hackathon/
├── data/
│   └── original/
│       ├── policy-manual.md          # Baseline manual as at 31 Dec 2025
│       └── Amendment No. 2026-01.md  # Day 2 Amendment effective 1 Mar 2026
├── docs/
│   ├── REQUIREMENTS.md               # Detailed requirements & trap analysis
│   ├── ARCHITECTURE.md               # Complete architectural specification
│   └── DEMO.md                       # 5-part interactive demo walkthrough
├── src/
│   ├── ingestion/                    # Markdown parser preserving §X.Y.Z clause metadata
│   ├── policy/                       # Core Pydantic models
│   ├── retrieval/                    # Zero-dependency BM25 & TF-IDF hybrid retriever
│   ├── reasoning/                    # Query analyzer, refusal, conflict, calculator
│   ├── temporal/                     # Amendment version resolver (pre vs post 2026-03-01)
│   ├── citations/                    # Citation extraction & post-verifier
│   └── generation/                   # Policy reasoning engine orchestrator
├── tests/
│   ├── evaluation_cases.json         # 10 evaluation test cases covering all categories
│   ├── test_ingestion.py
│   └── test_reasoning.py
├── app.py                            # CLI application interface
├── evaluate.py                       # Automated evaluation reporter (100% pass score)
├── run_tests.py                      # Zero-dependency unit test runner
├── DECISIONS.md                      # Key architectural trade-offs & Day 2 log
├── AI-USAGE.md                       # AI usage declaration
├── requirements.txt                  # Python dependencies
└── README.md
```

---

## Setup & Running Instructions

### 1. Requirements
- Python 3.10+ installed. Zero external dependencies required for core execution (standard library + Rich for formatting).

### 2. Run the Evaluation Suite (100% Pass Metric)
```bash
python evaluate.py
```

### 3. Run Unit Tests
```bash
python run_tests.py
```

### 4. Interactive CLI Mode
```bash
python app.py
```

### 5. Single Question Execution
```bash
# Pre-Amendment Determination (Jan 15, 2026)
python app.py -q "Calculate the monthly award for a single adult with 1 child earning $1,000 per month." -d 2026-01-15

# Post-Amendment Determination (March 15, 2026)
python app.py -q "Calculate the monthly award for a single adult with 1 child earning $1,000 per month." -d 2026-03-15
```

---

## Evaluation Benchmark Summary

| Case ID | Category | Expected | System Result | Status |
|:---|:---|:---|:---|:---|
| `case_001` | Basic Retrieval | `ANSWER` | `ANSWER` | **PASS** |
| `case_002` | Multi-Section Reasoning | `ANSWER` | `ANSWER` | **PASS** |
| `case_003` | Calculation | `ANSWER` | `ANSWER` | **PASS** |
| `case_004` | Citation Precision | `ANSWER` | `ANSWER` | **PASS** |
| `case_005` | Unsupported Question | `REFUSE` | `REFUSE` | **PASS** |
| `case_006` | Apparent Policy Gap | `REFUSE` | `REFUSE` | **PASS** |
| `case_007` | Policy Contradiction | `CONFLICT` | `CONFLICT` | **PASS** |
| `case_008` | Policy Exception | `ANSWER` | `ANSWER` | **PASS** |
| `case_009` | Unmentioned Expenses | `REFUSE` | `REFUSE` | **PASS** |
| `case_010` | Day 2 Temporal Amendment | `ANSWER` | `ANSWER` | **PASS** |

**Overall Evaluation Score:** **10 / 10 (100.0%)**

---

## Limitations

1. **Corpus Scope:** Engine is strictly scoped to Calder County HSP policy manuals (`policy-manual.md` and `Amendment No. 2026-01.md`). It intentionally refuses non-HSP queries (e.g. SNAP, Medicaid).
2. **Text Format:** Built for Markdown policy manuals structured with clause identifiers (`§X.Y.Z`).
