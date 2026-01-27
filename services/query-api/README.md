# Query Processing API

FastAPI service for processing RAG queries with vector search and LLM integration.

## Overview

This service implements Phase 3.2: Query Processing API from the technical roadmap. It:

- Processes user queries using RAG (Retrieval Augmented Generation)
- Generates query embeddings
- Performs vector similarity search
- Generates answers using LLM with context
- Returns answers with source citations

## Architecture

### Components

- **FastAPI Application** - Main API server
- **Authentication Middleware** - Supabase JWT validation
- **Query Endpoint** - `/api/query` for processing queries
- **Embedding Service** - Query embedding generation
- **Vector Search Service** - Similarity search integration
- **LLM Service** - Answer generation with OpenAI

## Setup

### Prerequisites

- Python 3.11+
- Supabase project with database schema deployed
- OpenAI API key
- Supabase JWT secret

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# OpenAI
OPENAI_API_KEY=sk-your-api-key
OPENAI_MODEL=gpt-4

# CORS
ALLOWED_ORIGINS=https://localhost:3000,https://your-domain.com
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
# Run with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or with Python
python -m uvicorn app.main:app --reload
```

### Deployment

```bash
# Deploy to GCP Cloud Run
gcloud run deploy query-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,OPENAI_API_KEY=...
```

## API Endpoints

### POST /api/query

Process a query using RAG.

**Request:**
```json
{
  "query": "What is the building code for fire exits?",
  "app_id": "optional-if-in-header",
  "top_k": 5,
  "similarity_threshold": 0.0,
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "According to the building code...",
  "sources": [
    {
      "chunk_id": "...",
      "email_id": "...",
      "email_subject": "...",
      "similarity": 0.85,
      "content_preview": "..."
    }
  ],
  "query_id": "...",
  "processing_time_ms": 1234
}
```

**Authentication:**
- Requires Bearer token (Supabase JWT)
- Requires `x-app-id` header or app_id in request body
- User must be a member of the app

### GET /health

Health check endpoint.

## Query Processing Flow

1. **Authentication** - Validate JWT token and app membership
2. **Embedding Generation** - Generate embedding for query text
3. **Vector Search** - Find similar chunks using pgvector
4. **Context Retrieval** - Format top-k chunks as context
5. **LLM Generation** - Generate answer using GPT-4 with context
6. **Response Formatting** - Format answer with citations
7. **Query Logging** - Log query to database

## Error Handling

- **401 Unauthorized** - Invalid or missing token
- **403 Forbidden** - User not a member of app
- **400 Bad Request** - Invalid request parameters
- **500 Internal Server Error** - Processing failure

## Rate Limiting

Rate limiting is not yet implemented but should be added:
- Per app limits
- Per user limits
- Per IP limits (optional)

## Testing

```bash
# Test query endpoint
curl -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "x-app-id: YOUR_APP_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the building code?",
    "top_k": 5
  }'
```

## TODO

- [ ] Add rate limiting
- [ ] Add conversation history support
- [ ] Add caching for embeddings
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add performance monitoring
- [ ] Add request ID tracking

## Related Documentation

- [Query Processing API Checklist](../../app/docs/technical-roadmap/checklists/11-query-processing-api-checklist.md)
- [Service Interfaces Specification](../../app/docs/technical-roadmap/specs/service-interfaces-specification.md)
