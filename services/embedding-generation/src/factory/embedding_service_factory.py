"""
Embedding Service Factory

Creates embedding service instances based on provider type.
"""

from typing import Dict, Any
from ..interfaces.embedding_service import EmbeddingService
from ..providers.openai_embedding_service import OpenAIEmbeddingService


class EmbeddingServiceFactory:
    """
    Factory for creating embedding service instances.
    
    Supports multiple providers: OpenAI, Cohere, Hugging Face, etc.
    """

    @staticmethod
    def create(provider_type: str, config: Dict[str, Any]) -> EmbeddingService:
        """
        Create embedding service instance based on provider type.
        
        Args:
            provider_type: Provider type ("openai", "cohere", "huggingface", etc.)
            config: Provider-specific configuration
            
        Returns:
            EmbeddingService instance
            
        Raises:
            ValueError: If provider type is unknown
        """
        if provider_type == "openai":
            return OpenAIEmbeddingService(
                api_key=config.get('api_key'),
                model=config.get('model', 'text-embedding-3-small'),
                dimensions=config.get('dimensions', 1536),
                timeout=config.get('timeout', 30)
            )
        elif provider_type == "cohere":
            # TODO: Implement CohereEmbeddingService
            raise NotImplementedError("Cohere provider not yet implemented")
        elif provider_type == "huggingface":
            # TODO: Implement HuggingFaceEmbeddingService
            raise NotImplementedError("Hugging Face provider not yet implemented")
        elif provider_type == "mock":
            # TODO: Implement MockEmbeddingService for testing
            raise NotImplementedError("Mock provider not yet implemented")
        else:
            raise ValueError(f"Unknown embedding provider: {provider_type}")
