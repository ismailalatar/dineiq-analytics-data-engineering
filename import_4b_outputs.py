"""Import Student 4B outputs into App DB."""
import os, glob
import pandas as pd
from app import create_app
from app.extensions import db
from app.models.integration import (Recommendation, DualPipelineComparison,
                                    SlowMovingDish, LocationIntelligence,
                                    ChannelIntelligence, WhatIfResult,
                                    SurpriseModificationReadiness)

SEARCH_ROOT = r"D:\DineIQ"

def find(name):
    hits = glob.glob(os.path.join(SEARCH_ROOT, "**", name), recursive=True)
    # prefer analytical_integration folder
    for h in hits:
        if "analytical_integration" in h:
            return h
    return hits[0] if hits else None

def read(name):
    p = find(name)
    if not p:
        print(f"  [skip] {name} not found")
        return None
    print(f"  [read] {p}")
    return pd.read_parquet(p) if p.endswith(".parquet") else pd.read_csv(p)

def s(v):
    if v is None: return None
    try:
        if pd.isna(v): return None
    except Exception:
        pass
    return str(v)

def f(v):
    try:
        if pd.isna(v): return None
        return float(v)
    except Exception:
        return None

def i(v):
    try:
        if pd.isna(v): return None
        return int(v)
    except Exception:
        return None

def import_all():
    app = create_app()
    with app.app_context():
        # 1. Recommendations
        df = read("recommendations.csv")
        if df is not None:
            Recommendation.query.delete()
            for _, r in df.iterrows():
                db.session.add(Recommendation(
                    finding=s(r.get("finding"))[:200] if s(r.get("finding")) else None,
                    evidence=s(r.get("evidence")),
                    action=s(r.get("action"))[:300] if s(r.get("action")) else None,
                    priority=s(r.get("priority")),
                    source=s(r.get("source")),
                    menu_item_id=s(r.get("menu_item_id")),
                    item_name=s(r.get("item_name")),
                ))
            db.session.commit()
            print(f"  recommendations: {len(df)}")

        # 2. Dual pipeline
        df = read("dual_pipeline_comparison.parquet")
        if df is not None:
            DualPipelineComparison.query.delete()
            for _, r in df.iterrows():
                db.session.add(DualPipelineComparison(
                    date=s(r.get("date")), time_index=i(r.get("time_index")),
                    actual=f(r.get("actual")), order_count=i(r.get("order_count")),
                    python_prediction=f(r.get("python_prediction")),
                    spark_prediction=f(r.get("spark_prediction")),
                    diff=f(r.get("diff")), error_pct=f(r.get("error_pct")),
                    match=i(r.get("match")), explanation=s(r.get("explanation")),
                ))
            db.session.commit()
            print(f"  dual_pipeline_comparison: {len(df)}")

        # 3. Slow moving
        df = read("slow_moving_dishes.parquet")
        if df is not None:
            SlowMovingDish.query.delete()
            for _, r in df.iterrows():
                db.session.add(SlowMovingDish(
                    menu_item_id=s(r.get("menu_item_id")), item_name=s(r.get("item_name")),
                    category_name=s(r.get("category_name")),
                    quantity_sold=f(r.get("quantity_sold")), revenue=f(r.get("revenue")),
                    profit_pct=f(r.get("profit_pct")), wastage_pct=f(r.get("wastage_pct")),
                    promotion_dependency=f(r.get("promotion_dependency")),
                    performance_class=s(r.get("performance_class")),
                    finding=s(r.get("finding")), evidence=s(r.get("evidence")),
                    action=s(r.get("action")), priority=s(r.get("priority")),
                ))
            db.session.commit()
            print(f"  slow_moving_dishes: {len(df)}")

        # 4. Location intelligence
        df = read("location_intelligence.parquet")
        if df is not None:
            LocationIntelligence.query.delete()
            for _, r in df.iterrows():
                db.session.add(LocationIntelligence(
                    menu_item_id=s(r.get("menu_item_id")), item_name=s(r.get("item_name")),
                    location_count=i(r.get("location_count")),
                    max_location_quantity=f(r.get("max_location_quantity")),
                    min_location_quantity=f(r.get("min_location_quantity")),
                    location_gap=f(r.get("location_gap")),
                    location_ratio=f(r.get("location_ratio")),
                    quantity_sold=f(r.get("quantity_sold")), revenue=f(r.get("revenue")),
                    case_type=s(r.get("case_type")),
                    finding=s(r.get("finding")), evidence=s(r.get("evidence")),
                    action=s(r.get("action")), priority=s(r.get("priority")),
                ))
            db.session.commit()
            print(f"  location_intelligence: {len(df)}")

        # 5. Channel intelligence
        df = read("channel_intelligence.parquet")
        if df is not None:
            ChannelIntelligence.query.delete()
            for _, r in df.iterrows():
                db.session.add(ChannelIntelligence(
                    preferred_channel=s(r.get("preferred_channel")),
                    customers=i(r.get("customers")), orders=i(r.get("orders")),
                    revenue=f(r.get("revenue")),
                    avg_order_value=f(r.get("avg_order_value")),
                    avg_basket_size=f(r.get("avg_basket_size")),
                    avg_recency=f(r.get("avg_recency")),
                    finding=s(r.get("finding")), evidence=s(r.get("evidence")),
                    action=s(r.get("action")), priority=s(r.get("priority")),
                ))
            db.session.commit()
            print(f"  channel_intelligence: {len(df)}")

        # 6. What-if
        df = read("what_if_results.csv")
        if df is not None:
            WhatIfResult.query.delete()
            for _, r in df.iterrows():
                db.session.add(WhatIfResult(
                    scenario=s(r.get("scenario")), assumption=s(r.get("assumption")),
                    estimate_flag=s(r.get("estimate_flag")),
                    menu_item_id=s(r.get("menu_item_id")), item_name=s(r.get("item_name")),
                    baseline_demand=f(r.get("baseline_demand")),
                    estimated_demand=f(r.get("estimated_demand")),
                    baseline_revenue=f(r.get("baseline_revenue")),
                    estimated_revenue=f(r.get("estimated_revenue")),
                    baseline_contribution_margin=f(r.get("baseline_contribution_margin")),
                    estimated_contribution_margin=f(r.get("estimated_contribution_margin")),
                    baseline_wastage_pct=f(r.get("baseline_wastage_pct")),
                    estimated_wastage_pct=f(r.get("estimated_wastage_pct")),
                    baseline_profitability_pct=f(r.get("baseline_profitability_pct")),
                    estimated_profitability_pct=f(r.get("estimated_profitability_pct")),
                    revenue_change=f(r.get("revenue_change")),
                    contribution_margin_change=f(r.get("contribution_margin_change")),
                    demand_change=f(r.get("demand_change")),
                ))
            db.session.commit()
            print(f"  what_if_results: {len(df)}")

        # 7. Surprise readiness
        df = read("surprise_modification_readiness.csv")
        if df is not None:
            SurpriseModificationReadiness.query.delete()
            for _, r in df.iterrows():
                db.session.add(SurpriseModificationReadiness(
                    modification=s(r.get("modification")),
                    parameter=s(r.get("parameter")),
                    current_value=s(r.get("current_value")),
                    status=s(r.get("status")),
                ))
            db.session.commit()
            print(f"  surprise_readiness: {len(df)}")

        print("\nDONE import 4B outputs")

if __name__ == "__main__":
    import_all()