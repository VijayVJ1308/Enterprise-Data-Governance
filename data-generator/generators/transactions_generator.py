import random
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

PAYMENT_METHODS = ["CREDIT_CARD", "DEBIT_CARD", "PAYPAL", "BANK_TRANSFER", "CRYPTO"]
TRANSACTION_STATUSES = ["SUCCESS", "FAILED", "PENDING", "REVERSED"]


class TransactionsGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int, orders: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        transactions = []
        for i in range(1, count + 1):
            tx_id = f"TX-{i:08d}"
            if orders and len(orders) > 0:
                ref_order = random.choice(orders)
                order_id = ref_order["order_id"]
                customer_id = ref_order["customer_id"]
                amount = ref_order["total_amount"]
                tx_date = ref_order["order_date"]
            else:
                order_id = f"ORD-{random.randint(1, count):08d}"
                customer_id = f"CUST-{random.randint(1, 100):06d}"
                amount = round(random.uniform(10.0, 1000.0), 2)
                tx_date = self.random_date(start_years_ago=1, end_days_ahead=0)

            payment_method = random.choice(PAYMENT_METHODS)
            status = random.choice(TRANSACTION_STATUSES)

            tx_record = {
                "transaction_id": tx_id,
                "order_id": order_id,
                "customer_id": customer_id,
                "payment_method": payment_method,
                "amount": amount,
                "transaction_date": tx_date,
                "status": status,
            }
            transactions.append(tx_record)

        return transactions
