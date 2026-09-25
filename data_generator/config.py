from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class GeneratorConfig:
    # Reproducibility
    seed: int = 42

    # Output
    output_dir: Path = Path(".")

    # Required SRS minimums for the full dataset
    n_customers: int = 50_000
    n_restaurants: int = 20
    n_categories: int = 10
    n_menu_items: int = 150
    n_promotions: int = 30
    n_orders: int = 100_000
    n_ratings: int = 100_000
    n_wastage: int = 50_000
    min_order_lines: int = 10

    # Historical data window: 12 full calendar months
    start_date: str = "2024-01-01"
    end_date: str = "2024-12-31"

    # Historical pricing records per item
    min_prices_per_item: int = 3
    max_prices_per_item: int = 6

    # Ordering behavior
    order_status_cancelled_rate: float = 0.05
    promotion_assignment_rate: float = 0.25
    average_additional_lines: int = 2

    # Intentional business-pattern coverage
    n_popular_loss_margin_items: int = 25
    n_profitable_low_selling_items: int = 15
    n_high_wastage_items: int = 20
    n_weekend_only_items: int = 12
    n_seasonal_items: int = 18
    n_price_sensitive_items: int = 18
    n_promo_dependent_items: int = 20
    n_high_rated_poor_profit_items: int = 12
    n_low_rated_high_sales_items: int = 12
    n_sales_anomaly_items: int = 12
    n_new_items: int = 12

    # Promotion traps: sales lift with declining contribution margin
    n_trap_promotions: int = 8
    trap_discount_min: float = 0.40
    trap_discount_max: float = 0.55
    trap_demand_multiplier: float = 5.0

    # Data-quality defects injected into raw data
    duplicate_order_rate: float = 0.01
    duplicate_order_item_rate: float = 0.01
    missing_id_rate: float = 0.003
    invalid_id_rate: float = 0.002
    missing_value_rate: float = 0.004
    invalid_date_rate: float = 0.002
    negative_quantity_rate: float = 0.002
    invalid_price_rate: float = 0.002
    invalid_rating_rate: float = 0.003
    incorrect_discount_rate: float = 0.002
    inconsistent_unit_rate: float = 0.003
    impossible_wastage_rate: float = 0.02

    # Customer lifecycle behavior
    new_customer_horizon_days: int = 90
    churn_customer_cutoff_days: int = 120
    high_value_weight: float = 5.0
    frequent_weight: float = 3.0
    churned_weight: float = 0.65
    occasional_weight: float = 0.85
    new_customer_weight: float = 1.15

    # Restaurant and temporal demand behavior
    weekend_boost: float = 1.35
    weekend_only_boost: float = 8.0
    weekend_only_weekday_suppression: float = 0.12
    seasonal_boost: float = 4.0
    seasonal_offseason_factor: float = 0.40
    anomaly_spike_multiplier: float = 10.0
    anomaly_suppression_factor: float = 0.05

    # Smoke run keeps relational dimensions intact but reduces fact-table volume.
    @classmethod
    def smoke(cls, output_dir: Path | str = Path("smoke_output"), seed: int = 42) -> "GeneratorConfig":
        return cls(
            seed=seed,
            output_dir=Path(output_dir),
            n_customers=2_000,
            n_restaurants=20,
            n_categories=10,
            n_menu_items=150,
            n_promotions=12,
            n_orders=3_000,
            n_ratings=6_000,
            n_wastage=2_000,
        )

    @property
    def start(self):
        return self._ts(self.start_date)

    @property
    def end(self):
        return self._ts(self.end_date)

    @staticmethod
    def _ts(value: str):
        import pandas as pd

        return pd.Timestamp(value)

    def ensure_output_dirs(self) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "raw_data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "processed_data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "parquet_data").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "reports").mkdir(parents=True, exist_ok=True)
