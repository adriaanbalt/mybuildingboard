"""
Embedding Service

Wrapper for embedding generation using the embedding service.
"""

import os
import httpx
from typing import List
import logging

logger = logging.getLogger(__name__)

# Configuration
EMBEDDING_API_URL = os.getenv("EMBEDDING_API_URL", "http://localhost:8080")  # Embedding service URL
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def generate_query_embedding(query_text: str) -> List[float]:
    """
    Generate embedding for query text.
    
    Args:
        query_text: Query text
        
    Returns:
        Embedding vector (1536 dimensions)
        
    Raises:
        Exception: If embedding generation fails
    """
    # For now, call OpenAI directly
    # TODO: Use embedding service API when available
    import openai
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required")
    
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        response = await client.embeddings.create(
            model="text-embedding-3-small",
            input=query_text,
            dimensions=1536
        )
        
        return response.data[0].embedding
        
    except Exception as e:
        logger.error(f"Failed to generate query embedding: {e}")
        raise Exception(f"Embedding generation failed: {str(e)}")
