"""
Embedding Generation Cloud Function

GCP Cloud Function to generate embeddings for document chunks and store them in the database.
Triggered by Pub/Sub (on chunk creation) or Cloud Scheduler.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, List
from supabase import create_client, Client
import numpy as np

from src.factory.embedding_service_factory import EmbeddingServiceFactory
from src.interfaces.embedding_service import EmbeddingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
EMBEDDING_PROVIDER = os.environ.get('EMBEDDING_PROVIDER', 'openai')
EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'text-embedding-3-small')
BATCH_SIZE = int(os.environ.get('BATCH_SIZE', '100'))  # Process chunks in batches


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("Supabase URL and key must be set")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_embedding_service() -> EmbeddingService:
    """Get embedding service instance."""
    config = {
        'api_key': OPENAI_API_KEY,
        'model': EMBEDDING_MODEL,
        'dimensions': 1536,  # text-embedding-3-small dimensions
        'timeout': 30,
    }
    return EmbeddingServiceFactory.create(EMBEDDING_PROVIDER, config)


def get_pending_chunks(supabase: Client, limit: int = None) -> List[Dict[str, Any]]:
    """
    Get chunks that need embeddings (status = 'pending').
    
    Args:
        supabase: Supabase client
        limit: Maximum number of chunks to retrieve (None for all)
        
    Returns:
        List of chunk records
    """
    query = supabase.table('document_chunks').select('*').eq('status', 'pending')
    
    if limit:
        query = query.limit(limit)
    
    result = query.execute()
    return result.data if result.data else []


def update_chunk_embedding(
    supabase: Client,
    chunk_id: str,
    embedding: List[float],
    status: str = 'completed'
) -> None:
    """
    Update chunk with embedding vector.
    
    Args:
        supabase: Supabase client
        chunk_id: Chunk ID
        embedding: Embedding vector
        status: New status ('completed' or 'failed')
    """
    # Convert embedding to string format for pgvector
    # pgvector expects format: '[0.1,0.2,0.3,...]'
    embedding_str = '[' + ','.join(map(str, embedding)) + ']'
    
    update_data = {
        'embedding': embedding_str,
        'status': status,
        'processed_at': datetime.utcnow().isoformat(),
    }
    
    supabase.table('document_chunks').update(update_data).eq('id', chunk_id).execute()


def process_batch(
    embedding_service: EmbeddingService,
    supabase: Client,
    chunks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Process a batch of chunks.
    
    Args:
        embedding_service: Embedding service instance
        supabase: Supabase client
        chunks: List of chunk records
        
    Returns:
        Result dictionary with success count and errors
    """
    if not chunks:
        return {'success': 0, 'failed': 0, 'errors': []}
    
    # Extract texts and IDs
    texts = [chunk['content'] for chunk in chunks]
    chunk_ids = [chunk['id'] for chunk in chunks]
    
    try:
        # Generate embeddings in batch
        embeddings = embedding_service.generate_embeddings(texts)
        
        # Update chunks with embeddings
        success_count = 0
        errors = []
        
        for i, (chunk_id, embedding) in enumerate(zip(chunk_ids, embeddings)):
            try:
                update_chunk_embedding(supabase, chunk_id, embedding, 'completed')
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to update chunk {chunk_id}: {e}")
                errors.append({'chunk_id': chunk_id, 'error': str(e)})
                # Mark chunk as failed
                try:
                    update_chunk_embedding(supabase, chunk_id, [], 'failed')
                except:
                    pass
        
        return {
            'success': success_count,
            'failed': len(errors),
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Failed to generate embeddings for batch: {e}")
        # Mark all chunks as failed
        for chunk_id in chunk_ids:
            try:
                update_chunk_embedding(supabase, chunk_id, [], 'failed')
            except:
                pass
        
        return {
            'success': 0,
            'failed': len(chunks),
            'errors': [{'error': str(e)}]
        }


def log_processing_result(
    supabase: Client,
    function_name: str,
    status: str,
    app_id: str = None,
    email_id: str = None,
    attachment_id: str = None,
    error: str = None,
    processing_time: float = None,
    chunks_processed: int = None,
    batch_count: int = None
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
        chunks_processed: Number of chunks processed (optional)
        batch_count: Number of batches processed (optional)
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
                'chunks_processed': chunks_processed,
                'batch_count': batch_count,
            } if chunks_processed or batch_count else None,
            'created_at': datetime.utcnow().isoformat(),
        }
        
        supabase.table('processing_logs').insert(log_record).execute()
    except Exception as e:
        logger.error(f"Failed to log processing result: {e}")


def generate_embeddings(event, context):
    """
    Cloud Function entry point for embedding generation.
    
    Triggered by Pub/Sub (on chunk creation) or Cloud Scheduler (periodic).
    
    Args:
        event: Pub/Sub event or Cloud Scheduler event
        context: Cloud Function context
    """
    start_time = datetime.utcnow()
    total_success = 0
    total_failed = 0
    
    try:
        # Initialize clients
        supabase = get_supabase_client()
        embedding_service = get_embedding_service()
        
        # Get pending chunks
        chunks = get_pending_chunks(supabase, limit=None)  # Process all pending chunks
        
        if not chunks:
            logger.info("No pending chunks to process")
            return {'status': 'success', 'chunks_processed': 0, 'message': 'no_pending_chunks'}
        
        logger.info(f"Processing {len(chunks)} pending chunks")
        
        # Process chunks in batches
        batch_count = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_count += 1
            
            logger.info(f"Processing batch {batch_count} ({len(batch)} chunks)")
            
            result = process_batch(embedding_service, supabase, batch)
            total_success += result['success']
            total_failed += result['failed']
            
            if result['errors']:
                logger.warning(f"Batch {batch_count} had {len(result['errors'])} errors")
        
        # Log summary
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(
            f"Embedding generation complete: {total_success} succeeded, "
            f"{total_failed} failed (took {processing_time:.2f}s)"
        )
        
        # Log processing result
        log_processing_result(
            supabase,
            'generate-embeddings',
            'success',
            processing_time=processing_time,
            chunks_processed=total_success,
            batch_count=batch_count
        )
        
        return {
            'status': 'success',
            'chunks_processed': total_success,
            'chunks_failed': total_failed,
            'batch_count': batch_count,
            'processing_time': processing_time
        }
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}", exc_info=True)
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Try to log error
        try:
            log_processing_result(
                supabase if 'supabase' in locals() else get_supabase_client(),
                'generate-embeddings',
                'failed',
                error=str(e),
                processing_time=processing_time
            )
        except:
            pass
        
        raise


# For local testing
if __name__ == '__main__':
    class MockEvent:
        pass
    
    class MockContext:
        pass
    
    result = generate_embeddings(MockEvent(), MockContext())
    print(json.dumps(result, indent=2))
