import os
import json
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import storage
from datetime import datetime
from google.genai.types import Content, Part
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from agent import orchestrator_agent
from dotenv import load_dotenv

load_dotenv()

BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("PROCESSOR_LOCATION")
PROCESSOR_ID = os.getenv("PROCESSOR_ID")

APP_NAME = "loan_underwriting_app"
USER_ID = "user_123"
SESSION_ID = "session_123"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---------------------------
# Upload PDF to GCS
# ---------------------------
def upload_to_gcs(bucket_name: str, blob_name: str, file: UploadFile) -> str:
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.upload_from_file(file.file, rewind=True)
    return f"gs://{bucket_name}/{blob_name}"

# ---------------------------
# ADK runner
# ---------------------------
session_service = InMemorySessionService()
runner = Runner(agent=orchestrator_agent, app_name=APP_NAME, session_service=session_service)

@app.post("/underwrite")
async def underwrite(
    application_pdf: UploadFile,
    bank_statement_pdf: UploadFile,
    pay_stub_pdf: UploadFile,
    tax_return_pdf: UploadFile,
    id_proof_pdf: UploadFile,
    declared_amount: int = Form(...)
):
    # Upload all PDFs to GCS
    app_gcs = upload_to_gcs(BUCKET_NAME, application_pdf.filename, application_pdf)
    bank_gcs = upload_to_gcs(BUCKET_NAME, bank_statement_pdf.filename, bank_statement_pdf)
    pay_gcs = upload_to_gcs(BUCKET_NAME, pay_stub_pdf.filename, pay_stub_pdf)
    tax_gcs = upload_to_gcs(BUCKET_NAME, tax_return_pdf.filename, tax_return_pdf)
    id_gcs = upload_to_gcs(BUCKET_NAME, id_proof_pdf.filename, id_proof_pdf)
    output_gcs_folder = f"gs://loan_approve_output/"
# "gs://loan_approve_output/"

    # Build ADK content payload
    user_content = Content(
        role="user",
        parts=[Part(text=json.dumps({
            "function": "process_single_doc",
            **{
                "application_gcs_uri": app_gcs,
                "bank_statement_gcs_uri": bank_gcs,
                "pay_stub_gcs_uri": pay_gcs,
                "tax_return_gcs_uri": tax_gcs,
                "id_proof_gcs_uri": id_gcs,
                "declared_amount": declared_amount,
                "project_id": PROJECT_ID,
                "location": LOCATION,
                "processor_id": PROCESSOR_ID,
                "bucket_name": BUCKET_NAME,
                "output_gcs_folder": output_gcs_folder
            }
        }))]
    )

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    final_decision = None
    async for event in runner.run_async(
        user_id=USER_ID, session_id=SESSION_ID, new_message=user_content
    ):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                final_decision = part.text
    now = datetime.now()
    stages = [
        {
            "stage": "Approval Initiated",
            "completed": True,
            "approver": "System",
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
        },
        {
            "stage": "Process",
            "completed": True,
            "approver": None,
            "date": None,
            "time": None,
        },
        {
            "stage": "Qualify",
            "completed": True,
            "approver": None,
            "date": None,
            "time": None,
        },
        {
            "stage": "Final Step",
            "completed": True,
            "approver": None,
            "date": None,
            "time": None,
        },
    ]
    print("final_decision",final_decision)
    # return json.dumps({"decision": final_decision,
    # "stages": stages})
    return {"decision": final_decision,
    "stages": stages}