"""
Vector Search Service

Wrapper for vector search using Supabase.
"""

import os
from typing import List, Optional
from supabase import create_client, Client
import logging

logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def get_supabase_client() -> Client:
    """Get Supabase client."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


async def search_similar_chunks(
    query_embedding: List[float],
    app_id: str,
    top_k: int = 5,
    similarity_threshold: float = 0.0,
    email_id: Optional[str] = None,
    attachment_id: Optional[str] = None
) -> List[dict]:
    """
    Search for similar chunks using vector similarity.
    
    Args:
        query_embedding: Query embedding vector
        app_id: App ID for tenant isolation
        top_k: Number of results to return
        similarity_threshold: Minimum similarity score
        email_id: Optional email ID filter
        attachment_id: Optional attachment ID filter
        
    Returns:
        List of search results with similarity scores
    """
    supabase = get_supabase_client()
    
    # Convert embedding to pgvector format
    embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
    
    # Call Postgres RPC function
    result = supabase.rpc('search_similar_chunks', {
        'query_embedding': embedding_str,
        'p_app_id': app_id,
        'p_top_k': top_k,
        'p_similarity_threshold': similarity_threshold,
        'p_email_id': email_id,
        'p_attachment_id': attachment_id,
    }).execute()
    
    if result.data:
        return result.data
    return []
