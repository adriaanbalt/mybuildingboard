"""
Text Chunking Utilities

Chunks text into segments for embedding generation.
"""

import re
from typing import List, Dict, Any


def estimate_tokens(text: str) -> int:
    """
    Estimate token count for text (approximate).
    
    Uses a simple heuristic: ~4 characters per token (average for English).
    
    Args:
        text: Text to estimate
        
    Returns:
        Estimated token count
    """
    # Rough estimate: 4 characters per token
    return len(text) // 4


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 200,
    preserve_sentences: bool = True,
    preserve_paragraphs: bool = False
) -> List[Dict[str, Any]]:
    """
    Chunk text into segments for embedding generation.
    
    Args:
        text: Text to chunk
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        preserve_sentences: Try to preserve sentence boundaries
        preserve_paragraphs: Try to preserve paragraph boundaries
        
    Returns:
        List of chunk dictionaries with 'content', 'index', and 'metadata'
    """
    if not text.strip():
        return []
    
    # Split by paragraphs first if preserve_paragraphs is True
    if preserve_paragraphs:
        paragraphs = text.split('\n\n')
    else:
        paragraphs = [text]
    
    chunks = []
    chunk_index = 0
    current_chunk = ""
    
    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        
        # If preserving sentences, split by sentence boundaries
        if preserve_sentences:
            # Simple sentence splitting (period, exclamation, question mark followed by space)
            sentences = re.split(r'([.!?]\s+)', paragraph)
            # Rejoin sentences with their punctuation
            sentences = [sentences[i] + (sentences[i+1] if i+1 < len(sentences) else '') 
                        for i in range(0, len(sentences), 2)]
        else:
            sentences = [paragraph]
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_tokens = estimate_tokens(sentence)
            current_tokens = estimate_tokens(current_chunk)
            
            # If adding this sentence would exceed chunk size
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                # Save current chunk
                chunks.append({
                    'content': current_chunk.strip(),
                    'index': chunk_index,
                    'metadata': {
                        'token_count': current_tokens,
                        'char_count': len(current_chunk),
                    }
                })
                chunk_index += 1
                
                # Start new chunk with overlap
                if chunk_overlap > 0 and chunks:
                    # Get last chunk and use its end as overlap
                    last_chunk = chunks[-1]['content']
                    overlap_text = last_chunk[-chunk_overlap * 4:]  # Approximate overlap in chars
                    current_chunk = overlap_text + '\n\n' + sentence
                else:
                    current_chunk = sentence
            else:
                # Add sentence to current chunk
                if current_chunk:
                    current_chunk += '\n\n' + sentence
                else:
                    current_chunk = sentence
    
    # Add final chunk if there's remaining text
    if current_chunk.strip():
        chunks.append({
            'content': current_chunk.strip(),
            'index': chunk_index,
            'metadata': {
                'token_count': estimate_tokens(current_chunk),
                'char_count': len(current_chunk),
            }
        })
    
    return chunks
