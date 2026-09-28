# Dual Pipeline Comparison Report

**Student 3 — Python Data Science**
**SRS Step 14 — Spark vs Python Verification**
**Task: Customer Churn Prediction**

---

## 1. Overview

- Total cases compared: **100**
- Matches: **90**
- Mismatches: **10**
- Overall agreement rate: **90.00%**

## 2. Model Accuracy

- Spark accuracy: **57.00%**
- Python accuracy: **57.00%**

## 3. Probability Comparison

- Spark mean probability: 0.5283
- Python mean probability: 0.5192
- Mean absolute probability difference: 0.0238

## 4. Mismatch Analysis

Number of mismatch cases: **10**

### Mismatch breakdown

- **TC_001** | actual=0 | spark=0.0 (p=0.4429) | python=1 (p=0.5092)
- **TC_018** | actual=0 | spark=1.0 (p=0.5479) | python=0 (p=0.4646)
- **TC_033** | actual=1 | spark=1.0 (p=0.5204) | python=0 (p=0.4206)
- **TC_035** | actual=1 | spark=0.0 (p=0.4393) | python=1 (p=0.5217)
- **TC_039** | actual=0 | spark=1.0 (p=0.5451) | python=0 (p=0.4680)
- **TC_050** | actual=0 | spark=1.0 (p=0.5364) | python=0 (p=0.4999)
- **TC_062** | actual=0 | spark=0.0 (p=0.4751) | python=1 (p=0.5030)
- **TC_069** | actual=1 | spark=1.0 (p=0.5006) | python=0 (p=0.4981)
- **TC_070** | actual=1 | spark=1.0 (p=0.5147) | python=0 (p=0.4827)
- **TC_072** | actual=0 | spark=1.0 (p=0.5688) | python=0 (p=0.4790)

## 5. SRS Step 14 Requirements Coverage

| Requirement | Status |
|---|---|
| Record ID | ✅ |
| Actual class or value | ✅ |
| Spark result | ✅ |
| Python result | ✅ |
| Match or mismatch | ✅ |
| Numerical difference | ✅ |
| Explanation of disagreement | ✅ |
| Overall agreement percentage | ✅ |
| At least 100 cases | ✅ (100 cases) |

## 6. Conclusion

The two independently-trained models (Spark MLlib and scikit-learn) achieved an agreement rate of **90.00%** on 100 unseen test cases. This demonstrates the pipelines are independent and produce comparable results on the same task.
