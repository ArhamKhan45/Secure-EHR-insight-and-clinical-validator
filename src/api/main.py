# uvicorn src.api.main:app --reload

import os
from typing import List

from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from pydantic import BaseModel
from nemoguardrails import RailsConfig, LLMRails
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

from src.pii_redaction.presidio_service import ClinicalPIIRedactor


load_dotenv()

app = FastAPI(title="Zero-Trust Clinical RAG API")

# Global state to hold heavy ML models so they only load once at startup
middleware = {}


@app.on_event("startup")
async def startup_event():
    print("⏳ Booting Enterprise AI Middlewares...")

    # 1. Load Presidio
    middleware["redactor"] = ClinicalPIIRedactor()

    # 2. Load NeMo Guardrails
    config = RailsConfig.from_path("./src/guardrails")
    middleware["rails"] = LLMRails(config)

    # 3. Load local embedding model
    print("⏳ Loading local BioClinical ModernBERT embedding model...")
    middleware["embedder"] = SentenceTransformer(
        "NeuML/bioclinical-modernbert-base-embeddings"
    )

    print("✅ System Ready on port 8000.")


# --- DATABASE CONNECTION HELPER ---

def get_db_engine():
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASSWORD")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")

    if db_host:
        db_url = (
            f"postgresql+psycopg://"
            f"{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        )
    else:
        db_url = os.getenv(
            "POSTGRES_URL",
            "postgresql+psycopg://postgres:password@localhost:5432/clinical_db",
        )

    return create_engine(db_url)


# --- MODELS ---

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    patient_id: str
    messages: List[ChatMessage]


class ClinicalQuery(BaseModel):
    patient_id: str
    prompt: str


# --- ENDPOINT 1: CLINICAL QUERY ---

@app.post("/api/v1/clinical-query")
async def process_clinical_query(query: ClinicalQuery):
    try:
        raw_db_context = f"""
        Patient John Doe (ID: {query.patient_id}) was admitted on March 15th.
        Last recorded Furosemide dosage was 40mg IV.
        Attending physician: Dr. Gregory House, ID: 20043.
        """

        redactor = middleware["redactor"]

        safe_context = redactor.redact_clinical_context(
            raw_text=raw_db_context
        )

        augmented_prompt = (
            f"Clinical Context:\n{safe_context}\n\n"
            f"User Question: {query.prompt}"
        )

        rails = middleware["rails"]

        response = await rails.generate_async(
            messages=[
                {
                    "role": "user",
                    "content": augmented_prompt,
                }
            ]
        )

        return {
            "status": "success",
            "redacted_context_used": safe_context.strip(),
            "llm_response": response["content"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# --- ENDPOINT 2: PRODUCTION CHAT ---

@app.post("/api/v1/chat")
async def process_chat(request: ChatRequest):
    try:
        latest_question = request.messages[-1].content

        engine = get_db_engine()

        # 1. Embed the user's question
        embedder = middleware["embedder"]

        query_vector = embedder.encode(
            latest_question
        ).tolist()

        # 2. Native pgvector similarity search
        with engine.connect() as conn:
            query = text(
                """
                SELECT
                    drug,
                    dose_val_rx,
                    dose_unit_rx,
                    route,
                    eventtype,
                    test_name,
                    comments,
                    description
                FROM patient_encounters
                WHERE subject_id = :subject_id
                  AND clinical_embedding IS NOT NULL
                ORDER BY clinical_embedding
                    <=> CAST(:query_embedding AS vector)
                LIMIT 5;
                """
            )

            result = conn.execute(
                query,
                {
                    "subject_id": int(request.patient_id),
                    "query_embedding": str(query_vector),
                },
            )

            rows = result.fetchall()

        # 3. Build clinical context
        if not rows:
            real_db_context = (
                f"No historical records found for patient "
                f"{request.patient_id}."
            )
        else:
            context_lines = []

            for row in rows:
                context_lines.append(
                    f"Drug: {row.drug} "
                    f"({row.dose_val_rx} {row.dose_unit_rx}), "
                    f"Route: {row.route}, "
                    f"Event: {row.eventtype}, "
                    f"Test: {row.test_name}, "
                    f"Comments: {row.comments}, "
                    f"Diagnosis: {row.description}"
                )

            real_db_context = (
                f"[Records for Patient ID: {request.patient_id}]\n"
                + "\n".join(context_lines)
            )

        # 4. Redact clinical context
        redactor = middleware["redactor"]

        safe_context = redactor.redact_clinical_context(
            raw_text=real_db_context
        )

        # 5. Add retrieved context to the conversation
        augmented_prompt = (
            f"Clinical Context:\n{safe_context}\n\n"
            f"User Question: {latest_question}"
        )

        nemo_history = [
            {
                "role": msg.role,
                "content": msg.content,
            }
            for msg in request.messages[:-1]
        ]

        nemo_history.append(
            {
                "role": "user",
                "content": augmented_prompt,
            }
        )

        # 6. Route through NeMo Guardrails
        rails = middleware["rails"]

        response = await rails.generate_async(
            messages=nemo_history
        )

        return {
            "status": "success",
            "llm_response": response["content"],
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# --- ENDPOINT 3: FETCH UNIQUE PATIENTS ---

@app.get("/api/v1/patients")
async def get_unique_patients():
    try:
        engine = get_db_engine()

        with engine.connect() as conn:
            query = text(
                """
                SELECT DISTINCT subject_id
                FROM patient_encounters
                WHERE subject_id IS NOT NULL
                  AND clinical_embedding IS NOT NULL
                ORDER BY subject_id;
                """
            )

            result = conn.execute(query)

            patients = [
                str(row[0])
                for row in result
            ]

        return {
            "patients": patients
            if patients
            else ["No embedded patients found"]
        }

    except Exception as e:
        return {
            "patients": [],
            "error": str(e),
        }