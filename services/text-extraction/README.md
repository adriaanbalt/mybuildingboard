# Text Extraction Service

GCP Cloud Function for extracting text from email attachments and chunking them for embedding generation.

## Overview

This service implements Phase 2.2: Attachment Processing from the technical roadmap. It:

- Extracts text from various file formats (PDF, DOCX, DOC, images, TXT)
- Chunks extracted text into segments (~500-1000 tokens)
- Stores chunks in the database for embedding generation
- Updates attachment metadata with processing results

## Supported Formats

- **PDF** - PyMuPDF (fitz)
- **DOCX** - python-docx
- **DOC** - LibreOffice conversion
- **Images** - pytesseract OCR (PNG, JPEG, GIF, BMP, TIFF)
- **TXT** - Direct text reading

## Architecture

### Provider-Agnostic Design

The service uses the `TextExtractionService` interface, enabling easy addition of new extractors:

- **PDFExtractor** - PDF text extraction
- **DOCXExtractor** - DOCX text extraction
- **DOCExtractor** - Legacy DOC conversion
- **ImageExtractor** - OCR for images
- **TXTExtractor** - Plain text files

### Components

- **`TextExtractionService` Interface** - Provider-agnostic interface
- **Extractors** - Format-specific implementations
- **`TextExtractionFactory`** - Factory for selecting appropriate extractor
- **`chunking.py`** - Text chunking utilities
- **`main.py`** - Cloud Function entry point

## Setup

### Prerequisites

- GCP project with Cloud Functions enabled
- Supabase project with database schema deployed
- GCP Cloud Storage bucket for attachments
- LibreOffice installed (for DOC conversion)
- Tesseract OCR installed (for image OCR)

### Environment Variables

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# GCP
GCP_PROJECT_ID=your-gcp-project-id
STORAGE_BUCKET=email-attachments

# Chunking Configuration
CHUNK_SIZE=800  # tokens per chunk
CHUNK_OVERLAP=200  # tokens overlap between chunks
```

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install system dependencies (for DOC conversion and OCR)
# Ubuntu/Debian:
sudo apt-get install libreoffice tesseract-ocr

# macOS:
brew install libreoffice tesseract
```

### Deployment

```bash
# Deploy to GCP Cloud Functions
gcloud functions deploy extract-attachments \
  --runtime python311 \
  --trigger-bucket email-attachments \
  --memory 2GB \
  --timeout 540s \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...,GCP_PROJECT_ID=...
```

## Usage

The Cloud Function is automatically triggered when files are uploaded to the configured Cloud Storage bucket.

### Processing Flow

1. **File Upload** - Attachment uploaded to Cloud Storage by email ingestion service
2. **Event Trigger** - Cloud Function triggered by storage event
3. **Download File** - File downloaded from Cloud Storage
4. **Extract Text** - Text extracted using appropriate extractor
5. **Chunk Text** - Text chunked into segments (~500-1000 tokens)
6. **Store Chunks** - Chunks stored in `document_chunks` table
7. **Update Status** - Attachment status updated to 'completed'

### Chunking Strategy

- **Chunk Size:** ~800 tokens (configurable)
- **Overlap:** ~200 tokens between chunks (configurable)
- **Preserve Sentences:** Yes (chunks break at sentence boundaries)
- **Preserve Paragraphs:** Optional (can be enabled)

## Testing

```bash
# Local testing
python main.py

# Test with specific file
python -c "
from src.factory.text_extraction_factory import TextExtractionFactory
factory = TextExtractionFactory()
with open('test.pdf', 'rb') as f:
    text = factory.extract_text(f.read(), 'application/pdf', 'test.pdf')
    print(text[:500])
"
```

## Error Handling

- **Unsupported Formats:** Returns error, logs to database
- **Corrupted Files:** Handles gracefully, logs error
- **Large Files:** Processes in memory (consider streaming for very large files)
- **Extraction Failures:** Updates attachment status to 'failed', logs error

## Processing Logs

All processing results are logged to the `processing_logs` table with:
- Function name: `extract-attachments`
- Status: `success` or `failed`
- App ID, Email ID, Attachment ID
- Chunk count (if successful)
- Processing time
- Error message (if failed)

## TODO

- [ ] Add streaming support for very large files
- [ ] Add support for more formats (XLSX, PPTX, etc.)
- [ ] Improve OCR accuracy with image preprocessing
- [ ] Add unit tests
- [ ] Add integration tests
- [ ] Add performance monitoring
- [ ] Add retry logic for transient failures

## Related Documentation

- [Attachment Processing Checklist](../../app/docs/technical-roadmap/checklists/07-attachment-processing-checklist.md)
- [Service Interfaces Specification](../../app/docs/technical-roadmap/specs/service-interfaces-specification.md)
