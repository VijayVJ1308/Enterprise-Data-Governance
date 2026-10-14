import random
from typing import List, Dict, Any
from data_generator.generators.base_generator import BaseDataGenerator
from data_generator.configs.generator_config import AnomalyRates

DEPARTMENTS = ["Engineering", "Sales", "Data & Analytics", "HR", "Finance", "Legal", "Operations"]
JOB_TITLES = ["Specialist", "Engineer", "Manager", "Director", "VP", "Analyst", "Lead"]
FIRST_NAMES = ["Alice", "Bob", "Charlie", "Diana", "Ethan", "Fiona", "George", "Hannah", "Ian", "Julia"]
LAST_NAMES = ["Smith", "Jones", "Taylor", "Williams", "Brown", "Davies", "Evans", "Wilson", "Thomas", "Roberts"]


class EmployeesGenerator(BaseDataGenerator):
    def __init__(self, seed: int = 42, anomaly_rates: AnomalyRates = None):
        super().__init__(seed=seed)
        self.anomaly_rates = anomaly_rates or AnomalyRates()

    def generate(self, count: int) -> List[Dict[str, Any]]:
        employees = []
        for i in range(1, count + 1):
            emp_id = f"EMP-{i:05d}"
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            emp_name = f"{first_name} {last_name}"
            department = random.choice(DEPARTMENTS)
            job_title = f"{random.choice(JOB_TITLES)} of {department}"
            email = f"{first_name.lower()}.{last_name.lower()}{i}@enterprise.com"
            manager_id = f"EMP-{random.randint(1, max(1, i-1)):05d}" if i > 1 else None
            hire_date = self.random_date(start_years_ago=10, end_days_ahead=0)
            salary = round(random.uniform(50000.0, 200000.0), 2)
            country = "USA"
            status = "ACTIVE"

            # Inject Invalid Email
            if random.random() < self.anomaly_rates.invalid_email_rate:
                email = f"{first_name.lower()}#invalid_domain"

            # Inject Missing Manager
            if random.random() < self.anomaly_rates.missing_manager_rate:
                manager_id = None

            # Inject Invalid Salary
            if random.random() < self.anomaly_rates.invalid_salary_rate:
                salary = -5000.00

            emp_record = {
                "employee_id": emp_id,
                "employee_name": emp_name,
                "department": department,
                "job_title": job_title,
                "email": email,
                "manager_id": manager_id,
                "hire_date": hire_date,
                "salary": salary,
                "country": country,
                "status": status,
            }
            employees.append(emp_record)

            # Inject Duplicate Employee
            if random.random() < self.anomaly_rates.duplicate_record_rate and len(employees) > 1:
                duplicate = dict(random.choice(employees))
                employees.append(duplicate)

        return employees[:count]
