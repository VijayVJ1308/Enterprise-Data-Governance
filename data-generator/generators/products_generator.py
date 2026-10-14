import random
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

CATEGORIES = {
    "Electronics": ["Laptops", "Smartphones", "Monitors", "Audio"],
    "Office": ["Desks", "Chairs", "Paper", "Pens"],
    "Software": ["OS", "Security", "Analytics", "Cloud"],
    "Hardware": ["Servers", "Networking", "Storage", "Cables"],
}
CURRENCIES = ["USD", "EUR", "GBP", "CAD", "AUD"]
STATUSES = ["ACTIVE", "DISCONTINUED", "OUT_OF_STOCK"]


class ProductsGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int, supplier_ids: List[str] = None) -> List[Dict[str, Any]]:
        suppliers = supplier_ids or [f"SUPP-{i:04d}" for i in range(1, 51)]
        products = []
        for i in range(1, count + 1):
            prod_id = f"PROD-{i:05d}"
            category = random.choice(list(CATEGORIES.keys()))
            subcategory = random.choice(CATEGORIES[category])
            prod_name = f"Enterprise {subcategory[:-1] if subcategory.endswith('s') else subcategory} {i}"
            supplier_id = random.choice(suppliers)
            unit_cost = round(random.uniform(10.0, 500.0), 2)
            selling_price = round(unit_cost * random.uniform(1.2, 2.5), 2)
            currency = random.choice(CURRENCIES)
            status = random.choice(STATUSES)
            created_date = self.random_date(start_years_ago=2, end_days_ahead=0)

            # Inject Negative Price
            if random.random() < self.anomaly_rates.negative_price_rate:
                selling_price = -round(selling_price, 2)

            # Inject Missing Category
            if random.random() < self.anomaly_rates.missing_category_rate:
                category = None

            # Inject Invalid Currency
            if random.random() < self.anomaly_rates.invalid_currency_rate:
                currency = "INVALID_CURR"

            product_record = {
                "product_id": prod_id,
                "product_name": prod_name,
                "category": category,
                "subcategory": subcategory,
                "supplier_id": supplier_id,
                "unit_cost": unit_cost,
                "selling_price": selling_price,
                "currency": currency,
                "status": status,
                "created_date": created_date,
            }
            products.append(product_record)

            # Inject Duplicate Product
            if random.random() < self.anomaly_rates.duplicate_record_rate and len(products) > 1:
                duplicate = dict(random.choice(products))
                products.append(duplicate)

        return products[:count]
