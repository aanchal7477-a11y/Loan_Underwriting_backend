STORAGE_PROMPT = """
Your task is to save loan underwriting results into BigQuery.

You will be provided a single JSON payload containing all required fields:

{
  "appicant_name": string,
  "credit": integer,
  "loan": number,
  "months": integer,
  "annual": number,
  "monthly_income": number,
  "monthly_debt": number,
  "dti": number,
  "net_pay": number,
  "tax_income": number,
  "id_number": string,
  "dob": string,
  "decision": string
}

Save these results to the BigQuery table defined in TABLE_ID.  
Log success or failure accordingly. Return the decision string only.

"""
