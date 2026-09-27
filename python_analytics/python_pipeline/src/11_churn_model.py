"""
Churn Model — Temporal Cohort Split with Feature Cutoff
=======================================================

Methodology (SRS Step 21):
- Each cohort uses a DIFFERENT feature window and label window.
- Train: features up to 2024-06-30, label from 2024-07-01 to 2024-09-30
- Val:   features up to 2024-08-31, label from 2024-09-01 to 2024-10-31
- Test:  features up to 2024-09-30, label from 2024-10-01 to 2024-12-31

This is a true time-aware validation: train uses earlier periods and
labels earlier outcomes, test uses later periods and labels later outcomes.

No random split. No data leakage.
"""

import json
import pickle
from datetime import datetime

import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from python_pipeline.config import MODELS_DIR, RANDOM_SEED
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)

FEATURES = [
    "recency", "frequency", "monetary", "aov", "distinct_items",
    "r_score", "f_score", "m_score",
    "promo_sensitivity", "peak_ratio", "weekend_ratio",
    "freq_recent_90d", "freq_trend",
    "avg_days_between_orders", "distinct_categories",
]

# نوافذ الcohorts
COHORTS = {
    "train": {
        "feature_end": pd.Timestamp("2024-06-30"),
        "label_start": pd.Timestamp("2024-07-01"),
        "label_end":   pd.Timestamp("2024-09-30"),
    },
    "val": {
        "feature_end": pd.Timestamp("2024-08-31"),
        "label_start": pd.Timestamp("2024-09-01"),
        "label_end":   pd.Timestamp("2024-10-31"),
    },
    "test": {
        "feature_end": pd.Timestamp("2024-09-30"),
        "label_start": pd.Timestamp("2024-10-01"),
        "label_end":   pd.Timestamp("2024-12-31"),
    },
}


def load_orders():
    o = load_clean_table("Orders")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o = o[o["order_status"] == "completed"].copy()
    return o


def build_features_for_cohort(orders, items, menu, feature_end):
    """بناء الميزات من نافذة محددة لكل cohort"""
    o = orders[orders["order_timestamp"] < feature_end].copy()
    if len(o) == 0:
        return pd.DataFrame(columns=["customer_id"] + FEATURES)

    # الميزات الاساسيه
    o["hour"] = o["order_timestamp"].dt.hour
    o["weekend"] = o["order_timestamp"].dt.dayofweek >= 5
    o["peak"] = o["hour"].between(11, 21)

    # RFM
    rfm = o.groupby("customer_id").agg(
        last_order=("order_timestamp", "max"),
        first_order=("order_timestamp", "min"),
        frequency=("order_id", "nunique"),
    ).reset_index()

    # monetary من items
    oi = items.merge(o[["order_id", "customer_id"]], on="order_id", how="inner")
    oi["quantity"] = pd.to_numeric(oi["quantity"], errors="coerce").fillna(0)
    oi["line_total"] = pd.to_numeric(oi["line_total"], errors="coerce").fillna(0)

    monetary = oi.groupby("customer_id").agg(
        monetary=("line_total", "sum"),
        distinct_items=("menu_item_id", "nunique"),
    ).reset_index()

    rfm = rfm.merge(monetary, on="customer_id", how="left")
    rfm["monetary"] = rfm["monetary"].fillna(0)
    rfm["distinct_items"] = rfm["distinct_items"].fillna(0)

    # recency و aov
    rfm["recency"] = (feature_end - rfm["last_order"]).dt.days
    rfm["aov"] = (rfm["monetary"] / rfm["frequency"].replace(0, 1)).round(2)

    # rfm scores
    rfm["r_score"] = pd.qcut(rfm["recency"].rank(method="first"), 4, labels=[4,3,2,1]).astype(int)
    rfm["f_score"] = pd.qcut(rfm["frequency"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)
    rfm["m_score"] = pd.qcut(rfm["monetary"].rank(method="first"), 4, labels=[1,2,3,4]).astype(int)

    # behavioral
    behavioral = o.groupby("customer_id").agg(
        peak_ratio=("peak", "mean"),
        weekend_ratio=("weekend", "mean"),
    ).reset_index()

    promo_col = o.assign(had_promo=o["promotion_id"].notna()).groupby("customer_id")["had_promo"].mean()
    promo_col = promo_col.rename("promo_sensitivity").reset_index()

    # freq_recent_90d
    recent_90 = feature_end - pd.Timedelta(days=90)
    freq_90 = o[o["order_timestamp"] >= recent_90].groupby("customer_id")["order_id"].nunique()
    freq_90 = freq_90.rename("freq_recent_90d").reset_index()

    # freq_trend
    freq_all = o.groupby("customer_id")["order_id"].nunique().rename("total_freq").reset_index()
    freq_df = freq_90.merge(freq_all, on="customer_id", how="outer").fillna(0)
    freq_df["freq_trend"] = (freq_df["freq_recent_90d"] / freq_df["total_freq"].replace(0, 1)).round(4)
    freq_df = freq_df[["customer_id", "freq_recent_90d", "freq_trend"]]

    # avg_days_between_orders
    def avg_gap(s):
        s = s.sort_values()
        if len(s) < 2:
            return 0
        return s.diff().dt.days.mean()

    gaps = o.groupby("customer_id")["order_timestamp"].apply(avg_gap).rename("avg_days_between_orders").reset_index()

    # distinct_categories
    oi_cat = oi.merge(menu[["menu_item_id", "category_id"]], on="menu_item_id", how="left")
    distinct_cat = oi_cat.groupby("customer_id")["category_id"].nunique().rename("distinct_categories").reset_index()

    # نضم كل شي
    out = rfm[["customer_id", "recency", "frequency", "monetary", "aov",
               "distinct_items", "r_score", "f_score", "m_score"]].copy()
    for df in [behavioral, promo_col, freq_df, gaps, distinct_cat]:
        out = out.merge(df, on="customer_id", how="left")

    # fill
    for c in ["peak_ratio", "weekend_ratio", "promo_sensitivity",
              "freq_recent_90d", "freq_trend", "avg_days_between_orders",
              "distinct_categories"]:
        if c in out.columns:
            out[c] = out[c].fillna(0)

    return out


def build_label_for_cohort(orders, label_start, label_end):
    """العميل نشط اذا اشترى خلال نافذه الlabel"""
    o = orders[(orders["order_timestamp"] >= label_start) & (orders["order_timestamp"] <= label_end)]
    return set(o["customer_id"].unique())


def build_cohort_dataset(orders, items, menu, cohort_cfg):
    feats = build_features_for_cohort(orders, items, menu, cohort_cfg["feature_end"])
    if len(feats) == 0:
        return feats, pd.Series()
    active = build_label_for_cohort(orders, cohort_cfg["label_start"], cohort_cfg["label_end"])
    feats["bought_later"] = feats["customer_id"].isin(active).astype(int)
    feats["churn"] = 1 - feats["bought_later"]
    feats = feats[feats["frequency"] > 0].reset_index(drop=True)
    return feats, feats["churn"]


def train_models(X_train, y_train, X_val, y_val, X_test, y_test):
    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    models = {
        "logistic": LogisticRegression(max_iter=2000, random_state=RANDOM_SEED, class_weight="balanced"),
        "random_forest": RandomForestClassifier(n_estimators=300, max_depth=12, min_samples_leaf=5,
                                                random_state=RANDOM_SEED, n_jobs=-1, class_weight="balanced"),
        "gradient_boosting": GradientBoostingClassifier(n_estimators=200, max_depth=5,
                                                       learning_rate=0.05, random_state=RANDOM_SEED),
    }

    results = []
    trained = {}
    for name, m in models.items():
        Xtr_use = X_train_s if name == "logistic" else X_train
        Xval_use = X_val_s if name == "logistic" else X_val
        Xte_use = X_test_s if name == "logistic" else X_test

        m.fit(Xtr_use, y_train)
        val_pred = m.predict(Xval_use)
        val_prob = m.predict_proba(Xval_use)[:, 1]
        test_pred = m.predict(Xte_use)
        test_prob = m.predict_proba(Xte_use)[:, 1]

        row = {
            "model": name,
            "train_size": int(len(X_train)),
            "val_size": int(len(X_val)),
            "test_size": int(len(X_test)),
            "val_accuracy": round(accuracy_score(y_val, val_pred), 4),
            "val_f1": round(f1_score(y_val, val_pred, zero_division=0), 4),
            "val_auc": round(roc_auc_score(y_val, val_prob), 4),
            "test_accuracy": round(accuracy_score(y_test, test_pred), 4),
            "test_precision": round(precision_score(y_test, test_pred, zero_division=0), 4),
            "test_recall": round(recall_score(y_test, test_pred, zero_division=0), 4),
            "test_f1": round(f1_score(y_test, test_pred, zero_division=0), 4),
            "test_auc": round(roc_auc_score(y_test, test_prob), 4),
            "split_method": "temporal_cohort_feature_cutoff",
            "confusion_matrix": json.dumps(confusion_matrix(y_test, test_pred).tolist()),
        }
        results.append(row)
        trained[name] = m
        log.info(f"{name}: val_auc={row['val_auc']} test_auc={row['test_auc']} test_f1={row['test_f1']}")

    return results, trained, scaler, X_test, y_test


def feature_importance(models):
    rf = models.get("random_forest")
    if rf is None:
        return pd.DataFrame()
    return pd.DataFrame({
        "feature": FEATURES,
        "importance": rf.feature_importances_.round(4),
    }).sort_values("importance", ascending=False).reset_index(drop=True)


def sample_predictions(models, X_test, y_test):
    rf = models["random_forest"]
    pred = rf.predict(X_test)
    prob = rf.predict_proba(X_test)[:, 1]
    sample = X_test.copy().head(100).reset_index(drop=True)
    sample["actual"] = y_test.values[:100]
    sample["predicted"] = pred[:100]
    sample["probability"] = prob[:100].round(4)
    return sample


def save_models(models, scaler):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    for name, m in models.items():
        with open(MODELS_DIR / f"churn_{name}.pkl", "wb") as f:
            pickle.dump(m, f)
    with open(MODELS_DIR / "churn_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    log.info(f"models saved in {MODELS_DIR}")


def save_model_versions(results):
    versions = {
        "churn_models": {
            "version": "v1.3",
            "created_at": datetime.now().isoformat(),
            "split_method": "temporal_cohort_feature_cutoff",
            "features": FEATURES,
            "algorithms": [
                {"name": r["model"], "test_accuracy": r["test_accuracy"],
                 "test_f1": r["test_f1"], "test_auc": r["test_auc"]}
                for r in results
            ],
        },
        "forecast_model": {
            "version": "v1.0",
            "model": "LinearRegression",
            "feature": "time_index",
            "n_train": 266,
            "n_test": 100,
        },
    }
    path = MODELS_DIR / "model_versions.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)
    log.info(f"model versions saved: {path}")


def run():
    log.info("Starting churn model with Feature Cutoff Temporal Cohorts")

    orders = load_orders()
    items = load_clean_table("Order_Items")
    menu = load_clean_table("Menu_Items")

    log.info(f"orders loaded: {len(orders):,}")

    # نبني 3 cohorts
    datasets = {}
    for name, cfg in COHORTS.items():
        df, y = build_cohort_dataset(orders, items, menu, cfg)
        log.info(f"cohort {name}: features_end={cfg['feature_end'].date()}, "
                 f"label={cfg['label_start'].date()} -> {cfg['label_end'].date()}, "
                 f"rows={len(df)}, churn_rate={df['churn'].mean():.3f}" if len(df) else "")
        datasets[name] = df

    train = datasets["train"]
    val = datasets["val"]
    test = datasets["test"]

    if len(train) == 0 or len(val) == 0 or len(test) == 0:
        log.error("empty cohort - check date ranges")
        return

    X_train = train[FEATURES].fillna(0).astype(float)
    y_train = train["churn"].astype(int)
    X_val = val[FEATURES].fillna(0).astype(float)
    y_val = val["churn"].astype(int)
    X_test = test[FEATURES].fillna(0).astype(float)
    y_test = test["churn"].astype(int)

    results, models, scaler, X_test_final, y_test_final = train_models(
        X_train, y_train, X_val, y_val, X_test, y_test
    )

    save_stage(pd.DataFrame(results), "11_churn", "churn_metrics.parquet")

    # نحفظ test فقط (cohort test)
    test_save = test[["customer_id", "churn"] + FEATURES].copy()
    save_stage(test_save, "11_churn", "churn_dataset.parquet")

    imp = feature_importance(models)
    if len(imp):
        save_stage(imp, "11_churn", "churn_feature_importance.parquet")
        log.info(f"\nTop features:\n{imp.to_string(index=False)}")

    samples = sample_predictions(models, X_test_final, y_test_final)
    save_stage(samples, "11_churn", "churn_predictions_sample.parquet")
    log.info("saved 100 sample predictions")

    save_models(models, scaler)
    save_model_versions(results)
    log.info("churn model done")


if __name__ == "__main__":
    run()