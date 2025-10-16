import asyncio
import logging
from google.cloud import documentai_v1 as documentai
from ..shared.utils import extract_fields, safe_float, clean_int, safe_int
from ..shared.logger import get_logger

logger = get_logger("doc_parsing_agent")

# ---------------------------
# DocAI Processing
# ---------------------------
async def process_single_doc(project_id, location, processor_id, gcs_uri):
    logger.info(f"Starting document processing: {gcs_uri}")
    
    def blocking_task():
        try:
            client = documentai.DocumentProcessorServiceClient()
            name = client.processor_path(project_id, location, processor_id)
            logger.debug(f"Processor path: {name}")

            request = documentai.ProcessRequest(
                name=name,
                gcs_document=documentai.GcsDocument(
                    gcs_uri=gcs_uri,
                    mime_type="application/pdf"
                )
            )
            result = client.process_document(request=request)
            logger.info(f"Document processed successfully: {gcs_uri}")
            return documentai.Document.to_dict(result.document)
        except Exception as e:
            logger.exception(f"Failed to process document: {gcs_uri}")
            return {"error": str(e)}

    return await asyncio.to_thread(blocking_task)


# ---------------------------
# Orchestration Layer
# ---------------------------
async def process_and_parse_docs(payload: dict):
    logger.info("Starting process_and_parse_docs")
    logger.debug(f"Payload received: {payload}")

    project_id = payload.get("project_id")
    location = payload.get("location")
    processor_id = payload.get("processor_id")

    gcs_uris = {
        "application": payload.get("application_gcs_uri"),
        "bank": payload.get("bank_statement_gcs_uri"),
        "pay_stub": payload.get("pay_stub_gcs_uri"),
        "tax": payload.get("tax_return_gcs_uri"),
        "id": payload.get("id_proof_gcs_uri"),
    }

    logger.info("Submitting documents for processing")
    tasks = {key: process_single_doc(project_id, location, processor_id, uri)
             for key, uri in gcs_uris.items() if uri}

    results = await asyncio.gather(*tasks.values())
    docs_json = dict(zip(tasks.keys(), results))

    logger.debug("Documents processed. Parsing fields now...")

    # Initialize placeholders for outputs
    credit = loan = months = annual = dti = net_pay = tax_income = None
    monthly_income = monthly_debt = None
    id_name = id_number = dob = applicant_name = None
    documents = {}
    document_mismatch = False

    # Parse each document with safe wrappers
    try:
        credit, loan, months, annual, documents, applicant_name = parse_application_form(docs_json.get("application", {}))
    except Exception as e:
        logger.warning(f"Application form parsing failed or mismatched: {e}")
        document_mismatch = True

    try:
        monthly_income, monthly_debt, dti = parse_bank_statement(docs_json.get("bank", {}))
    except Exception as e:
        logger.warning(f"Bank statement parsing failed or mismatched: {e}")
        document_mismatch = True

    try:
        net_pay = parse_pay_stub(docs_json.get("pay_stub", {}))
    except Exception as e:
        logger.warning(f"Pay stub parsing failed or mismatched: {e}")
        document_mismatch = True

    try:
        tax_income = parse_tax_return(docs_json.get("tax", {}))
    except Exception as e:
        logger.warning(f"Tax return parsing failed or mismatched: {e}")
        document_mismatch = True

    try:
        id_name, id_number, dob = parse_id_proof(docs_json.get("id", {}))
    except Exception as e:
        logger.warning(f"ID proof parsing failed or mismatched: {e}")
        document_mismatch = True

    logger.info(f"Parsed applicant: {applicant_name}, credit={credit}, loan={loan}, months={months}, dti={dti}")

    # If everything failed, mark as mismatched
    if document_mismatch or not any([credit, loan, dti, net_pay, tax_income]):
        logger.warning("Uploaded documents appear mismatched or invalid for underwriting pipeline.")
        return {"document_mismatch": True, "message": "Document mismatched or unrecognized document type"}

    return {
        "credit": credit,
        "loan": loan,
        "months": months,
        "annual": annual,
        "documents": documents,
        "applicant_name": applicant_name,
        "monthly_income": monthly_income,
        "monthly_debt": monthly_debt,
        "dti": dti,
        "net_pay": net_pay,
        "tax_income": tax_income,
        "id_name": id_name,
        "id_number": id_number,
        "dob": dob,
        "document_mismatch": False,
    }


# ---------------------------
# Parsers (with extra validation)
# ---------------------------
def parse_application_form(doc_json: dict):
    logger.debug("Parsing application form document")
    fields = extract_fields(doc_json)
    if not fields:
        raise ValueError("No recognizable fields found in application form")

    credit_score = safe_int(fields.get("Credit_score"))
    loan_amount = safe_float(fields.get("Loan_amount"))
    months = clean_int(fields.get("months"))
    annual_income = safe_float(fields.get("Annual_income"))
    applicant_name = fields.get("Full_Name")

    documents = {
        "Pay Stub": "(✔) Recent Pay Stub or Business Financials" in fields.get("document_uploads", ""),
        "Bank Statement": "(✔) Bank Statement" in fields.get("document_uploads", ""),
        "Tax Return": "(✔) Tax Return" in fields.get("document_uploads", ""),
        "ID Proof": "(✔) ID Proof" in fields.get("document_uploads", ""),
    }

    logger.info(f"Application parsed for {applicant_name}")
    return credit_score, loan_amount, months, annual_income, documents, applicant_name


def parse_bank_statement(doc_json: dict):
    logger.debug("Parsing bank statement document")
    fields = extract_fields(doc_json)
    if not fields:
        raise ValueError("No recognizable bank fields found")

    monthly_income = safe_float(fields.get("salary_deposit"))
    closing_balance = safe_float(fields.get("closing_balance"))
    monthly_debt = monthly_income - closing_balance if monthly_income else 0
    dti = (monthly_debt / monthly_income) * 100 if monthly_income > 0 else None
    logger.info(f"Bank statement parsed: income={monthly_income}, debt={monthly_debt}, dti={dti}")
    return monthly_income, monthly_debt, dti


def parse_pay_stub(doc_json: dict):
    logger.debug("Parsing pay stub document")
    fields = extract_fields(doc_json)
    if not fields:
        raise ValueError("No recognizable pay stub fields found")

    net_pay = safe_float(fields.get("net_pay")) if fields.get("net_pay") else None
    logger.info(f"Pay stub parsed: net_pay={net_pay}")
    return net_pay


def parse_tax_return(doc_json: dict):
    logger.debug("Parsing tax return document")
    fields = extract_fields(doc_json)
    if not fields:
        raise ValueError("No recognizable tax fields found")

    tax_income = safe_float(fields.get("Annual_income")) if fields.get("Annual_income") else None
    logger.info(f"Tax return parsed: annual_income={tax_income}")
    return tax_income


def parse_id_proof(doc_json: dict):
    logger.debug("Parsing ID proof document")
    fields = extract_fields(doc_json)
    if not fields:
        raise ValueError("No recognizable ID fields found")

    id_name = fields.get("Full_Name")
    id_number = fields.get("id_number")
    dob = fields.get("Date_of_birth")
    logger.info(f"ID proof parsed: id_name={id_name}, id_number={id_number}, dob={dob}")
    return id_name, id_number, dob
