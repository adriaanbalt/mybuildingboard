# Embedding Generation Service

GCP Cloud Function for generating vector embeddings for document chunks and storing them in the database.

## Overview

This service implements Phase 2.3: Embedding Generation Pipeline from the technical roadmap. It:

- Generates embeddings for document chunks using OpenAI (or alternative providers)
- Processes chunks in batches for efficiency
- Stores embeddings in the database (pgvector format)
- Handles errors and retries with exponential backoff
- Logs processing results for monitoring

## Architecture

### Provider-Agnostic Design

The service uses the `EmbeddingService` interface, enabling easy swapping of embedding providers:

- **OpenAIEmbeddingService** - OpenAI text-embedding-3-small (✅ Implemented)
- **CohereEmbeddingService** - Cohere embeddings (⏳ TODO)
- **HuggingFaceEmbeddingService** - Hugging Face models (⏳ TODO)

### Components

- **`EmbeddingService` Interface** - Provider-agnostic interface
- **`OpenAIEmbeddingService`** - OpenAI implementation
- **`EmbeddingServiceFactory`** - Factory for creating provider instances
- **`main.py`** - Cloud Function entry point

## Setup

### Prerequisites

- GCP project with Cloud Functions enabled
- Supabase project with database schema deployed (pgvector extension enabled)
- OpenAI API key (or alternative provider credentials)

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# OpenAI
OPENAI_API_KEY=sk-your-api-key

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
BATCH_SIZE=100  # Process chunks in batches
```

### Deployment

```bash
# Deploy to GCP Cloud Functions
gcloud functions deploy generate-embeddings \
  --runtime python311 \
  --trigger-topic embedding-generation \
  --memory 512MB \
  --timeout 540s \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,OPENAI_API_KEY=...
```

### Cloud Scheduler Setup

```bash
# Set up Cloud Scheduler trigger (every 5 minutes)
gcloud scheduler jobs create pubsub embedding-generation-trigger \
  --schedule="*/5 * * * *" \
  --topic=embedding-generation \
  --message-body='{"trigger": "scheduler"}'
```

## Usage

The Cloud Function is triggered by:
- **Pub/Sub** - When chunks are created (recommended)
- **Cloud Scheduler** - Periodic processing (every 5 minutes)

### Processing Flow

1. **Get Pending Chunks** - Retrieves chunks with status 'pending' from database
2. **Batch Processing** - Processes chunks in batches (default: 100)
3. **Generate Embeddings** - Calls embedding API for each batch
4. **Store Embeddings** - Updates chunks with embedding vectors (pgvector format)
5. **Update Status** - Sets chunk status to 'completed' or 'failed'
6. **Log Results** - Logs processing results to `processing_logs` table

### Embedding Model

- **Model:** `text-embedding-3-small` (default)
- **Dimensions:** 1536
- **Cost:** ~$0.02 per 1M tokens
- **Max Text Length:** ~8000 characters

## Error Handling

- **Rate Limits:** Automatic retry with exponential backoff (up to 3 attempts)
- **Network Errors:** Automatic retry with exponential backoff
- **Invalid Text:** Chunk marked as 'failed', error logged
- **API Errors:** Chunk marked as 'failed', error logged

## Cost Monitoring

The service logs processing results including:
- Number of chunks processed
- Number of batches
- Processing time

Cost can be calculated from:
- Tokens processed (approximate: ~4 characters per token)
- OpenAI pricing: $0.02 per 1M tokens

## Performance

- **Batch Size:** Default 100 chunks per batch (configurable)
- **Parallel Processing:** OpenAI API handles batching internally
- **Database Updates:** Batch updates for efficiency

## Testing

```bash
# Local testing
python main.py

# Test with specific chunks
python -c "
from src.factory.embedding_service_factory import EmbeddingServiceFactory
factory = EmbeddingServiceFactory()
service = factory.create('openai', {'api_key': 'sk-...'})
embedding = service.generate_embedding('Test text')
print(f'Dimensions: {len(embedding)}')
"
```

## TODO

- [ ] Add Cohere provider support
- [ ] Add Hugging Face provider support
- [ ] Add mock provider for testing
- [ ] Add cost tracking per app
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add performance monitoring
- [ ] Add Pub/Sub trigger setup

## Related Documentation

- [Embedding Generation Checklist](../../app/docs/technical-roadmap/checklists/08-embedding-generation-checklist.md)
- [Service Interfaces Specification](../../app/docs/technical-roadmap/specs/service-interfaces-specification.md)
