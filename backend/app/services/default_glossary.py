from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.app.services.glossary_service import GlossaryService

DEFAULT_ENTERPRISE_TERMS: List[Dict[str, Any]] = [
    {
        "term": "Customer",
        "definition": "A person or organization with an active commercial or transacting relationship with the enterprise.",
        "business_domain": "Sales",
        "owner": "Head of Customer Experience",
        "status": "APPROVED",
        "related_datasets": ["customers", "dim_customers", "sales_mart"],
    },
    {
        "term": "Revenue",
        "definition": "Total recognized net sales monetary value generated during a specific financial reporting period.",
        "business_domain": "Finance",
        "owner": "Chief Financial Officer",
        "status": "APPROVED",
        "related_datasets": ["orders", "fact_orders", "sales_mart"],
    },
    {
        "term": "Order",
        "definition": "A commercial agreement or customer request to purchase one or more enterprise products or services.",
        "business_domain": "Sales",
        "owner": "VP of Sales Operations",
        "status": "APPROVED",
        "related_datasets": ["orders", "fact_orders"],
    },
    {
        "term": "Employee",
        "definition": "An individual directly employed by the enterprise with compensation and organizational hierarchy attributes.",
        "business_domain": "HR",
        "owner": "Chief Human Resources Officer",
        "status": "APPROVED",
        "related_datasets": ["employees", "hr_employees_api"],
    },
    {
        "term": "Supplier",
        "definition": "An external corporate entity providing goods, components, or services to the enterprise supply chain.",
        "business_domain": "Supply Chain",
        "owner": "Head of Procurement",
        "status": "APPROVED",
        "related_datasets": ["suppliers", "products"],
    },
    {
        "term": "Transaction",
        "definition": "An executed monetary payment or financial movement associated with an enterprise order.",
        "business_domain": "Finance",
        "owner": "VP of Treasury",
        "status": "APPROVED",
        "related_datasets": ["transactions"],
    },
]


def seed_default_glossary_terms(db_session: Session):
    for item in DEFAULT_ENTERPRISE_TERMS:
        GlossaryService.create_term(
            db_session=db_session,
            term=item["term"],
            definition=item["definition"],
            business_domain=item["business_domain"],
            owner=item["owner"],
            status=item["status"],
            related_datasets=item["related_datasets"],
        )
