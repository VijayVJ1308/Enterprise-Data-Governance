import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class ScaleConfig:
    customers_count: int
    products_count: int
    orders_count: int
    employees_count: int
    suppliers_count: int
    transactions_count: int


SCALE_PRESETS: Dict[str, ScaleConfig] = {
    "small": ScaleConfig(
        customers_count=1000,
        products_count=200,
        orders_count=3000,
        employees_count=100,
        suppliers_count=50,
        transactions_count=5000,
    ),
    "medium": ScaleConfig(
        customers_count=50000,
        products_count=2000,
        orders_count=150000,
        employees_count=1000,
        suppliers_count=300,
        transactions_count=250000,
    ),
    "large": ScaleConfig(
        customers_count=500000,
        products_count=10000,
        orders_count=1500000,
        employees_count=5000,
        suppliers_count=1000,
        transactions_count=2500000,
    ),
}


@dataclass
class AnomalyRates:
    null_email_rate: float = 0.05
    invalid_email_rate: float = 0.03
    duplicate_record_rate: float = 0.02
    invalid_phone_rate: float = 0.04
    invalid_postal_code_rate: float = 0.03
    null_country_rate: float = 0.02
    negative_price_rate: float = 0.03
    missing_category_rate: float = 0.04
    invalid_currency_rate: float = 0.02
    invalid_fk_rate: float = 0.04
    negative_quantity_rate: float = 0.03
    incorrect_total_rate: float = 0.05
    future_date_rate: float = 0.02
    missing_manager_rate: float = 0.05
    invalid_salary_rate: float = 0.03


def get_generator_config(scale_name: str = None) -> ScaleConfig:
    scale = scale_name or os.getenv("DATA_GENERATOR_SCALE", "small").lower()
    return SCALE_PRESETS.get(scale, SCALE_PRESETS["small"])
