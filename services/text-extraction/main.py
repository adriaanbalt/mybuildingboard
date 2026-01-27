"""
Text Extraction Cloud Function

GCP Cloud Function to extract text from attachments and chunk them for embedding generation.
Triggered by Cloud Storage file upload events.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any
from google.cloud import storage
from supabase import create_client, Client

from src.factory.text_extraction_factory import TextExtractionFactory
from src.utils.chunking import chunk_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET', 'email-attachments')

# Chunking configuration
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '800'))  # tokens
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '200'))  # tokens


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_storage_client() -> storage.Client:
    """Get GCP Cloud Storage client."""
    return storage.Client(project=GCP_PROJECT_ID)


def download_file_from_storage(storage_client: storage.Client, storage_path: str) -> bytes:
    """
    Download file from Cloud Storage.
    
    Args:
        storage_client: GCP Storage client
        storage_path: Storage path (gs://bucket/path or bucket/path)
        
    Returns:
        File data as bytes
    """
    # Parse storage path
    if storage_path.startswith('gs://'):
        storage_path = storage_path[5:]  # Remove gs:// prefix
    
    parts = storage_path.split('/', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid storage path: {storage_path}")
    
    bucket_name, blob_path = parts
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)
    
    return blob.download_as_bytes()


def get_attachment_info(supabase: Client, attachment_id: str) -> Dict[str, Any]:
    """
    Get attachment information from database.
    
    Args:
        supabase: Supabase client
        attachment_id: Attachment ID
        
    Returns:
        Attachment record with email and app information
    """
    result = supabase.table('attachments').select(
        '*, emails(*, app_id)'
    ).eq('id', attachment_id).execute()
    
    if not result.data:
        raise ValueError(f"Attachment {attachment_id} not found")
    
    attachment = result.data[0]
    email = attachment.get('emails', {})
    
    return {
        'attachment': attachment,
        'email_id': attachment.get('email_id'),
        'app_id': email.get('app_id'),
        'storage_path': attachment.get('storage_path'),
        'filename': attachment.get('filename'),
        'content_type': attachment.get('content_type'),
    }


def store_chunks(
    supabase: Client,
    app_id: str,
    email_id: str,
    attachment_id: str,
    chunks: list
) -> int:
    """
    Store text chunks in database.
    
    Args:
        supabase: Supabase client
        app_id: App ID
        email_id: Email ID
        attachment_id: Attachment ID
        chunks: List of chunk dictionaries
        
    Returns:
        Number of chunks stored
    """
    if not chunks:
        return 0
    
    chunk_records = []
    for chunk in chunks:
        chunk_records.append({
            'app_id': app_id,
            'email_id': email_id,
            'attachment_id': attachment_id,
            'chunk_index': chunk['index'],
            'content': chunk['content'],
            'metadata': chunk.get('metadata', {}),
            'status': 'pending',  # Will be updated when embeddings are generated
        })
    
    # Insert chunks in batch
    result = supabase.table('document_chunks').insert(chunk_records).execute()
    
    return len(result.data) if result.data else 0


def update_attachment_status(
    supabase: Client,
    attachment_id: str,
    status: str,
    chunk_count: int = None,
    extracted_text: str = None,
    error_message: str = None
) -> None:
    """
    Update attachment status and metadata.
    
    Args:
        supabase: Supabase client
        attachment_id: Attachment ID
        status: New status ('processing', 'completed', 'failed')
        chunk_count: Number of chunks created
        extracted_text: Full extracted text (optional)
        error_message: Error message if failed
    """
    update_data = {
        'status': status,
        'processed_at': datetime.utcnow().isoformat(),
    }
    
    if chunk_count is not None:
        update_data['chunk_count'] = chunk_count
    
    if extracted_text is not None:
        # Store first 10000 characters of extracted text (optional, for preview)
        update_data['extracted_text'] = extracted_text[:10000] if len(extracted_text) > 10000 else extracted_text
    
    if error_message:
        update_data['error_message'] = error_message
    
    supabase.table('attachments').update(update_data).eq('id', attachment_id).execute()


def log_processing_result(
    supabase: Client,
    function_name: str,
    status: str,
    app_id: str = None,
    email_id: str = None,
    attachment_id: str = None,
    error: str = None,
    processing_time: float = None,
    chunk_count: int = None
) -> None:
    """
    Log processing result to processing_logs table.
    
    Args:
        supabase: Supabase client
        function_name: Function name
        status: Status ('success', 'failed')
        app_id: App ID (optional)
        email_id: Email ID (optional)
        attachment_id: Attachment ID (optional)
        error: Error message (optional)
        processing_time: Processing time in seconds (optional)
        chunk_count: Number of chunks created (optional)
    """
    try:
        log_record = {
            'function_name': function_name,
            'status': status,
            'app_id': app_id,
            'email_id': email_id,
            'attachment_id': attachment_id,
            'error_message': error,
            'processing_time_ms': int(processing_time * 1000) if processing_time else None,
            'metadata': {
                'chunk_count': chunk_count,
            } if chunk_count else None,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        supabase.table('processing_logs').insert(log_record).execute()
    except Exception as e:
        logger.error(f"Failed to log processing result: {e}")


def extract_attachment(event, context):
    """
    Cloud Function entry point for attachment text extraction.
    
    Triggered by Cloud Storage file upload events.
    
    Args:
        event: Cloud Storage event
        context: Cloud Function context
    """
    start_time = datetime.utcnow()
    
    try:
        # Get file information from event
        bucket_name = event['bucket']
        file_path = event['name']
        
        logger.info(f"Processing attachment: gs://{bucket_name}/{file_path}")
        
        # Initialize clients
        supabase = get_supabase_client()
        storage_client = get_storage_client()
        
        # Find attachment record by storage path
        storage_path = f"gs://{bucket_name}/{file_path}"
        result = supabase.table('attachments').select('id, email_id, emails(app_id)').eq('storage_path', storage_path).execute()
        
        if not result.data:
            logger.warning(f"No attachment record found for {storage_path}, skipping")
            return {'status': 'skipped', 'reason': 'no_attachment_record'}
        
        attachment_record = result.data[0]
        attachment_id = attachment_record['id']
        email_id = attachment_record['email_id']
        email = attachment_record.get('emails', {})
        app_id = email.get('app_id')
        
        if not app_id:
            logger.warning(f"No app_id found for attachment {attachment_id}, skipping")
            return {'status': 'skipped', 'reason': 'no_app_id'}
        
        # Get attachment info
        attachment_info = get_attachment_info(supabase, attachment_id)
        filename = attachment_info['filename']
        content_type = attachment_info['content_type']
        
        # Update status to processing
        update_attachment_status(supabase, attachment_id, 'processing')
        
        # Download file from storage
        file_data = download_file_from_storage(storage_client, storage_path)
        
        # Extract text using factory
        factory = TextExtractionFactory()
        extracted_text = factory.extract_text(file_data, content_type, filename)
        
        if not extracted_text.strip():
            logger.warning(f"No text extracted from {filename}")
            update_attachment_status(supabase, attachment_id, 'completed', chunk_count=0)
            log_processing_result(
                supabase,
                'extract-attachments',
                'success',
                app_id=app_id,
                email_id=email_id,
                attachment_id=attachment_id,
                processing_time=(datetime.utcnow() - start_time).total_seconds(),
                chunk_count=0
            )
            return {'status': 'success', 'chunk_count': 0, 'reason': 'no_text'}
        
        # Chunk text
        chunks = chunk_text(
            extracted_text,
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            preserve_sentences=True,
            preserve_paragraphs=False
        )
        
        logger.info(f"Created {len(chunks)} chunks from {filename}")
        
        # Store chunks in database
        chunk_count = store_chunks(supabase, app_id, email_id, attachment_id, chunks)
        
        # Update attachment status
        update_attachment_status(
            supabase,
            attachment_id,
            'completed',
            chunk_count=chunk_count,
            extracted_text=extracted_text
        )
        
        # Log success
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        log_processing_result(
            supabase,
            'extract-attachments',
            'success',
            app_id=app_id,
            email_id=email_id,
            attachment_id=attachment_id,
            processing_time=processing_time,
            chunk_count=chunk_count
        )
        
        logger.info(f"Successfully processed attachment {attachment_id}: {chunk_count} chunks created")
        
        return {
            'status': 'success',
            'attachment_id': attachment_id,
            'chunk_count': chunk_count,
            'processing_time': processing_time
        }
        
    except ValueError as e:
        # Unsupported format or missing data
        logger.error(f"Validation error: {e}")
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Try to update attachment status if we have the ID
        try:
            if 'attachment_id' in locals():
                update_attachment_status(
                    supabase if 'supabase' in locals() else get_supabase_client(),
                    attachment_id,
                    'failed',
                    error_message=str(e)
                )
                log_processing_result(
                    supabase if 'supabase' in locals() else get_supabase_client(),
                    'extract-attachments',
                    'failed',
                    attachment_id=attachment_id,
                    error=str(e),
                    processing_time=processing_time
                )
        except:
            pass
        
        return {'status': 'failed', 'error': str(e)}
        
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error processing attachment: {e}", exc_info=True)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Try to log error
        try:
            if 'attachment_id' in locals() and 'supabase' in locals():
                update_attachment_status(
                    supabase,
                    attachment_id,
                    'failed',
                    error_message=str(e)
                )
                log_processing_result(
                    supabase,
                    'extract-attachments',
                    'failed',
                    attachment_id=attachment_id,
                    error=str(e),
                    processing_time=processing_time
                )
        except:
            pass
        
        raise


# For local testing
if __name__ == '__main__':
    # Mock event for testing
    class MockEvent:
        def __init__(self):
            self.bucket = STORAGE_BUCKET
            self.name = 'attachments/test-email-id/test-attachment-id/test.pdf'
    
    class MockContext:
        pass
    
    result = extract_attachment(MockEvent(), MockContext())
    print(json.dumps(result, indent=2))
