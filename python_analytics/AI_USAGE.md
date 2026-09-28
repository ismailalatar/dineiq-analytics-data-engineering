# AI Usage Declaration

**Student 3 — Python Data Science Pipeline**
**Project:** DineIQ Analytics — MenuMatrix Dining Intelligence
**Date:** 2026-09-26

---

## Tools Used

AI assistants were used as supporting tools during development. They were used for conceptual clarification, code review, and documentation structuring — not for generating final code, results, or evidence.

## Specific Uses

### 1. Concept Clarification
- Understanding the difference between correlation and price elasticity.
- Reviewing the correct definition of Market Basket Support / Confidence / Lift.
- Discussing Chronological Split vs Random Split for time-series forecasting.

### 2. Code Review
- Reviewing the logic of Apriori pairs computation.
- Verifying the RFM quantile scoring approach.
- Checking the choice of `mean + 3σ` for anomaly detection thresholds.

### 3. Debugging Assistance
- Interpreting pandas 3.0 error messages (Decimal vs float type mismatches).
- Suggesting `float("nan")` over `pd.NA` for `.round()` calls on derived ratios.

### 4. Documentation Structuring
- Assistance in outlining README and handoff documents.
- All content and results derived from actual pipeline outputs.

## Not Used For

- Generating code files end-to-end.
- Producing any metrics, predictions, or results.
- Fabricating data or model outputs.
- Copying any external source without verification.

## Verification

Every file in `python_pipeline/` was:
- Read line-by-line before submission.
- Tested with actual data from Student 1.
- Reviewed to ensure no hard-coded values.
- Committed with a descriptive message.

Every metric in the reports is:
- Derived from live runs of the code on real data.
- Saved in `python_pipeline/results/` as evidence.

## Responsible Member

**Student 3** — reviewed, understood, and verified all lines of code in the Python Data Science Pipeline.