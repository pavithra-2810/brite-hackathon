# Demo Walkthrough Guide — Grounded Policy Reasoning System

**Project:** Calder County Household Support Program (HSP) Policy Reasoning Assistant  
**Document Version:** 1.0.0

---

## Overview

This guide demonstrates the 5 core capabilities of our Grounded Policy Reasoning System:
1. **Normal Grounded Answer with Clause Citation**
2. **Deterministic Award Calculation**
3. **Refusal Engine (Handling Unsupported Questions & Gaps)**
4. **Contradiction Detection Engine (Surfacing Policy Inconsistencies)**
5. **Temporal & Version-Aware Policy Reasoning (Day 2 Amendment)**

---

## Demo Scenario 1: Normal Policy Answer

### Command
```bash
python app.py -q "What is the maximum countable resource limit for a household under §2.4.1?" -d 2026-01-15
```

### Expected Output
- **Decision:** `ANSWER`
- **Answer:** *"According to §2.4.1 (Resources): A household is not eligible where the total countable resources of the household exceed $4,000."*
- **Citations:** `[§2.4.1]`
- **Policy Proof:** Matched relevant clause §2.4.1 in Part 2 — General Conditions of Eligibility.

---

## Demo Scenario 2: Deterministic Award Calculation

### Command
```bash
python app.py -q "Calculate the monthly award for a single adult with 1 child having gross earnings of $1,000 per month." -d 2026-01-15
```

### Expected Output
- **Decision:** `ANSWER`
- **Answer:** *"The calculated monthly award for the household is **$930.00**. This is derived from the monthly needs figure of $1,810.00 [§7.2.1], less countable monthly income of $880.00 [§7.1.1]. An earnings disregard of $120.00 was applied under §6.4.1(a)."*
- **Citations:** `[§7.1.1, §6.4.1(a), §7.2.1]`
- **Policy Proof:**
  - Household Composition: 1 adult(s), 1 child(ren) (total size: 2).
  - Base needs figure for Single Adult with 1 child under §7.2.1: $1,480 base + $330 = $1,810.00.
  - Gross earnings: $1,000.00.
  - Applied earnings disregard of $120.00/mo under §6.4.1(a).
  - Net Countable Monthly Income under Part 6: $880.00.
  - Final Monthly Award: $930.00.

---

## Demo Scenario 3: Unsupported Question & Gap Refusal

### Command
```bash
python app.py -q "What is the award calculation rule or needs figure adjustment for full-time students under §5.4?" -d 2026-01-15
```

### Expected Output
- **Decision:** `REFUSE`
- **Answer:** *"REFUSE: The policy manual contains an apparent gap / broken cross-reference. While §7.1.3 states that full-time student needs figures are adjusted under §5.4, §5.4 actually deals exclusively with Care Allowances and contains no provisions for full-time students. Because the manual is the sole authority and does not establish this rule, this question cannot be answered from policy.*  
  *Suggested Next Action: Caseworkers should refer this case to a supervisor or the Board of Social Services under §1.1.3."*
- **Citations:** `[§7.1.3, §5.4]`

---

## Demo Scenario 4: Contradiction Detection

### Command
```bash
python app.py -q "If a recipient reported a change of income after 20 days on February 10, 2026, can an overpayment be established under §4.3.2 and §9.1.4?" -d 2026-02-10
```

### Expected Output
- **Decision:** `CONFLICT`
- **Answer:** *"⚠️ Genuine Policy Conflict Detected (Determination Date: 2026-02-10).*  
  *The policy manual contains a direct internal contradiction regarding the change of circumstances reporting period:*  
  *1. §4.3.2 mandates that a recipient must report a change of circumstances within 10 calendar days.*  
  *2. §9.1.4 states that no overpayment shall be established if reported within the '30 calendar days required under §4.3'.*  
  *The baseline manual provides no precedence rule resolving whether 10 days or 30 days applies for pre-March 1, 2026 determinations."*
- **Citations:** `[§4.3.2, §9.1.4]`

---

## Demo Scenario 5: Temporal Policy Reasoning (Day 2 Amendment)

### Pre-Amendment Determination (Jan 15, 2026)
```bash
python app.py -q "Calculate the monthly award for a single adult with 1 child earning $1,000 per month." -d 2026-01-15
```
- **Disregard applied:** **$120.00** [§6.4.1(a)]
- **Final Award:** **$930.00**

### Post-Amendment Determination (March 15, 2026)
```bash
python app.py -q "Calculate the monthly award for a single adult with 1 child earning $1,000 per month." -d 2026-03-15
```
- **Disregard applied:** **$175.00** [§6.4.1(a) as amended by Amendment No. 2026-01]
- **Final Award:** **$985.00**
