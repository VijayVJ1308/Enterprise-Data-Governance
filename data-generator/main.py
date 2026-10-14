import os
import sys
import argparse
import logging
from typing import Dict, Any, List

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_generator.configs.generator_config import get_generator_config, AnomalyRates
from data_generator.generators.customers_generator import CustomersGenerator
from data_generator.generators.products_generator import ProductsGenerator
from data_generator.generators.orders_generator import OrdersGenerator
from data_generator.generators.employees_generator import EmployeesGenerator
from data_generator.generators.suppliers_generator import SuppliersGenerator
from data_generator.generators.transactions_generator import TransactionsGenerator

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DataGenerator")


def generate_all_datasets(scale_name: str = "small", output_dir: str = "data/raw") -> Dict[str, List[Dict[str, Any]]]:
    config = get_generator_config(scale_name)
    rates = AnomalyRates()
    os.makedirs(output_dir, exist_ok=True)

    logger.info(f"Starting synthetic dataset generation using scale preset: '{scale_name.upper()}'")

    # 1. Suppliers
    logger.info(f"Generating Suppliers dataset ({config.suppliers_count} records)...")
    supp_gen = SuppliersGenerator(seed=42, anomaly_rates=rates)
    suppliers = supp_gen.generate(config.suppliers_count)
    supp_gen.export_csv(suppliers, os.path.join(output_dir, "suppliers.csv"))
    supp_gen.export_json(suppliers, os.path.join(output_dir, "suppliers.json"))

    # 2. Products
    logger.info(f"Generating Products dataset ({config.products_count} records)...")
    supplier_ids = [s["supplier_id"] for s in suppliers]
    prod_gen = ProductsGenerator(seed=43, anomaly_rates=rates)
    products = prod_gen.generate(config.products_count, supplier_ids=supplier_ids)
    prod_gen.export_csv(products, os.path.join(output_dir, "products.csv"))
    prod_gen.export_json(products, os.path.join(output_dir, "products.json"))

    # 3. Customers
    logger.info(f"Generating Customers dataset ({config.customers_count} records)...")
    cust_gen = CustomersGenerator(seed=44, anomaly_rates=rates)
    customers = cust_gen.generate(config.customers_count)
    cust_gen.export_csv(customers, os.path.join(output_dir, "customers.csv"))
    cust_gen.export_json(customers, os.path.join(output_dir, "customers.json"))

    # 4. Employees
    logger.info(f"Generating Employees dataset ({config.employees_count} records)...")
    emp_gen = EmployeesGenerator(seed=45, anomaly_rates=rates)
    employees = emp_gen.generate(config.employees_count)
    emp_gen.export_csv(employees, os.path.join(output_dir, "employees.csv"))
    emp_gen.export_json(employees, os.path.join(output_dir, "employees.json"))

    # 5. Orders
    logger.info(f"Generating Orders dataset ({config.orders_count} records)...")
    cust_ids = [c["customer_id"] for c in customers if c.get("customer_id")]
    prod_ids = [p["product_id"] for p in products if p.get("product_id")]
    orders_gen = OrdersGenerator(seed=46, anomaly_rates=rates)
    orders = orders_gen.generate(config.orders_count, customer_ids=cust_ids, product_ids=prod_ids)
    orders_gen.export_csv(orders, os.path.join(output_dir, "orders.csv"))
    orders_gen.export_json(orders, os.path.join(output_dir, "orders.json"))

    # 6. Transactions
    logger.info(f"Generating Transactions dataset ({config.transactions_count} records)...")
    tx_gen = TransactionsGenerator(seed=47, anomaly_rates=rates)
    transactions = tx_gen.generate(config.transactions_count, orders=orders)
    tx_gen.export_csv(transactions, os.path.join(output_dir, "transactions.csv"))
    tx_gen.export_json(transactions, os.path.join(output_dir, "transactions.json"))

    logger.info(f"Synthetic data generation completed successfully! Files written to '{output_dir}'.")
    return {
        "suppliers": suppliers,
        "products": products,
        "customers": customers,
        "employees": employees,
        "orders": orders,
        "transactions": transactions,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enterprise Synthetic Data Generator")
    parser.add_argument("--scale", choices=["small", "medium", "large"], default="small", help="Dataset scale preset")
    parser.add_argument("--output-dir", default="data/raw", help="Output directory path")
    args = parser.parse_args()
    generate_all_datasets(scale_name=args.scale, output_dir=args.output_dir)
