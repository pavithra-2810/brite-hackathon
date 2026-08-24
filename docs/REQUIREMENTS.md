# Requirements Document — Grounded Policy Reasoning System

**Project:** Calder County Household Support Program (HSP) Policy Reasoning Engine  
**Event:** Brite Spark 2026 — Problem 1: The Grounded Answer  
**Document Version:** 1.0.0 (Consolidated Day 1 + Day 2 Amendment No. 2026-01 Requirements)

---

## 1. Official Challenge Objective

The goal of this challenge is to build a **Grounded Policy Reasoning Assistant** for caseworkers at the Calder County Department of Household Services. Front-line staff field roughly 200 policy questions a week regarding the Household Support Program (HSP).

Unlike generic AI chatbots that guess plausible-sounding answers from internal pre-trained weights, this system must operate as a strict **Policy Reasoning System**:
1. Every substantive answer MUST be strictly grounded in the official policy manual.
2. Every claim MUST include exact clause-level citations (e.g., `[§6.4.1(a)]`).
3. If the policy manual does NOT establish an answer, the system MUST **REFUSE** to answer and guide the user on next steps.
4. If the policy manual CONTRADICTS itself without a resolution rule, the system MUST report a **CONFLICT** and surface both conflicting clauses.
5. If an amendment (e.g., Amendment No. 2026-01) alters policy values or rules based on claim/determination dates, the system MUST resolve the correct version dynamically.

---

## 2. Required Functionality

1. **Clause-Preserving Ingestion:**
   - Parse `policy-manual.md` (consolidated text as at 31 Dec 2025) and `Amendment No. 2026-01.md` (effective 1 March 2026).
   - Preserve hierarchical section boundaries (`§X.Y.Z`), titles, tables, cross-references, and temporal effective dates.

2. **Temporal & Version-Aware Policy Resolver:**
   - Support queries spanning different determination or event dates.
   - Resolve whether pre-amendment or post-amendment rules apply according to transitional provisions (§5.1 - §5.3 of Amendment No. 2026-01).

3. **Hybrid Evidence Retrieval:**
   - Search across policy clauses using combined Keyword (BM25) and Dense Vector / Semantic Retrieval.
   - Rank and extract structured candidate evidence chunks with full section metadata.

4. **Query Analysis & Deterministic Calculations:**
   - Extract household attributes (size, adults, children, ages, ADL assistance needs, income components, care allowances, dates).
   - Compute countable income, disregards, needs figures, net awards, and sanction reductions using deterministic Python calculation logic rather than LLM mental math.

5. **Coverage & Answerability Check (Refusal Engine):**
   - Evaluate whether retrieved policy clauses contain sufficient explicit facts to answer the question.
   - Decline to answer with an explicit `REFUSE` status when text is missing, out-of-scope, or ambiguous.

6. **Contradiction Detection Engine:**
   - Detect direct contradictions between policy clauses (e.g., §4.3.2 requiring 10-day change reporting vs §9.1.4 referencing 30-day reporting for pre-March 2026 determinations).
   - Return a `CONFLICT` status displaying both conflicting provisions instead of silently picking one.

7. **Citation Generation & Verification:**
   - Embed exact section citations (`[§X.Y.Z]`) for all claims.
   - Execute a post-generation verification step to validate that cited sections exist in the retrieved evidence set and support the claim.

8. **Verifiable Policy Proof / Decision Trace:**
   - Provide a step-by-step, transparent evidence chain (e.g., Household Size -> Threshold -> Countable Income -> Entitlement) without exposing hidden LLM chain-of-thought.

---

## 3. Expected Input

The system accepts a plain-language question, optionally accompanied by context parameters:
- `question` (string, required): The caseworker's query (e.g., *"What is the monthly earnings disregard for a household of 3?"* or *"If a recipient reported a change of income after 20 days on February 10, 2026, can an overpayment be established?"*).
- `determination_date` (ISO date string `YYYY-MM-DD`, optional, defaults to evaluation date / current date): The date on which the policy decision is being made.
- `event_date` (ISO date string `YYYY-MM-DD`, optional): The date on which a change of circumstances or event occurred.

---

## 4. Expected Output

The system produces a structured response containing:
1. **Decision**: One of `ANSWER`, `REFUSE`, `CONFLICT`.
2. **Answer Text**:
   - For `ANSWER`: Grounded response with clause citations.
   - For `REFUSE`: Clear refusal message explaining what policy provisions are missing and advising who to consult.
   - For `CONFLICT`: Explanation of the contradiction surfacing both conflicting clauses.
3. **Citations**: List of exact section identifiers cited (`["§6.4.1(a)", "§6.6.1"]`).
4. **Policy Proof**: Concise step-by-step reasoning trace derived from policy facts and calculations.
5. **Retrieved Clauses**: List of section IDs used as evidence.

---

## 5. Evaluation Criteria

According to the challenge floor and problem statement:
1. **Groundedness & Citation Accuracy:** 100% of substantive claims cite valid, retrieved policy clauses. No hallucinated section numbers or external benefit assumptions.
2. **Refusal Behavior:** Explicit `REFUSE` output when the manual lacks coverage or contains unsupported assumptions, complete with actionable next-step guidance for caseworkers.
3. **Contradiction Surfacing:** Surface conflicts cleanly (`CONFLICT`) when clauses directly contradict each other without selecting an arbitrary preference.
4. **Temporal / Version Correctness:** Accurate rule selection based on claim date / determination date across Day 1 baseline and Day 2 Amendment No. 2026-01.
5. **Deterministic Calculation Accuracy:** Exact numerical calculations for earnings disregards ($120 vs $175), needs figures, net award thresholds ($25 minimum award rule), and sanction percentage reductions (20% vs 15%).
6. **Self-Contained Execution:** Ability to run cleanly from a fresh repository clone via standard commands.

---

## 6. Policy Structure Summary

The consolidated policy manual is structured as follows:
- **Part 1 — Scope and Definitions:** Purpose (§1.1), Structure (§1.2), Interpretation (§1.3), Key Definitions (§1.4: Applicant, Recipient, Household, Dependent Child, Full-time student, Countable income, etc.).
- **Part 2 — General Conditions of Eligibility:** Basic conditions (§2.1), Continuing eligibility (§2.2), Under 18 applicants (§2.3), Resource limits ($4,000 max, home/vehicle disregards under §2.4).
- **Part 3 — Residence:** Residence condition (§3.1), Temporary absence (28 days standard, 90 days medical under §3.2), No fixed address (§3.3).
- **Part 4 — Exclusions:** Excluded persons (§4.1), Residential care (§4.2), Recipient obligations & reporting (§4.3: 10 days reporting window).
- **Part 5 — Special Household Circumstances:** Residential care (§5.1), Absent members (§5.2), Training allowance (§5.3), Care allowance (§5.4), Immigration conditions (§5.5).
- **Part 6 — Income:** Counted income (§6.1-§6.2), Lump sum & irregular income (§6.3), Disregards (§6.4: $120/mo earnings disregard, $200 care allowance, child support, training allowance), Self-employment (§6.5), Income thresholds table (§6.6.1).
- **Part 7 — Calculation of Award:** Award formula (§7.1: Needs - Income; $25 minimum award threshold), Needs figures table (§7.2.1), Adjustments (§7.3: $90 for 2+ ADLs, $140 for child under 2, housing assistance deduction), Payment (§7.4).
- **Part 8 — Applications and Determinations:** Application methods (§8.1), Evidence (§8.2), Time limits (30 days determination under §8.3), Interim payments (§8.4), Interviews (§8.5), Failure to respond (§8.6), Notifications (§8.7).
- **Part 9 — Overpayments and Recovery:** Overpayment grounds (§9.1; §9.1.4 30-day reporting anomaly), Amount recoverable (§9.2), Recovery rates (§9.3: 10% standard, 20% misrep), Waiver (§9.4), Time limits (§9.5: 6 yrs), Deliberate misrepresentation (§9.6).
- **Part 10 — Suspension, Termination and Sanctions:** Termination (§10.1), Suspension (§10.2: 60 days supervisor review), Reinstatement (§10.3), Sanctions (§10.5: 20% reduction for 4/8 weeks; exceptions for child <2 or 2+ ADLs).
- **Part 11 — Review:** Right to review (§11.1: 30 days limit), Review procedure (§11.2), Outcome (§11.3), Payment pending (§11.4).
- **Part 12 — Appeal:** Right of appeal to Appeals Panel (§12.1: 30 days post-review), Procedure (§12.2), Decisions (§12.3).

**Amendment No. 2026-01 (Effective 1 March 2026):**
- Paragraph 1: Earnings disregard increases from $120 to **$175/mo** (§6.4.1(a)).
- Paragraph 2: Change reporting window aligned to **14 calendar days** in both §4.3.2 and §9.1.4.
- Paragraph 3: Updated monthly income thresholds in §6.6.1 (1: $1225, 2: $1650, 3: $2075, 4: $2500, 5: $2925, +$425).
- Paragraph 4: Sanction reduction reduced from 20% to **15%** (§10.5.2); added §10.5.3A (no sanction if unreported change would have increased award).
- Paragraph 5 (Transitional rules):
  - §5.1: Disregard, income threshold, and sanction rate changes apply to determinations made **on or after 1 March 2026**.
  - §5.2: Reporting period change applies **only to changes of circumstances occurring on or after 1 March 2026**.
  - §5.3: Claims spanning 1 March 2026 are apportioned daily under §7.4.3.

---

## 7. Deliberate Traps Identified in Challenge Materials

1. **Genuine Internal Contradiction (Pre-March 1, 2026 baseline):**
   - **§4.3.2** commands recipients to report changes within **10 calendar days**.
   - **§9.1.4** explicitly states: *"Where an overpayment has arisen... and the recipient reported the change within the 30 calendar days required under §4.3..."*
   - *Conflict:* §9.1.4 asserts §4.3 requires 30 days, whereas §4.3.2 actually specifies 10 days! For determinations prior to March 1, 2026, querying overpayment rules for a report made at 20 days triggers a genuine policy conflict between §4.3.2 and §9.1.4. (Note: Amendment 2026-01 explicitly resolves this starting 1 March 2026 by changing both to 14 days, as noted in staff notes).

2. **Apparent Policy Gap / Broken Cross-Reference:**
   - **§7.1.3** states: *"The needs figure is calculated by reference to household size and composition, except in the case of full-time students (see §5.4)..."*
   - However, **§5.4** is titled *"Households including a person in receipt of a care allowance"* and contains zero provisions regarding full-time students! Full-time students are defined in §1.4.6, but Part 5 contains no §5.4 student rules. Asking for the special student needs figure formula under §5.4 triggers an explicit `REFUSE` response because the policy manual does not contain this rule.

3. **Out-of-Scope Benefits & Unmentioned Expenses (Hallucination Traps):**
   - Queries asking about deductions for childcare expenses or pet assistance: §6.4.1 lists explicit disregards (a)-(g); childcare expenses are NOT listed. The system must NOT assume standard benefit rules (e.g. SNAP childcare deductions) apply, but must refuse or state zero disregard based solely on the text.
   - Vehicle valuation caps: §2.4.2(b) excludes "one motor vehicle per household" without any monetary value limit. Asking if a $50,000 vehicle invalidates eligibility must return eligible under §2.4.2(b) rather than applying an external $15,000 threshold.

---

## 8. Day-2 Readiness: Temporal Architecture Design

To handle Day 2 requirements seamlessly without refactoring core logic:
- Ingestion converts policy documents into version-tagged clauses: `version="2025-12-31"` (original) and `version="2026-03-01"` (amended).
- Every query passes through a **Policy Version Resolver** taking `determination_date` and `event_date`.
- Rules with transitional overrides (§5.1 vs §5.2 of Amendment 2026-01) select the correct numeric constants ($120 vs $175 disregard; 20% vs 15% sanction; 10/30 vs 14 days reporting window) depending on whether the determination date is before or after March 1, 2026.
