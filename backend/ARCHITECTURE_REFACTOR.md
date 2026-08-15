# AI Document Intelligence Backend Refactor

This backend keeps the medical-document RAG use case and restructures the implementation around production boundaries:

```text
route -> service -> agent/tool -> repository -> infrastructure
```

## API

- `GET /api/v1/health`
- `POST /api/v1/documents`
- `GET /api/v1/documents`
- `GET /api/v1/documents/{document_id}`
- `DELETE /api/v1/documents`
- `POST /api/v1/queries`
- `POST /api/v1/queries/stream`
- `POST /api/v1/queries/resume`
- `GET /api/v1/queries/{thread_id}/state`
- `GET /api/v1/metrics`
- `POST /api/v1/evaluations/golden`

The original React-compatible endpoints still exist:

- `POST /upload`
- `POST /query`
- `DELETE /delete-document`

## Data Responsibilities

- MongoDB stores document metadata, conversations, messages, AI runs, and evaluations.
- Chroma stores embeddings and retrieval metadata.
- Redis is used as a best-effort query cache. If Redis is unavailable, queries continue without cache.

Document uploads now use SHA-256 checksums and a unique MongoDB index instead of filename-only duplicate checks.

## LangGraph Agent Workflow

The query flow now runs as a LangGraph `StateGraph`, compiled with a checkpointer. Each request passes a
`thread_id` through `config={"configurable": {"thread_id": ...}}`, so graph state can be inspected and resumed.

```text
START
  -> classify_query
  -> retrieve_documents
  -> verify_evidence
     -> rewrite_query -> retrieve_documents
     -> human_review -> generate_answer
     -> insufficient_evidence
  -> generate_answer
  -> validate_answer
  -> END
```

`LANGGRAPH_CHECKPOINTER=mongo` plus `MONGODB_URL` stores checkpoints in MongoDB. Local development falls back to
`InMemorySaver`.

The tool layer exposes MCP-style definitions with names, descriptions, and JSON schemas:

- `search_documents`
- `get_document_metadata`
- `list_uploaded_documents`

## Failure Handling

- Request IDs are added to every response.
- API errors use `ErrorResponse`.
- LLM calls use timeout and retry handling.
- Invalid LLM JSON gets one structured-output retry.
- Redis and Mongo startup failures degrade to in-memory/no-cache behavior where possible.
- Document ingestion marks documents `FAILED` instead of `READY` if parsing, chunking, embedding, or vector writes fail.
- Suspicious prompt-injection-like content routes to a human-review interrupt and can be resumed through
  `POST /api/v1/queries/resume`.
- Low evidence scores trigger a bounded retrieval rewrite loop before returning an insufficient-evidence response.

## Observability

- Prometheus metrics are exposed at `/api/v1/metrics`.
- OpenTelemetry spans are emitted when `OTEL_EXPORTER_OTLP_ENDPOINT` is configured.
- Langfuse traces are enabled when `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are configured.
- Telemetry records request IDs, thread IDs, counts, timing, statuses, and scores. It intentionally avoids raw medical
  document text and full prompts.
