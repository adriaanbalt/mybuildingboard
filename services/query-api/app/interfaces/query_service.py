"""
QueryService Interface

Provider-agnostic interface for LLM query services (OpenAI GPT-4, Claude, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class TokenUsage:
    """Token usage statistics."""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_usd: Optional[float] = None  # Estimated cost in USD


@dataclass
class QueryResult:
    """Result from query processing."""
    answer: str
    token_usage: TokenUsage
    model: str
    metadata: Optional[Dict[str, Any]] = None


class QueryService(ABC):
    """
    Abstract interface for LLM query services.
    
    Enables provider-agnostic code, making it easy to swap providers
    (e.g., OpenAI → Anthropic) without refactoring application code.
    """
    
    @abstractmethod
    def process_query(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> QueryResult:
        """
        Process a query with context using LLM.
        
        Args:
            query: User query text
            context_chunks: Retrieved context chunks with metadata
            conversation_history: Optional conversation history for context
            
        Returns:
            QueryResult with answer, token usage, and metadata
            
        Raises:
            Exception: If query processing fails
        """
        pass
    
    @abstractmethod
    def get_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Get answer text only (simplified method).
        
        Args:
            query: User query text
            context_chunks: Retrieved context chunks with metadata
            conversation_history: Optional conversation history for context
            
        Returns:
            Answer text
            
        Raises:
            Exception: If answer generation fails
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get provider name (e.g., "openai", "anthropic").
        
        Returns:
            Provider name
        """
        pass
