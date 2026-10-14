import random
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin"]
COUNTRIES = ["USA", "Canada", "UK", "Germany", "France", "Japan", "Australia", "India", "Brazil", "Singapore"]
CITIES = ["New York", "London", "Toronto", "Berlin", "Paris", "Tokyo", "Sydney", "Mumbai", "Sao Paulo", "Singapore"]
TYPES = ["INDIVIDUAL", "CORPORATE", "ENTERPRISE", "SME"]
STATUSES = ["ACTIVE", "INACTIVE", "SUSPENDED", "PENDING"]


class CustomersGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int) -> List[Dict[str, Any]]:
        customers = []
        for i in range(1, count + 1):
            cust_id = f"CUST-{i:06d}"
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            phone = f"+1-{random.randint(200, 999)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
            dob = self.random_date(start_years_ago=50, end_days_ahead=0)
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES)
            postal_code = f"{random.randint(10000, 99999)}"
            cust_type = random.choice(TYPES)
            reg_date = self.random_date(start_years_ago=3, end_days_ahead=0)
            status = random.choice(STATUSES)

            # Inject Null Email
            if random.random() < self.anomaly_rates.null_email_rate:
                email = None
            # Inject Invalid Email
            elif random.random() < self.anomaly_rates.invalid_email_rate:
                email = f"{first_name.lower()}#invalid_at_domain"

            # Inject Invalid Phone
            if random.random() < self.anomaly_rates.invalid_phone_rate:
                phone = "PHONE_INVALID_123"

            # Inject Invalid Postal Code
            if random.random() < self.anomaly_rates.invalid_postal_code_rate:
                postal_code = "ABC-INVALID"

            # Inject Null Country
            if random.random() < self.anomaly_rates.null_country_rate:
                country = None

            cust_record = {
                "customer_id": cust_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "phone": phone,
                "date_of_birth": dob,
                "country": country,
                "city": city,
                "postal_code": postal_code,
                "customer_type": cust_type,
                "registration_date": reg_date,
                "status": status,
            }
            customers.append(cust_record)

            # Inject Duplicate Customer
            if random.random() < self.anomaly_rates.duplicate_record_rate and len(customers) > 1:
                duplicate = dict(random.choice(customers))
                customers.append(duplicate)

        return customers[:count] # Trim back to target count
