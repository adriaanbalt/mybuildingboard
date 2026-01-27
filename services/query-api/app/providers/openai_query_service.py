"""
OpenAI QueryService Implementation

OpenAI GPT-4 implementation of QueryService interface.
"""

import os
import logging
from typing import List, Dict, Any, Optional
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)

from app.interfaces.query_service import QueryService, QueryResult, TokenUsage

logger = logging.getLogger(__name__)

# OpenAI pricing (as of 2024, adjust as needed)
# GPT-4: $0.03 per 1K input tokens, $0.06 per 1K output tokens
OPENAI_PRICING = {
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
}


class OpenAIQueryService(QueryService):
    """
    OpenAI implementation of QueryService.
    
    Uses OpenAI GPT-4 for query processing with retry logic,
    token tracking, and cost monitoring.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        timeout: int = 60
    ):
        """
        Initialize OpenAI QueryService.
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            model: Model to use (default: gpt-4)
            temperature: Sampling temperature (default: 0.7)
            max_tokens: Maximum tokens in response (default: 1000)
            timeout: Request timeout in seconds (default: 60)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required (set OPENAI_API_KEY env var)")
        
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        
        self.client = openai.AsyncOpenAI(api_key=self.api_key, timeout=self.timeout)
    
    def get_provider_name(self) -> str:
        """Get provider name."""
        return "openai"
    
    def _create_prompt(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Create prompt for LLM with context.
        
        Args:
            query: User query
            context_chunks: Retrieved context chunks
            conversation_history: Optional conversation history
            
        Returns:
            Formatted prompt
        """
        # Format context chunks
        context_text = "\n\n".join([
            f"[Source {i+1}]\n{chunk.get('content', '')}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Format conversation history if provided
        history_text = ""
        if conversation_history:
            history_text = "\n\nPrevious conversation:\n" + "\n".join([
                f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}"
                for msg in conversation_history[-3:]  # Last 3 exchanges
            ])
        
        prompt = f"""You are a helpful assistant that answers questions based on the provided context from email documents and attachments.

Context:
{context_text}
{history_text}

Question: {query}

Instructions:
- Answer the question based only on the provided context
- If the context doesn't contain enough information, say so
- Cite sources using [Source 1], [Source 2], etc. in your answer
- Be concise and accurate
- If you're unsure, indicate that

Answer:"""
        
        return prompt
    
    def _calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int
    ) -> float:
        """
        Calculate estimated cost in USD.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in USD
        """
        pricing = OPENAI_PRICING.get(self.model, OPENAI_PRICING["gpt-4"])
        input_cost = (input_tokens / 1000) * pricing["input"]
        output_cost = (output_tokens / 1000) * pricing["output"]
        return input_cost + output_cost
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((
            openai.RateLimitError,
            openai.APIConnectionError,
            openai.APITimeoutError
        )),
        reraise=True
    )
    async def _call_openai(
        self,
        prompt: str,
        system_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with retry logic.
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            
        Returns:
            OpenAI API response
            
        Raises:
            Exception: If API call fails after retries
        """
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            else:
                messages.append({
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context."
                })
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            return {
                "answer": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
            }
            
        except openai.RateLimitError as e:
            logger.warning(f"OpenAI rate limit error: {e}")
            raise
        except (openai.APIConnectionError, openai.APITimeoutError) as e:
            logger.warning(f"OpenAI connection/timeout error: {e}")
            raise
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise Exception(f"OpenAI API error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error calling OpenAI: {e}")
            raise Exception(f"Failed to call OpenAI: {str(e)}")
    
    async def process_query(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> QueryResult:
        """
        Process a query with context using OpenAI.
        
        Args:
            query: User query text
            context_chunks: Retrieved context chunks with metadata
            conversation_history: Optional conversation history for context
            
        Returns:
            QueryResult with answer, token usage, and metadata
            
        Raises:
            Exception: If query processing fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        if not context_chunks:
            raise ValueError("Context chunks cannot be empty")
        
        try:
            prompt = self._create_prompt(query, context_chunks, conversation_history)
            
            response = await self._call_openai(prompt)
            
            answer = response["answer"]
            if not answer:
                raise Exception("OpenAI returned empty response")
            
            usage = response["usage"]
            token_usage = TokenUsage(
                input_tokens=usage["prompt_tokens"],
                output_tokens=usage["completion_tokens"],
                total_tokens=usage["total_tokens"],
                cost_usd=self._calculate_cost(
                    usage["prompt_tokens"],
                    usage["completion_tokens"]
                )
            )
            
            return QueryResult(
                answer=answer,
                token_usage=token_usage,
                model=response["model"],
                metadata={
                    "provider": "openai",
                    "model": response["model"],
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
                }
            )
            
        except RetryError as e:
            logger.error(f"OpenAI query failed after retries: {e}")
            raise Exception(f"Query processing failed after retries: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to process query: {e}", exc_info=True)
            raise
    
    async def get_answer(
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
        result = await self.process_query(query, context_chunks, conversation_history)
        return result.answer
