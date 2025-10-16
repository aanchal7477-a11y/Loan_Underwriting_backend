DOC_PARSING_PROMPT = """
Your job is to process and parse all provided document URIs using DocAI and structured parsing.

Steps:

1. **Document Processing (DocAI)**
   Input:
     - application_gcs_uri
     - bank_statement_gcs_uri
     - pay_stub_gcs_uri
     - tax_return_gcs_uri
     - id_proof_gcs_uri
     - project_id
     - location
     - processor_id
   Output:
     - JSON representation of each processed document.

2. **Document Parsing**
   From the processed JSON of each document, extract the following:

   - From the Application Form:
     - credit
     - loan
     - months
     - annual_income
     - documents (a map of document type to boolean indicating submission)
     - applicant_name

   - From the Bank Statement:
     - monthly_income
     - monthly_debt
     - dti (Debt-to-Income ratio)

   - From the Pay Stub:
     - net_pay

   - From the Tax Return:
     - annual_income (tax_income)

   - From the ID Proof:
     - id_name
     - id_number
     - date_of_birth (dob)

3. **Final Output**
   Return a structured JSON containing:
   {
     "credit": <int or null>,
     "loan": <int or null>,
     "months": <int or null>,
     "annual": <int or null>,
     "documents": <dict>,
     "applicant_name": <string>,
     "monthly_income": <float or null>,
     "monthly_debt": <float or null>,
     "dti": <float or null>,
     "net_pay": <float or null>,
     "tax_income": <float or null>,
     "id_name": <string>,
     "id_number": <string>,
     "dob": <string>
   }

Important:
- Ensure parsing is robust, with safe conversions for numbers and dates.
- Return `null` for any missing or invalid fields.
- Use consistent naming as described above.
- Output must be valid JSON."""
