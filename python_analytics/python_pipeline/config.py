"""
اعدادات المشروع
كل شي في مكان واحد عشان لو احتجنا نغير رقم ما ندور عليه في كل الملفات
"""

from pathlib import Path

# مسار المشروع
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# من هنا نقرا بيانات الطالب الاول
CLEAN_DIR = PROJECT_ROOT / "full_output" / "processed_data" / "clean"

# مجلداتنا
PIPELINE_DIR = PROJECT_ROOT / "python_pipeline"
SRC_DIR      = PIPELINE_DIR / "src"
LIB_DIR      = PIPELINE_DIR / "lib"
TESTS_DIR    = PIPELINE_DIR / "tests"
LOGS_DIR     = PIPELINE_DIR / "logs"

# النتائج - كلها في مكان واحد
RESULTS_DIR = PIPELINE_DIR / "results"
PARQUET_DIR = RESULTS_DIR / "parquet"
CSV_DIR     = RESULTS_DIR / "csv"
JSON_DIR    = RESULTS_DIR / "json"
MODELS_DIR  = RESULTS_DIR / "models"
REPORTS_DIR = RESULTS_DIR / "reports"

#  time
# cutoff للميزات عشان ما يدخل المستقبل في التدريب
FEATURE_WINDOW_END = "2024-09-30"

# من هنا نقيس سلوك العميل للـchurn
LABEL_WINDOW_START = "2024-10-01"
LABEL_WINDOW_END = "2024-12-31"

# seed عشان النتايج تتكرر
RANDOM_SEED = 42

# rfm
RFM_QUANTILES = 4

# clustering
KMEANS_K_RANGE = [3, 4, 5, 6, 7, 8]

# market basket
MIN_SUPPORT    = 0.002
MIN_CONFIDENCE = 0.15
MIN_LIFT       = 1.2
MAX_ITEMSET    = 3

# wastage
WASTAGE_LOW    = 0.33
WASTAGE_MEDIUM = 0.66

# anomalies
Z_THRESHOLD      = 3.0
SALES_SPIKE_MULT = 4.0
SALES_DROP_MULT  = 0.15
RATING_HIGH      = 4.3
RATING_LOW       = 2.2

# churn split
TEST_SIZE = 0.2
VAL_SIZE  = 0.2

# الجداول المطلوبه
REQUIRED_TABLES = [
    "Customers",
    "Orders",
    "Order_Items",
    "Menu_Items",
    "Menu_Categories",
    "Restaurants",
    "Pricing_History",
    "Promotions",
    "Promotion_Items",
    "Ratings",
    "Inventory",
    "Wastage",
]

# الحد الادنى للسطور
MIN_ROWS = {
    "Customers":       50_000,
    "Orders":          100_000,
    "Order_Items":     1_000_000,
    "Menu_Items":      150,
    "Menu_Categories": 10,
    "Restaurants":     20,
    "Ratings":         100_000,
    "Wastage":         50_000,
}

def stage_dir(stage_name):
    from pathlib import Path
    p = PARQUET_DIR / stage_name
    Path(p).mkdir(parents=True, exist_ok=True)
    return p