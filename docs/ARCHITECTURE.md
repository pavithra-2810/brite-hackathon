# Architecture Specification — Grounded Policy Reasoning System

**Project:** Calder County Household Support Program (HSP) Policy Reasoning Engine  
**Document Version:** 1.0.0

---

## 1. System Overview & Data Flow

The system is designed as a modular, deterministic, evidence-first policy reasoning engine. It prioritizes policy correctness, citation precision, explicit refusal on gaps, and transparent contradiction detection over generative fluency.

```text
                           USER QUESTION
                    (+ determination/event date)
                                 │
                                 ▼
                          Query Analyzer
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
              Entities       Dates/Period    Calculations
                 │               │               │
                 └───────────────┼───────────────┘
                                 ▼
                      Policy Version Resolver
                                 │
                                 ▼
                          Hybrid Retrieval
                       (BM25 + Vector + Rerank)
                                 │
                                 ▼
                         Evidence Collector
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

## 2. Ingestion & Structured Policy Knowledge Model

### 2.1 Clause-Preserving Chunking
Standard text splitters chop text by arbitrary token lengths, destroying section boundaries (`§4.3.2`) and critical context. Our ingestion pipeline uses a **Section-Aware Markdown Parser**:
- Detects headings, subheadings, and clause numbers matching `§X.Y.Z` or `X.Y`.
- Extracts individual policy clauses as independent atomic units while preserving parent section titles, part titles, tables, and cross-references.

### 2.2 Clause Data Model Schema
```json
{
  "clause_id": "§6.4.1(a)",
  "part_title": "Part 6 — Income",
  "section_title": "Disregards",
  "text": "(a) the first $120 per month of household earnings from employment;",
  "full_path": "Part 6 > §6.4 Disregards > §6.4.1(a)",
  "document": "policy-manual.md",
  "policy_version": "2025-12-31",
  "effective_from": "2025-12-31",
  "effective_to": null,
  "referenced_sections": ["§6.4.2"],
  "numeric_values": {
    "disregard_amount": 120.0,
    "frequency": "monthly"
  }
}
```

---

## 3. Temporal Policy Version Resolver

To support Day 2 policy amendments (Amendment No. 2026-01):
- Clauses are tagged with `policy_version` and effective dates.
- The **Temporal Resolver** takes `determination_date` and `event_date` from the query:
  - If `determination_date < 2026-03-01`: Baseline rules apply (§6.4.1(a) earnings disregard = $120/mo, §4.3.2 reporting window = 10 days, §10.5.2 sanction = 20%).
  - If `determination_date >= 2026-03-01`: Amended rules apply (§6.4.1(a) earnings disregard = $175/mo, income thresholds under §3.1 of Amendment, sanction = 15%).
  - Transitional rules (§5.2 of Amendment): Reporting window changes (14 days) apply *only if `event_date >= 2026-03-01`*. If `event_date < 2026-03-01`, the reporting window remains the pre-amendment window (10 days / 30 days anomaly).

---

## 4. Query Analysis & Feature Extraction

The Query Analyzer combines rule-based regex parsing and LLM entity extraction:
1. **Fact Extraction:** Identifies household size, number of adults, number of children, child ages, ADL needs, gross earnings, care allowances, dates, and reporting delay.
2. **Intent Classification:**
   - `ELIGIBILITY_CHECK`: Checks general conditions, resources, income limits.
   - `AWARD_CALCULATION`: Requires exact numerical calculation.
   - `REPORTING_SANCTION`: Involves change of circumstance reporting timelines and sanctions.
   - `GENERAL_POLICY`: Direct policy interpretation question.

---

## 5. Hybrid Retrieval Engine

Retrieval combines multiple complementary algorithms:
1. **Keyword Retrieval (BM25):** Matches exact section numbers (`§6.4.1`), policy terms (`"earnings disregard"`, `"residential care"`), and numeric figures.
2. **Dense Vector Retrieval:** Embeds clauses using a local sentence transformer or vector similarity to capture semantic similarity.
3. **Candidate Merging & Reranking:** Combines vector scores and BM25 scores with Reciprocal Rank Fusion (RRF), prioritizing direct section matches when explicit section numbers are mentioned in the query.

---

## 6. Decision & Reasoning Pipeline

The core decision layer evaluates evidence against three explicit outcomes: `ANSWER`, `REFUSE`, `CONFLICT`.

```text
                       Retrieved Evidence Chunks
                                   │
                                   ▼
                    Is evidence coverage complete?
                        │                      │
                       YES                     NO
                        │                      │
                        ▼                      ▼
         Are there conflicting clauses?     REFUSE
            │                      │      (Explain missing
           YES                     NO       policy provisions)
            │                      │
            ▼                      ▼
        CONFLICT                 ANSWER
    (Surface clauses)      (Compute & Generate)
```

### 6.1 Coverage Check (Refusal Logic)
The Coverage Checker tests whether retrieved clauses provide sufficient facts to establish a conclusive answer:
- **Condition 1:** Required policy parameters exist (e.g. if query asks for student needs figure under §5.4, check if §5.4 contains student rules).
- **Condition 2:** No missing unstated policy assumptions.
- If coverage fails: Decision is set to `REFUSE`. System outputs a helpful refusal explaining what is missing and recommending referral to a supervisor or Board of Social Services.

### 6.2 Contradiction Detection Engine
The Contradiction Detector checks retrieved clauses for opposing rules:
- Example: Pre-March 1 2026 reporting window (§4.3.2 states 10 days vs §9.1.4 states 30 days).
- When incompatible constraints exist without a resolving precedence rule: Decision is set to `CONFLICT`. Both clauses are surfaced with their exact text.

### 6.3 Deterministic Calculation Engine
Arithmetic is NEVER delegated to LLM generative output.
- `calculate_award(household_size, adults, children, earnings, care_allowance, adl_count, housing_assist, determination_date)`:
  - Selects disregards based on `determination_date`: Earnings disregard = $120 ($175 post-March 2026), Care allowance disregard = min(care_allowance, $200).
  - Computes `net_income = max(0, gross_income - total_disregard)`.
  - Looks up Needs Figure from §7.2.1 table + §7.3 adjustments (+$140 for child <2, +$90 for 2+ ADLs).
  - Computes `award = max(0, needs_figure - net_income)`.
  - Applies $25 minimum award rule (§7.1.2): If `0 < award < 25`, final award is `$0`.

---

## 7. Citation Generation & Verification

1. **Citation Generation:** Every substantive statement produced by the answer generator includes an inline citation `[§X.Y.Z]`.
2. **Post-Generation Citation Verifier:**
   - Extracts all section references `[§...]` from generated text.
   - Verifies that every cited section exists in the ingested corpus.
   - Verifies that every cited section was present in the retrieved evidence set.
   - If an unretrieved or non-existent section is cited, the verifier strips the hallucinated citation or triggers regeneration.

---

## 8. Policy Proof / Decision Trace

The response includes a `policy_proof` field: a list of verifiable logical steps connecting inputs to policy rules and calculations.

*Example:*
```json
[
  "Household composition: 1 adult, 2 children (total size 3).",
  "Base needs figure under §7.2.1: $1,480 base + $330 = $1,810.",
  "Gross monthly earnings: $1,000.",
  "Applicable earnings disregard under §6.4.1(a) (as at 2026-01-15): $120.",
  "Countable income: $1,000 - $120 = $880.",
  "Calculated award: $1,810 - $880 = $930.",
  "Award exceeds $25 minimum threshold (§7.1.2). Final monthly award: $930."
]
```

---

## 9. Technology Selection

- **Runtime Environment:** Python 3.10+
- **CLI Framework:** Rich / standard argparse for clean terminal formatting.
- **Retrieval Engine:** `rank_bm25` (BM25Okapi) + SentenceTransformers (`all-MiniLM-L6-v2` / local TF-IDF cosine similarity fallback).
- **LLM / Provider:** Flexible provider adapter (OpenAI / Gemini / local Ollama / Mock fallback for deterministic offline evaluation).
- **Data Validation & Schemas:** Pydantic v2.
