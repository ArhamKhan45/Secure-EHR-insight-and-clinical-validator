# Secure EHR Insight & Clinical Validator

An AI-powered **Retrieval-Augmented Generation (RAG)** system for clinical information retrieval and validation.

The project combines EHR data, biomedical embeddings, semantic search with pgvector, PII redaction, guardrails, FastAPI, and Streamlit to provide a secure workflow for querying clinical information.

## Features

- Retrieval-Augmented Generation (RAG)
- EHR data ingestion and processing
- PostgreSQL with pgvector
- Semantic clinical search
- Biomedical embeddings using BioClinical ModernBERT
- Patient and clinical-record retrieval
- PII detection and redaction with Microsoft Presidio
- Custom PII recognizers
- NeMo Guardrails for controlled AI interactions
- FastAPI backend
- Streamlit clinical interface
- Dockerized deployment
- PostgreSQL running on AWS EC2

## Tech Stack

- **Python 3.12+**
- **RAG / LLM Application**
- **FastAPI**
- **Streamlit**
- **PostgreSQL 16**
- **pgvector**
- **SQLAlchemy**
- **Sentence Transformers**
- **BioClinical ModernBERT**
- **Microsoft Presidio**
- **NeMo Guardrails**
- **Docker**
- **AWS EC2**

## RAG Architecture

```text
Clinical EHR Data
       │
       ▼
   PostgreSQL
       │
       ▼
Clinical Text Extraction
       │
       ▼
Biomedical Embeddings
       │
       ▼
    pgvector
       │
       │
User Clinical Query
       │
       ▼
Query Embedding
       │
       ▼
Semantic Retrieval
       │
       ▼
Relevant Clinical Context
       │
       ▼
PII Redaction + Guardrails
       │
       ▼
      LLM
       │
       ▼
Clinical Response
```

## Project Structure

```text
.
├── .dockerignore
├── .gitignore
├── .vercel
│   ├── project.json
│   └── README.txt
├── .vscode
│   └── settings.json
├── data
│   └── MIMIC_IV_Trasncript.csv
├── Dockerfile
├── instruction_notes
│   ├── AWS_EC2_Docker_Deployment_Guide.md
│   ├── instructions.txt
│   └── uv_instructions.txt
├── README.md
├── requirements.txt
├── scripts
│   ├── 01_ingest_baseline_data.py
│   ├── 02_verify_ingestion.py
│   ├── 03_apply_vector_schema.py
│   ├── 04_generate_embeddings.py
│   ├── 05_test_vector_search.py
│   └── 06_test_guardrails.py
├── src
│   ├── api
│   │   └── main.py
│   ├── database
│   │   └── schema.sql
│   ├── guardrails
│   │   ├── config.yml
│   │   └── rails.co
│   ├── pii_redaction
│   │   └── presidio_service.py
│   └── ui
│       └── app.py
└── start.sh
```

> `EHR-database.pem` is a local SSH key and should remain private and should not be committed to GitHub.

## 1. Clone the Repository

```bash
git clone https://github.com/ArhamKhan45/Secure-EHR-insight-and-clinical-validator.git
cd Secure-EHR-insight-and-clinical-validator
```

## 2. Create Virtual Environment

```bash
uv venv
```

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```powershell
.venv\Scripts\activate
```

## 3. Install Dependencies

```bash
uv pip install -r requirements.txt
```

## 4. Environment Variables

Create a `.env` file:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ehr_db
DB_USER=fde_admin
DB_PASSWORD=your_password

HF_TOKEN=your_huggingface_token

BACKEND_API_URL=http://127.0.0.1:8000/api/v1
```

Never commit `.env` or private credentials to GitHub.

## 5. PostgreSQL Setup

The project uses **PostgreSQL 16** with **pgvector**.

### Install PostgreSQL

For Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y curl ca-certificates

sudo install -d /usr/share/postgresql-common/pgdg

sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
  --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc

sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

sudo apt update

sudo apt install -y postgresql-16 postgresql-contrib-16
```

### Configure PostgreSQL

```bash
sudo nano /etc/postgresql/16/main/postgresql.conf
```

Configure:

```conf
listen_addresses = '*'
```

Then:

```bash
sudo nano /etc/postgresql/16/main/pg_hba.conf
```

Add the appropriate host authentication rule:

```conf
host    all    all    0.0.0.0/0    scram-sha-256
```

Restart PostgreSQL:

```bash
sudo systemctl restart postgresql
```

## 6. Create Database

```bash
sudo -u postgres psql -c "CREATE DATABASE ehr_db;"
```

Create the application user:

```bash
sudo -i -u postgres psql
```

Inside PostgreSQL:

```sql
CREATE USER fde_admin WITH PASSWORD 'your_password';

ALTER ROLE fde_admin SET client_encoding TO 'utf8';

ALTER ROLE fde_admin SET default_transaction_isolation TO 'read committed';

ALTER ROLE fde_admin SET timezone TO 'UTC';

GRANT ALL PRIVILEGES ON DATABASE ehr_db TO fde_admin;

\c ehr_db

GRANT ALL ON SCHEMA public TO fde_admin;

\q
```

## 7. Install pgvector

```bash
sudo apt update
sudo apt install -y postgresql-16-pgvector
```

Verify:

```bash
ls /usr/share/postgresql/16/extension/vector*
```

Enable:

```bash
sudo -u postgres psql -d ehr_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 8. Database Schema

```bash
python scripts/03_apply_vector_schema.py
```

The clinical embedding column uses:

```text
vector(768)
```

Semantic search uses cosine distance:

```sql
clinical_embedding <=> CAST(:query_vector AS vector(768))
```

## 9. Data Ingestion Pipeline

### Ingest EHR Data

```bash
python scripts/01_ingest_baseline_data.py
```

### Verify Ingestion

```bash
python scripts/02_verify_ingestion.py
```

### Apply Vector Schema

```bash
python scripts/03_apply_vector_schema.py
```

### Generate Clinical Embeddings

```bash
python scripts/04_generate_embeddings.py
```

The project uses:

```text
NeuML/bioclinical-modernbert-base-embeddings
```

### Test Vector Search

```bash
python scripts/05_test_vector_search.py
```

## 10. PII Redaction

The project uses **Microsoft Presidio** to detect and anonymize sensitive information.

Service:

```text
src/pii_redaction/presidio_service.py
```

Run:

```bash
python src/pii_redaction/presidio_service.py
```

The implementation includes:

- Presidio `AnalyzerEngine`
- Presidio `AnonymizerEngine`
- Custom SSN recognition
- Hospital-specific deny-list recognition
- Sensitive clinical information protection

## 11. Guardrails

Configuration:

```text
src/guardrails/config.yml
src/guardrails/rails.co
```

Test:

```bash
python scripts/06_test_guardrails.py
```

## 12. FastAPI Backend

Start:

```bash
uvicorn src.api.main:app --reload
```

API:

```text
http://localhost:8000
```

Documentation:

```text
http://localhost:8000/docs
```

### API Endpoints

```http
GET  /api/v1/patients
POST /api/v1/clinical-query
POST /api/v1/chat
```

## 13. Streamlit UI

Start:

```bash
streamlit run src/ui/app.py
```

Application:

```text
http://localhost:8501
```

## 14. Local Startup Workflow

### Terminal 1 — FastAPI

```bash
source .venv/bin/activate
uvicorn src.api.main:app --reload
```

### Terminal 2 — Streamlit

```bash
source .venv/bin/activate
streamlit run src/ui/app.py
```

Open:

```text
http://localhost:8501
```

## 15. Docker

Build:

```bash
docker build --pull \
  -t secure-ehr-insight-and-clinical-validator:latest .
```

Run:

```bash
docker run -d \
  --name secure-ehr-insight-and-clinical-validator \
  --restart unless-stopped \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  -p 8000:8000 \
  -p 8501:8501 \
  secure-ehr-insight-and-clinical-validator:latest
```

Check:

```bash
docker ps
```

Logs:

```bash
docker logs -f secure-ehr-insight-and-clinical-validator
```

Stop:

```bash
docker stop secure-ehr-insight-and-clinical-validator
```

Remove:

```bash
docker rm -f secure-ehr-insight-and-clinical-validator
```

## 16. Docker Database Configuration

When PostgreSQL runs directly on the EC2 host:

```env
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=ehr_db
DB_USER=fde_admin
DB_PASSWORD=your_password
```

The container uses:

```bash
--add-host=host.docker.internal:host-gateway
```

## 17. Docker Internal Backend URL

FastAPI and Streamlit run inside the same container.

```env
BACKEND_API_URL=http://127.0.0.1:8000/api/v1
```

## 18. Updating Environment Variables

`.env` changes do not require a Docker rebuild.

Recreate the container:

```bash
docker rm -f secure-ehr-insight-and-clinical-validator
```

```bash
docker run -d \
  --name secure-ehr-insight-and-clinical-validator \
  --restart unless-stopped \
  --env-file .env \
  --add-host=host.docker.internal:host-gateway \
  -p 8000:8000 \
  -p 8501:8501 \
  secure-ehr-insight-and-clinical-validator:latest
```

Rebuild only when changing application code, `Dockerfile`, `requirements.txt`, or `start.sh`.

```bash
docker build --pull \
  -t secure-ehr-insight-and-clinical-validator:latest .
```

## 19. Health Checks

FastAPI:

```bash
curl http://localhost:8000/openapi.json
```

Streamlit:

```bash
curl http://localhost:8501/_stcore/health
```

## 20. Application Flow

```text
                 ┌─────────────────────┐
                 │     Clinical EHR    │
                 │        Data         │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │     PostgreSQL      │
                 │      + pgvector     │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │ Biomedical Embedding│
                 │      Model          │
                 └──────────┬──────────┘
                            │
                            ▼
                 ┌─────────────────────┐
                 │  Vector Retrieval   │
                 │      / RAG          │
                 └──────────┬──────────┘
                            │
             ┌──────────────┴──────────────┐
             ▼                             ▼
      ┌──────────────┐             ┌──────────────┐
      │    Presidio  │             │   Guardrails │
      │ PII Redaction│             │    / NeMo    │
      └──────┬───────┘             └──────┬───────┘
             └──────────────┬──────────────┘
                            ▼
                     ┌────────────┐
                     │    LLM     │
                     └─────┬──────┘
                           ▼
                  ┌──────────────────┐
                  │ Clinical Response│
                  └──────────────────┘
```

## 21. Security

Do not commit:

```text
.env
*.pem
private SSH keys
API keys
database passwords
Hugging Face tokens
```

## 22. Deployment Architecture

```text
                    Internet
                       │
                       ▼
              ┌─────────────────┐
              │     AWS EC2     │
              │     Ubuntu      │
              └────────┬────────┘
                       │
              ┌────────▼────────┐
              │     Docker      │
              │                 │
              │  ┌───────────┐  │
              │  │  FastAPI  │  │
              │  │   :8000   │  │
              │  └─────┬─────┘  │
              │        │        │
              │  ┌─────▼─────┐  │
              │  │ Streamlit │  │
              │  │   :8501   │  │
              │  └───────────┘  │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   PostgreSQL    │
              │   + pgvector    │
              │     :5432       │
              └─────────────────┘
```

## 23. Project Goal

The project demonstrates how a clinical AI application can combine:

- Retrieval-Augmented Generation
- Biomedical embeddings
- Vector databases
- Clinical EHR data
- Semantic search
- PII protection
- AI guardrails
- FastAPI backend services
- Streamlit interfaces
- PostgreSQL
- Docker
- AWS deployment

The focus is on building a secure, retrieval-driven architecture for working with clinical information.

---

## Developer

**[Arham Ullah Khan — Developer](https://arhamullahkhan.vercel.app/)**
