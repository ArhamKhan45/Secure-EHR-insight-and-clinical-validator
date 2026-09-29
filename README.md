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

Using `uv`:

```bash
uv venv
```

Activate the environment.

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
OPENROUTER_API_KEY=xxx-xx-x-x-x-x-x-x-x-x-x-
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

Create the database:

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

Verify the extension:

```bash
ls /usr/share/postgresql/16/extension/vector*
```

Enable pgvector:

```bash
sudo -u postgres psql -d ehr_db \
  -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

## 8. Database Schema

Apply the project schema:

```bash
python scripts/03_apply_vector_schema.py
```

The clinical embedding column uses:

```text
vector(768)
```

The system uses cosine distance for semantic similarity search.

Example:

```sql
clinical_embedding <=> CAST(:query_vector AS vector(768))
```

## 9. Data Ingestion Pipeline

### Step 1 — Ingest EHR Data

```bash
python scripts/01_ingest_baseline_data.py
```

### Step 2 — Verify Ingestion

```bash
python scripts/02_verify_ingestion.py
```

### Step 3 — Apply Vector Schema

```bash
python scripts/03_apply_vector_schema.py
```

### Step 4 — Generate Clinical Embeddings

```bash
python scripts/04_generate_embeddings.py
```

The project uses:

```text
NeuML/bioclinical-modernbert-base-embeddings
```

The generated embeddings are stored in PostgreSQL using pgvector.

### Step 5 — Test Vector Search

```bash
python scripts/05_test_vector_search.py
```

## 10. PII Redaction

The project uses **Microsoft Presidio** to detect and anonymize sensitive information.

The service is located at:

```text
src/pii_redaction/presidio_service.py
```

Run the service test:

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

Guardrails are configured in:

```text
src/guardrails/config.yml
src/guardrails/rails.co
```

Run the guardrail test:

```bash
python scripts/06_test_guardrails.py
```

The guardrail layer helps control and validate AI interactions before generating clinical responses.

## 12. FastAPI Backend

Start the FastAPI backend:

```bash
uvicorn src.api.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### API Endpoints

#### Get Patients

```http
GET /api/v1/patients
```

#### Clinical Query

```http
POST /api/v1/clinical-query
```

#### Chat

```http
POST /api/v1/chat
```

## 13. Streamlit UI

Start Streamlit:

```bash
streamlit run src/ui/app.py
```

The application will be available at:

```text
http://localhost:8501
```

## 14. Local Startup Workflow

After PostgreSQL and pgvector are configured:

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

The database ingestion and embedding scripts only need to be executed when setting up or updating the dataset.

## 15. Docker

Build the Docker image:

```bash
docker build --pull \
  -t secure-ehr-insight-and-clinical-validator:latest .
```

Run the container:

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

### Check Container

```bash
docker ps
```

### View Logs

```bash
docker logs -f secure-ehr-insight-and-clinical-validator
```

### Stop Container

```bash
docker stop secure-ehr-insight-and-clinical-validator
```

### Remove Container

```bash
docker rm -f secure-ehr-insight-and-clinical-validator
```

## 16. Docker Database Configuration

When PostgreSQL is running directly on the EC2 host and the application is running inside Docker, use:

```env
DB_HOST=host.docker.internal
DB_PORT=5432
DB_NAME=ehr_db
DB_USER=fde_admin
DB_PASSWORD=your_password
```

The Docker container is started with:

```bash
--add-host=host.docker.internal:host-gateway
```

This allows the container to communicate with PostgreSQL running on the host machine.

## 17. Docker Internal Backend URL

FastAPI and Streamlit run inside the same container.

Therefore Streamlit communicates with FastAPI through:

```env
BACKEND_API_URL=http://127.0.0.1:8000/api/v1
```

## 18. Updating Environment Variables

Changing `.env` does not require rebuilding the Docker image.

Recreate the container:

```bash
docker rm -f secure-ehr-insight-and-clinical-validator
```

Then:

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

A Docker rebuild is required when changing:

- `Dockerfile`
- `requirements.txt`
- `start.sh`
- Application source code

Rebuild with:

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

Sensitive configuration should be stored in environment variables.

Do not commit:

```text
.env
*.pem
private SSH keys
API keys
database passwords
Hugging Face tokens
```

Use `.gitignore` to prevent sensitive files from being committed.

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

**Arham Ullah Khan — Developer**
