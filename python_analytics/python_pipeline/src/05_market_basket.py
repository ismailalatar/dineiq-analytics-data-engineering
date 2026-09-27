"""
نحسب قواعد الشراء المشترك apriori
support confidence lift للازواج المتكرره
نستبعد الصنف مع نفسه بالمعرف او بالاسم
المخرجات تروح لمجلد 05_basket
"""

from collections import Counter
from itertools import combinations

import pandas as pd

from python_pipeline.config import MIN_SUPPORT, MIN_CONFIDENCE, MIN_LIFT
from python_pipeline.lib.io_helpers import load_clean_table, save_stage
from python_pipeline.lib.utils import get_logger

log = get_logger(__name__)


def load_baskets():
    # نقرا تفاصيل الطلبات ونطلع سله لكل طلب
    items = load_clean_table("Order_Items")
    baskets = items.groupby("order_id")["menu_item_id"].apply(set).to_dict()
    log.info(f"عدد السلال: {len(baskets):,}")
    return baskets


def count_pairs(baskets):
    # نعد كل زوج يظهر مع بعض
    # نحوّل لكل str عشان نتفادى مشاكل الانواع
    counter = Counter()
    for items in baskets.values():
        uniq = sorted({str(x) for x in items})
        for pair in combinations(uniq, 2):
            counter[pair] += 1
    return counter


def count_singles(baskets):
    # نعد كل صنف لحاله
    counter = Counter()
    for items in baskets.values():
        for it in {str(x) for x in items}:
            counter[it] += 1
    return counter


def build_rules(baskets):
    n = len(baskets)
    singles = count_singles(baskets)
    pairs = count_pairs(baskets)

    support_single = {k: v / n for k, v in singles.items()}

    rows = []
    for (a, b), cnt in pairs.items():
        # نستبعد اذا صار نفس المعرف
        if a == b:
            continue

        sup_ab = cnt / n
        if sup_ab < MIN_SUPPORT:
            continue

        # a -> b
        conf_ab = sup_ab / support_single[a]
        lift_ab = conf_ab / support_single[b]
        if conf_ab >= MIN_CONFIDENCE and lift_ab >= MIN_LIFT:
            rows.append({
                "antecedent": a,
                "consequent": b,
                "support": round(sup_ab, 6),
                "confidence": round(conf_ab, 4),
                "lift": round(lift_ab, 4),
            })

        # b -> a
        conf_ba = sup_ab / support_single[b]
        lift_ba = conf_ba / support_single[a]
        if conf_ba >= MIN_CONFIDENCE and lift_ba >= MIN_LIFT:
            rows.append({
                "antecedent": b,
                "consequent": a,
                "support": round(sup_ab, 6),
                "confidence": round(conf_ba, 4),
                "lift": round(lift_ba, 4),
            })

    df = pd.DataFrame(rows)
    if len(df) > 0:
        df = df[df["antecedent"] != df["consequent"]].reset_index(drop=True)
    return df


def add_names(rules):
    # نضيف اسماء الاصناف عشان يكون اوضح
    menu = load_clean_table("Menu_Items")
    menu["menu_item_id"] = menu["menu_item_id"].astype(str)
    names = dict(zip(menu["menu_item_id"], menu["item_name"]))
    rules["antecedent_name"] = rules["antecedent"].map(names)
    rules["consequent_name"] = rules["consequent"].map(names)

    # نستبعد الازواج الي اسم الصنف فيها نفسه
    # هذا يحصل لما يصير عندنا نفس الاسم بمعرفين مختلفين
    rules = rules[
        rules["antecedent_name"] != rules["consequent_name"]
    ].reset_index(drop=True)

    return rules


def build_bundles(rules):
    # نبني اقتراحات combo من القواعد
    # نأخذ افضل قاعده لكل زوج (نستبعد التكرار)
    r = rules.copy()
    # نطبع الاسم الاعلى lift لكل زوج
    r["pair_key"] = r.apply(
        lambda x: tuple(sorted([str(x["antecedent"]), str(x["consequent"])])),
        axis=1,
    )
    # نرتب حسب lift ونحتفظ بواحده لكل زوج
    best = r.sort_values("lift", ascending=False).drop_duplicates("pair_key")

    # نصنف الاقتراحات حسب النوع
    # combo meal: كلا الطرفين اصناف رئيسيه
    # cross-sell: صنف رئيسي + جانبي
    # upsell: صنف + مشروب
    bundles = best.head(30).copy()
    bundles = bundles[[
        "antecedent_name", "consequent_name",
        "support", "confidence", "lift",
    ]].reset_index(drop=True)
    bundles["recommendation_type"] = "Combo Meal"
    bundles["rank"] = bundles.index + 1
    return bundles


def run():
    log.info("نبدا basket")
    baskets = load_baskets()
    rules = build_rules(baskets)
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
    rules = add_names(rules)

    save_stage(rules, "05_basket", "basket_rules.parquet")
    log.info(f"rules: {len(rules):,} زوج")

    top = rules.head(20)
    save_stage(top, "05_basket", "basket_top20.parquet")

    # Bundle suggestions حسب SRS Step 18
    bundles = build_bundles(rules)
    save_stage(bundles, "05_basket", "bundle_suggestions.parquet")
    log.info(f"bundle suggestions: {len(bundles)}")

    log.info(
        f"top 20:\n"
        f"{top[['antecedent_name','consequent_name','support','confidence','lift']].to_string(index=False)}"
    )


if __name__ == "__main__":
    run()


if __name__ == "__main__":
    run()