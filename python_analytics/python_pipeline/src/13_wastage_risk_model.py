"""
Wastage Risk Model - Fix Data Leakage
======================================
historical_wastage = فقط قبل wastage_date (shift)
demand_qty = متوسط آخر 7 و 30 يوم فقط
popularity_rank = computed من Train فقط
Temporal split
"""

import json
import pickle
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, f1_score, precision_score,
    recall_score, roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

from python_pipeline.config import MODELS_DIR, RANDOM_SEED
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


FEATURES = [
    "lag_demand_7d",
    "lag_demand_30d",
    "hist_wastage_before",
    "dow_num",
    "month_num",
    "is_promo",
    "popularity_rank_train",
]


def load_sources():
    # تحميل البيانات الخام
    w = load_clean_table("Wastage")
    w["wastage_date"] = pd.to_datetime(w["wastage_date"])
    w["quantity_wasted"] = pd.to_numeric(w["quantity_wasted"], errors="coerce").fillna(0).astype(float)
    w["wastage_cost"] = pd.to_numeric(w["wastage_cost"], errors="coerce").fillna(0).astype(float)

    o = load_clean_table("Orders")
    i = load_clean_table("Order_Items")
    o["order_timestamp"] = pd.to_datetime(o["order_timestamp"])
    o["date"] = o["order_timestamp"].dt.normalize()
    i["quantity"] = pd.to_numeric(i["quantity"], errors="coerce").fillna(0).astype(float)

    m = i.merge(
        o[["order_id", "date", "restaurant_id", "promotion_id"]],
        on="order_id", how="inner",
    )

    demand = m.groupby(["menu_item_id", "restaurant_id", "date"]).agg(
        demand_qty=("quantity", "sum"),
        is_promo=("promotion_id", lambda s: int(s.notna().any())),
    ).reset_index()
    demand["demand_qty"] = demand["demand_qty"].astype(float)

    wd = w.groupby(["menu_item_id", "restaurant_id", "wastage_date"]).agg(
        wastage_qty=("quantity_wasted", "sum"),
        wastage_cost=("wastage_cost", "sum"),
    ).reset_index()
    wd["wastage_qty"] = wd["wastage_qty"].astype(float)

    df = wd.merge(
        demand,
        left_on=["menu_item_id", "restaurant_id", "wastage_date"],
        right_on=["menu_item_id", "restaurant_id", "date"],
        how="left",
    )
    df["demand_qty"] = df["demand_qty"].fillna(0).astype(float)
    df["is_promo"] = df["is_promo"].fillna(0).astype(int)
    df["dow_num"] = df["wastage_date"].dt.dayofweek
    df["month_num"] = df["wastage_date"].dt.month

    return df


def add_lag_features(df):
    # ميزات زمنيه من الماضي فقط
    df = df.sort_values(["menu_item_id", "restaurant_id", "wastage_date"]).copy()
    grp = df.groupby(["menu_item_id", "restaurant_id"])

    # متوسط الطلب لاخر 7 ايام
    df["lag_demand_7d"] = grp["demand_qty"].transform(
        lambda s: s.shift(1).rolling(7, min_periods=1).mean()
    ).fillna(0)

    # متوسط الطلب لاخر 30 يوم
    df["lag_demand_30d"] = grp["demand_qty"].transform(
        lambda s: s.shift(1).rolling(30, min_periods=1).mean()
    ).fillna(0)

    # الهدر التاريخي قبل هذا اليوم فقط
    df["hist_wastage_before"] = grp["wastage_qty"].transform(
        lambda s: s.shift(1).expanding().sum()
    ).fillna(0)

    return df


def add_popularity_rank(df, train_item_ids=None):
    # Popularity Rank محسوب من Train فقط
    df = df.copy()

    if train_item_ids is None:
        df["popularity_rank_train"] = 9999
        return df

    train_df = df[df["menu_item_id"].isin(train_item_ids)].copy()
    if len(train_df) == 0:
        df["popularity_rank_train"] = 9999
        return df

    pop = train_df.groupby("menu_item_id")["lag_demand_30d"].mean().rank(
        ascending=False
    ).reset_index()
    pop.columns = ["menu_item_id", "popularity_rank_train"]

    if "popularity_rank_train" in df.columns:
        df = df.drop(columns=["popularity_rank_train"])

    df = df.merge(pop, on="menu_item_id", how="left")
    df["popularity_rank_train"] = df["popularity_rank_train"].fillna(9999)
    return df


def build_label(df):
    # label: هل الهدر عالي (>= Q75)
    q75 = df["wastage_qty"].quantile(0.75)
    df = df.copy()
    df["is_high_waste"] = (df["wastage_qty"] >= q75).astype(int)
    return df, q75


def temporal_split(df):
    # تقسيم زمني
    df = df.sort_values("wastage_date").reset_index(drop=True)

    n = len(df)
    n_train = int(n * 0.6)
    n_val = int(n * 0.2)

    train = df.iloc[:n_train].copy()
    val = df.iloc[n_train:n_train + n_val].copy()
    test = df.iloc[n_train + n_val:].copy()

    log.info("Temporal Split:")
    log.info(f"  Train: {len(train):,} | {train['wastage_date'].min()} -> {train['wastage_date'].max()}")
    log.info(f"  Val:   {len(val):,} | {val['wastage_date'].min()} -> {val['wastage_date'].max()}")
    log.info(f"  Test:  {len(test):,} | {test['wastage_date'].min()} -> {test['wastage_date'].max()}")

    return train, val, test


def train_models(train, val, test):
    X_train = train[FEATURES].fillna(0).astype(float)
    y_train = train["is_high_waste"].astype(int)
    X_val = val[FEATURES].fillna(0).astype(float)
    y_val = val["is_high_waste"].astype(int)
    X_test = test[FEATURES].fillna(0).astype(float)
    y_test = test["is_high_waste"].astype(int)

    scaler = StandardScaler().fit(X_train)
    X_train_s = scaler.transform(X_train)
    X_val_s = scaler.transform(X_val)
    X_test_s = scaler.transform(X_test)

    models = {
        "logistic": LogisticRegression(
            max_iter=1000, random_state=RANDOM_SEED, class_weight="balanced"
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=10,
            random_state=RANDOM_SEED, n_jobs=-1, class_weight="balanced"
        ),
    }

    results = []
    trained = {}
    for name, m in models.items():
        Xtr = X_train_s if name == "logistic" else X_train
        Xva = X_val_s if name == "logistic" else X_val
        Xte = X_test_s if name == "logistic" else X_test

        m.fit(Xtr, y_train)

        val_pred = m.predict(Xva)
        val_prob = m.predict_proba(Xva)[:, 1]
        test_pred = m.predict(Xte)
        test_prob = m.predict_proba(Xte)[:, 1]

        row = {
            "model": name,
            "val_accuracy": round(accuracy_score(y_val, val_pred), 4),
            "val_f1": round(f1_score(y_val, val_pred, zero_division=0), 4),
            "val_auc": round(roc_auc_score(y_val, val_prob), 4),
            "test_accuracy": round(accuracy_score(y_test, test_pred), 4),
            "test_precision": round(precision_score(y_test, test_pred, zero_division=0), 4),
            "test_recall": round(recall_score(y_test, test_pred, zero_division=0), 4),
            "test_f1": round(f1_score(y_test, test_pred, zero_division=0), 4),
            "test_auc": round(roc_auc_score(y_test, test_prob), 4),
            "n_train": int(len(X_train)),
            "n_val": int(len(X_val)),
            "n_test": int(len(X_test)),
        }
        results.append(row)
        trained[name] = m
        log.info(f"{name}: val_auc={row['val_auc']} test_auc={row['test_auc']} test_f1={row['test_f1']}")

    return results, trained, scaler


def predict_test(test, model, scaler):
    X = test[FEATURES].fillna(0).astype(float)
    X_s = scaler.transform(X)
    prob = model.predict_proba(X_s)[:, 1]
    out = test.copy()
    out["wastage_risk_prob"] = prob.round(4)
    out["wastage_risk_class"] = (prob >= 0.5).astype(int)
    return out


def run():
    log.info("Starting wastage risk model (No Leakage)")

    # 1. تحميل
    df = load_sources()
    log.info(f"Raw rows: {len(df):,}")

    # 2. Lag features
    df = add_lag_features(df)

    # 3. Label
    df, q75 = build_label(df)
    log.info(f"Q75 threshold: {q75:.2f}")

    # 4. Temporal Split
    train, val, test = temporal_split(df)

    # 5. Popularity من Train فقط
    train_items = set(train["menu_item_id"].unique())
    train = add_popularity_rank(train, train_item_ids=train_items)
    val = add_popularity_rank(val, train_item_ids=train_items)
    test = add_popularity_rank(test, train_item_ids=train_items)

    # 6. التدريب
    results, models, scaler = train_models(train, val, test)

    # 7. التنبؤ على Test
    best = models["random_forest"]
    scored = predict_test(test, best, scaler)

    # 8. الحفظ
    save_stage(pd.DataFrame(results), "13_wastage_risk_model", "metrics.parquet")
    save_stage(
        scored[["menu_item_id", "restaurant_id", "wastage_date",
                "wastage_qty", "lag_demand_7d", "hist_wastage_before",
                "wastage_risk_prob", "wastage_risk_class"]],
        "13_wastage_risk_model", "wastage_risk_predictions.parquet",
    )

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MODELS_DIR / "wastage_risk_model.pkl", "wb") as f:
        pickle.dump(best, f)
    with open(MODELS_DIR / "wastage_risk_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # 9. تحديث الاصدارات
    version_path = MODELS_DIR / "model_versions.json"
    if version_path.exists():
        with open(version_path, encoding="utf-8") as f:
            versions = json.load(f)
    else:
        versions = {}

    versions["wastage_risk_model"] = {
        "version": "v1.1-no-leakage",
        "created_at": datetime.now().isoformat(),
        "model": "RandomForest",
        "split_method": "temporal",
        "n_features": len(FEATURES),
        "features": FEATURES,
        "test_auc": [r["test_auc"] for r in results if r["model"] == "random_forest"][0],
        "q75_threshold": float(q75),
    }
    with open(version_path, "w", encoding="utf-8") as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)

    log.info("Wastage risk model done")


if __name__ == "__main__":
    run()