"""
Phase 3 Synthetic Enterprise Data Generator Verification Tests

Verifies scale configurations, dataset schemas, anomaly injection, and file output.
"""

import os
import sys
import shutil
import tempfile
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_generator.configs.generator_config import get_generator_config, SCALE_PRESETS
from data_generator.generators.customers_generator import CustomersGenerator
from data_generator.generators.products_generator import ProductsGenerator
from data_generator.generators.orders_generator import OrdersGenerator
from data_generator.generators.employees_generator import EmployeesGenerator
from data_generator.generators.suppliers_generator import SuppliersGenerator
from data_generator.generators.transactions_generator import TransactionsGenerator
from data_generator.main import generate_all_datasets


class TestPhase3DataGenerator(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_scale_configurations(self):
        small_cfg = get_generator_config("small")
        medium_cfg = get_generator_config("medium")
        large_cfg = get_generator_config("large")

        self.assertEqual(small_cfg.customers_count, 1000)
        self.assertEqual(medium_cfg.customers_count, 50000)
        self.assertEqual(large_cfg.customers_count, 500000)

    def test_customers_generation_and_anomalies(self):
        gen = CustomersGenerator(seed=123)
        customers = gen.generate(100)
        self.assertEqual(len(customers), 100)

        # Verify key fields present
        first_cust = customers[0]
        expected_fields = ["customer_id", "first_name", "last_name", "email", "phone", "date_of_birth", "country", "city", "postal_code", "customer_type", "registration_date", "status"]
        for field in expected_fields:
            self.assertIn(field, first_cust)

        # Verify presence of injected anomalies across 100 records
        null_emails = [c for c in customers if c["email"] is None]
        invalid_emails = [c for c in customers if c["email"] and "#invalid_at_domain" in c["email"]]
        self.assertGreater(len(null_emails) + len(invalid_emails), 0, "Expected at least 1 email anomaly")

    def test_products_generation_and_anomalies(self):
        gen = ProductsGenerator(seed=456)
        products = gen.generate(50)
        self.assertEqual(len(products), 50)

        first_prod = products[0]
        expected_fields = ["product_id", "product_name", "category", "subcategory", "supplier_id", "unit_cost", "selling_price", "currency", "status", "created_date"]
        for field in expected_fields:
            self.assertIn(field, first_prod)

        # Check negative price anomaly
        negative_prices = [p for p in products if p["selling_price"] < 0]
        missing_categories = [p for p in products if p["category"] is None]
        self.assertTrue(len(negative_prices) > 0 or len(missing_categories) > 0, "Expected price or category anomaly")

    def test_orders_generation_and_anomalies(self):
        gen = OrdersGenerator(seed=789)
        orders = gen.generate(50)
        self.assertEqual(len(orders), 50)

        first_order = orders[0]
        expected_fields = ["order_id", "customer_id", "product_id", "order_date", "quantity", "unit_price", "discount", "tax", "total_amount", "currency", "order_status"]
        for field in expected_fields:
            self.assertIn(field, first_order)

        # Check negative quantity or invalid FK anomalies
        neg_qty = [o for o in orders if o["quantity"] < 0]
        invalid_cust_fk = [o for o in orders if "NONEXISTENT" in o["customer_id"]]
        self.assertTrue(len(neg_qty) > 0 or len(invalid_cust_fk) > 0, "Expected order anomaly")

    def test_generate_all_datasets_end_to_end(self):
        datasets = generate_all_datasets(scale_name="small", output_dir=self.temp_dir)
        self.assertIn("customers", datasets)
        self.assertIn("products", datasets)
        self.assertIn("orders", datasets)
        self.assertIn("employees", datasets)
        self.assertIn("suppliers", datasets)
        self.assertIn("transactions", datasets)

        # Verify CSV and JSON files were written to temp output directory
        expected_files = ["customers.csv", "customers.json", "products.csv", "products.json", "orders.csv", "orders.json", "employees.csv", "employees.json", "suppliers.csv", "suppliers.json", "transactions.csv", "transactions.json"]
        for fname in expected_files:
            fpath = os.path.join(self.temp_dir, fname)
            self.assertTrue(os.path.exists(fpath), f"File was not exported: {fname}")
            self.assertGreater(os.path.getsize(fpath), 0, f"Exported file is empty: {fname}")


if __name__ == "__main__":
    unittest.main()
