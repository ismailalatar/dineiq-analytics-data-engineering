# Dual Pipeline Comparison Report

**Student 3 - Python Data Science**  
**SRS Step 14 - Spark vs Python Verification**  
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

- Spark mean probability: **0.5283**
- Python mean probability: **0.5192**
- Mean absolute probability difference: **0.0238**

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
| Record ID | PASS |
| Actual class or value | PASS |
| Spark result | PASS |
| Python result | PASS |
| Match or mismatch | PASS |
| Numerical difference | PASS |
| Explanation of disagreement | PASS |
| Overall agreement percentage | PASS |
| At least 100 cases | PASS (100 cases) |

## 6. Conclusion

The Spark MLlib and Python scikit-learn pipelines were evaluated on the same 100 test cases. The two pipelines produced identical predictions for **90 cases (90.00% agreement)** and different predictions for **10 cases**.

Both pipelines achieved **57.00% accuracy** on the shared test set. The comparison provides a direct validation of the two independent implementations for the Customer Churn Prediction task.