"""
QueryService Factory

Factory for creating QueryService instances based on provider type.
"""

import os
import logging
from typing import Dict, Any

from app.interfaces.query_service import QueryService
from app.providers.openai_query_service import OpenAIQueryService

logger = logging.getLogger(__name__)


def create_query_service(
    provider_type: str = None,
    config: Dict[str, Any] = None
) -> QueryService:
    """
    Create QueryService instance based on provider type.
    
    Args:
        provider_type: Provider type ("openai", "anthropic", etc.)
                      Defaults to QUERY_PROVIDER env var or "openai"
        config: Optional configuration dict
        
    Returns:
        QueryService instance
        
    Raises:
        ValueError: If provider type is not supported
    """
    if provider_type is None:
        provider_type = os.getenv("QUERY_PROVIDER", "openai")
    
    if config is None:
        config = {}
    
    provider_type = provider_type.lower()
    
    if provider_type == "openai":
        return OpenAIQueryService(
            api_key=config.get("api_key"),
            model=config.get("model", os.getenv("OPENAI_MODEL", "gpt-4")),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 60)
        )
    elif provider_type == "anthropic":
        # TODO: Implement AnthropicQueryService when needed
        raise NotImplementedError("Anthropic provider not yet implemented")
    else:
        raise ValueError(f"Unsupported query provider: {provider_type}")
