import random
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

SUPPLIER_NAMES = ["Acme Corp", "Global Tech Supplies", "Apex Logistics", "Nexus Components", "Vanguard Industries", "Zenith Trading", "Starlight Manufacturing", "Quantum Solutions"]
COUNTRIES = ["USA", "Germany", "Japan", "China", "UK", "Taiwan", "South Korea"]


class SuppliersGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int) -> List[Dict[str, Any]]:
        suppliers = []
        for i in range(1, count + 1):
            supp_id = f"SUPP-{i:04d}"
            base_name = random.choice(SUPPLIER_NAMES)
            supp_name = f"{base_name} #{i}"
            country = random.choice(COUNTRIES)
            contact_email = f"contact@{supp_name.lower().replace(' ', '').replace('#', '')}.com"
            lead_time = random.randint(1, 30)
            rating = round(random.uniform(3.0, 5.0), 1)
            status = "ACTIVE" if random.random() > 0.1 else "INACTIVE"

            supplier_record = {
                "supplier_id": supp_id,
                "supplier_name": supp_name,
                "country": country,
                "contact_email": contact_email,
                "lead_time_days": lead_time,
                "rating": rating,
                "status": status,
            }
            suppliers.append(supplier_record)

        return suppliers
