# AI Document Intelligence Platform

An evidence-grounded medical document intelligence platform built with React, FastAPI, LangGraph, MongoDB, Redis, ChromaDB, Gemini, and a local observability stack.

The project started as a verifiable RAG proof of concept for uploaded medical PDFs. It has been refactored into a more production-style backend that demonstrates asynchronous API design, typed API contracts, stateful agent orchestration, tool calling, persistent workflow checkpoints, background ingestion, caching, observability, and evaluation.

> This application is for document analysis and software architecture practice. It is not a medical diagnosis tool.

## What The App Does

Users can upload medical PDF documents such as lab reports, blood reports, scanned reports, and other clinical documents. The system extracts text, chunks it, embeds it, stores searchable vectors, and lets the user ask questions about the uploaded documents.

The answer flow is designed to be evidence-grounded:

- It retrieves relevant chunks from uploaded documents.
- It generates answers only from retrieved context.
- It returns citations with document name, page number, snippet, and score.
- It validates answer grounding.
- It returns a safe insufficient-evidence response when documents do not support an answer.

Example questions:

- "What was my RBC value in the November report?"
- "Compare hemoglobin values across all uploaded reports."
- "Show a trend analysis for WBC across the reports."
- "Which document contains platelet count information?"
- "How many uploaded documents are ready for querying?"

## Current Architecture

```text
React Client
    |
    | REST / SSE
    v
FastAPI API
    |
    | request id, validation, errors, metrics
    v
Query Service
    |
    v
LangGraph StateGraph
    |
    +--> Query Classifier
    +--> Retrieval Worker
    +--> Verification Worker
    +--> Query Rewrite / Retry
    +--> Human Review Interrupt
    +--> Answer Generator
    +--> Answer Validator
    |
    v
Tool Registry
    |
    +--> search_documents
    +--> get_document_metadata
    +--> list_uploaded_documents
    |
    v
Data Layer
    |
    +--> MongoDB: metadata, conversations, checkpoints
    +--> Redis: query cache and Celery broker
    +--> ChromaDB: vector embeddings
    +--> Local storage: temporary uploads and persisted vector DB

Observability
    |
    +--> Prometheus metrics
    +--> OpenTelemetry traces
    +--> Tempo traces
    +--> Loki logs
    +--> Grafana dashboard target
    +--> Optional Langfuse AI traces
```

## Repository Layout

```text
verifiable-rag/
|-- docker-compose.yml
|-- .env.example
|-- README.md
|-- ARCHITECTURE.txt
|-- INSTALLATION_GUIDE.txt
|-- startup.ps1
|
|-- backend/
|   |-- Dockerfile
|   |-- docker-compose.yml
|   |-- requirements.txt
|   |-- main.py
|   |-- vectorstore.py
|   |-- ocr.py
|   |-- chunking.py
|   |-- rag.py
|   |-- ARCHITECTURE_REFACTOR.md
|   |
|   |-- app/
|   |   |-- main.py
|   |   |-- api/
|   |   |-- core/
|   |   |-- schemas/
|   |   |-- services/
|   |   |-- agents/
|   |   |-- tools/
|   |   |-- repositories/
|   |   |-- integrations/
|   |   |-- workers/
|   |
|   |-- evaluations/
|   |-- observability/
|   |-- tests/
|
|-- frontend/
|   |-- Dockerfile
|   |-- package.json
|   |-- public/
|   |-- src/
|
|-- Trurth Script and sample pdfs/
|-- Screen captures/
```

## Main Technologies

### Frontend

- React
- Create React App
- Browser session storage for local conversation display
- Legacy-compatible API calls to `/upload`, `/query`, and `/delete-document`

### Backend

- FastAPI
- Pydantic contracts
- Async route handlers
- Dependency-injected services
- Structured error responses
- Request ID middleware
- Server-Sent Events for streaming query responses

### AI And RAG

- Gemini API through `google-genai`
- Sentence Transformers for local embeddings
- ChromaDB for vector search
- LangGraph for stateful workflow orchestration
- Pydantic structured LLM output parsing
- Grounding verification
- Evidence citations

### Data Layer

- MongoDB for document metadata and LangGraph checkpoints
- Redis for best-effort query caching
- Celery workers for durable document ingestion
- ChromaDB for vector embeddings
- Local filesystem for upload staging and vector persistence

### Observability

- Prometheus metrics
- OpenTelemetry trace hooks
- Grafana Tempo
- Grafana Loki
- Grafana UI
- Optional Langfuse tracing

## Quick Start With Docker

The easiest way to run the full project is from the repository root with Docker Compose.

### 1. Create `.env`

```powershell
cd C:\Users\DELL\Documents\Codex\2026-08-15\co\work\verifiable-rag
Set-Content -Path .env -Value "GEMINI_API_KEY=your_new_gemini_api_key_here"
```

Or create `.env` manually:

```env
GEMINI_API_KEY=your_new_gemini_api_key_here
```

### 2. Start Everything

```powershell
docker compose up --build
```

This starts:

- FastAPI backend
- Celery ingestion worker
- React frontend
- MongoDB
- Redis
- Prometheus
- OpenTelemetry Collector
- Tempo
- Loki
- Grafana

The first build can take a while because the backend installs machine-learning and vector database dependencies.

### 3. Open The App

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs
- API health: http://localhost:8000/api/v1/health
- Prometheus metrics: http://localhost:8000/api/v1/metrics
- Prometheus UI: http://localhost:9090
- Grafana: http://localhost:3001
- Grafana login: `admin` / `admin`

### 4. Stop Everything

```powershell
docker compose down
```

To delete volumes as well:

```powershell
docker compose down -v
```

This removes MongoDB and Grafana persisted data.

## Environment Variables

The root `docker-compose.yml` reads environment variables from `.env`.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `GEMINI_API_KEY` | Yes | None | API key for Gemini LLM calls |
| `MONGODB_URL` | No in Docker | `mongodb://mongo:27017` | MongoDB connection string |
| `MONGODB_DATABASE` | No | `verifiable_rag` | Main Mongo database name |
| `REDIS_URL` | No in Docker | `redis://redis:6379/0` | Redis connection string |
| `CELERY_BROKER_URL` | No in Docker | `redis://redis:6379/0` | Celery task broker |
| `CELERY_RESULT_BACKEND` | No in Docker | `redis://redis:6379/1` | Celery job status/result backend |
| `USE_CELERY_INGESTION` | No | `true` in Docker | Enqueue uploads through Celery instead of local task fallback |
| `LANGGRAPH_CHECKPOINTER` | No | `mongo` in Docker, `memory` in settings | Checkpoint backend |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | `http://otel-collector:4317` in Docker | OTEL trace export endpoint |
| `LANGFUSE_PUBLIC_KEY` | No | None | Enables Langfuse traces when paired with secret key |
| `LANGFUSE_SECRET_KEY` | No | None | Langfuse secret key |
| `LANGFUSE_HOST` | No | Langfuse default | Self-hosted Langfuse URL |

Minimal `.env`:

```env
GEMINI_API_KEY=your_new_gemini_api_key_here
```

Optional `.env` with Langfuse:

```env
GEMINI_API_KEY=your_new_gemini_api_key_here
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3002
```

## Backend Architecture

The backend follows this dependency direction:

```text
route -> service -> agent/tool -> repository -> infrastructure
```

### Routes

Routes live in `backend/app/api/routes`.

- `health.py`: health and metrics endpoints
- `documents.py`: upload, list, inspect, and delete documents
- `queries.py`: query, stream, resume, and inspect LangGraph state
- `evaluations.py`: run golden dataset checks

Routes are intentionally thin. They validate request bodies, get services through dependencies, and return typed response models.

### Services

Services live in `backend/app/services`.

- `DocumentService`: accepts uploads, computes checksums, creates metadata, enqueues ingestion
- `QueryService`: handles query cache, request validation, LangGraph execution, streaming, resume, and state inspection
- `EvaluationService`: runs golden dataset evaluation cases
- `EmbeddingService`: marks the embedding provider boundary for future provider swaps

### Agents

Agents live in `backend/app/agents`.

- `supervisor.py`: LangGraph `StateGraph` orchestration
- `classifier.py`: classifies user intent using structured LLM output
- `retriever.py`: calls retrieval tools
- `verifier.py`: filters evidence and checks answer grounding
- `answer_generator.py`: generates final grounded answers
- `state.py`: graph state contract

### Tools

Tools live in `backend/app/tools`.

The tool layer is intentionally MCP-style. Each tool exposes:

- `name`
- `description`
- `input_schema`
- async invocation handler

Current tools:

- `search_documents`
- `get_document_metadata`
- `list_uploaded_documents`

This lets the agent layer stay decoupled from concrete storage and retrieval implementations.

### Repositories

Repositories live in `backend/app/repositories`.

- `DocumentRepository`: Mongo-backed document metadata with in-memory fallback
- `ConversationRepository`: conversation/message persistence boundary
- `VectorRepository`: async wrapper around Chroma vector search

### Integrations

Integrations live in `backend/app/integrations`.

- `llm_client.py`: Gemini client, structured output parsing, timeout/retry handling
- `mongodb.py`: MongoDB client and index creation
- `redis_client.py`: Redis cache with graceful fallback
- `langgraph_checkpointer.py`: Mongo or memory LangGraph checkpoint factory
- `otel.py`: OpenTelemetry setup

### Workers

Workers live in `backend/app/workers`.

- `IngestionWorker`: parses PDFs, chunks text, embeds chunks, writes vectors, updates document status
- `celery_app.py`: Celery application configured with Redis broker/result backend
- `tasks.py`: Celery task entry point for durable document ingestion

In Docker, uploads use the full queue path:

```text
FastAPI -> Mongo PENDING -> Redis broker -> Celery worker -> Mongo READY/FAILED
```

For manual local development, `USE_CELERY_INGESTION=false` keeps an in-process async fallback available.

## Document Ingestion Flow

```text
POST /api/v1/documents
    |
    v
DocumentService
    |
    +--> compute SHA-256 checksum
    +--> insert Mongo metadata with status PENDING
    +--> unique checksum index prevents duplicate content race conditions
    +--> save temporary upload
    +--> enqueue Celery ingestion task with job ID
    |
    v
Redis broker
    |
    v
Celery Worker
    |
    v
IngestionWorker
    |
    +--> status PROCESSING
    +--> extract PDF text with PyMuPDF
    +--> OCR fallback with Tesseract for scanned pages
    +--> chunk page text
    +--> embed and persist chunks in ChromaDB
    +--> status READY
```

Failure behavior:

- PDF parsing failure -> document status `FAILED`
- OCR failure -> document status `FAILED`
- embedding/vector write failure -> document status `FAILED`
- Celery task crash -> retry with exponential backoff, then `FAILED`
- partial ingestion does not mark document `READY`

Document statuses:

- `PENDING`
- `PROCESSING`
- `READY`
- `FAILED`

The upload response includes an `ingestion_job_id`, which can be checked through:

```http
GET /api/v1/documents/jobs/{job_id}
```

Recent ready documents use a concrete Mongo access pattern:

```text
find({"status": "READY"}).sort("created_at", -1).limit(20)
```

That query is backed by this compound index:

```python
await documents.create_index([("status", 1), ("created_at", -1)])
```

The point of this index is not "add indexes everywhere." It supports a specific read path: listing recent documents that are ready to query without scanning the whole collection.

## Query Flow

```text
POST /api/v1/queries
    |
    v
QueryService
    |
    +--> validate query
    +--> check Redis cache for non-threaded query
    +--> invoke LangGraph with thread_id
    |
    v
LangGraph
    |
    +--> classify_query
    +--> retrieve_documents
    +--> verify_evidence
    +--> rewrite_query if evidence is weak
    +--> human_review interrupt if suspicious content is detected
    +--> generate_answer
    +--> validate_answer
    |
    v
QueryResponse
```

The response contains:

- `answer`
- `citations`
- `confidence`
- `request_id`
- `thread_id`
- `requires_human_review`

## LangGraph Persistence

The graph is compiled with a checkpointer.

In Docker:

```env
LANGGRAPH_CHECKPOINTER=mongo
MONGODB_URL=mongodb://mongo:27017
```

Each query can provide a `thread_id`.

```json
{
  "query": "Compare RBC values across my reports",
  "thread_id": "conversation-123"
}
```

LangGraph receives:

```python
config = {
    "configurable": {
        "thread_id": "conversation-123"
    }
}
```

This allows:

- checkpointed graph state
- thread-level execution history
- state inspection
- human-in-the-loop resume
- fault-tolerant workflow design

Important distinction:

- Application conversation data is user-facing chat history.
- LangGraph thread state is internal agent execution state.

They can share the same identifier, but they are different concepts.

## Human Review And Resume

Suspicious prompt-injection-like content routes to a human-review interrupt.

Example risk markers:

- "ignore previous instructions"
- "reveal your instructions"
- "system prompt"
- "developer message"

When the graph pauses, the query response marks:

```json
{
  "requires_human_review": true
}
```

Resume endpoint:

```http
POST /api/v1/queries/resume
```

Body:

```json
{
  "thread_id": "conversation-123",
  "approved": true,
  "comment": "Reviewed and approved."
}
```

Inspect state:

```http
GET /api/v1/queries/conversation-123/state
```

## API Reference

### Health

```http
GET /api/v1/health
```

Response:

```json
{
  "status": "ok"
}
```

### Metrics

```http
GET /api/v1/metrics
```

Returns Prometheus text-format metrics.

### Upload Document

```http
POST /api/v1/documents
Content-Type: multipart/form-data
```

Form field:

- `file`: PDF file

Response:

```json
{
  "id": "document-uuid",
  "filename": "lab-report.pdf",
  "checksum": "sha256...",
  "status": "PENDING",
  "ingestion_job_id": "ingest_...",
  "request_id": "req_...",
  "message": "Document accepted and queued for Celery ingestion"
}
```

### List Documents

```http
GET /api/v1/documents
```

### Get Document

```http
GET /api/v1/documents/{document_id}
```

### List Recent Ready Documents

```http
GET /api/v1/documents/recent-ready?limit=20
```

This endpoint demonstrates a real MongoDB query/index story:

- filter by `status`
- sort by `created_at`
- limit the result set
- support the query with a compound index

### Check Ingestion Job

```http
GET /api/v1/documents/jobs/{job_id}
```

Response:

```json
{
  "job_id": "ingest_...",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "failed": false,
  "result": {
    "document_id": "document-uuid",
    "status": "READY",
    "retry_count": 0
  }
}
```

### Delete Document By Name

```http
DELETE /api/v1/documents
Content-Type: application/json
```

Body:

```json
{
  "doc_name": "lab-report.pdf"
}
```

### Query Documents

```http
POST /api/v1/queries
Content-Type: application/json
```

Body:

```json
{
  "query": "What was my RBC value?",
  "thread_id": "conversation-123",
  "stream": false
}
```

Response:

```json
{
  "answer": "The RBC value reported in the document is ...",
  "citations": [
    {
      "document_id": "document-uuid",
      "document_name": "lab-report.pdf",
      "page": 1,
      "snippet": "RBC ...",
      "score": 0.82
    }
  ],
  "confidence": 0.75,
  "request_id": "req_...",
  "thread_id": "conversation-123",
  "requires_human_review": false
}
```

### Stream Query With SSE

```http
POST /api/v1/queries/stream
Content-Type: application/json
```

Events:

```text
event: status
data: {"stage":"langgraph_started","request_id":"req_...","thread_id":"conversation-123"}

event: token
data: {"text":"The "}

event: complete
data: {"answer":"...","citations":[...]}
```

### Run Golden Evaluation

```http
POST /api/v1/evaluations/golden
```

Runs cases from:

```text
backend/evaluations/golden_dataset.json
```

## Legacy API Compatibility

The frontend currently uses the original endpoints:

- `POST /upload`
- `POST /query`
- `DELETE /delete-document`

These are still registered in `backend/app/main.py`, so the existing React app continues to work while the new `/api/v1` API exists for production-style usage and interview discussion.

## Observability

### Prometheus Metrics

Endpoint:

```http
GET /api/v1/metrics
```

Important metrics:

- `http_requests_total`
- `http_request_duration_seconds`
- `agent_runs_total`
- `agent_run_duration_seconds`
- `agent_retries_total`
- `llm_requests_total`
- `llm_request_duration_seconds`
- `retrieval_duration_seconds`
- `retrieval_results_count`
- `retrieval_empty_total`
- `cache_hits_total`
- `cache_misses_total`

### OpenTelemetry

When `OTEL_EXPORTER_OTLP_ENDPOINT` is configured, the backend exports traces to the OTEL collector.

Docker default:

```env
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
```

The Compose stack routes traces to Tempo.

### Grafana

Grafana runs at:

```text
http://localhost:3001
```

Default login:

```text
admin / admin
```

Grafana can be connected to:

- Prometheus: `http://prometheus:9090`
- Tempo: `http://tempo:3200`
- Loki: `http://loki:3100`

### Langfuse

Langfuse is optional. If configured, the app records privacy-safe AI traces.

The app intentionally avoids sending:

- raw medical document text
- full prompts
- API keys
- sensitive PII

It records:

- request ID
- thread ID
- node name
- intent
- evidence score
- result counts
- citation count
- timing metadata

## Privacy And Safety Boundaries

The system treats retrieved document content as data, not instructions.

Safety features:

- Pydantic input validation
- maximum query length
- structured LLM outputs
- controlled JSON parsing retry
- tool allowlist through registry
- prompt-injection marker detection
- human-review interrupt
- grounding validation
- insufficient-evidence fallback
- request IDs for audit trails
- telemetry that avoids raw medical text

Limitations:

- This is not a complete medical compliance implementation.
- It does not implement full authentication or authorization yet.
- It does not include production PII redaction for all fields.
- It should not be used for real clinical decision-making without substantial security, privacy, and regulatory work.

## Testing

Tests are organized by type:

```text
backend/tests/
|-- unit/
|-- integration/
|-- contract/
```

Current examples:

- classifier behavior
- duplicate checksum repository behavior
- tool registry invocation
- LLM structured output contract
- health endpoint integration
- malformed LLM structured output
- Redis unavailable graceful degradation
- Mongo duplicate insert mapping
- ingestion failure marking documents `FAILED`
- weak-evidence graph retry to safe response
- human-review graph interruption

Run backend tests locally:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pytest
```

Run static compilation:

```powershell
python -m compileall app tests
```

## Manual Local Development

Docker is recommended, but you can also run manually.

### Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
Set-Content -Path .env -Value "GEMINI_API_KEY=your_new_gemini_api_key_here"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```powershell
cd frontend
npm install
npm start
```

Manual mode requires your own MongoDB and Redis if you want persistent metadata, Redis cache, Celery ingestion, and Mongo-backed LangGraph checkpoints. Without those services, parts of the backend degrade to memory/no-cache behavior where implemented.

To use the local in-process ingestion fallback while developing manually:

```powershell
Set-Content -Path backend\.env -Value @"
GEMINI_API_KEY=your_new_gemini_api_key_here
USE_CELERY_INGESTION=false
"@
```

## Docker Services

The root `docker-compose.yml` defines:

| Service | Port | Purpose |
| --- | --- | --- |
| `frontend` | `3000` | React UI |
| `api` | `8000` | FastAPI backend |
| `worker` | none | Celery document ingestion worker |
| `mongo` | `27017` | Metadata and LangGraph checkpoints |
| `redis` | `6379` | Query cache, Celery broker, Celery result backend |
| `prometheus` | `9090` | Metrics scraping |
| `otel-collector` | `4317`, `4318` | Trace collection |
| `tempo` | `3200` | Trace backend |
| `loki` | `3100` | Log backend |
| `grafana` | `3001` | Observability UI |

## Data Persistence

Docker volumes:

- `mongo_data`: MongoDB metadata and checkpoints
- `grafana_data`: Grafana state

Bind mounts:

- `./backend/vector_db:/app/vector_db`
- `./backend/uploads:/app/uploads`

To reset application data:

```powershell
docker compose down -v
Remove-Item -Recurse -Force backend\vector_db -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force backend\uploads -ErrorAction SilentlyContinue
```

Use care with deletion commands if you have uploaded documents you want to keep.

## Common Troubleshooting

### Docker says `GEMINI_API_KEY` is missing

Create `.env` in the repository root:

```env
GEMINI_API_KEY=your_new_gemini_api_key_here
```

Then rerun:

```powershell
docker compose up --build
```

### First backend build is slow

Expected. The backend installs packages for:

- ChromaDB
- sentence transformers
- PyTorch transitive dependencies
- PDF/OCR processing
- LangGraph
- OpenTelemetry

### Frontend cannot reach backend

Confirm backend is running:

```text
http://localhost:8000/api/v1/health
```

The current frontend uses:

```text
http://localhost:8000
```

### Upload succeeds but query finds nothing

Possible causes:

- ingestion is still `PROCESSING`
- OCR failed
- the PDF contains images Tesseract cannot parse well
- the document does not contain the requested value
- Chroma vectors were reset

Check:

```http
GET /api/v1/documents
```

### Tesseract problems

The Docker backend installs `tesseract-ocr`.

For manual Windows development, `backend/ocr.py` expects:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

### Mongo unavailable

The backend can fall back for some repository behavior, but Mongo is required for the full Docker architecture and Mongo-backed LangGraph checkpointing.

### Redis unavailable

Queries should continue without cache. Latency may increase, and cache metrics/logs will show misses or failures.

### Grafana has no dashboards

Grafana is included as a service, but dashboards and data sources may need to be added manually. Use:

- Prometheus URL: `http://prometheus:9090`
- Tempo URL: `http://tempo:3200`
- Loki URL: `http://loki:3100`

## Interview Talking Points

This project demonstrates:

- async FastAPI route design
- typed API contracts with Pydantic
- route/service/repository boundaries
- background document ingestion
- Celery, Redis, and background worker architecture
- job IDs, retry policy, and failed ingestion status
- content-hash duplicate protection with a database uniqueness guarantee
- MongoDB schema and indexing concepts tied to access patterns
- Redis graceful degradation
- Chroma vector retrieval
- structured LLM output validation
- retries and timeouts around LLM calls
- MCP-style internal tool registry
- LangGraph stateful workflow orchestration
- persistent checkpoints with `thread_id`
- conditional graph routing
- retriever/verifier retry loop
- human-in-the-loop interrupt/resume
- SSE streaming
- Prometheus metrics
- OpenTelemetry tracing
- Grafana/Tempo/Loki observability architecture
- privacy-aware telemetry for medical documents
- golden dataset evaluation
- unit, integration, and contract test organization

## Known Gaps And Future Work

The repo is now a strong practice architecture, but it is not a finished production medical platform.

Useful next steps:

- add authentication and user-level document isolation
- add real rate limiting middleware
- add idempotency-key storage for uploads
- add automated Grafana datasource and dashboard provisioning
- add Langfuse self-host service to Compose
- add explicit PII redaction before logging and tracing
- add provider-swappable embedding service
- add robust document deletion from both MongoDB and Chroma
- add more golden evaluation cases
- add end-to-end browser tests

At this point, avoid adding more tools just for breadth. The most valuable improvements are hardening the pieces already present.
