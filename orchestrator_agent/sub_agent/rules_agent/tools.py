from ..shared.logger import get_logger

logger = get_logger("rules_agent")

def loan_approval(payload: dict) -> str:
    logger.info("Evaluating loan approval rules")

    try:
        credit = payload.get("credit")
        loan = payload.get("loan")
        months = payload.get("months")
        dti = payload.get("dti")
        annual = payload.get("annual")
        documents = payload.get("documents", {})
        net_pay = payload.get("net_pay")
        bank_income = payload.get("bank_income")
        tax_income = payload.get("tax_income")
        id_name = payload.get("id_name")
        applicant_name = payload.get("applicant_name")

        # --- Detect missing or mismatched document data ---
        # If key expected from docs are missing entirely, it’s probably a random file.
        expected_keys = ["credit", "loan", "months", "dti", "annual"]
        if not any(payload.get(k) for k in expected_keys) and not any([net_pay, bank_income, tax_income]):
            logger.warning("Uploaded document does not match expected financial data structure.")
            return "Document mismatched or unrecognized document type"

        # --- Missing document detection ---
        missing_docs = [doc for doc, submitted in documents.items() if not submitted]
        if missing_docs:
            logger.warning(f"Missing documents: {missing_docs}")

        # --- Validation Rules ---
        if id_name and applicant_name and id_name.lower() != applicant_name.lower():
            return f"Flagged: ID Proof Name ({id_name}) does not match Application Form ({applicant_name})"
        if net_pay and bank_income and abs(net_pay - bank_income) > (0.2 * net_pay):
            return f"Flagged: Pay Stub Net Pay ({net_pay}) does not match Bank Income ({bank_income})"
        if tax_income and annual and abs(tax_income - annual) > (0.2 * tax_income):
            return f"Flagged: Tax Return Income ({tax_income}) does not match Verified Annual Income ({annual})"
        if None in [credit, loan, months, dti, annual]:
            return "Error: Missing required data"
        if credit < 580:
            return "Denied: Credit too low"
        if loan > 50000 or months > 60:
            if credit < 700 or dti > 36:
                return "Extra approval required"
        if credit >= 740 and dti <= 36:
            return "Approved"
        if credit >= 670 and dti <= 25:
            return "Approved"
        if credit >= 600 and dti <= 20:
            return "Approved (higher interest rate)"
        if credit >= 700 and dti <= 80:
            return "Approved"
        return "Denied"

    except Exception as e:
        logger.error(f"Error while evaluating loan approval: {str(e)}")
        return "Document mismatched or invalid format"
