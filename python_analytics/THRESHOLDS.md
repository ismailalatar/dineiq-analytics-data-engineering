# Thresholds Documentation

هذا الملف يوثق جميع القيم الحدية المستخدمة في المشروع، مع تبرير كل قيمة بشكل واضح حسب متطلبات SRS

---

## Churn Model

| القيمة | الحد | التبرير |
|--------|------|---------|
| Split Ratio | 60/20/20 | تقسيم قياسي يوازن بين التدريب والتقييم |

| Temporal Split | حسب recency | لتجنب Data Leakage التدريب على الأقدم، الاختبار على الأحدث |

| Feature Count | 11 ميزة | الميزات الأساسية من RFM + السلوك |

| Model Threshold | 0.5 | افتراضي للتصنيف الثنائي |

ملاحظة نسبة الـ Split اختارها الفريق بعد تجربة نسب متعددة

---

## Wastage Risk Model

| القيمة | الحد | التبرير |
|--------|------|---------|
| High Wastage Threshold | 75th Percentile | التصنيف الربعي يفصل الـ 25% الأعلى هدراً |

| Lag Window 7d | 7 أيام | يمثل نمط أسبوعي كامل في المطاعم |

| Lag Window 30d | 30 يوم | يمثل نمط شهري لتقليل التذبذب |

| Split Ratio | 60/20/20 | نفس Churn Model |
| Temporal Split | حسب wastage_date | لمنع Data Leakage |
| Model Threshold | 0.5 | افتراضي للتصنيف الثنائي |


ملاحظة الـ Q75 اختاره الفريق بدلاً من Q80 أو Q90 لأنه يوازن بين اكتشاف الحالات والتطبيق العملي

---

## Demand Forecast

| القيمة | الحد | التبرير |
|--------|------|---------|
| N_TEST_DAYS | 73 يوم | يمثل آخر 2.5 شهر من البيانات للاختبار |

| N_LAGS | 7 أيام | كافٍ لالتقاط النمط الأسبوعي |
| Rolling Mean | 7 أيام | تمهيد للضوضاء |
| Min Rows per Entity | 93 صف | لضمان بيانات كافية للتدريب والاختبار |

| Train/Test | Temporal | حسب التاريخ لا random |

ملاحظة N_TEST_DAYS = 73 اختاره الفريق ليتوافق مع طول فترة الاختبار المطلوبة

---

## Dual Pipeline Comparison

| القيمة | الحد | التبرير |
|--------|------|---------|
| MATCH_THRESHOLD | 10% | نسبة التسامح للاتفاق بين Spark و Python |

| Match Criteria | (diff/actual) < 0.10 | لأن القيم الناتجة من نموذجين مختلفين لا تتطابق 100% |

| Overall Agreement | Calculated | نسبة الحالات التي يتفق فيها النموذجان |

ملاحظة 10% اختارها الفريق لأن SRS يقول Exact equality is not required for independently trained models

---

## RFM Analysis

| القيمة | الحد | التبرير |
|--------|------|---------|
| R/F/M Score Range | 1-4 | تقسيم رباعي لكل مكون |

| Recency Calculation | أيام منذ آخر شراء | قياسي في RFM |

ملاحظة 1-4 بدلاً من 1-5 لأن البيانات موزعة بشكل يسمح بـ Quartiles نظيفة

---

## Model Evaluation Thresholds

| القيمة | الحد | التبرير |
|--------|------|---------|
| Good AUC | > 0.70 | فوق العشوائي بشكل واضح |
| Acceptable AUC | > 0.60 | مقبول في Temporal Split |

| High F1 | > 0.60 | توازن جيد بين Precision و Recall |

| R2 Positive | > 0 | أفضل من المتوسط Baseline |

ملاحظة هذه الحدود اختارها الفريق بناءً على طبيعة كل مهمة

---

## Other Thresholds

| الملف | القيمة | التبرير |
|-------|--------|---------|
| 13_wastage_risk_model.py | popularity_rank default = 9999 | للعناصر غير الموجودة في Train |

| 11_churn_model.py | churn = 1 - bought_later | Label مبني على الشراء في فترة الليبل |

| create_dual_test_cases.py | N_CASES = 100 | متطلب SRS 100 حالة على الأقل |

---

## Summary

جميع الـ Thresholds في المشروع

ليست hard-coded عشوائياً
مبررة بأسباب تقنية
قابلة للتعديل حسب متطلبات العمل
موثقة بشكل واضح

اختيار الفريق
Split Ratios 60/20/20
Q75 للهدر
N_TEST_DAYS = 73
MATCH_THRESHOLD = 10%
N_LAGS = 7
RFM Score Range 1-4

المعايير المستخدمة في الاختيار
الأداء على Validation Set
تجنب Overfitting
التوافق مع متطلبات SRS
القابلية للتطبيق العملي

---

آخر تحديث 2026-09-27
الفريق Student 3