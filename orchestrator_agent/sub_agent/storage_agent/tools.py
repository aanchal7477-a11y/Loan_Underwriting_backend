# from sub_agent.shared.utils import extract_fields, safe_float, clean_int
# from sub_agent.shared.logger import logger

import logging
import os
from google.cloud import bigquery
from ..shared.utils import normalize_date
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

bq_client = bigquery.Client()
TABLE_ID = os.getenv("TABLE_ID")

logger = logging.getLogger("storage_agent")

def save_to_bigquery(payload: dict):
    print(payload, "payload")
    """
    Saves underwriting results to BigQuery.
    Expects a single payload dictionary containing all required fields.
    """

    logger.info("Saving underwriting result to BigQuery")

    row = [{
        "appicant_name": payload.get("applicant_name", ""),
        "credit_score": payload.get("credit"),
        "loan_amount": payload.get("loan"),
        "term_months": payload.get("months"),
        "annual_income": payload.get("annual"),
        "monthly_income": payload.get("monthly_income"),
        "monthly_debt": payload.get("monthly_debt"),
        "dti": payload.get("dti"),
        "net_pay": payload.get("net_pay"),
        "tax_income": payload.get("tax_income"),
        "id_number": payload.get("id_number", ""),
        "dob": normalize_date(payload.get("dob")) if payload.get("dob") else None,
        "decision": payload.get("decision"),
        "timestamp": datetime.utcnow().isoformat()
    }]

    errors = bq_client.insert_rows_json(TABLE_ID, row)

    if errors:
        logger.error(f"❌ BigQuery insert failed: {errors}")
    else:
        logger.info("✅ Data saved to BigQuery")