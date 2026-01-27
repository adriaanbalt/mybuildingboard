"""
OpenAI Embedding Service

Implements EmbeddingService interface for OpenAI embeddings API.
"""

import logging
from typing import List, Optional
import openai
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ..interfaces.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class OpenAIEmbeddingService(EmbeddingService):
    """
    OpenAI embedding service implementation.
    
    Uses OpenAI's text-embedding-3-small model (1536 dimensions).
    """

    DEFAULT_MODEL = 'text-embedding-3-small'
    DEFAULT_DIMENSIONS = 1536
    MAX_BATCH_SIZE = 2048  # OpenAI's max batch size
    MAX_TEXT_LENGTH = 8000  # Approximate max tokens (model limit is 8191)

    def __init__(
        self,
        api_key: str,
        model: str = DEFAULT_MODEL,
        dimensions: Optional[int] = None,
        timeout: int = 30
    ):
        """
        Initialize OpenAI embedding service.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: text-embedding-3-small)
            dimensions: Number of dimensions (default: 1536 for text-embedding-3-small)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.model = model
        self.dimensions = dimensions or self.DEFAULT_DIMENSIONS
        self.timeout = timeout
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            Embedding vector as list of floats
            
        Raises:
            ValueError: If text is invalid
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        if len(text) > self.MAX_TEXT_LENGTH:
            raise ValueError(f"Text too long (max {self.MAX_TEXT_LENGTH} characters)")
        
        try:
            response = self._call_api([text])
            return response[0]
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
            
        Raises:
            ValueError: If any text is invalid
            Exception: If embedding generation fails
        """
        if not texts:
            return []
        
        # Validate texts
        for i, text in enumerate(texts):
            if not text or not text.strip():
                raise ValueError(f"Text at index {i} is empty")
            if len(text) > self.MAX_TEXT_LENGTH:
                raise ValueError(f"Text at index {i} is too long (max {self.MAX_TEXT_LENGTH} characters)")
        
        # Process in batches if needed
        all_embeddings = []
        for i in range(0, len(texts), self.MAX_BATCH_SIZE):
            batch = texts[i:i + self.MAX_BATCH_SIZE]
            try:
                batch_embeddings = self._call_api(batch)
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Failed to generate embeddings for batch {i}: {e}")
                raise
        
        return all_embeddings

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError))
    )
    def _call_api(self, texts: List[str]) -> List[List[float]]:
        """
        Call OpenAI embeddings API with retry logic.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions if self.model == 'text-embedding-3-small' else None
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            
            return embeddings
            
        except openai.RateLimitError as e:
            logger.warning(f"Rate limit exceeded, will retry: {e}")
            raise
        except openai.APIConnectionError as e:
            logger.warning(f"API connection error, will retry: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI API: {e}")
            raise

    def get_dimensions(self) -> int:
        """Get the dimension of embeddings."""
        return self.dimensions

    def get_provider_name(self) -> str:
        """Get provider name."""
        return 'openai'
