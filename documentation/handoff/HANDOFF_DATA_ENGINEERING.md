\# وثيقة تسليم — الجانب الهندسي للبيانات

\## DineIQ Analytics — الطالب الأول (Data Engineering \& Big Data Foundation)



\---



\## 1. نطاق العمل المنجز



حسب SRS v1.0، نطاق الطالب الأول هو الخطوات 1 إلى 7:



| الخطوة | الوصف | الحالة |

|---|---|---|

| Step 1 | إنشاء Dataset المطعم | ✅ مكتمل |

| Step 2 | تخزين Big Data (CSV + Parquet) | ✅ مكتمل |

| Step 3 | Ingestion بـSpark | ⏳ قيد التنفيذ |

| Step 4 | تقييم جودة البيانات | ⏳ قيد التنفيذ |

| Step 5 | تنظيف البيانات | ⏳ قيد التنفيذ |

| Step 6 | دمج الجداول (10 Joins) | ⏳ قيد التنفيذ |

| Step 7 | هندسة الميزات (22 Feature) | ⏳ قيد التنفيذ |



\*\*الخطوات 8 وما بعدها خارج نطاق الطالب الأول\*\* (EDA، ML، Dashboards، Recommendation).



\---



\## 2. ما تم تسليمه فعليًا حتى الآن



\### 2.1 البيانات الخام (Raw Data)



\*\*الموقع:\*\* `full\_output/raw\_data/`



| الجدول | عدد الصفوف | حجم الملف |

|---|---|---|

| Customers | 50,000 | 889 KB |

| Restaurants | 20 | 714 B |

| Menu\_Categories | 10 | 151 B |

| Menu\_Items | 150 | 12 KB |

| Pricing\_History | 689 | 17 KB |

| Promotions | 30 | 1.8 KB |

| Promotion\_Items | 181 | 1.3 KB |

| Orders | 101,000 | 8.1 MB |

| Order\_Items | 1,066,785 | 43.9 MB |

| Ratings | 100,518 | 3.8 MB |

| Inventory | 159,000 | 9.1 MB |

| Wastage | 50,000 | 2.7 MB |

| \*\*الإجمالي\*\* | \*\*\~1.7 مليون صف\*\* | \*\*68 MB\*\* |



\### 2.2 البيانات الخام بصيغة Parquet



\*\*الموقع:\*\* `full\_output/parquet\_data/`



نفس الجداول الـ12 بصيغة Parquet — الحجم الكلي 21 MB.



\### 2.3 سكربت توليد البيانات



\*\*الموقع:\*\* `data\_generator/`



برنامج Python قابل لإعادة التشغيل بالكامل، بـSeed قابل للتحكم، والإعدادات مفصولة عن المنطق.



\### 2.4 قاموس البيانات



\*\*الموقع:\*\* `documentation/data\_dictionary/`



\- `data\_dictionary.json` — نسخة آلية

\- `DATA\_DICTIONARY.md` — نسخة مقروءة



يشرح كل عمود: الاسم، النوع، Nullability، PK/FK، الوصف، القيم المسموحة.



\### 2.5 تقارير الفحص



\*\*الموقع:\*\* `full\_output/reports/`



\- `dataset\_statistics.json` — إحصاءات الجداول

\- `data\_generation\_validation.json` — 53 فحصًا كلها نجحت



\---



\## 3. مطابقة متطلبات SRS — الأحجام



| المتطلب من SRS ص.24 | الحد الأدنى | المُسلَّم | الحالة |

|---|---|---|---|

| Order-line records | 1,000,000 | 1,066,785 | ✅ |

| Unique orders | 100,000 | 100,000 | ✅ |

| Customers | 50,000 | 50,000 | ✅ |

| Menu items | 150 | 150 | ✅ |

| Menu categories | 10 | 10 | ✅ |

| Restaurant locations | 20 | 20 | ✅ |

| Transaction history | 12 months | 364 days (2024) | ✅ |

| Rating records | 100,000 | 100,518 | ✅ |

| Wastage records | 50,000 | 50,000 | ✅ |

| Historical pricing records | Multiple | 689 | ✅ |

| Promotion campaigns | Multiple | 30 | ✅ |



\---



\## 4. مطابقة متطلبات SRS — جودة البيانات



البيانات الخام \*\*تحتوي عمدًا\*\* على 15 حالة عدم جودة، وهي مطلوبة من SRS Step 4:



| # | الحالة | العدد |

|---|---|---|

| 1 | قيم مفقودة | 4,674 |

| 2 | طلبات مكررة | 1,000 |

| 3 | سطور طلبات مكررة | 10,562 |

| 4 | أسعار منيو غير صالحة | 1 |

| 5 | كميات سالبة | 2,133 |

| 6 | تواريخ غير صالحة | 101 |

| 7 | تقييمات غير صالحة | 301 |

| 8 | معرّفات عملاء مفقودة | 303 |

| 9 | معرّفات أصناف مفقودة | 3,200 |

| 10 | معرّفات مطاعم غير صالحة | 202 |

| 11 | كميات هدر مستحيلة | 74 |

| 12 | خصومات غير صحيحة | 2,134 |

| 13 | معاملات ملغاة | 5,025 |

| 14 | وحدات قياس غير متسقة | 627 |

| 15 | مراجع مواقع غير صالحة | 202 |



\---



\## 5. مطابقة متطلبات SRS — الحالات الصعبة (Step 11)



كل الحالات العشر موجودة ومُقاسة من البيانات الفعلية:



| # | الحالة | العدد |

|---|---|---|

| 1 | طبق عالي البيع لكن خاسر | 4 |

| 2 | طبق مربح لكن قليل البيع | 19 |

| 3 | طبق شعبي مع هدر عالٍ | 12 |

| 4 | طبق عالي التقييم لكن ضعيف الربح | 7 |

| 5 | طبق منخفض التقييم مع بيع عالٍ | 4 |

| 6 | طبق يعتمد على العروض | 13 |

| 7 | طبق يختلف أداؤه بين المواقع | 139 |

| 8 | طبق يبيع في الويكند فقط | 14 |

| 9 | طبق موسمي | 21 |

| 10 | طبق جديد بتاريخ غير كافٍ | 12 |



\---



\## 6. العلاقات بين الجداول



جميع العلاقات العشر من SRS Step 6 موجودة بـPK/FK صريح:



| العلاقة | التنفيذ |

|---|---|

| Orders ↔ Customers | customer\_id |

| Orders ↔ Order\_Items | order\_id |

| Order\_Items ↔ Menu\_Items | menu\_item\_id |

| Menu\_Items ↔ Menu\_Categories | category\_id |

| Orders ↔ Restaurants | restaurant\_id |

| Orders ↔ Promotions | promotion\_id |

| Menu\_Items ↔ Pricing\_History | menu\_item\_id |

| Menu\_Items ↔ Ratings | menu\_item\_id |

| Menu\_Items ↔ Inventory | menu\_item\_id |

| Menu\_Items ↔ Wastage | menu\_item\_id |



\*\*جدول ربط تقني:\*\* Promotion\_Items — يربط Promotions بـMenu\_Items (مشتق من SRS FR viii "applicable menu items").



\---



\## 7. الملفات التي يستلمها كل طالب



\### للطالب 2 (Data Science \& ML):



\- `full\_output/raw\_data/` — البيانات الخام

\- `full\_output/parquet\_data/` — البيانات بصيغة Parquet

\- `full\_output/processed\_data/clean/` — البيانات النظيفة (قريبًا)

\- `full\_output/processed\_data/features/` — الميزات الجاهزة (قريبًا)

\- `documentation/data\_dictionary/data\_dictionary.json` — المرجع للـSchemas

\- `documentation/reports/DATA\_ENGINEERING\_REPORT.md` — التقرير الكامل



\### للطالب 3 (Dashboard \& Recommendations):



\- `full\_output/reports/` — تقارير الفحوصات

\- `full\_output/processed\_data/features/` — الميزات (قريبًا)

\- `documentation/data\_dictionary/DATA\_DICTIONARY.md` — المرجع للعرض



\### لمسؤول التوثيق:



\- هذه الوثيقة

\- `documentation/reports/DATA\_ENGINEERING\_REPORT.md` — التقرير التفصيلي

\- `documentation/data\_dictionary/` — قاموس البيانات

\- `data\_generator/` — سكربت توليد البيانات



\---



\## 8. المخرجات المتبقية



| المخرَج | يعتمد على | الحالة |

|---|---|---|

| `step3\_ingestion\_report.json` | Spark Ingestion | ⏳ |

| `data\_quality\_report.json` | Spark Quality Engine | ⏳ |

| `cleaning\_report.json` | Spark Cleaning | ⏳ |

| `feature\_engineering\_report.json` | Spark Features | ⏳ |

| `processed\_data/clean/` | Spark Cleaning | ⏳ |

| `processed\_data/features/` | Spark Features | ⏳ |



هذه المخرجات ستُسلَّم فور اكتمال تشغيل Spark.



\---



\## 9. طريقة إعادة إنتاج كل شيء



```bash

\# توليد البيانات الخام

python -m data\_generator.run\_generator --out full\_output



\# تفعيل بيئة Spark

.venv\_spark\\Scripts\\activate



\# تشغيل الوحدات الأربعة

python -m spark\_jobs.tests.test\_u11\_ingestion

python -m spark\_jobs.tests.test\_u12\_quality

python -m spark\_jobs.tests.test\_u13\_cleaning

python -m spark\_jobs.tests.test\_u14\_features

