import random
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

ORDER_STATUSES = ["COMPLETED", "PENDING", "SHIPPED", "CANCELLED", "REFUNDED"]


class OrdersGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int, customer_ids: List[str] = None, product_ids: List[str] = None) -> List[Dict[str, Any]]:
        cust_list = customer_ids or [f"CUST-{i:06d}" for i in range(1, 101)]
        prod_list = product_ids or [f"PROD-{i:05d}" for i in range(1, 51)]
        orders = []

        for i in range(1, count + 1):
            order_id = f"ORD-{i:08d}"
            customer_id = random.choice(cust_list)
            product_id = random.choice(prod_list)
            order_date = self.random_date(start_years_ago=1, end_days_ahead=0)
            quantity = random.randint(1, 10)
            unit_price = round(random.uniform(20.0, 300.0), 2)
            discount = round(random.uniform(0.0, 15.0), 2)
            tax = round((quantity * unit_price - discount) * 0.08, 2)
            total_amount = round(quantity * unit_price - discount + tax, 2)
            currency = "USD"
            order_status = random.choice(ORDER_STATUSES)

            # Inject Invalid Customer ID (FK failure)
            if random.random() < self.anomaly_rates.invalid_fk_rate:
                customer_id = "CUST-999999_NONEXISTENT"

            # Inject Invalid Product ID (FK failure)
            if random.random() < self.anomaly_rates.invalid_fk_rate:
                product_id = "PROD-99999_NONEXISTENT"

            # Inject Negative Quantity
            if random.random() < self.anomaly_rates.negative_quantity_rate:
                quantity = -random.randint(1, 5)

            # Inject Incorrect Total Amount Calculation
            if random.random() < self.anomaly_rates.incorrect_total_rate:
                total_amount = round(total_amount + 500.0, 2)

            # Inject Future Date
            if random.random() < self.anomaly_rates.future_date_rate:
                future_dt = datetime.now(timezone.utc) + timedelta(days=random.randint(10, 30))
                order_date = future_dt.strftime("%Y-%m-%d")

            order_record = {
                "order_id": order_id,
                "customer_id": customer_id,
                "product_id": product_id,
                "order_date": order_date,
                "quantity": quantity,
                "unit_price": unit_price,
                "discount": discount,
                "tax": tax,
                "total_amount": total_amount,
                "currency": currency,
                "order_status": order_status,
            }
            orders.append(order_record)

            # Inject Duplicate Order
            if random.random() < self.anomaly_rates.duplicate_record_rate and len(orders) > 1:
                duplicate = dict(random.choice(orders))
                orders.append(duplicate)

        return orders[:count]
