# Architectural Decisions Log — Grounded Policy Reasoning System

**Project:** Calder County Household Support Program (HSP) Policy Engine  
**Event:** Brite Spark 2026 — Problem 1: The Grounded Answer  
**Document:** `DECISIONS.md`

---

## 1. Trade-Off: Answering vs. Refusing

### The Decision
We established a strict **Evidence Coverage Rule**: The system will ONLY produce an `ANSWER` decision if the retrieved policy clauses explicitly contain the governing rule and factual inputs necessary to establish the conclusion.

If the policy manual:
- Lacks a rule for the requested scenario (e.g., childcare expense disregards, pet allowances),
- Contains a broken cross-reference or policy gap (e.g., §7.1.3 referring to §5.4 for student needs figures, where §5.4 only covers Care Allowances),
- Lacks explicit statutory authorization,

The system MUST return **`REFUSE`**.

### Rationale & Trade-Offs
In public benefits administration, a fluent but wrong answer causes real human harm—a caseworker tells a resident they qualify when they do not, resulting in subsequent benefit recovery and hardship. Therefore:
- **Precision > Recall:** We deliberately chose to minimize false positives (hallucinated entitlements) at the cost of declining to answer ambiguous edge cases.
- **Actionable Refusal:** When refusing, the system does not fail silently; it explicitly explains *which* provisions are missing and instructs the caseworker to refer the file to a supervisor or the Board of Social Services under §1.1.3.

---

## 2. Trade-Off: Contradiction Surfacing vs. Silent Resolution

### The Decision
When the system detects conflicting policy provisions without a governing precedence rule (such as pre-March 1, 2026 determinations involving the 10-day reporting window in §4.3.2 vs the 30-day window in §9.1.4):
- The system returns **`CONFLICT`**.
- It surfaces **both** conflicting clauses explicitly in the output.

### Rationale
An automated system must never silently make policy decisions reserved for human caseworkers or legal counsel. Silently choosing one clause over another conceals institutional inconsistency. Surfacing the conflict alerts staff to apply administrative discretion or seek supervisory review.

---

## 3. Trade-Off: Deterministic Calculation vs. LLM Generative Arithmetic

### The Decision
We completely decoupled arithmetic logic from LLM text generation. All needs figures, income disregards, net award subtractions, and minimum award rules ($25 minimum under §7.1.2) are executed in pure Python code (`PolicyCalculator`).

### Rationale
Large Language Models are non-deterministic and prone to arithmetic hallucinations. By using deterministic code for calculations and feeding the verified result to the output builder, we guarantee 100% calculation accuracy across all family compositions and income levels.

---

## 4. Day 2 Requirement Change: Amendment No. 2026-01 Handling

### What Changed
On Day 2, Amendment No. 2026-01 was issued, taking effect on **1 March 2026**. Key updates included:
- §6.4.1(a) earnings disregard increased from $120 to $175/mo.
- §4.3.2 and §9.1.4 reporting windows aligned to 14 calendar days.
- §6.6.1 income thresholds increased.
- §10.5.2 sanction rate reduced from 20% to 15%.
- §5.1-§5.3 transitional rules governing determination date vs change-of-circumstances event date.

### How We Handled It
Because our Day 1 architecture used a **Temporal Policy Resolver** (`src/temporal/resolver.py`) and modular clause metadata:
- We ingested `Amendment No. 2026-01.md` as an additional versioned corpus (`version="2026-03-01"`).
- We passed `determination_date` into the resolver.
- For queries before March 1, 2026, baseline rules apply. For queries on or after March 1, 2026, amended rules apply automatically.
- Per §5.2 of the Amendment, reporting windows evaluate the `event_date` to preserve pre-amendment reporting periods for historical changes.

### What We Would Have Done Differently
Had we known temporal versioning was coming, we would have stored all numeric thresholds in an external JSON configuration matrix keyed by `(version, effective_date)` from Day 1 rather than incorporating date branches in the resolver class.
