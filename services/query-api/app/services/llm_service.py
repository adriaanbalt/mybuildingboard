"""
LLM Service

Integration with OpenAI GPT-4 for answer generation.
"""

import os
from typing import List, Dict
import openai
import logging

logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")


def create_prompt(query: str, context_chunks: List[Dict]) -> str:
    """
    Create prompt for LLM with context.
    
    Args:
        query: User query
        context_chunks: Retrieved context chunks
        
    Returns:
        Formatted prompt
    """
    # Format context chunks
    context_text = "\n\n".join([
        f"[Source {i+1}]\n{chunk['content']}"
        for i, chunk in enumerate(context_chunks)
    ])
    
    prompt = f"""You are a helpful assistant that answers questions based on the provided context from email documents and attachments.

Context:
{context_text}

Question: {query}

Instructions:
- Answer the question based only on the provided context
- If the context doesn't contain enough information, say so
- Cite sources using [Source 1], [Source 2], etc.
- Be concise and accurate
- If you're unsure, indicate that

Answer:"""
    
    return prompt


async def generate_answer(query: str, context_chunks: List[Dict]) -> str:
    """
    Generate answer using LLM with context.
    
    Args:
        query: User query
        context_chunks: Retrieved context chunks
        
    Returns:
        Generated answer text
        
    Raises:
        Exception: If LLM generation fails
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required")
    
    try:
        client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)
        
        prompt = create_prompt(query, context_chunks)
        
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000,
        )
        
        answer = response.choices[0].message.content
        
        if not answer:
            raise Exception("LLM returned empty response")
        
        return answer
        
    except Exception as e:
        logger.error(f"Failed to generate answer: {e}")
        raise Exception(f"Answer generation failed: {str(e)}")
